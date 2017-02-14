define(function (require, exports, module) {
    "use strict";

    var $ = require('jqueryui'),
        IPython = require('base/js/namespace'),
        events = require('base/js/events'),
        utils = require('base/js/utils'),

        kill_and_exit = function () {
            var close = function () {
                var parent = utils.url_path_split(IPython.notebook.notebook_path)[0],
                    url = utils.url_path_join(IPython.notebook.base_url, 'tree', utils.encode_uri_components(parent));

                window.open(url, IPython._target);
            };

            // finish with close on success or failure
            IPython.notebook.session.delete(close, close);
        };

    Jupyter._target = '_self';

    /** Extending NotebookList class. */
    {
        var NotebookList = require('tree/js/notebooklist').NotebookList;

        NotebookList.prototype.parent_selection_changed = NotebookList.prototype._selection_changed;
        NotebookList.prototype.parent_add_link = NotebookList.prototype.add_link;
        NotebookList.prototype.parent_bind_events = NotebookList.prototype.bind_events;
        NotebookList.prototype.parent_new_item = NotebookList.prototype.new_item;

        NotebookList.prototype.bind_events = function () {
            this.parent_bind_events();
            // Bind events for action buttons.
            $('.shared-button').off('click').on('click', $.proxy(this.toggle_shared_selected, this));
        };

        NotebookList.prototype.toggle_shared_selected = function () {
            var that = this;
            this.selected.forEach(function (item) {
                if (item.type === 'notebook') {
                    that.contents.save(item.path, {
                        id: item.id,
                        shared: !item.shared
                    }).then(function () {
                        that.session_list.load_sessions();
                    })
                }
            });
        };

        NotebookList.prototype._selection_changed = function () {
            this.parent_selection_changed();

            var that = this,
                checked = 0,
                has_not_writable = false;

            $('.list_item :checked').each(function (index, item) {
                var parent = $(item).parent().parent(),
                    shared = parent.data('shared');

                // If the item doesn't have an upload button, isn't the
                // breadcrumbs and isn't the parent folder '..', then it can be selected.
                // Breadcrumbs path == ''.
                if (parent.find('.upload_button').length === 0 && parent.data('path') !== '' && parent.data('path') !== utils.url_path_split(that.notebook_path)[0]) {
                    checked++;
                    that.selected[index] = parent.data();
                    has_not_writable = has_not_writable || !that.selected[index].writable
                }
            });

            // Shared is only visible when one item is selected.
            if (checked > 0 && !has_not_writable) {
                $('.shared-button').css('display', 'inline-block');
            } else {
                $('.shared-button').css('display', 'none');
            }

            // Rename is only visible when one item is selected, it is not a running notebook and writable.
            if (checked === 1 && !this.is_running(this.selected[0]) && !has_not_writable) {
                $('.rename-button').css('display', 'inline-block');
            } else {
                $('.rename-button').css('display', 'none');
            }
        };

        NotebookList.prototype.is_running = function (model) {
            return (model.type === 'notebook' && this.sessions[model.path] !== undefined)
        };

        NotebookList.prototype.add_link = function (model, item) {
            var running = this.is_running(model);

            this.parent_add_link(model, item);
            item.data('id', model.id);
            item.data('shared', model.shared);
            item.data('writable', model.writable);
            item.data('notebook_path', model.writable);

            item.find(".item_name").text(model.name.replace(/\.ipynb/, ''));

            item.addClass(running ? 'running' : 'stopped');
            item.addClass(model.type);
            item.addClass(model.shared ? 'shared' : 'private');
            item.addClass(model.writable ? 'writable' : 'read-only');

            $('<i/>').addClass('item_icon').addClass('shared_icon').insertAfter(item.find('.item_icon'));
        };

        NotebookList.prototype.draw_notebook_list = function (list, error_msg) {
            // Remember what was selected before the refresh.
            var selected_before = this.selected;

            this.clear_list();

            var message = error_msg || 'Notebook list empty.',
                item = null,
                model = null,
                len = list.content.length,
                n_uploads = this.element.children('.list_item').length;

            if (len === 0) {
                item = this.new_item(0);
                var span12 = item.children().first();
                span12.empty();
                span12.append($('<div style="margin:auto;text-align:center;color:grey"/>').text(message));
            }

            var path = this.notebook_path,
                offset = n_uploads, m;

            if (path !== '' && (m = path.match(/^([^\/]+\/[^\/]+)\//))) {
                item = this.new_item(offset, false);
                model = {
                    type: 'directory',
                    name: '..',
                    path: m[1],
                };
                this.add_link(model, item);
                offset += 1;
            }
            for (var i = 0; i < len; i++) {
                model = list.content[i];
                item = this.new_item(i + offset, model['type'] != 'directory');
                try {
                    this.add_link(model, item);
                } catch (err) {
                    console.log('Error adding link: ' + err);
                }
            }
            // Trigger an event when we've finished drawing the notebook list.
            events.trigger('draw_notebook_list.NotebookList');

            // Reselect the items that were selected before.  Notify listeners
            // that the selected items may have changed.  O(n^2) operation.
            selected_before.forEach(function (item) {
                var list_items = $('.list_item');
                for (var i = 0; i < list_items.length; i++) {
                    var $list_item = $(list_items[i]);
                    if ($list_item.data('path') === item.path) {
                        $list_item.find('input[type=checkbox]').prop('checked', true);
                        break;
                    }
                }
            });
            this._selection_changed();
        };

    }

    /** Extending Notebook class. */
    {
        var SaveWidget = require('notebook/js/savewidget').SaveWidget;

        SaveWidget.prototype.parent_rename_notebook = SaveWidget.prototype.rename_notebook;

        SaveWidget.prototype.rename_notebook = function (options) {
            if (!options.notebook.writable) {
                var error = new Error("Notebook is read-only");
                this.events.trigger('notebook_save_failed.Notebook', error);
                return Promise.reject(error);
            }

            this.parent_rename_notebook(options);
        }
    }

    /** Extending MenuBar class. */
    {
        var MenuBar = require('notebook/js/menubar').MenuBar;

        MenuBar.prototype.parent_bind_events = MenuBar.prototype.bind_events;

        MenuBar.prototype.bind_events = function () {
            this.parent_bind_events();
            this.element.find('#kill_and_exit').off('click').on('click', kill_and_exit);
        };
    }

    /** Extending notebook actions. */
    $([IPython.events]).on('notebook_loaded.Notebook', function () {
        /* Add toolbar buttons */
        IPython.toolbar.add_buttons_group([
            {
                id: 'close',
                label: 'Close this notebook and goto notebooks list',
                icon: 'fa-close',
                callback: kill_and_exit
            }
        ]);
    });
});
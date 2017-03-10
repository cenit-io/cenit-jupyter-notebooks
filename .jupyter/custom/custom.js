define(function (require, exports, module) {
    "use strict";

    var $ = require('jqueryui'),
        IPython = require('base/js/namespace'),
        events = require('base/js/events'),
        utils = require('base/js/utils'),
        dialog = require('base/js/dialog'),

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

        NotebookList.prototype.bind_events = function () {
            this.parent_bind_events();
            // Bind events for singleton controls.
            if (!NotebookList._custom_bound_singletons) {
                NotebookList._custom_bound_singletons = true;
                // Bind events for action buttons.
                $('.cross-origin').off('click').on('click', $.proxy(this.cross_origin, this));
            }
        };

        NotebookList.prototype.cross_origin = function (e) {
            var that = this,
                origin = $(e.target).parents('li').data('origin');

            this.selected.forEach(function (item) {
                that.contents.save(item.path, {
                    id: item.id,
                    origin: origin
                }).then(function () {
                    that.session_list.load_sessions();
                });
            });
        };

        NotebookList.prototype._selection_changed = function () {
            this.parent_selection_changed();

            var that = this,
                checked = 0,
                has_read_only = false,
                has_directories = false,
                has_shared = false,
                anonymous = $('body').data('notebookPath').match(/^-\/-\//);

            $('.list_item :checked').each(function (index, item) {
                var parent = $(item).parent().parent();

                // If the item doesn't have an upload button, isn't the
                // breadcrumbs and isn't the parent folder '..', then it can be selected.
                // Breadcrumbs path == ''.
                if (parent.find('.upload_button').length === 0 && parent.data('path') !== '' && parent.data('path') !== utils.url_path_split(that.notebook_path)[0]) {
                    checked++;
                    that.selected[index] = parent.data();
                    has_shared = has_shared || (that.selected[index].origin != 'default');
                    has_read_only = has_read_only || !that.selected[index].writable;
                    has_directories = has_directories || (that.selected[index].type == 'directory');
                }
            });

            // Shared is only visible when one item is selected.
            if (checked > 0 && !anonymous && !has_read_only && !has_directories) {
                $('.shared-button').css('display', 'inline-block');
            } else {
                $('.shared-button').css('display', 'none');
            }

            // Rename is only visible when one item is selected, it is writable notebook and not a running.
            if (checked === 1 && !anonymous && !this.is_running(this.selected[0]) && !has_read_only && !has_directories) {
                $('.rename-button').css('display', 'inline-block');
            } else {
                $('.rename-button').css('display', 'none');
            }

            // Duplicate isn't visible when a directory is selected.
            if (checked > 0 && !anonymous && !has_directories) {
                $('.duplicate-button').css('display', 'inline-block');
            } else {
                $('.duplicate-button').css('display', 'none');
            }

            // Delete is visible if one or more items are selected.
            if (checked > 0 && !anonymous && !has_read_only && !has_shared) {
                $('.delete-button').css('display', 'inline-block');
            } else {
                $('.delete-button').css('display', 'none');
            }

            // New isn't visible when access is anonymous.
            if (!anonymous) {
                $('.new-buttons').css('display', 'inline-block');
            } else {
                $('.new-buttons').css('display', 'none');
            }
        };

        NotebookList.prototype.is_running = function (model) {
            return (model.type === 'notebook' && this.sessions[model.path] !== undefined)
        };

        NotebookList.prototype.add_link = function (model, item) {
            var running = this.is_running(model),
                titles = {
                    default: 'Non shared',
                    owner: 'Shared with my tenants',
                    shared: 'Shared with all users',
                };

            this.parent_add_link(model, item);
            item.data('id', model.id);
            item.data('origin', model.origin);
            item.data('writable', model.writable);
            item.data('notebook_path', model.writable);

            item.find(".item_name").text(model.name.replace(/^setup\/|\.ipynb$/g, ''));

            item.addClass(running ? 'running' : 'stopped');
            item.addClass(model.type);
            item.addClass(model.origin);
            item.addClass(model.writable ? 'writable' : 'read-only');

            $('<i/>').addClass('item_icon')
                .addClass('writable_icon')
                .insertBefore(item.find('.item_link'));

            $('<i/>').addClass('item_icon')
                .addClass('shared_icon')
                .prop('title', titles[model.origin])
                .insertBefore(item.find('.item_link'));
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
            var that = this;

            this.parent_bind_events();
            this.element.find('#kill_and_exit').off('click').on('click', kill_and_exit);
            // this.element.find('#cenit-io-key-tokens').off('click').on('click', )
        };
    }

    /** Extending notebook actions. */
    $([IPython.events]).on('notebook_loaded.Notebook', function () {
        var that = this,

            cenit_io_key_tokens = function () {
                var path = $('body').data('notebookPath').split('/');

                dialog.modal({
                    title: "Cenit-IO user access key and token:",
                    body: $('<ul>')
                        .append($('<li>')
                            .append($('<strong>').text('user_access_key: '))
                            .append($('<span>').text(path[0]))
                        )
                        .append($('<li>')
                            .append($('<strong>').addClass('bold').text('user_access_token: '))
                            .append($('<span>').text(path[1]))
                        ),
                    buttons: {"OK": {class: "btn-primary"}}
                });

                console.log(path);
            };

        console.log(IPython);

        /* Add toolbar buttons */
        IPython.toolbar.add_buttons_group([
            {
                id: 'cenit-io-key-tokens',
                label: 'Show my Cenit-IO access key and token',
                icon: 'fa-key',
                callback: cenit_io_key_tokens
            }
        ]);

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
define(function (require, exports, module) {
    "use strict";

    var $ = require('jqueryui'),
        IPython = require('base/js/namespace'),
        utils = require('base/js/utils'),
        NotebookList = require('tree/js/notebooklist').NotebookList;

    Jupyter._target = '_self';

    NotebookList.prototype.parent_selection_changed = NotebookList.prototype._selection_changed;
    NotebookList.prototype.parent_add_link = NotebookList.prototype.add_link;
    NotebookList.prototype.parent_bind_events = NotebookList.prototype.bind_events;

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

        if (running) item.addClass('running');
        if (model.shared) item.addClass('shared');
        if (model.writable) item.addClass('writable');

        $('<i/>').addClass('item_icon').addClass('shared_icon').insertAfter(item.find('.item_icon'));
    };


    $([IPython.events]).on('notebook_loaded.Notebook', function () {
        /* add toolbar buttons */
        IPython.toolbar.add_buttons_group([
            {
                id: 'close',
                label: 'Close this notebook and goto notebooks list',
                icon: 'fa-close',
                callback: function () {
                    var parent = utils.url_path_split(IPython.notebook.notebook_path)[0],
                        url = utils.url_path_join(IPython.notebook.base_url, 'tree', utils.encode_uri_components(parent));
                    window.open(url, IPython._target);
                }
            }
        ]);
    });
});
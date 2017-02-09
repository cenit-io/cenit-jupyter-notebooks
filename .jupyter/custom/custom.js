define(function (require, exports, module) {
    "use strict";

    var $ = require('jqueryui'),
        utils = require('base/js/utils'),
        NotebookList = require('tree/js/notebooklist').NotebookList;

    NotebookList.prototype.parent_selection_changed = NotebookList.prototype._selection_changed;
    NotebookList.prototype.parent_add_link = NotebookList.prototype.add_link;

    NotebookList.prototype.connect_custom_events = function () {
        NotebookList._custom_events = true;
        // Bind events for action buttons.
        $('.shared-button').click($.proxy(this.toggle_shared_selected, this));
    };

    NotebookList.prototype.toggle_shared_selected = function () {
        var that = this;
        this.selected.forEach(function (item) {
            if (item.type === 'notebook') {
                that.contents.save(item.path, {
                    id: item.id,
                    shared: !item.shared,
                    content: False
                }).then(function () {
                    that.session_list.load_sessions();
                })
            }
        });
    };

    NotebookList.prototype._selection_changed = function () {
        if (!NotebookList._custom_events) this.connect_custom_events();

        this.parent_selection_changed();

        var that = this,
            checked = 0;

        $('.list_item :checked').each(function (index, item) {
            var parent = $(item).parent().parent(),
                shared = parent.data('shared');

            // If the item doesn't have an upload button, isn't the
            // breadcrumbs and isn't the parent folder '..', then it can be selected.
            // Breadcrumbs path == ''.
            if (parent.find('.upload_button').length === 0 && parent.data('path') !== '' && parent.data('path') !== utils.url_path_split(that.notebook_path)[0]) {
                checked++;
                that.selected[index] = parent.data()
            }
        });

        // Shared is only visible when one item is selected.
        if (checked > 0) {
            $('.shared-button').css('display', 'inline-block');
        } else {
            $('.shared-button').css('display', 'none');
        }
    };

    NotebookList.prototype.add_link = function (model, item) {
        var running = (model.type === 'notebook' && this.sessions[model.path] !== undefined);

        this.parent_add_link(model, item);
        item.data('id', model.id);
        item.data('shared', model.shared);
        item.data('writable', model.writable);

        if (running) item.addClass('running');
        if (model.shared) item.addClass('shared');
        if (model.writable) item.addClass('writable');

        $('<i/>').addClass('item_icon').addClass('shared_icon').insertAfter(item.find('.item_icon'));
    };

    return {'NotebookList': NotebookList};
});
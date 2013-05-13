var ImageBatchActionFormHelper = {

    init: function() {
        this.changeActionForm();

        var $actionField = $("#id_action");
        $actionField.change(function() {
            ImageBatchActionFormHelper.changeActionForm();
        });

        var $deleteSubmit = $("#id_delete_submit");
        $deleteSubmit.click(function() {
            return ImageBatchActionFormHelper.areYouSureDelete();
        });
    },

    areYouSureDelete: function() {
        return window.confirm("Are you sure you want to delete these images? You won't be able to undo this.");
    },

    changeActionForm: function() {
        var action = $("#id_action").val();
        var $deleteForm = $("#id_delete_form");

        // Hide all forms first
        $deleteForm.hide();

        // Then show only the relevant form (if any)
        if (action === 'delete') {
            $deleteForm.show();
        }
    }
};

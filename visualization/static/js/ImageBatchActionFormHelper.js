var ImageBatchActionFormHelper = {

    init: function(numOfImages) {
        this.numOfImages = numOfImages;

        this.changeSubmitButton();

        var actionFieldJQ = $("#id_action");
        actionFieldJQ.change(function() {
            ImageBatchActionFormHelper.changeSubmitButton();
        });

        var submitWithConfirmJQ = $("#id_actionFormSubmitButton_withConfirm");
        submitWithConfirmJQ.click(function() {
            return ImageBatchActionFormHelper.areYouSureDelete();
        });
    },

    areYouSureDelete: function() {
        return window.confirm("Are you sure you want to delete these {0} images?".format(this.numOfImages));
    },

    changeSubmitButton: function() {
        var actionField = $("#id_action")[0];
        var submitWithoutConfirmJQ = $("#id_actionFormSubmitButton_withoutConfirm");
        var submitWithConfirmJQ = $("#id_actionFormSubmitButton_withConfirm");

        if (actionField.value == 'delete') {
            submitWithConfirmJQ.show();
            submitWithoutConfirmJQ.hide();
        }
        else {
            submitWithConfirmJQ.hide();
            submitWithoutConfirmJQ.show();
        }
    }
};

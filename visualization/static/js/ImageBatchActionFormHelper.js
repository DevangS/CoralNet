var ImageBatchActionFormHelper = (function() {

    var $radioDownloadField;
    var $radioDeleteField;

    function areYouSureDelete() {
        return window.confirm("Are you sure you want to delete these images? You won't be able to undo this.");
    }

    function changeActionForm() {
//        var action = $("#id_action").val();
        var $downloadForm = $("#id_download_form");
        var $deleteForm = $("#id_delete_form");

        // Hide all forms first
        $downloadForm.hide();
        $deleteForm.hide();

        // Then show only the relevant form (if any)
        if ($radioDownloadField.prop('checked')) {
            $downloadForm.show();
        }
        else if ($radioDeleteField.prop('checked')) {
            $deleteForm.show();
        }
//        if (action === 'download') {
//            $downloadForm.show();
//        }
//        else if (action === 'delete') {
//            $deleteForm.show();
//        }
    }

    return {
        init: function() {

    //        var $actionField = $("#id_action");
    //        $actionField.change(function() {
    //            ImageBatchActionFormHelper.changeActionForm();
    //        });

            $radioDownloadField = $("#id_radio_download");
            $radioDeleteField = $("#id_radio_delete");
            $radioDownloadField.change(function() {
                changeActionForm();
            });
            $radioDeleteField.change(function() {
                changeActionForm();
            });

            var $deleteSubmit = $("#id_delete_submit");
            $deleteSubmit.click(function() {
                return areYouSureDelete();
            });

            changeActionForm();
        }
    }
})();

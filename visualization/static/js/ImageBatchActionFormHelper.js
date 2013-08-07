var BrowseActionHelper = (function() {

    var hasDownloadForm;
    var hasDeleteForm;

    var $downloadForm;
    var $deleteForm;

    var $radioDownloadField;
    var $radioDeleteField;


    function areYouSureDelete() {
        return window.confirm("Are you sure you want to delete these images? You won't be able to undo this.");
    }

    function changeActionForm() {

        if (hasDownloadForm) {

            if ($radioDownloadField.prop('checked')) {
                $downloadForm.show();
            }
            else {
                $downloadForm.hide();
            }
        }

        if (hasDeleteForm) {

            if ($radioDeleteField.prop('checked')) {
                $deleteForm.show();
            }
            else {
                $deleteForm.hide();
            }
        }
    }


    return {

        /*
        hasDownloadForm - true if the download form is on the page, else false
        hasDeleteForm - true if the delete form is on the page, else false
         */
        init: function(params) {

            // Each of the action forms may or may not be on the page.
            //
            // We have to account for the cases where each form may
            // or may not be on the page.
            hasDownloadForm = params.hasDownloadForm;
            hasDeleteForm = params.hasDeleteForm;

            if (hasDownloadForm) {

                $downloadForm = $("#id_download_form");

                $radioDownloadField = $("#id_radio_download");
                $radioDownloadField.change(function() {
                    changeActionForm();
                });
            }

            if (hasDeleteForm) {

                $deleteForm = $("#id_delete_form");

                $radioDeleteField = $("#id_radio_delete");
                $radioDeleteField.change(function() {
                    changeActionForm();
                });

                var $deleteSubmit = $("#id_delete_submit");
                $deleteSubmit.click(function() {
                    return areYouSureDelete();
                });
            }

            changeActionForm();
        }
    }
})();

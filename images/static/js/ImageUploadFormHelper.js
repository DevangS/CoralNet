/* The following design pattern is from
 * http://stackoverflow.com/a/1479341/859858 */
var ImageUploadFormHelper = (function() {

    var i;

    var $uploadTableArea = null;
    var $uploadTable = null;
    var $uploadTableRowArray = [];
    var $totalSizeHeader = null;
    var $uploadStatusHeader = null;
    var $uploadStatusCellArray = [];

    var filesField = null;
    var dupeOptionField = null;
    var metadataOptionField = null;
    var $uploadButton = null;

    var sourceId = null;
    var hasAnnotations = null;

    var uploadStartUrl = null;
    //var uploadProgressUrl = null;

    var $formClone = null;
    var uploadOptions = null;
    var files = null;
    var currentFileIndex = null;

    var statusArray = [];
    var uploadableArray = [];
    var atLeastOneUploadable = false;


    function filesizeDisplay(bytes) {
        var KILO = 1024;
        var MEGA = 1024*1024;

        if (bytes < KILO) {
            return bytes + " bytes";
        }
        else if (bytes < MEGA) {
            return Math.floor(bytes / KILO) + " KB";
        }
        else {
            return (Math.floor(bytes * 100 / MEGA) / 100) + " MB";
        }
    }

    /*
    Get the file details and display them in a table.
    */
    function refreshFiles() {
        // Clear the table of all elements
        $uploadTable.empty();
        // Clear the arrays pointing to table elements
        $uploadTableRowArray.length = 0;
        $uploadStatusCellArray.length = 0;

        files = filesField.files;

        if (!files) {
            return;
        }

        // Initialize upload statuses to null
        statusArray.length = 0;
        for (i = 0; i < files.length; i++) {
            statusArray.push(null);
        }
        updatePreUploadSummary();

        // Create first row of the upload table.
        var $tableHeaderRow = $("<tr>");
        $tableHeaderRow.append($("<th>").text(files.length + " file(s)"));
        $totalSizeHeader = $("<th>");
        $uploadStatusHeader = $("<th>");
        $tableHeaderRow.append($uploadStatusHeader);
        $uploadTable.append($tableHeaderRow);

        for (i = 0; i < files.length; i++) {

            // Create a table row containing file details
            var $uploadTableRow = $("<tr>");

            // filename, filesize
            $uploadTableRow.append($("<td>").text(files[i].name));
            $uploadTableRow.append($("<td>").text(filesizeDisplay(files[i].size)));

            // filename status, to be filled in with an Ajax response
            var $statusCell = $("<td>");
            $uploadTableRow.append($statusCell);
            $uploadStatusCellArray.push($statusCell);

            $uploadTable.append($uploadTableRow);
            $uploadTableRowArray.push($uploadTableRow);
        }

        var filenameList = new Array(files.length);
        for (i = 0; i < files.length; i++) {
            filenameList[i] = files[i].name;
        }

        // AJAX call to a Django method in ajax.py of this app
        if ($(metadataOptionField).val() === 'filenames') {
            Dajaxice.CoralNet.images.ajax_assess_file_status(
                ajaxUpdateFilenameStatuses,    // JS callback that the ajax.py method returns to.
                {'filenames': filenameList,
                 'sourceId': sourceId,
                 'checkDupes': true}    // Args to the ajax.py method.
            );
        }
        else {
            var statusList = new Array(files.length);
            for (i = 0; i < files.length; i++) {
                statusList[i] = {'status':'ok'};
            }
            updateFilenameStatuses(statusList);
        }
    }

    function updateUploadability() {
        atLeastOneUploadable = false;

        for (i = 0; i < files.length; i++) {
            // Uploadable: ok, dupe+replace
            // Not uploadable: dupe+skip, error, null(uninitialized status)
            var isUploadable = (
                statusArray[i] === 'ok'
                || (statusArray[i] === 'dupe' && $(dupeOptionField).val() === 'replace')
            );

            if (isUploadable) {
                $uploadTableRowArray[i].removeClass('not-uploadable');
                atLeastOneUploadable = true;
            }
            else {
                $uploadTableRowArray[i].addClass('not-uploadable');
            }

            uploadableArray[i] = isUploadable;
        }
    }

    /* Figure out the combined size of all the files selected for upload. */
    function updateUploadSize() {
        if (files.length === 0) {
            $totalSizeHeader.text("");
            return;
        }

        var totalSize = 0;
        for (i = 0; i < files.length; i++) {
            if (uploadableArray[i])
                totalSize += files[i].size;
        }
        $totalSizeHeader.text(filesizeDisplay(totalSize));
    }

    function updateFormFields() {
        if ($(metadataOptionField).val() === 'filenames') {
            $("#id_skip_or_replace_duplicates_wrapper").show();
        }
        else {
            $("#id_skip_or_replace_duplicates_wrapper").hide();
        }

        if (atLeastOneUploadable) {
            $uploadButton.attr('disabled', false);
            $uploadButton.text("Start Upload");
        }
        else {
            $uploadButton.attr('disabled', true);
            $uploadButton.text("");
        }
    }

    function updatePreUploadSummary() {
        // Are the files uploadable or not?
        updateUploadability();

        // Compute the combined size of the uploadable files
        updateUploadSize();

        // Make sure to update the form once more after the AJAX call completes
        updateFormFields();
    }

    function updateFilenameStatuses(statusList) {
        var numOfDupes = 0, numOfErrors = 0;

        for (i = 0; i < statusList.length; i++) {

            var uploadStatusCell = $uploadStatusCellArray[i];
            uploadStatusCell.empty();

            var statusStr = statusList[i].status;
            var containerElmt;

            if (statusStr === 'dupe') {

                var linkToDupe = $("<a>").text("Duplicate found");
                linkToDupe.attr("href", statusList[i].url);    // Link to the image's page
                linkToDupe.attr("target", "_blank");    // Open in new window

                containerElmt = $("<span>").addClass("dupeStatus");
                containerElmt.append(linkToDupe);
                uploadStatusCell.append(containerElmt);

                numOfDupes += 1;
            }
            else if (statusStr === 'error') {
                containerElmt = $("<span>").addClass("errorStatus");
                containerElmt.text("Filename error");
                uploadStatusCell.append(containerElmt);

                numOfErrors += 1;
            }
            else if (statusStr === 'ok') {
                uploadStatusCell.text("Ready");
            }
        }

        // Update the status summary.
        var statusSummary = "";
        var statusMessages = [];

        if (numOfErrors > 0)
            statusMessages.push(numOfErrors + " error(s)");
        if (numOfDupes > 0)
            statusMessages.push(numOfDupes + " duplicate(s)");

        for (i = 0; i < statusMessages.length; i++) {
            if (i === 0)
                statusSummary += statusMessages[i];
            else
                statusSummary += (', ' + statusMessages[i])
        }
        $uploadStatusHeader.text(statusSummary);

        updatePreUploadSummary();
    }

    function ajaxUpdateFilenameStatuses(data) {
        updateFilenameStatuses(data.statusList);
    }

    function ajaxUpload() {

        $(filesField).disable();
        $(dupeOptionField).disable();
        $(metadataOptionField).disable();
        $uploadButton.disable();
        $uploadButton.text("Uploading...");

        // Submit the form.
        uploadOptions = {
            // Expected datatype of response
            dataType: 'json',
            // URL to submit to
            url: uploadStartUrl,

            // Callbacks
            beforeSubmit: addFileToAjaxRequest,
            success: ajaxUploadHandleResponse
        };
        $formClone = $('#id_upload_form').clone();
        currentFileIndex = 0;
        uploadFile();

        // Remnants of an attempt at a progress bar...
/*        var $ajaxUploadID = $('#id_ajax_upload_id');
        $ajaxUploadID.val(util.randomString(10));

        var options = {
            dataType: 'xml',
            url: uploadStartUrl + '?ajax-upload-id=' + $ajaxUploadID.val(),
            beforeSubmit: prepareProgressBar,
            success: ajaxUploadHandleResponse
        };*/
    }

    function uploadFile() {
        $formClone.ajaxSubmit(uploadOptions);
        var $uploadStatusCell = $uploadStatusCellArray[currentFileIndex];
        $uploadStatusCell.empty();
        $uploadTableRowArray[currentFileIndex].addClass('upload-started');
        $uploadStatusCell.text("Uploading...");
    }

    // Remnants of an attempt at a progress bar...
/*    function prepareProgressBar() {
        $('#progress_bar').progressBar();
    }*/

    /* Callback before the Ajax form is submitted.
     * arr - the form data in array format
     * $form - the jQuery-wrapped form object
     * options - the options object used in the form submit call */
    function addFileToAjaxRequest(arr, $form, options) {
        // Push the file as 'files' so that it can be validated
        // on the server-side with an ImageUploadForm.
        arr.push({
            name: 'files',
            type: 'files',
            value: files[currentFileIndex]
        });
    }

    /* Callback after the Ajax response is received, indicating that
     * the server upload and processing are done. */
    function ajaxUploadHandleResponse(response) {

        // TODO: Show this upload status message in a results table
        // on the page.
        var $uploadStatusCell = $uploadStatusCellArray[currentFileIndex];
        $uploadStatusCell.empty();
        $uploadStatusCell.text(response.message);

        currentFileIndex++;
        // Note that this index starts from 0.
        if (currentFileIndex < files.length)
            uploadFile();
        else
            $uploadButton.text("Upload Complete");

        // Remnants of an attempt at a progress bar...
/*        // Get the completion percentage from the response, and then
        // update the progress bar accordingly.
        $('#progress_bar').progressBar(percentage);*/
    }

    /* Public methods.
     * These are the only methods that need to be referred to as
     * ImageUploadFormHelper.methodname. */
    return {

        initForm: function(params){

            // Initializing.
            sourceId = params.sourceId;
            hasAnnotations = params.hasAnnotations;
            uploadStartUrl = params.uploadStartUrl;
            //uploadProgressUrl = params.uploadProgressUrl;

            $uploadTableArea = $('#uploadTableArea');
            $uploadTable = $("<table>").attr("id", "uploadTable");
            $uploadTableArea.append($uploadTable);

            filesField = $('#id_files')[0];
            dupeOptionField = $('#id_skip_or_replace_duplicates')[0];
            metadataOptionField = $('#id_specify_metadata')[0];
            $uploadButton = $('#id_upload_submit');

            updatePreUploadSummary();

            // Set onchange handlers for form fields.
            $(filesField).change( function(){
                refreshFiles();
                updatePreUploadSummary();
            });

            $(dupeOptionField).change( function() {
                updatePreUploadSummary();
            });

            // This'll become relevant again when we support other methods of specifying metadata
            /*        $("#id_specify_metadata").change( function(){
             refreshFiles();
             updatePreUploadSummary();
             });*/

            // "(More info)" link on the 'specify metadata' field
            var metadataHelptextJQ = $("#metadata_short_helptext");
            var metadataExtraHelptextLinkJQ = $("<a>").text("(More info)");
            metadataHelptextJQ.append(" ");
            metadataHelptextJQ.append($("<span>").append(metadataExtraHelptextLinkJQ));

            // Extra help text is initially hidden
            $("#metadata_extra_helptext").hide();

            // (More info) shows the extra help text, (Less info) hides it
            metadataExtraHelptextLinkJQ.click(function() {
                var extraHelptextJQ = $("#metadata_extra_helptext");

                if (extraHelptextJQ.is(':hidden')) {
                    extraHelptextJQ.show();
                    $(this).text("(Less info)");
                }
                else {
                    extraHelptextJQ.hide();
                    $(this).text("(More info)");
                }
            });

            // Attach ajax upload handler
            $uploadButton.click(ajaxUpload);
        }
    }
})();

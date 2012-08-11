/* The following design pattern is from
 * http://stackoverflow.com/a/1479341/859858 */
var ImageUploadFormHelper = (function() {

    var i;

    var $preUploadSummary = null;
    var $duringUploadSummary = null;
    var $filesTable = null;

    var filesField = null;
    var dupeOptionFieldId = 'id_skip_or_replace_duplicates';
    var dupeOptionField = null;
    var metadataOptionFieldId = 'id_specify_metadata';
    var metadataOptionField = null;
    var $uploadButton = null;

    var sourceId = null;
    var hasAnnotations = null;

    var uploadStartUrl = null;
    //var uploadProgressUrl = null;

    var $formClone = null;
    var uploadOptions = null;
    var files = [];
    var currentFileIndex = null;

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

    /* Makes cssClass the only style class of the row (tr) of index rowIndex.
     * Pass in '' as the cssClass to just remove the style.
     *
     * Assumes we only need up to 1 style on any row at any given time.
     * If that assumption is no longer valid, then this function should be
     * changed. */
    function styleRow(rowIndex, cssClass) {
        files[rowIndex].$tableRow.attr('class', cssClass);
    }

    /*
    Get the file details and display them in a table.
    */
    function refreshFiles() {
        // Clear the table rows
        for (i = 0; i < files.length; i++) {
            files[i].$tableRow.remove();
        }
        // Clear the file array
        files.length = 0;

        // Re-build the file array.
        // Set the image files as files[0].file, files[1].file, etc.
        for (i = 0; i < filesField.files.length; i++) {
            files.push({'file': filesField.files[i]});
        }

        // TODO: What is this for exactly? Do we need it anymore?
        if (!files) {
            return;
        }

        // Make a table row for each file
        for (i = 0; i < files.length; i++) {

            // Create a table row containing file details
            var $filesTableRow = $("<tr>");

            // filename, filesize
            $filesTableRow.append($("<td>").text(files[i].file.name));
            $filesTableRow.append($("<td>").text(filesizeDisplay(files[i].file.size)));

            // filename status, to be filled in with an Ajax response
            var $statusCell = $("<td>");
            $statusCell.addClass('status_cell');
            $filesTableRow.append($statusCell);
            files[i].$statusCell = $statusCell;

            $filesTable.append($filesTableRow);
            files[i].$tableRow = $filesTableRow;
        }

        // Initialize upload statuses to null
        for (i = 0; i < files.length; i++) {
            //statusArray.push(null);
            files[i].status = null;
        }
        // Ensure the files are marked as non-uploadable until we check
        // for their uploadability
        updatePreUploadSummary();

        var filenameList = new Array(files.length);
        for (i = 0; i < files.length; i++) {
            filenameList[i] = files[i].file.name;
        }

        if ($(metadataOptionField).val() === 'filenames') {

            // Ask the server (via Ajax) about the filenames: are they in the
            // right format? Do they have duplicate keys with existing files?
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
                files[i].status === 'ok'
                || (files[i].status === 'dupe' && $(dupeOptionField).val() === 'replace')
            );

            if (isUploadable) {
                atLeastOneUploadable = true;
            }

            files[i].isUploadable = isUploadable;
        }
    }

    function updatePreUploadStyle() {
        for (i = 0; i < files.length; i++) {
            if (files[i].status === 'ok') {
                styleRow(i, '');
            }
            else if (files[i].status === 'dupe') {
                if ($(dupeOptionField).val() === 'skip') {
                    styleRow(i, 'dupe_skip');
                }
                else {  // 'replace'
                    styleRow(i, 'preupload_dupe_replace');
                }
            }
            else {
                // 'error' status
                styleRow(i, 'preupload_error');
            }
        }
    }

    function updatePreUploadSummaryText() {
        $preUploadSummary.empty();

        if (files.length === 0) {
            return;
        }

        var summaryTextLines = [];

        var uploadableTotalSize = 0;
        for (i = 0; i < files.length; i++) {
            if (files[i].isUploadable)
                uploadableTotalSize += files[i].file.size;
        }

        summaryTextLines.push(files.length + " file(s) total");
        // TODO: Fill in x, y, and z with appropriate variables
        summaryTextLines.push("{0} ({1}) can be uploaded".format("x", filesizeDisplay(uploadableTotalSize)));
        // TODO: If any duplicates, and duplicates are being skipped...
        if (true) {
            summaryTextLines.push("{0} are duplicates that will be skipped".format("y"));
        }
        // TODO: If any filename errors...
        if (true) {
            summaryTextLines.push("{0} have filename errors".format("z"));
        }

        for (i = 0; i < summaryTextLines.length; i++) {
            // If not the first line, append a <br> first.
            // That way, the lines are separated by linebreaks.
            if (i > 0) {
                $preUploadSummary.append('<br>');
            }

            $preUploadSummary.append(summaryTextLines[i]);
        }
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
            //$uploadButton.css('display', 'auto');
            $uploadButton.text("Start Upload");
        }
        else {
            $uploadButton.attr('disabled', true);
            //$uploadButton.css('display', 'none');
            $uploadButton.text("");
        }
    }

    function updatePreUploadSummary() {
        // Are the files uploadable or not?
        updateUploadability();

        // Update table row styles according to file status
        updatePreUploadStyle();

        // Update the summary text above the files table
        updatePreUploadSummaryText();

        // Make sure to update the form once more after the AJAX call completes
        updateFormFields();
    }

    function updateFilenameStatuses(statusList) {
        var numOfDupes = 0, numOfErrors = 0;

        for (i = 0; i < statusList.length; i++) {

            var $statusCell = files[i].$statusCell;
            $statusCell.empty();

            var statusStr = statusList[i].status;

            if (statusStr === 'dupe') {

                var linkToDupe = $("<a>").text("Duplicate found");
                linkToDupe.attr('href', statusList[i].url);    // Link to the image's page
                linkToDupe.attr('target', '_blank');    // Open in new window
                linkToDupe.attr('title', statusList[i].title);
                $statusCell.append(linkToDupe);

                numOfDupes += 1;
            }
            else if (statusStr === 'error') {
                $statusCell.text("Filename error");

                numOfErrors += 1;
            }
            else if (statusStr === 'ok') {
                $statusCell.text("Ready");
            }

            files[i].status = statusStr;
        }

        updatePreUploadSummary();
    }

    function ajaxUpdateFilenameStatuses(data) {
        updateFilenameStatuses(data.statusList);
    }

    function ajaxUpload() {

        $(filesField).prop('disabled', true);
        $uploadButton.prop('disabled', true);
        $uploadButton.text("Uploading...");

        // Submit the form.
        uploadOptions = {
            // Expected datatype of response
            dataType: 'json',
            // URL to submit to
            url: uploadStartUrl,

            // Callbacks
            beforeSubmit: beforeAjaxUploadSubmit,
            success: ajaxUploadHandleResponse
        };

        // Create a clone of the form, passing in true, true to copy all
        // elements' data (i.e. the actual values of the fields) and
        // event handlers (not needed, but not harmful either, since we're
        // not going to change the clone form's fields at any time).
        $formClone = $('#id_upload_form').clone();
        // clone() doesn't copy values of select inputs for some reason,
        // even when the data parameter to clone() is true. So copy these
        // values manually...
        $formClone.find('#'+dupeOptionFieldId).val($(dupeOptionField).val());
        $formClone.find('#'+metadataOptionFieldId).val($(metadataOptionField).val());

        // Now that the form's cloned, go ahead and disable the option fields
        // on the actual form. (ajaxSubmit() won't add form fields if they're
        // disabled.)
        $(dupeOptionField).prop('disabled', true);
        $(metadataOptionField).prop('disabled', true);

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

        var $statusCell = files[currentFileIndex].$statusCell;
        $statusCell.empty();
        styleRow(currentFileIndex, 'uploading');
        $statusCell.text("Uploading...");
    }

    // Remnants of an attempt at a progress bar...
/*    function prepareProgressBar() {
        $('#progress_bar').progressBar();
    }*/

    /* Callback before the Ajax form is submitted.
     * arr - the form data in array format
     * $form - the jQuery-wrapped form object
     * options - the options object used in the form submit call */
    function beforeAjaxUploadSubmit(arr, $form, options) {
        // Add the next file to this upload request.
        // Push the file as 'files' so that it can be validated
        // on the server-side with an ImageUploadForm.
        arr.push({
            name: 'files',
            type: 'files',
            value: files[currentFileIndex].file
        });
    }

    /* Callback after the Ajax response is received, indicating that
     * the server upload and processing are done. */
    function ajaxUploadHandleResponse(response) {

        // Update the table with the upload status from the server.
        var $statusCell = files[currentFileIndex].$statusCell;
        $statusCell.empty();

        if (response.link !== null) {
            var linkToImage = $('<a>').text(response.message);
            linkToImage.attr('href', response.link);
            linkToImage.attr('target', '_blank');
            linkToImage.attr('title', response.title);
            $statusCell.append(linkToImage);
        }
        else {
            $statusCell.text(response.message);
        }

        if (response.status === 'ok') {
            styleRow(currentFileIndex, 'uploaded');
        }
        else {  // 'error'
            styleRow(currentFileIndex, 'upload_error');
        }

        // Find the next file to upload, if any.
        // Note that the file index starts from 0.
        currentFileIndex++;
        while (currentFileIndex < files.length) {
            if (files[currentFileIndex].isUploadable) {
                uploadFile();
                return;
            }
            currentFileIndex++;
        }
        // Reached the end of the files array, so the upload's done.
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

            // Upload status summary.
            $preUploadSummary = $('td#pre_upload_summary');
            $duringUploadSummary = $('td#during_upload_summary');

            // The upload file table.
            $filesTable = $('table#files_table');

            filesField = $('#id_files')[0];
            dupeOptionField = $('#' + dupeOptionFieldId)[0];
            metadataOptionField = $('#' + metadataOptionFieldId)[0];
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

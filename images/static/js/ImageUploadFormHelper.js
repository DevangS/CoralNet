/* The following design pattern is from
 * http://stackoverflow.com/a/1479341/859858 */
var ImageUploadFormHelper = (function() {

    var i;

    var $preUploadSummary = null;
    var $midUploadSummary = null;
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
    var numDupes = 0;
    var numPreUploadErrors = 0;
    var numUploadables = 0;
    var uploadableTotalSize = 0;

    var numUploaded = 0;
    var numUploadSuccesses = 0;
    var numUploadErrors = 0;
    var uploadedTotalSize = 0;
    var currentFileIndex = null;


    function filesizeDisplay(bytes) {
        var KILO = 1024;
        var MEGA = 1024*1024;

        if (bytes < KILO) {
            return bytes + " B";
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

        // No need to do anything more if there are no files anyway.
        if (filesField.files.length === 0) {
            return;
        }

        // Re-build the file array.
        // Set the image files as files[0].file, files[1].file, etc.
        for (i = 0; i < filesField.files.length; i++) {
            files.push({'file': filesField.files[i]});
        }

        // Make a table row for each file
        for (i = 0; i < files.length; i++) {

            // Create a table row containing file details
            var $filesTableRow = $("<tr>");

            // filename, filesize
            $filesTableRow.append($("<td>").text(files[i].file.name));

            var $sizeCell = $("<td>");
            $sizeCell.addClass('size_cell');
            $sizeCell.text(filesizeDisplay(files[i].file.size));
            $filesTableRow.append($sizeCell);

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
            files[i].status = null;
        }
        // Ensure the files are marked as non-uploadable until we check
        // for their uploadability
        updatePreUploadStatus();

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
        numUploadables = 0;
        uploadableTotalSize = 0;

        for (i = 0; i < files.length; i++) {
            // Uploadable: ok, dupe+replace
            // Not uploadable: dupe+skip, error, null(uninitialized status)
            var isUploadable = (
                files[i].status === 'ok'
                || (files[i].status === 'dupe' && $(dupeOptionField).val() === 'replace')
            );

            if (isUploadable) {
                numUploadables++;
                uploadableTotalSize += files[i].file.size;
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

    function updatePreUploadSummary() {
        $preUploadSummary.empty();

        if (files.length === 0) {
            return;
        }

        var summaryTextLines = [];

        summaryTextLines.push(files.length + " file(s) total");
        summaryTextLines.push($('<strong>').text("{0} file(s) ({1}) will be uploaded".format(numUploadables, filesizeDisplay(uploadableTotalSize))));
        if (numDupes > 0) {
            if ($(dupeOptionField).val() === 'skip') {
                summaryTextLines.push("{0} file(s) are duplicates that will be skipped".format(numDupes));
            }
            else {  // 'replace'
                summaryTextLines.push("... {0} file(s) are new".format(numUploadables-numDupes));
                summaryTextLines.push("... {0} file(s) are duplicates that will replace the originals".format(numDupes));
            }
        }
        if (numPreUploadErrors > 0) {
            summaryTextLines.push("{0} file(s) have filename errors".format(numPreUploadErrors));
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

        if (files.length === 0) {
            // No files
            $uploadButton.attr('disabled', true);
            $uploadButton.text("No files selected yet");
        }
        else if (numUploadables === 0) {
            // No uploadable files
            $uploadButton.attr('disabled', true);
            $uploadButton.text("Cannot upload any of these files");
        }
        else {
            // Uploadable files present
            $uploadButton.attr('disabled', false);
            $uploadButton.text("Start Upload");
        }
    }

    function updatePreUploadStatus() {
        // Are the files uploadable or not?
        updateUploadability();

        // Update table row styles according to file status
        updatePreUploadStyle();

        // Update the summary text above the files table
        updatePreUploadSummary();

        // Make sure to update the form once more after the AJAX call completes
        updateFormFields();
    }

    function updateFilenameStatuses(statusList) {
        numDupes = 0;
        numPreUploadErrors = 0;

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

                numDupes += 1;
            }
            else if (statusStr === 'error') {
                $statusCell.text("Could not extract metadata from filename");

                numPreUploadErrors += 1;
            }
            else if (statusStr === 'ok') {
                $statusCell.text("Ready");
            }

            files[i].status = statusStr;
        }

        updatePreUploadStatus();
    }

    function updateMidUploadSummary() {
        $midUploadSummary.empty();

        var summaryTextLines = [];

        summaryTextLines.push($('<strong>').text("Uploaded: {0} of {1} ({2} of {3}, {4}%)".format(
            numUploaded,
            numUploadables,
            filesizeDisplay(uploadedTotalSize),
            filesizeDisplay(uploadableTotalSize),
            ((uploadedTotalSize/uploadableTotalSize)*100).toFixed(1)  // Percentage with 1 decimal place
        )));

        if (numUploadErrors > 0) {
            summaryTextLines.push("Upload successes: {0} of {1}".format(numUploadSuccesses, numUploaded));
            summaryTextLines.push("Upload errors: {0} of {1}".format(numUploadErrors, numUploaded));
        }

        for (i = 0; i < summaryTextLines.length; i++) {
            // If not the first line, append a <br> first.
            // That way, the lines are separated by linebreaks.
            if (i > 0) {
                $midUploadSummary.append('<br>');
            }

            $midUploadSummary.append(summaryTextLines[i]);
        }
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

        numUploaded = 0;
        numUploadSuccesses = 0;
        numUploadErrors = 0;
        uploadedTotalSize = 0;
        updateMidUploadSummary();

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

    /* Find a file to upload, starting from the current currentFileIndex.
     * If the current file is not uploadable, increment the currentFileIndex
     * and try the next file.  Once an uploadable file is found, begin
     * uploading that file. */
    function uploadFile() {
        while (currentFileIndex < files.length) {

            if (files[currentFileIndex].isUploadable) {
                // An uploadable file was found, so upload it.
                $formClone.ajaxSubmit(uploadOptions);

                // In the files table, update the status for that file.
                var $statusCell = files[currentFileIndex].$statusCell;
                $statusCell.empty();
                styleRow(currentFileIndex, 'uploading');
                $statusCell.text("Uploading...");
                return;
            }

            // No uploadable file was found yet; keep looking.
            currentFileIndex++;
        }

        // Reached the end of the files array.
        $uploadButton.text("Upload Complete");
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
        // Push the file as 'file' so that it can be validated
        // on the server-side with an ImageUploadForm.
        arr.push({
            name: 'file',
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
            numUploadSuccesses++;
        }
        else {  // 'error'
            styleRow(currentFileIndex, 'upload_error');
            numUploadErrors++;
        }
        numUploaded++;
        uploadedTotalSize += files[currentFileIndex].file.size;

        updateMidUploadSummary();

        // Find the next file to upload, if any, and upload it.
        currentFileIndex++;
        uploadFile();

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
            $midUploadSummary = $('td#mid_upload_summary');

            // The upload file table.
            $filesTable = $('table#files_table');

            filesField = $('#id_files')[0];
            dupeOptionField = $('#' + dupeOptionFieldId)[0];
            metadataOptionField = $('#' + metadataOptionFieldId)[0];
            $uploadButton = $('#id_upload_submit');

            updatePreUploadStatus();

            // Set onchange handlers for form fields.
            $(filesField).change( function(){
                refreshFiles();
                updatePreUploadStatus();
            });

            $(dupeOptionField).change( function() {
                updatePreUploadStatus();
            });

            // This'll become relevant again when we support other methods of specifying metadata
            /*        $("#id_specify_metadata").change( function(){
             refreshFiles();
             updatePreUploadStatus();
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

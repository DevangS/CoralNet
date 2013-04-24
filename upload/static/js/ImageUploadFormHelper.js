/* The following "singleton" design pattern is from
 * http://stackoverflow.com/a/1479341/859858
 *
 * Main update functions called in event handling code:
 * updateFormFields
 * updateFilesTable (calls updateFormFields)
 * clearAnnotationFileStatus (calls updateFilesTable)
 *
 * Typically, any event handling function will only need to call
 * one of these functions.
 */
var ImageUploadFormHelper = (function() {

    var i;

    var $preUploadSummary = null;
    var $midUploadSummary = null;
    var $filesTable = null;
    var $filesTableContainer = null;
    var $filesTableAutoScrollCheckbox = null;
    var $filesTableAutoScrollCheckboxContainer = null;

    var annotationFileStatus = null;
    var $annotationFileStatusDisplay = null;
    var annotationsPerImage = null;
    var annotationDictId = null;

    var filesField = null;
    var dupeOptionFieldId = 'id_skip_or_replace_duplicates';
    var dupeOptionField = null;
    var metadataOptionFieldId = 'id_specify_metadata';
    var metadataOptionField = null;
    var annotationsCheckboxFieldId = 'annotations_checkbox';
    var annotationsCheckboxField = null;
    var $annotationsCheckboxLabel = null;
    var annotationFileField = null;
    var pointsOnlyFieldId = 'id_is_uploading_annotations_not_just_points';
    var pointsOnlyField = null;

    var $csvForm = null;
    var $csvFileStatusDisplay = null;
    var csvFileField = null;
    var csvFileStatus = null;
    var csvFileDictId = null;
    var $csvFileTable = null;
    var $csvFileUploadPreview = null;

    var $annotationFileProcessButton = null;
    var $uploadStartButton = null;
    var $uploadAbortButton = null;

    var $uploadStartInfo = null;

    var $dupeOptionWrapper = null;
    var $annotationForm = null;
    var $annotationSection = null;
    var $pointGenText = null;
    var $annoFileExtraHelpText = null;
    var $annoFileExtraHelpTextLink = null;
    var $filesExtraHelpText = null;
    var $filesExtraHelpTextLink = null;

    var uploadPreviewUrl = null;
    var annotationFileProcessUrl = null;
    var uploadStartUrl = null;
    var csvFileProcessUrl = null;
    var uploadPreviewWithCsvUrl = null;
    //var uploadProgressUrl = null;

    var $formToSubmit = null;
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

    var numImagesWithAnnotations = 0;
    var numTotalAnnotations = 0;
    var annotationCountUnits = null;

    var currentFileIndex = null;
    var uploadXhrObj = null;


    /* Makes cssClass the only style class of a particular row (tr element)
     * of the files table.
     * Pass in '' as the cssClass to just remove the style.
     *
     * Assumes we only need up to 1 style on any row at any given time.
     * If that assumption is no longer valid, then this function should be
     * changed. */
    function styleFilesTableRow(rowIndex, cssClass) {
        files[rowIndex].$tableRow.attr('class', cssClass);
    }

    function updateFormFields() {
        // Show or hide the skip-or-replace-dupes option
        // depending on whether it's relevant or not.
        var metadataOptionFieldValue = $(metadataOptionField).val();

        if (metadataOptionFieldValue === 'filenames') {
            $dupeOptionWrapper.show();
            $csvForm.hide();
        }
        else {
            $csvForm.show();
            $dupeOptionWrapper.hide();
        }

        var annotationsChecked = $(annotationsCheckboxField).prop('checked');

        // Show or hide the annotations section depending
        // on the checkbox's value.
        if (annotationsChecked) {
            $annotationForm.show();
            $pointGenText.hide();
            $annotationsCheckboxLabel.removeClass('disabled');
        }
        else {
            $annotationForm.hide();
            $pointGenText.show();
            $annotationsCheckboxLabel.addClass('disabled');
        }

        // Update the annotation file process button.
        if (annotationsChecked) {
            $annotationFileProcessButton.show();
        }
        else {
            $annotationFileProcessButton.hide();
        }

        if (annotationFileField.files.length === 0) {
            $annotationFileProcessButton.prop('disabled', true);
        }
        else {
            $annotationFileProcessButton.prop('disabled', false);
        }

        // Update the upload start button.
        if (annotationsChecked && annotationFileField.files.length === 0) {
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("Points/annotations file not selected yet");
        }
        else if (annotationsChecked && annotationFileStatus === null) {
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("Points/annotations file needs processing");
        }
        else if (annotationsChecked && annotationFileStatus === 'error') {
            // No annotation file
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("Points/annotations file has an error");
        }
        else if (metadataOptionFieldValue === "csv" && csvFileField.files.length === 0) {
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("CSV file not selected yet");
        }
        else if (metadataOptionFieldValue === "csv" && csvFileStatus === null) {
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("CSV file needs processing");
        }
        else if (metadataOptionFieldValue === "csv" && csvFileStatus === 'error') {
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("CSV file has an error");
        }
        else if (files.length === 0) {
            // No image files
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("No image files selected yet");
        }
        else if (numUploadables === 0) {
            // No uploadable image files
            $uploadStartButton.prop('disabled', true);
            $uploadStartInfo.text("Cannot upload any of these image files");
        }
        else {
            // Uploadable image files present
            $uploadStartButton.prop('disabled', false);
            $uploadStartInfo.empty();
        }

        // Show or hide the files list auto-scroll option
        // depending on whether it's relevant or not.
        if ($filesTableContainer[0].scrollHeight > $filesTableContainer[0].clientHeight) {
            // There is overflow in the files table container, such that
            // it has a scrollbar. So the auto-scroll option is relevant.
            $filesTableAutoScrollCheckboxContainer.show();
        }
        else {
            // No scrollbar. The auto-scroll option is not relevant.
            $filesTableAutoScrollCheckboxContainer.hide();
        }
    }

    function updateFilesTable() {
        // Are the files uploadable or not?
        updateUploadability();

        // Update the point/annotation count for each file
        updateFilesTableAnnotationCounts();

        // Update table row styles according to file status
        updatePreUploadStyle();

        // Update the summary text above the files table
        updatePreUploadSummary();

        // Update the form fields. For example, depending on the file statuses,
        // the ability to click the start upload button could change.
        updateFormFields();
    }

    /* Update the isUploadable status of each file. */
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

    /* Update the files table rows' styles according to the file statuses. */
    function updatePreUploadStyle() {
        for (i = 0; i < files.length; i++) {
            if (files[i].status === 'ok') {
                styleFilesTableRow(i, '');
            }
            else if (files[i].status === 'dupe') {
                if ($(dupeOptionField).val() === 'skip') {
                    styleFilesTableRow(i, 'dupe_skip');
                }
                else {  // 'replace'
                    styleFilesTableRow(i, 'preupload_dupe_replace');
                }
            }
            else {
                // 'error' status
                styleFilesTableRow(i, 'preupload_error');
            }
        }
    }

    /* Update the summary text above the files table. */
    function updatePreUploadSummary() {
        $preUploadSummary.empty();

        if (files.length === 0) {
            return;
        }

        $preUploadSummary.text(files.length + " file(s) total");

        var $summaryList = $('<ul>');
        $preUploadSummary.append($summaryList);

        if (numPreUploadErrors > 0) {
            $summaryList.append($('<li>').text(
                "{0} file(s) have filename errors".format(numPreUploadErrors)
            ));
        }

        if (numDupes > 0 && $(dupeOptionField).val() === 'skip') {
            $summaryList.append($('<li>').text(
                "{0} file(s) are duplicate images that will be skipped".format(numDupes)
            ));
        }

        var $uploadableImagesListItem = $('<li>').append($('<strong>').text(
            "{0} file(s) ({1}) are uploadable images".format(
                numUploadables, util.filesizeDisplay(uploadableTotalSize)
            )
        ));
        $summaryList.append($uploadableImagesListItem);

        var $summarySubList = $('<ul>');
        $uploadableImagesListItem.append($summarySubList);

        if (numDupes > 0 && $(dupeOptionField).val() === 'replace') {
            $summarySubList.append($('<li>').text(
                "{0} image(s) are new".format(numUploadables-numDupes)
            ));
            $summarySubList.append($('<li>').text(
                "{0} image(s) are duplicates that will replace the originals".format(numDupes)
            ));
        }

        if (annotationsPerImage && numUploadables > 0) {
            $summarySubList.append($('<li>').text(
                "{0} image(s) have {2} specified, for a total of {1} {2}".format(
                    numImagesWithAnnotations, numTotalAnnotations, annotationCountUnits
                )
            ));

            if (numUploadables !== numImagesWithAnnotations) {
                $summarySubList.append($('<li>').text(
                    "{0} image(s) don't have {1} specified, so we'll auto-generate points for these images".format(
                        numUploadables-numImagesWithAnnotations, annotationCountUnits
                    )
                ));
            }
        }
    }

    /* Get the file details and display them in the table. */
    function updateFiles() {
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

            // Filename, filesize
            $filesTableRow.append($("<td>").text(files[i].file.name));

            var $sizeCell = $("<td>");
            $sizeCell.addClass('size_cell');
            $sizeCell.text(util.filesizeDisplay(files[i].file.size));
            $filesTableRow.append($sizeCell);

            // Filename status, to be filled in with an Ajax response
            var $statusCell = $("<td>");
            $statusCell.addClass('status_cell');
            $filesTableRow.append($statusCell);
            files[i].$statusCell = $statusCell;

            // Point/annotation count, filled in if points/annotations
            // are being uploaded
            var $annotationCountCell = $("<td>");
            $annotationCountCell.addClass('annotation_count_cell');
            $filesTableRow.append($annotationCountCell);
            files[i].$annotationCountCell = $annotationCountCell;

            // Add the row to the table
            $filesTable.append($filesTableRow);
            files[i].$tableRow = $filesTableRow;
        }

        // Initialize upload statuses to null
        for (i = 0; i < files.length; i++) {
            files[i].status = null;
        }

        var filenameList = new Array(files.length);
        for (i = 0; i < files.length; i++) {
            filenameList[i] = files[i].file.name;
        }

        if ($(metadataOptionField).val() === 'filenames') {

            // Ask the server (via Ajax) about the filenames: are they in the
            // right format? Do they have duplicate keys with existing files?
            $.ajax({
                // Data to send in the request
                data: {
                    filenames: filenameList
                },

                // Callback on successful response
                success: filenameStatusAjaxResponseHandler,

                type: 'POST',

                // URL to make request to
                url: uploadPreviewUrl
            });
        }
        else {
            // This is done if there is a CSV file present. This will do separate
            // error checking.
            $.ajax({
                // Data to send in the request
                data: {
                    filenames: filenameList,
                    csv_file_id: csvFileDictId
                },

                // Callback on successful response
                success: filenameStatusWithCsvAjaxResponseHandler,

                type: 'POST',

                // URL to make request to
                url: uploadPreviewWithCsvUrl
            });
        }
    }

    function filenameStatusWithCsvAjaxResponseHandler(response) {
        updateFilenameStatuses(response.statusList);
        updateMetadataPopupTable(response.statusList);
    }

    function updateMetadataPopupTable(statusList) {

        //Before adding anything to the table, set the table headers first
        var $csvFileTableHeader = $("<tr>");
        $csvFileTableHeader.append($("<th>").text("Filename"));
        // Loop through one of the vals in order to find out # of location key headers
        for (i = 0; i < statusList[0].metadata_list.values.length; i++)
        {
            var keyVal = i+1;
            $csvFileTableHeader.append($("<th>").text("Value " + keyVal));
        }
        $csvFileTableHeader.append($("<th>").text("Height"));
        $csvFileTableHeader.append($("<th>").text("Latitude"));
        $csvFileTableHeader.append($("<th>").text("Longitude"));
        $csvFileTableHeader.append($("<th>").text("Depth"));
        $csvFileTableHeader.append($("<th>").text("Camera"));
        $csvFileTableHeader.append($("<th>").text("Photographer"));
        $csvFileTableHeader.append($("<th>").text("Water Quality"));
        $csvFileTableHeader.append($("<th>").text("Strobes"));
        $csvFileTableHeader.append($("<th>").text("Framing Gear"));
        $csvFileTableHeader.append($("<th>").text("White Balance"));

        // Add header to the table
        $csvFileTable.append($csvFileTableHeader);

        for (i = 0; i < statusList.length; i++) {

            // Get the metadata list for a filename
            var metadata = statusList[i].metadata_list;
            var filename = statusList[i].filename;

            // Create a table row containing file details
            var $csvFileTableRow = $("<tr>");

            // append data into a row
            $csvFileTableRow.append($("<td>").text(filename));
            for (j = 0; j < metadata.values.length; j++)
            {
                $csvFileTableRow.append($("<td>").text(metadata.values[j]));
            }
            $csvFileTableRow.append($("<td>").text(metadata.height));
            $csvFileTableRow.append($("<td>").text(metadata.latitude));
            $csvFileTableRow.append($("<td>").text(metadata.longitude));
            $csvFileTableRow.append($("<td>").text(metadata.depth));
            $csvFileTableRow.append($("<td>").text(metadata.camera));
            $csvFileTableRow.append($("<td>").text(metadata.photographer));
            $csvFileTableRow.append($("<td>").text(metadata.water_quality));
            $csvFileTableRow.append($("<td>").text(metadata.strobes));
            $csvFileTableRow.append($("<td>").text(metadata.framing_gear));
            $csvFileTableRow.append($("<td>").text(metadata.white_balance));

            // Add the row to the table
            $csvFileTable.append($csvFileTableRow);
        }
    }

    function filenameStatusAjaxResponseHandler(response) {
        updateFilenameStatuses(response.statusList);
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
                $statusCell.text(statusList[i].message);

                numPreUploadErrors += 1;
            }
            else if (statusStr === 'ok') {
                $statusCell.text("Ready");
            }

            files[i].status = statusStr;
            if (statusList[i].hasOwnProperty('metadataKey')) {
                files[i].metadataKey = statusList[i].metadataKey;
            }
        }

        updateFilesTable();
    }

    // This calls an ajax view to process the CSV file just uploaded.
    function processCsvFile() {
        if (csvFileField.files.length === 0) {
            // No file, return.
            return;
        }

        var options = {
            // Expected datatype of response
            dataType: 'json',
            // URL to submit to
            url: csvFileProcessUrl,

            // Callback
            success: processCsvFileAjaxResponseHandler
        };
        $csvForm.ajaxSubmit(options);
        $csvFileStatusDisplay.text("Processing...");
    }

    function processCsvFileAjaxResponseHandler(response) {

        $csvFileStatusDisplay.empty();
        csvFileStatus = response.status;

        if (csvFileStatus === 'ok') {
            $csvFileStatusDisplay.text("CSV file is OK.");
            $csvFileStatusDisplay.removeClass('ok error');
            $csvFileStatusDisplay.addClass('ok');

            csvFileDictId = response.csv_dict_id;
        }
        else if (csvFileStatus === 'error') {
            var messageLines = response.message.split('\n');
            messageLines[0] = "Error: " + messageLines[0];

            for (i = 0; i < messageLines.length; i++) {
                $csvFileStatusDisplay.append(messageLines[i]);

                if (i < messageLines.length-1) {
                    $csvFileStatusDisplay.append('<br>');
                }
            }

            $csvFileStatusDisplay.removeClass('ok error');
            $csvFileStatusDisplay.addClass('error');
        }

        updateFilesTable();
    }

    /* Clear any previous results of annotation file processing. */
    function clearAnnotationFileStatus() {
        annotationFileStatus = null;
        $annotationFileStatusDisplay.empty();
        $annotationFileStatusDisplay.removeClass('ok error');

        annotationsPerImage = null;
        annotationDictId = null;
        // Update the files table's annotation count column.
        updateFilesTable();
    }

    /* Send the annotation file to the server via Ajax, to extract
     * the point/annotation data from the file. */
    function processAnnotationFile() {

        if (annotationFileField.files.length === 0) {
            // No annotation file; return.
            return;
        }

        var options = {
            // Expected datatype of response
            dataType: 'json',
            // URL to submit to
            url: annotationFileProcessUrl,

            // Callback
            success: annotationFileAjaxResponseHandler
        };
        $('#annotations_form').ajaxSubmit(options);
        $annotationFileStatusDisplay.text("Processing...");
    }

    function annotationFileAjaxResponseHandler(response) {

        $annotationFileStatusDisplay.empty();
        annotationFileStatus = response.status;

        if (response.status === 'ok') {
            $annotationFileStatusDisplay.text("Points/annotations file is OK.");
            $annotationFileStatusDisplay.removeClass('ok error');
            $annotationFileStatusDisplay.addClass('ok');

            annotationsPerImage = response.annotations_per_image;
            annotationDictId = response.annotation_dict_id;
        }
        else if (response.status === 'error') {
            var messageLines = response.message.split('\n');
            messageLines[0] = "Error: " + messageLines[0];

            for (i = 0; i < messageLines.length; i++) {
                $annotationFileStatusDisplay.append(messageLines[i]);

                if (i < messageLines.length-1) {
                    $annotationFileStatusDisplay.append('<br>');
                }
            }

            $annotationFileStatusDisplay.removeClass('ok error');
            $annotationFileStatusDisplay.addClass('error');
        }

        updateFilesTable();
    }

    /* Update the files table's annotation count column, which tells how
     * many points/annotations the annotation file has for each image file. */
    function updateFilesTableAnnotationCounts() {

        // First, clear the annotation count table cells and
        // hide the annotation count column.
        for (i = 0; i < files.length; i++) {
            files[i].$annotationCountCell.empty();
        }
        $('#files_table td.annotation_count_cell').hide();

        // If the annotations checkbox option is off, then we don't care about
        // annotations, so return.
        if (!$(annotationsCheckboxField).prop('checked')) {
            return;
        }
        // If annotationsPerImage is null, then we have no annotation count
        // data, so return.
        if (annotationsPerImage === null) {
            return;
        }
        // If none of the files are uploadable, then we have no data to add to
        // the column, so return.
        if (numUploadables === 0) {
            return;
        }

        // Otherwise, show the column and fill it in.
        $('#files_table td.annotation_count_cell').show();

        numImagesWithAnnotations = 0;
        numTotalAnnotations = 0;

        if (pointsOnlyField.value === 'yes') {
            annotationCountUnits = 'annotation(s)';
        }
        else {
            annotationCountUnits = 'point(s)';
        }

        for (i = 0; i < files.length; i++) {
            if (!files[i].isUploadable) {
                continue;
            }

            var metadataKey = files[i].metadataKey;

            if (annotationsPerImage.hasOwnProperty(metadataKey)) {
                // The image has annotations.
                files[i].$annotationCountCell.text(
                    annotationsPerImage[metadataKey] + ' ' + annotationCountUnits
                );
                numImagesWithAnnotations++;
                numTotalAnnotations += annotationsPerImage[metadataKey];
            }
            else {
                // The image doesn't have annotations.
                files[i].$annotationCountCell.text('0 ' + annotationCountUnits);
            }
        }
    }

    function enablePageLeaveWarning() {
        // When the user tries to leave the page by clicking a link,
        // closing the tab, etc., a confirmation dialog will pop up, with
        // the specified message and a generic message from the browser
        // like "Are you sure you want to leave this page?".
        window.onbeforeunload = function (e) {
            var message = "The upload is still going.";

            // Apparently some browsers take the message with e.returnValue,
            // and other browsers take it with this function's return value.
            // (Other browsers don't take any message...)
            e.returnValue = message;
            return message;
        };
    }
    function disablePageLeaveWarning() {
        window.onbeforeunload = null;
    }

    function startAjaxImageUpload() {

        // Define the options for $.ajaxSubmit().
        uploadOptions = {
            // Expected datatype of response
            dataType: 'json',
            // URL to submit to
            url: uploadStartUrl,

            // Callbacks
            beforeSend: ajaxUploadBeforeSend,
            beforeSubmit: ajaxUploadBeforeSubmit,
            success: ajaxUploadHandleResponse
        };

        // Create a new form out of the various form fields on the page.
        // This form will be used with ajaxSubmit().
        //
        // Side note: even if all the fields were already in a single form,
        // we'd have to create a new form for ajaxSubmit() anyway.  The
        // reason is that we want to disable the form fields on the page so
        // their values can't be changed mid-upload, and disabling form fields
        // means the fields can't be used with ajaxSubmit().
        //
        // Start by cloning the options form.
        $formToSubmit = $('#upload_options_form').clone();

        // clone() doesn't copy values of select inputs for some reason,
        // even when the data parameter to clone() is true. So copy these
        // values manually...
        $formToSubmit.find('#'+dupeOptionFieldId).val($(dupeOptionField).val());
        $formToSubmit.find('#'+metadataOptionFieldId).val($(metadataOptionField).val());

        // Add the (cloned) annotation fields.
        $formToSubmit.append($(annotationsCheckboxField).clone());
        $formToSubmit.append($(pointsOnlyField).clone());
        // And copy the select input's value manually...
        $formToSubmit.find('#'+pointsOnlyFieldId).val($(pointsOnlyField).val());
        // Also add a field for the shelved annotation dict's id.
        $formToSubmit.append($('<input type="text" name="annotation_dict_id">').val(annotationDictId));
        // Add a field for the shelved csv dict's id.
        $formToSubmit.append($('<input type="text" name="csv_dict_id">').val(csvFileDictId));
        // Disable all form fields and buttons on the page.
        $(filesField).prop('disabled', true);
        $(dupeOptionField).prop('disabled', true);
        $(metadataOptionField).prop('disabled', true);

        $(annotationsCheckboxField).prop('disabled', true);
        $(annotationFileField).prop('disabled', true);
        $(pointsOnlyField).prop('disabled', true);

        $annotationFileProcessButton.prop('disabled', true);

        $uploadStartButton.prop('disabled', true);
        $uploadStartButton.text("Uploading...");

        $uploadAbortButton.prop('disabled', false);
        $uploadAbortButton.show();

        // Initialize the upload progress stats.
        numUploaded = 0;
        numUploadSuccesses = 0;
        numUploadErrors = 0;
        uploadedTotalSize = 0;
        updateMidUploadSummary();

        // Warn the user if they're trying to
        // leave the page during the upload.
        enablePageLeaveWarning();

        // Finally, upload the first file.
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

    /* Callback before the Ajax form is submitted.
     * arr - the form data in array format
     * $form - the jQuery-wrapped form object
     * options - the options object used in the form submit call */
    function ajaxUploadBeforeSubmit(arr, $form, options) {
        // Add the next file to this upload request.
        // Push the file as 'file' so that it can be validated
        // on the server-side with an ImageUploadForm.
        arr.push({
            name: 'file',
            type: 'files',
            value: files[currentFileIndex].file
        });
    }

    /* Callback before the Ajax form is submitted.
     * Provides access to the XHR object. */
    function ajaxUploadBeforeSend(jqXHR, settings) {
        uploadXhrObj = jqXHR;
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
            styleFilesTableRow(currentFileIndex, 'uploaded');
            numUploadSuccesses++;
        }
        else {  // 'error'
            styleFilesTableRow(currentFileIndex, 'upload_error');
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

    /* Find a file to upload, starting from the current currentFileIndex.
     * If the current file is not uploadable, increment the currentFileIndex
     * and try the next file.  Once an uploadable file is found, begin
     * uploading that file. */
    function uploadFile() {
        while (currentFileIndex < files.length) {

            if (files[currentFileIndex].isUploadable) {
                // An uploadable file was found, so upload it.
                $formToSubmit.ajaxSubmit(uploadOptions);

                // In the files table, update the status for that file.
                var $statusCell = files[currentFileIndex].$statusCell;
                $statusCell.empty();
                styleFilesTableRow(currentFileIndex, 'uploading');
                $statusCell.text("Uploading...");

                if ($filesTableAutoScrollCheckbox.prop('checked')) {
                    // Scroll the upload table's window to the file
                    // that's being uploaded.
                    // Specifically, scroll the file to the
                    // middle of the table view.
                    var scrollRowToTop = files[currentFileIndex].$tableRow[0].offsetTop;
                    var tableContainerHalfMaxHeight = parseInt($filesTableContainer.css('max-height')) / 2;
                    var scrollRowToMiddle = Math.max(scrollRowToTop - tableContainerHalfMaxHeight, 0);
                    $filesTableContainer.scrollTop(scrollRowToMiddle);
                }

                return;
            }

            // No uploadable file was found yet; keep looking.
            currentFileIndex++;
        }

        // Reached the end of the files array.
        $uploadStartButton.text("Upload Complete");

        postUploadCleanup();
    }

    function postUploadCleanup() {
        uploadXhrObj = null;

        $uploadAbortButton.hide();
        $uploadAbortButton.prop('disabled', true);

        disablePageLeaveWarning();
    }

    function updateMidUploadSummary() {
        $midUploadSummary.empty();

        var summaryTextLines = [];

        summaryTextLines.push($('<strong>').text("Uploaded: {0} of {1} ({2} of {3}, {4}%)".format(
            numUploaded,
            numUploadables,
            util.filesizeDisplay(uploadedTotalSize),
            util.filesizeDisplay(uploadableTotalSize),
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

    // This displays a confirmation message to the user, and displays metadata applied to each file
    // This will only display a dialog box if the CSV file upload is selected. Otherwise it is ignored.
    // After confirmation, this will then begin the image upload process
    function confirmUpload() {
        var metadataOptionFieldValue = $(metadataOptionField).val();
        if (metadataOptionFieldValue !== "csv") {
            startAjaxImageUpload();
        }
        else {
            $csvFileUploadPreview.dialog({
                resizable: false,
                modal: true,
                width:'auto',
                buttons: {
                    "Upload": function() {
                        $ (this).dialog("close");
                        startAjaxImageUpload();
                    },
                    "Abort": function() {
                        $(this).dialog("close");
                    }
                }
            });
        }
    }

    /* Abort the Ajax upload.
     *
     * Notes:
     *
     * - If a file has finished uploading and is currently processing on
     * the server, and the user clicks Abort, that file MAY still finish
     * getting processed, and the result won't be received by the client
     * because it is no longer listening for the response.  This is
     * undesired behavior, but there is not much that can be done about this.
     *
     * - There should be no concurrency issues, because Javascript is single
     * threaded, and event handling code is guaranteed to complete before the
     * invocation of an AJAX callback or a later event's callback.  At least
     * in the absence of Web Workers.
     * http://stackoverflow.com/questions/9999056/are-event-handlers-guaranteed-to-complete-before-ajax-callbacks-are-invoked */
    function abortAjaxUpload() {
        var confirmation = window.confirm("Are you sure you want to abort the upload?");

        if (confirmation) {
            if (uploadXhrObj !== null) {
                uploadXhrObj.abort();
                $uploadStartButton.text("Upload aborted");
                postUploadCleanup();
            }
            // Else, the upload finished before the user could confirm the
            // abort (so there's nothing to abort anymore).  This could
            // happen in Firefox, where scripts don't stop even when a
            // confirmation dialog is showing.
        }
    }

    // Remnants of an attempt at a progress bar...
/*    function prepareProgressBar() {
        $('#progress_bar').progressBar();
    }*/


    /* Public methods.
     * These are the only methods that need to be referred to as
     * ImageUploadFormHelper.methodname. */
    return {

        /* Initialize the upload form. */
        initForm: function(params){

            // Get the parameters.
            uploadPreviewUrl = params.uploadPreviewUrl;
            annotationFileProcessUrl = params.annotationFileProcessUrl;
            uploadStartUrl = params.uploadStartUrl;
            csvFileProcessUrl = params.csvFileProcessUrl;
            uploadPreviewWithCsvUrl = params.uploadPreviewWithCsvUrl;
            //uploadProgressUrl = params.uploadProgressUrl;

            // Upload status summary elements.
            $preUploadSummary = $('#pre_upload_summary');
            $midUploadSummary = $('#mid_upload_summary');
            // Annotation file status elements.
            $annotationFileStatusDisplay = $('#annotation_file_status');
            // CSV file status elements.
            $csvFileStatusDisplay = $('#csv_file_status');
            // CSV file preview upload div.
            $csvFileUploadPreview = $("#csv_file_upload_preview");
            // The metadata preview table.
            $csvFileTable = $("#metadata_table");

            // The upload file table.
            $filesTable = $('table#files_table');
            // And its container element.
            $filesTableContainer = $('#files_table_container');
            // The checkbox to enable/disable auto-scrolling
            // of the files table.
            $filesTableAutoScrollCheckbox = $('input#files_table_auto_scroll_checkbox');
            // And its container element.
            $filesTableAutoScrollCheckboxContainer = $('#files_table_auto_scroll_checkbox_container');

            // Field elements.
            filesField = $('#id_files')[0];
            dupeOptionField = $('#' + dupeOptionFieldId)[0];
            metadataOptionField = $('#' + metadataOptionFieldId)[0];
            annotationsCheckboxField = $('#' + annotationsCheckboxFieldId)[0];
            $annotationsCheckboxLabel = $('#annotations_checkbox_label');
            annotationFileField = $('#id_annotations_file')[0];
            csvFileField = $('#id_csv_file')[0];
            pointsOnlyField = $('#' + pointsOnlyFieldId)[0];

            // Other form field related elements.
            $dupeOptionWrapper = $("#id_skip_or_replace_duplicates_wrapper");
            $annotationSection = $('#annotations_section');
            $annotationForm = $('#annotations_form');
            $pointGenText = $('#auto_generate_points_page_section');
            $csvForm = $('#csv_form');

            // Button elements.
            $annotationFileProcessButton = $('#annotation_file_process_button');
            $uploadStartButton = $('#id_upload_submit');
            $uploadAbortButton = $('#id_upload_abort_button');

            $uploadStartInfo = $('#upload_start_info');

            // Set onchange handlers for form fields.
            $(filesField).change( function(){
                updateFiles();
                updateFilesTable();
            });

            $(dupeOptionField).change( function() {
                updateFilesTable();
            });

            $(metadataOptionField).change( function(){
                // For now, annotation upload is only allowed when getting
                // metadata from filenames.
                if ($(metadataOptionField).val() === 'filenames') {
                    $annotationSection.show();
                    $(annotationsCheckboxField).prop('disabled', false);
                }
                else {
                    $annotationSection.hide();
                    $(annotationsCheckboxField).prop('checked', false);
                    $(annotationsCheckboxField).prop('disabled', true);
                }

                updateFiles();
                updateFilesTable();
            });

            // Ensure that the annotations section is also toggled properly
            // upon page load.  Yes, this code is duplicated from above...
            if ($(metadataOptionField).val() === 'filenames') {
                $annotationSection.show();
                $(annotationsCheckboxField).prop('disabled', false);
            }
            else {
                $annotationSection.hide();
                $(annotationsCheckboxField).prop('checked', false);
                $(annotationsCheckboxField).prop('disabled', true);
            }

            // Make sure the files table initially looks right
            updateFilesTable();


            // Separate-dialog help text for specify_metadata field.
            // Can show by clicking "(More info)".
            $("#id_specify_metadata_dialog_help_text_link").click(function() {

                // TODO: Reduce the text size in this dialog
                // TODO: Come up with sensible (possibly flexible) dimensions
                $("#id_specify_metadata_dialog_help_text").dialog({
                        width: 800,
                        height: 400,
                        title: "Specifying Metadata"
                });
            });

            // Extra help text for annotation file field.
            $annoFileExtraHelpText = $("#id_annotations_file_extra_help_text");
            $annoFileExtraHelpTextLink = $("#id_annotations_file_extra_help_text_link");

            $annoFileExtraHelpTextLink.click(function() {
                if ($annoFileExtraHelpText.is(':hidden')) {
                    $annoFileExtraHelpText.show();
                    $(this).text("(Less info)");
                }
                else {
                    $annoFileExtraHelpText.hide();
                    $(this).text("(More info)");
                }
            });

            // Extra help text for image files field.
            $filesExtraHelpText = $("#id_files_extra_help_text");
            $filesExtraHelpTextLink = $("#id_files_extra_help_text_link");

            $filesExtraHelpTextLink.click(function() {
                if ($filesExtraHelpText.is(':hidden')) {
                    $filesExtraHelpText.show();
                    $(this).text("(Less info)");
                }
                else {
                    $filesExtraHelpText.hide();
                    $(this).text("(More info)");
                }
            });

            // csv field event handlers.
            $(metadataOptionField).change(function() {
                updateFiles();
                updateFilesTable();
            });

            $(csvFileField).change(function() {
                processCsvFile();
            });

            // Annotation field event handlers.
            $(annotationsCheckboxField).change(function() {
                updateFilesTable();
            });
            $(pointsOnlyField).change(function() {
                clearAnnotationFileStatus();
                processAnnotationFile();
            });
            $(annotationFileField).change(function() {
                clearAnnotationFileStatus();
                processAnnotationFile();
            });

            // Button event handlers.
            $annotationFileProcessButton.click(function() {
                clearAnnotationFileStatus();
                processAnnotationFile();
            });
            // This one begins file upload. But if CSV files are made use of, do
            // an extra check with the user to see if the data is correct.
            $uploadStartButton.click(function() {
                confirmUpload();
            });
            $uploadAbortButton.click(abortAjaxUpload);

        }
    }
})();

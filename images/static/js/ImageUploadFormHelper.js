/* The following design pattern is from
 * http://stackoverflow.com/a/1479341/859858 */
var ImageUploadFormHelper = (function() {

    var previewArea = null;
    var previewTable = null;
    var filesField = null;

    var sourceId = null;
    var hasAnnotations = null;

    var numOfDupes = 0;
    var numOfErrors = 0;

    var uploadStartUrl = null;
    //var uploadProgressUrl = null;

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
    Get the file details from the form field, and
    display the files in a list.
    */
    function previewUpload() {
        previewTable.empty();

        var files = filesField.files;

        if (!files) {
            numOfDupes = 0;
            numOfErrors = 0;
            return;
        }

        var i,j;
        var totalBytes = 0;

        for (i = 0; i < files.length; i++) {
            totalBytes += files[i].size;
        }

        var tableHeader = $("<tr>");
        tableHeader.append($("<th>").text(files.length + " files"));
        tableHeader.append($("<th>").text(filesizeDisplay(totalBytes)));
        tableHeader.append($("<th>").attr("id", "previewColHeader_status"));
        previewTable.append(tableHeader);

        for (i = 0; i < files.length; i++) {

            // Create a table row containing file details
            var fileEntry = $("<tr>").attr("id", "previewFile"+i);

            // filename, filesize, dupe or not (last one is filled in with AJAX)
            fileDetails = [files[i].name,
                           filesizeDisplay(files[i].size)];

            for (j = 0; j < fileDetails.length; j++) {
                fileEntry.append($("<td>").text(fileDetails[j]));
            }
            fileEntry.append($("<td>").attr("id", "previewFile"+i+"_status"));

            previewTable.append(fileEntry);
        }

        var filenameList = new Array(files.length);
        for (i = 0; i < files.length; i++) {
            filenameList[i] = files[i].name;
        }

        // AJAX call to a Django method in ajax.py of this app
        if ($("#id_specify_metadata").val() == 'filenames') {
            Dajaxice.CoralNet.images.ajax_assess_file_status(
                ajaxUpdateStatus,    // JS callback that the ajax.py method returns to.
                {'filenames': filenameList,
                 'sourceId': sourceId,
                 'checkDupes': true}    // Args to the ajax.py method.
            );
        }
        else {
            var statusList = new Array(files.length);
            for (i = 0; i < files.length; i++) {
                statusList[i] = {'status':'Ready'};
            }
            updateStatus(statusList);
        }
    }

    function updateFormFields() {
        if ($("#id_specify_metadata").val() == 'filenames') {
            $("#id_skip_or_replace_duplicates_wrapper").show();
        }
        else {
            $("#id_skip_or_replace_duplicates_wrapper").hide();
        }

        if (numOfErrors > 0) {
            $("#id_upload_submit").attr('disabled', true);
            $("#id_upload_submit").attr('value', "Cannot upload with errors");
        }
        else {
            $("#id_upload_submit").attr('disabled', false);

            if (hasAnnotations) {
                $("#id_upload_submit").attr('value', "Upload Images and Annotations");
            }
            else {
                $("#id_upload_submit").attr('value', "Upload Images");
            }
        }
    }

    function updateStatus(statusList) {
        var i;
        var numOfDupes = 0, numOfErrors = 0;

        for (i = 0; i < statusList.length; i++) {

            var statusTableCell = $("#previewFile"+i+"_status");
            statusTableCell.empty();

            var statusStr = statusList[i].status;
            var containerElmt;

            if (statusStr == 'Duplicate found') {

                var linkToDupe = $("<a>").text(statusStr);
                linkToDupe.attr("href", statusList[i].url);    // Link to the image's page
                linkToDupe.attr("target", "_blank");    // Open in new window

                containerElmt = $("<span>").addClass("dupeStatus");
                containerElmt.append(linkToDupe);
                statusTableCell.append(containerElmt);

                numOfDupes += 1;
            }
            else if (statusStr == 'Filename error') {
                containerElmt = $("<span>").addClass("errorStatus");
                containerElmt.text(statusStr);
                statusTableCell.append(containerElmt);

                numOfErrors += 1;
            }
            else if (statusStr == 'Ready') {
                statusTableCell.text(statusStr);
            }
        }

        var overallStatus = "", errorStatus = "", dupeStatus = "";

        if (numOfErrors > 0)
            errorStatus = numOfErrors + " errors";
        if (numOfDupes > 0)
            dupeStatus = numOfDupes + " duplicates";

        overallStatus += errorStatus + ' ' + dupeStatus;
        $("#previewColHeader_status").text(overallStatus);

        // Make sure to update the form once more after the AJAX call completes
        updateFormFields();
    }

    /*
    This AJAX callback function is called by the browser window object.
    It's not called by the ImageUploadFormHelper object.  Therefore, don't
    use "this" in this function to refer to an ImageUploadFormHelper member.
     */
    function ajaxUpdateStatus(data) {
        updateStatus(data.statusList);
    }

    function ajaxUpload() {

        // Submit the form.
        var options = {
            dataType: 'json',    // Expected datatype of response
            url: uploadStartUrl,
            beforeSubmit: addFileToAjaxRequest,
            success: ajaxUploadHandleResponse    // Callback
        };
        $('#id_upload_form').ajaxSubmit(options);

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

    // Remnants of an attempt at a progress bar...
/*    function prepareProgressBar() {
        $('#progress_bar').progressBar();
    }*/

    function addFileToAjaxRequest(arr, $form, options) {
        // Push the file as 'files' so that it can be validated
        // on the server-side with an ImageUploadForm.
        //
        // Just push the first file onto the Ajax request.
        // TODO: Implement submitting multiple files, one by one.
        arr.push({
            name: 'files',
            type: 'files',
            value: filesField.files[0]
        });
    }

    function ajaxUploadHandleResponse(response) {

        // TODO: Show this upload status message in a results table
        // on the page.
        console.log(response.message);

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

            previewArea = $('#previewArea');
            previewTable = $("<table>").attr("id", "previewTable");
            previewArea.append(previewTable);

            filesField = $('#id_files')[0];

            // Initialize the status of form fields (show/hide, etc.).
            updateFormFields();

            // Set onchange handlers for form fields.
            $(filesField).change( function(){
                previewUpload();
                updateFormFields();
            });

            // This'll become relevant again when we support other methods of specifying metadata
            /*        $("#id_specify_metadata").change( function(){
             previewUpload();
             updateFormFields();
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
            $("#id_upload_submit").click(ajaxUpload);
        }
    }
})();

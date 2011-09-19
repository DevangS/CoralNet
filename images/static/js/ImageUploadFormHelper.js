var ImageUploadFormHelper = {

    previewArea: null,
    previewTable: null,

    sourceId: null,
    hasAnnotations: null,

    numOfDupes: 0,
    numOfErrors: 0,

    initForm: function(previewAreaId, sourceId, hasAnnotations){

        // Initializing.
        this.previewArea = $('#' + previewAreaId);
        this.sourceId = sourceId;
        this.hasAnnotations = hasAnnotations;

        this.previewTable = $("<table>").attr("id", "previewTable");
        this.previewArea.append(this.previewTable);

        // Initialize the status of form fields (show/hide, etc.).
        this.updateFormFields();

        // Set onchange handlers for form fields.
        $("#id_files").change( function(){
            ImageUploadFormHelper.previewUpload();
            ImageUploadFormHelper.updateFormFields();
        });

        // This'll become relevant again when we support other methods of specifying metadata
/*        $("#id_specify_metadata").change( function(){
            ImageUploadFormHelper.previewUpload();
            ImageUploadFormHelper.updateFormFields();
        });*/
    },

    filesizeDisplay: function(bytes) {
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
    },

    /*
    Get the file details from the form field, and
    display the files in a list.
    */
    previewUpload: function() {
        this.previewTable.empty();

        var fileField = $("#id_files").get(0);
        var files = fileField.files;

        if (!files) {
            this.numOfDupes = 0;
            this.numOfErrors = 0;
            return;
        }

        var i,j;
        var totalBytes = 0;

        for (i = 0; i < files.length; i++) {
            totalBytes += files[i].size;
        }

        var tableHeader = $("<tr>");
        tableHeader.append($("<th>").text(files.length + " files"));
        tableHeader.append($("<th>").text(this.filesizeDisplay(totalBytes)));
        tableHeader.append($("<th>").attr("id", "previewColHeader_status"));
        this.previewTable.append(tableHeader);

        for (i = 0; i < files.length; i++) {

            // Create a table row containing file details
            var fileEntry = $("<tr>").attr("id", "previewFile"+i);

            // filename, filesize, dupe or not (last one is filled in with AJAX)
            fileDetails = [files[i].name,
                           this.filesizeDisplay(files[i].size)];

            for (j = 0; j < fileDetails.length; j++) {
                fileEntry.append($("<td>").text(fileDetails[j]));
            }
            fileEntry.append($("<td>").attr("id", "previewFile"+i+"_status"));

            this.previewTable.append(fileEntry);
        }

        var filenameList = new Array(files.length);
        for (i = 0; i < files.length; i++) {
            filenameList[i] = files[i].name;
        }

        // AJAX call to a Django method in ajax.py of this app
        if ($("#id_specify_metadata").val() == 'filenames') {
            Dajaxice.CoralNet.images.ajax_assess_file_status(
                this.ajaxUpdateStatus,    // JS callback that the ajax.py method returns to.
                {'filenames': filenameList,
                 'sourceId': this.sourceId,
                 'checkDupes': true}    // Args to the ajax.py method.
            );
        }
        else {
            var statusList = new Array(files.length);
            for (i = 0; i < files.length; i++) {
                statusList[i] = {'status':'Ready'};
            }
            this.updateStatus(statusList);
        }
    },

    updateFormFields: function() {
        if ($("#id_specify_metadata").val() == 'filenames') {
            $("#id_skip_or_replace_duplicates_wrapper").show();
        }
        else {
            $("#id_skip_or_replace_duplicates_wrapper").hide();
        }

        if (this.numOfErrors > 0) {
            $("#id_upload_submit").attr('disabled', true);
            $("#id_upload_submit").attr('value', "Cannot upload with errors");
        }
        else {
            $("#id_upload_submit").attr('disabled', false);

            if (this.hasAnnotations) {
                $("#id_upload_submit").attr('value', "Upload Images and Annotations");
            }
            else {
                $("#id_upload_submit").attr('value', "Upload Images");
            }
        }
    },

    updateStatus: function(statusList) {
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

        this.numOfDupes = numOfDupes;
        this.numOfErrors = numOfErrors;

        var overallStatus = "", errorStatus = "", dupeStatus = "";

        if (numOfErrors > 0)
            errorStatus = numOfErrors + " errors";
        if (numOfDupes > 0)
            dupeStatus = numOfDupes + " duplicates";

        overallStatus += errorStatus + ' ' + dupeStatus;
        $("#previewColHeader_status").text(overallStatus);

        // Make sure to update the form once more after the AJAX call completes
        this.updateFormFields();
    },

    /*
    This AJAX callback function is called by the browser window object.
    It's not called by the ImageUploadFormHelper object.  Therefore, don't
    use "this" in this function to refer to an ImageUploadFormHelper member.
     */
    ajaxUpdateStatus: function(data) {
        ImageUploadFormHelper.updateStatus(data.statusList);
    }
};

// Selects all of the checkboxes given the value of the check all box.
function selectall() {
    var id = "#id_selected";
    if ($(id).attr('checked'))
        setCheckedRows(true);
    else
        setCheckedRows(false);
}

// Given the row/column, this will return the value at that cell in the table.
function getValueFromCell(row, column)
{
    return $('#metadataFormTable')[0].rows[row+1].cells[column+1].childNodes[0].value;
}

// Given the row/column, this sets the value in that cell to what value is.
function setValueFromCell(row, column, value)
{
    $('#metadataFormTable')[0].rows[row+1].cells[column+1].childNodes[0].value = value;
}

// This returns an bool array that represents what checkboxes are checked.
function checkedRows() {
    var rows = $("#metadataFormTable tr").length;
    var checkedRows = new Array();
    for (var i = 0; i < rows; i++)
    {
        var id = "#id_form-" + i + "-selected";
        if ($(id).attr('checked') != null)
            checkedRows[i] = true;
        else
            checkedRows[i] = false;
    }
    return checkedRows;
}

// Takes a boolean value that sets all of the checkboxes to that value.
function setCheckedRows(checked) {
    var rows = $("#metadataFormTable tr").length;
    for (var i = 0; i < rows; i++)
    {
        var id = "#id_form-" + i + "-selected";
        $(id).attr("checked", checked);
    }
}

// This will handle updating all checked rows in the form. This is called whenever a user
// types in one of the text fields.
function updateCheckedRowFields(row, column) {
    var checked = checkedRows();
    if (checked[row] == false) return;
    var input = getValueFromCell(row, column);
    for (var i = 0; i < checked.length; i++)
    {
        if(checked[i] == true) setValueFromCell(i, column, input);
    }
}

// Update indicators that a value in the form has changed.
function updateMetadataChangeStatus(fieldId) {

    // Un-disable the Save Edits button
    $('#id_metadata_form_save_button').prop('disabled', false);

    // Update text next to the Save button
    $('#id_metadata_save_status').text("There are unsaved changes");

    // Add warning when trying to navigate away
    util.pageLeaveWarningEnable("You have unsaved changes.");

    // Style the changed field differently, so the user can keep track of
    // what's changed
    $(fieldId).addClass('changed').removeClass('error');
}

// This initializes the form with the correct bindings.
function setUpBindings(params) {
    var rows = $("#metadataFormTable tr").length;
    var columns = $("#metadataFormTable tr")[0].cells.length;
    var id;
    for (var i = 1; i < rows; i++)
    {
        // This row should correspond to an image.

        for (var j = 3; j < columns; j++)
        {
            // This column should correspond to an editable field.

            id = '#' + $('#metadataFormTable')[0].rows[i].cells[j].childNodes[0].getAttribute('id');

            if (j == 3)
            {
                // This is the date field.
                $(id).datepicker({ dateFormat: 'yy-mm-dd' });
                setRowColumnBindingsChange({id: id, isDate: true});
            }
            else
            {
                setRowColumnBindingsChange({id: id, isDate: false});
                setRowColumnBindingsKeyUp(id);
            }
        }
    }

    // When the top checkbox is checked/unchecked, check/uncheck
    // all the checkboxes
    id = "#id_selected";
    $(id).bind("change", function() {
        selectall();
    });

    // When the metadata save button is clicked...
    id = '#id_metadata_form_save_button';
    $(id).bind("click", submitMetadataForm.curry(params.metadataSaveAjaxUrl));

/*  For later use (ajax)
    id = "#id_view";
    $(id).bind("change", function() {
        ajax(ajax_url);
    });*/
}

// Given the id, this will set a key-up binding that calls
// updateCheckedRowFields with the given row and column of the table form.
function setRowColumnBindingsKeyUp(id) {
    $(id).bind("keyup", function() {
        var row_index = $(this).parent().parent().index('tr');
        var col_index = $(this).parent().index('tr:eq('+row_index+') td');
        updateCheckedRowFields(row_index-1, col_index-1);
    });
}

function setRowColumnBindingsChange(params) {
    if (params.isDate === true) {
        $(params.id).bind("change", function() {
            // Update indicators that a value in the form
            // has changed.
            updateMetadataChangeStatus(params.id);

            // Update checked rows.
            var row_index = $(this).parent().parent().index('tr');
            var col_index = $(this).parent().index('tr:eq('+row_index+') td');
            updateCheckedRowFields(row_index-1, col_index-1);
        });
    }
    else {
        $(params.id).bind("change", function() {
            // Update indicators that a value in the form
            // has changed.
            updateMetadataChangeStatus(params.id);
        });
    }
}

// Submit the metadata form (using Ajax).
function submitMetadataForm(metadataSaveAjaxUrl) {
    // Disable the save button
    $('#id_metadata_form_save_button').prop('disabled', true);

    // Remove any error messages from a previous edit attempt
    $('ul#id_metadata_errors_list').empty();

    // Update text next to the Save button
    $('#id_metadata_save_status').text("Now saving...");

    // Submit the metadata form with Ajax
    $.ajax({
        // Data to send in the request
        data: $('#id_metadata_form').serialize(),

        // Callback on successful response
        success: metadataSaveAjaxResponseHandler,

        type: 'POST',

        // URL to make request to
        url: metadataSaveAjaxUrl
    });
}

// This function runs when the metadata-save-via-Ajax returns from
// the server side.
function metadataSaveAjaxResponseHandler(response) {
    console.log(response.status);

    // Update text next to the Save button
    if (response.status === 'success') {
        $('#id_metadata_save_status').text("All changes saved");

        // Disable "You have unsaved changes" warning when trying to navigate away
        util.pageLeaveWarningDisable();

        // Remove field stylings
        $('#id_metadata_form input[type="text"]').removeClass('changed', 'error');
    }
    else {  // 'error'
        $('#id_metadata_save_status').text("There were error(s); couldn't save");

        var $errorsList = $('ul#id_metadata_errors_list');
        var numOfErrors = response.errors.length;

        for (var i = 0; i < numOfErrors; i++) {
            // Display the error message(s) next to the Save button
            $errorsList.append($('<li>').text(
                response.errors[i].errorMessage
            ));
            // Style the field to indicate an error
            $('#' + response.errors[i].fieldId).addClass('error').removeClass('changed');
        }
    }
}

/* For later use (ajax)
function ajax(url) {

    var checked = $("#id_view").attr('checked');
    $.ajax({
        type: "POST",
        url:url,
        data: {
            'checked': checked
        },
        success: function(data){
            $("#result").val(data.result);
        },
        error: function(request){
            console.log(request.responseText);
        }
    });
}
*/

function initMetadataForm(params) {
    // Initialize save status
    $('#id_metadata_save_status').text("All changes saved");
    $('#id_metadata_form_save_button').prop('disabled', true);

    // Set up event bindings
    setUpBindings(params);
}
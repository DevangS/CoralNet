var ATS = {

    $saveButton: undefined,
    $settingsForm: undefined,

    settings: {
        pointMarker: undefined,
        pointMarkerSize: undefined,
        pointMarkerIsScaled: undefined,
        unannotatedColor: undefined,
        robotAnnotatedColor: undefined,
        humanAnnotatedColor: undefined,
        selectedColor: undefined
    },
    $fields: {
        pointMarker: undefined,
        pointMarkerSize: undefined,
        pointMarkerIsScaled: undefined,
        unannotatedColor: undefined,
        robotAnnotatedColor: undefined,
        humanAnnotatedColor: undefined,
        selectedColor: undefined
    },
    validators: {
        pointMarkerSize: undefined
    },


    init: function(settingsFieldSelectors) {
        ATS.$saveButton = $('#saveSettingsButton');
        ATS.$settingsForm = $('#annotationToolSettingsForm');

        ATS.$fields.pointMarker = $('#id_point_marker');
        ATS.$fields.pointMarkerSize = $('#id_point_marker_size');
        ATS.$fields.pointMarkerIsScaled = $('#id_point_marker_is_scaled');
        ATS.$fields.unannotatedColor = $('#id_unannotated_point_color');
        ATS.$fields.robotAnnotatedColor = $('#id_robot_annotated_point_color');
        ATS.$fields.humanAnnotatedColor = $('#id_human_annotated_point_color');
        ATS.$fields.selectedColor = $('#id_selected_point_color');

        ATS.validators.pointMarkerSize = ATS.pointMarkerSizeIsValid;

        // Initialize settings
        ATS.updateSettingsObj();

        // When the show settings button is clicked, show settings;
        // when the hide settings button is clicked, hide settings.
        $('#id_button_show_settings').click(ATS.showSettings);
        $('#id_button_hide_settings').click(ATS.hideSettings);

        // When a settings field is changed:
        // - enable the save button.
        // - update the settings object, which the annotation tool code
        //   refers to during point drawing, etc.
        // - redraw all points
        for (var fieldName in ATS.$fields) {
            if (!ATS.$fields.hasOwnProperty(fieldName)){ continue; }

            ATS.$fields[fieldName].change( function() {
                ATS.enableSaveButton();
                ATS.updateSettingsObj();
                ATH.redrawAllPoints();
            });
        }

        // When the save button is clicked, save.
        ATS.$saveButton.click(ATS.saveSettings);
    },

    showSettings: function() {
        $('#id_settings_wrapper').show();
        $('#id_button_show_settings').hide();
    },
    hideSettings: function() {
        $('#id_settings_wrapper').hide();
        $('#id_button_show_settings').show();
    },

    /* Update: $fields -> settings.
     * Revert settings -> $fields for any erroneous field values.
     */
    updateSettingsObj: function() {
        for (var fieldName in ATS.$fields) {
            if (!ATS.$fields.hasOwnProperty(fieldName)){ continue; }

            var $field = ATS.$fields[fieldName];

            if (ATS.validators.hasOwnProperty(fieldName)) {
                var fieldIsValid = ATS.validators[fieldName]();
                if (fieldIsValid === false) {
                    ATS.revertField(fieldName);
                    continue;
                }
            }

            // Update the setting
            if ($field.hasClass('color'))
                ATS.settings[fieldName] = '#' + $field.val();
            else
                ATS.settings[fieldName] = $field.val();
        }
    },

    pointMarkerSizeIsValid: function() {
        var fieldValue = ATS.$fields.pointMarkerSize.val();

        return (util.isIntStr(fieldValue)
                && parseInt(fieldValue) >= 1
                && parseInt(fieldValue) <= 30);
    },
    revertField: function(fieldName) {
        ATS.$fields[fieldName].val(ATS.settings[fieldName]);
    },

    enableSaveButton: function() {
        ATS.$saveButton.removeAttr('disabled');
        ATS.$saveButton.text("Save settings");
    },
    saveSettings: function() {
        ATS.$saveButton.attr('disabled', 'disabled');
        ATS.$saveButton.text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_settings(
            // JS callback that handles the ajax.py function's return value.
            ATS.saveSettingsAjaxCallback,
            // Args to the ajax.py function.
            {'submitted_settings_form': ATS.$settingsForm.serializeArray()}
        );
    },
    saveSettingsAjaxCallback: function(returnDict) {
        if (returnDict.success === true)
            ATS.$saveButton.text("Settings saved");
        else
            ATS.$saveButton.text("Error");
    }
};
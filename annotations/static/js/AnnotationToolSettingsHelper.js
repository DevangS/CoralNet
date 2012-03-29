var ATS = {

    $saveButton: undefined,
    $settingsForm: undefined,

    settings: {
        pointMarker: undefined,
        unannotatedColor: undefined,
        robotAnnotatedColor: undefined,
        humanAnnotatedColor: undefined,
        selectedColor: undefined
    },
    $settingsFields: {
        pointMarker: undefined,
        unannotatedColor: undefined,
        robotAnnotatedColor: undefined,
        humanAnnotatedColor: undefined,
        selectedColor: undefined
    },


    init: function(settingsFieldSelectors) {
        ATS.$saveButton = $('#saveSettingsButton');
        ATS.$settingsForm = $('#annotationToolSettingsForm');

        ATS.$settingsFields.pointMarker = $('#id_point_marker');
        ATS.$settingsFields.unannotatedColor = $('#id_unannotated_point_color');
        ATS.$settingsFields.robotAnnotatedColor = $('#id_robot_annotated_point_color');
        ATS.$settingsFields.humanAnnotatedColor = $('#id_human_annotated_point_color');
        ATS.$settingsFields.selectedColor = $('#id_selected_point_color');

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
        for (var fieldName in ATS.$settingsFields) {
            if (!ATS.$settingsFields.hasOwnProperty(fieldName)){ continue; }

            ATS.$settingsFields[fieldName].change( function() {
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

    updateSettingsObj: function() {
        for (var fieldName in ATS.$settingsFields) {
            if (!ATS.$settingsFields.hasOwnProperty(fieldName)){ continue; }

            var $field = ATS.$settingsFields[fieldName];
            if ($field.hasClass('color'))
                ATS.settings[fieldName] = '#' + $field.val();
            else
                ATS.settings[fieldName] = $field.val();
        }
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
    saveSettingsAjaxCallback: function() {
        ATS.$saveButton.text("Settings saved");
    }
};
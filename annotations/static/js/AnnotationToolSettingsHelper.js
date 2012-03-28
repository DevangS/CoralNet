var ATS = {

    $saveButton: undefined,
    $settingsForm: undefined,

    init: function(settingsFieldSelectors) {
        ATS.$saveButton = $('#saveSettingsButton');
        ATS.$settingsForm = $('#annotationToolSettingsForm');

        // When the show settings button is clicked, show settings;
        // when the hide settings button is clicked, hide settings.
        $('#id_button_show_settings').click(ATS.showSettings);
        $('#id_button_hide_settings').click(ATS.hideSettings);

        // When a settings field is changed, enable the save button.
        var $settingsFields = $();
        for (var i = 0; i < settingsFieldSelectors.length; i++) {
            $settingsFields = $settingsFields.add(settingsFieldSelectors[i]);
        }
        $settingsFields.each( function() {
            $(this).change(ATS.enableSaveButton);
        });

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
var VSH = {

    $pageViewField: undefined,
    $imagePatchViewFieldsWrapper: undefined,
    $imageOrMetadataViewFieldsWrapper: undefined,

    sourceUsesMachineAnnotator: undefined,

    init: function(sourceUsesMachineAnnotator) {
        VSH.$pageViewChoices = $('#id_page_view_wrapper input[type="radio"]');
        VSH.$pageViewPatchesChoice = $('#id_page_view_wrapper input[value="patches"]');

        VSH.$imagePatchViewFieldsWrapper = $('#id_image_patch_view_fields_wrapper');
        VSH.$imageOrMetadataViewFieldsWrapper = $('#id_image_or_metadata_view_fields_wrapper');
        VSH.sourceUsesMachineAnnotator = sourceUsesMachineAnnotator;

        // Based on initial value of the page view field, show one group
        // of fields or the other.
        VSH.displayStatusOrAnnotatorField();

        // When any of the radio buttons are clicked, show/hide the appropriate fields.
        VSH.$pageViewChoices.click(VSH.displayStatusOrAnnotatorField);
    },

    displayStatusOrAnnotatorField: function() {
        if (VSH.$pageViewPatchesChoice.prop('checked') === true) {
            // Image patches
            // TODO: Account for VSH.sourceUsesMachineAnnotator to show the annotated_by field or not?
            VSH.$imagePatchViewFieldsWrapper.show();
            VSH.$imageOrMetadataViewFieldsWrapper.hide();
        }
        else {
            // Images or metadata
            VSH.$imagePatchViewFieldsWrapper.hide();
            VSH.$imageOrMetadataViewFieldsWrapper.show();
        }
    }
};
var VSH = {

    $pageViewField: undefined,
    $imagePatchViewFieldsWrapper: undefined,
    $imageOrMetadataViewFieldsWrapper: undefined,

    sourceUsesMachineAnnotator: undefined,

    init: function(sourceUsesMachineAnnotator) {
        VSH.$pageViewField = $('#id_page_view');
        VSH.$imagePatchViewFieldsWrapper = $('#id_image_patch_view_fields_wrapper');
        VSH.$imageOrMetadataViewFieldsWrapper = $('#id_image_or_metadata_view_fields_wrapper');
        VSH.sourceUsesMachineAnnotator = sourceUsesMachineAnnotator;

        // Based on initial value of the 'labels' field, show either the
        // image annotation status field or the annotator field.
        VSH.displayStatusOrAnnotatorField();

        // When the 'labels' field changes, show/hide the appropriate field.
        VSH.$pageViewField.change(VSH.displayStatusOrAnnotatorField);
    },

    displayStatusOrAnnotatorField: function() {
        if (VSH.$pageViewField.val() === 'patches') {
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
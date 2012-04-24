var VSH = {
    $labelsField: undefined,
    $imageStatusFieldWrapper: undefined,
    $annotatorFieldWrapper: undefined,

    init: function() {
        VSH.$labelsField = $('#id_labels');
        VSH.$imageStatusFieldWrapper = $('#id_image_status_wrapper');
        VSH.$annotatorFieldWrapper = $('#id_annotator_wrapper');

        // Based on initial value of the 'labels' field, show either the
        // image annotation status field or the annotator field.
        VSH.displayStatusOrAnnotatorField();

        // When the 'labels' field changes, show/hide the appropriate field.
        VSH.$labelsField.change(VSH.displayStatusOrAnnotatorField);
    },

    displayStatusOrAnnotatorField: function() {
        if (VSH.$labelsField.val() === '') {
            // Whole images
            VSH.$imageStatusFieldWrapper.show();
            VSH.$annotatorFieldWrapper.hide();
        }
        else {
            // Patches
            VSH.$annotatorFieldWrapper.show();
            VSH.$imageStatusFieldWrapper.hide();
        }
    }
};
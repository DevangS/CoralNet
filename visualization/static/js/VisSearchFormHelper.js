var VSH = {
    $labelsField: undefined,
    $imageStatusFieldWrapper: undefined,
    $viewFieldWrapper: undefined,
    $annotatorFieldWrapper: undefined,

    sourceUsesRobotClassifier: undefined,

    init: function(sourceUsesRobotClassifier) {
        VSH.$labelsField = $('#id_labels');
        VSH.$imageStatusFieldWrapper = $('#id_image_status_wrapper');
        VSH.$viewFieldWrapper = $('#id_view_wrapper');
        VSH.$annotatorFieldWrapper = $('#id_annotator_wrapper');
        VSH.sourceUsesRobotClassifier = sourceUsesRobotClassifier;

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
            VSH.$viewFieldWrapper.show();
            VSH.$annotatorFieldWrapper.hide();
        }
        else {
            // Patches
            if (VSH.sourceUsesRobotClassifier)
                VSH.$annotatorFieldWrapper.show();
            else
                VSH.$annotatorFieldWrapper.hide();
            VSH.$imageStatusFieldWrapper.hide();
            VSH.$viewFieldWrapper.hide();
        }
    }
};
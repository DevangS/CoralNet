var BrowseHelper = (function() {

    var $pageViewChoices;
    var $pageViewPatchesChoice;
    var $imagePatchViewFieldsWrapper;
    var $imageOrMetadataViewFieldsWrapper;

    var sourceUsesMachineAnnotator;

    function displayStatusOrAnnotatorField() {
        if ($pageViewPatchesChoice.prop('checked') === true) {
            // Image patches
            $imagePatchViewFieldsWrapper.show();
            $imageOrMetadataViewFieldsWrapper.hide();
        }
        else {
            // Images or metadata
            $imagePatchViewFieldsWrapper.hide();
            $imageOrMetadataViewFieldsWrapper.show();
        }
    }

    return {

        init: function(sourceUsesMachineAnnotator) {
            $pageViewChoices = $('#id_page_view_wrapper input[type="radio"]');
            $pageViewPatchesChoice = $('#id_page_view_wrapper input[value="patches"]');

            $imagePatchViewFieldsWrapper = $('#id_image_patch_view_fields_wrapper');
            $imageOrMetadataViewFieldsWrapper = $('#id_image_or_metadata_view_fields_wrapper');

            // TODO: If this is false, don't show the Annotator field?
            sourceUsesMachineAnnotator = sourceUsesMachineAnnotator;

            // Based on initial value of the page view field, show one group
            // of fields or the other.
            displayStatusOrAnnotatorField();

            // When any of the radio buttons are clicked, show/hide the appropriate fields.
            $pageViewChoices.click(function() {
                displayStatusOrAnnotatorField();
            });
        }
    }
})();

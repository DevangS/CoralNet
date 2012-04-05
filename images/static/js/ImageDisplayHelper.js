var IDH = {

    $originalImageContainer: undefined,
    $scaledImageContainer: undefined,
    $useOriginalButton: undefined,
    $useScaledButton: undefined,

    init: function(hasThumbnail) {
        IDH.$originalImageContainer = $("#original_image_container");

        if (!hasThumbnail) {
            // There's no scaled image; just show the original image.
            // No further JS needed.
            IDH.$originalImageContainer.show();
            return;
        }

        IDH.$scaledImageContainer = $("#scaled_image_container");
        IDH.$useOriginalButton = $("#originalWidthButton");
        IDH.$useScaledButton = $("#scaledWidthButton");

        IDH.$useOriginalButton.click(IDH.useOriginalImage);
        IDH.$useScaledButton.click(IDH.useScaledImage);

        // Use the scaled image upon page load.
        IDH.useScaledImage();
    },

    useOriginalImage: function() {
        IDH.$originalImageContainer.show();
        IDH.$scaledImageContainer.hide();

        IDH.$useScaledButton.show();
        IDH.$useOriginalButton.hide();
    },
    useScaledImage: function() {
        IDH.$scaledImageContainer.show();
        IDH.$originalImageContainer.hide();

        IDH.$useOriginalButton.show();
        IDH.$useScaledButton.hide();
    }
};
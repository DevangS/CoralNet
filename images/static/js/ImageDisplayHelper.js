var IDH = {

    $originalImageContainer: undefined,
    $scaledImageContainer: undefined,
    $useOriginalButton: undefined,
    $useScaledButton: undefined,

    ORIGINAL_WIDTH: undefined,
    SCALED_WIDTH: undefined,

    init: function(originalWidth, scaledWidth) {
        IDH.$originalImageContainer = $("#original_image_container");

        if (originalWidth === scaledWidth) {
            // There's no scaled image; just show the original image.
            // No further JS needed.
            IDH.$originalImageContainer.show();
            return;
        }

        IDH.$scaledImageContainer = $("#scaled_image_container");
        IDH.$useOriginalButton = $("#originalWidthButton");
        IDH.$useScaledButton = $("#scaledWidthButton");

        IDH.ORIGINAL_WIDTH = originalWidth;
        IDH.SCALED_WIDTH = scaledWidth;

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
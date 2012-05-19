var ATI = {

    $fields: {
        brightness: undefined,
        contrast: undefined
    },
    sourceImages: {
        full: undefined,
        scaled: undefined
    },
    currentSourceImage: undefined,
    imageCanvas: undefined,

    init: function(sourceImages) {
        ATI.$fields.brightness = $('#id_brightness');
        ATI.$fields.contrast = $('#id_contrast');
        ATI.sourceImages = sourceImages;

        // When the show image tools button is clicked, show image tools;
        // when the hide image tools button is clicked, hide image tools.
        $('#id_button_show_image_tools').click(ATI.showImageTools);
        $('#id_button_hide_image_tools').click(ATI.hideImageTools);

        ATI.imageCanvas = $("#imageCanvas")[0];
        ATI.imageCanvas.width = ATI.sourceImages.scaled.width;
        ATI.imageCanvas.height = ATI.sourceImages.scaled.height;

        // Create a new img element.
        ATI.sourceImages.scaled.imgBuffer = new Image();
        // When the img element's src has loaded, draw it onto the image canvas.
        ATI.sourceImages.scaled.imgBuffer.onload = function(){
            ATI.imageCanvas.getContext("2d").drawImage(ATI.sourceImages.scaled.imgBuffer, 0, 0);
            ATI.currentSourceImage = ATI.sourceImages.scaled;

            // TODO: Check if there are separate scaled and full versions.
            ATI.preloadAndSwapFullImage();
        };
        // Set the img element's src to make it start loading.
        ATI.sourceImages.scaled.imgBuffer.src = ATI.sourceImages.scaled.url;

        ATI.$fields.brightness.change( function() {
            ATI.updateBrightnessAndContrast();
        });
        ATI.$fields.contrast.change( function() {
            ATI.updateBrightnessAndContrast();
        });
    },

    showImageTools: function() {
        $('#id_image_tools_wrapper').show();
        $('#id_button_show_image_tools').hide();
    },
    hideImageTools: function() {
        $('#id_image_tools_wrapper').hide();
        $('#id_button_show_image_tools').show();
    },

    /*
     * Preload the full image; once it's loaded, swap it in as the annotation image.
     * Code from: http://stackoverflow.com/a/1662153/859858
     */
    preloadAndSwapFullImage: function() {
        // Create an Image object.
        ATI.sourceImages.full.imgBuffer = new Image();

        // When image preloading is done, swap images.
        ATI.sourceImages.full.imgBuffer.onload = function() {
            ATI.imageCanvas.width = ATI.sourceImages.full.width;
            ATI.imageCanvas.height = ATI.sourceImages.full.height;
            ATI.imageCanvas.getContext("2d").drawImage(ATI.sourceImages.full.imgBuffer, 0, 0);

            ATI.currentSourceImage = ATI.sourceImages.full;

            ATI.updateBrightnessAndContrast();
        };

        // Image preloading starts as soon as we set this src attribute.
        ATI.sourceImages.full.imgBuffer.src = ATI.sourceImages.full.url;

        // For debugging, it sometimes helps to load an image that
        // (1) has different image content, so you can tell when it's swapped in, and/or
        // (2) is loaded after a delay, so you can zoom in first and then
        //     notice the resolution change when it happens.
        // Here's (2) in action.  The second parameter to setTimeout() is milliseconds
        // (thousandths of seconds) until the first parameter function is called.
        // NOTE: only use this for debugging, not for production code.
        //setTimeout(function() {
        //    ATI.sourceImages.full.imgBuffer.src = ATI.sourceImages.full.url;
        //}, 10000);
    },

    updateBrightnessAndContrast: function() {
        // Get the values in the brightness and contrast fields.
        var brightnessValue = ATI.$fields.brightness.val();
        var contrastValue = ATI.$fields.contrast.val();

        // TODO: Make sure that the initial image (the scaled one) is already drawn on the canvas.
        // Perhaps make a boolean variable that is set to true onload?
        // Also, shouldn't we prevent the image processing changes from being
        // attempted while the image is still loading?  Like gray out the "apply"
        // button or whatever it is.

        // Revert the canvas to pre-image-processing by re-drawing
        // from the source image.
        // (Pixastic has a revert function, but it's not really flexible
        // enough for our purposes, so we're reverting manually.)
        ATI.imageCanvas.getContext("2d").drawImage(ATI.currentSourceImage.imgBuffer, 0, 0);

        // Apply the Pixastic operations to the canvas.
        ATI.imageCanvas = Pixastic.process(
            ATI.imageCanvas,
            'brightness',
            {'brightness': brightnessValue, 'contrast': contrastValue}
        );
    }
};
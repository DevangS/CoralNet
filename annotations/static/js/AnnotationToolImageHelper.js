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

        // TODO: Check if there are separate scaled and full versions.
        ATI.preloadAndUseSourceImage('scaled');

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

    /* Preload a source image; once it's loaded, swap it in as the image
     * used in the annotation tool.
     *
     * Parameters:
     * code - Which version of the image it is: 'scaled' or 'full'.
     *
     * Basic code pattern from: http://stackoverflow.com/a/1662153/859858
     */
    preloadAndUseSourceImage: function(code) {
        // Create an Image object.
        ATI.sourceImages[code].imgBuffer = new Image();

        // When image preloading is done, swap images.
        ATI.sourceImages[code].imgBuffer.onload = function() {
            ATI.imageCanvas.width = ATI.sourceImages[code].width;
            ATI.imageCanvas.height = ATI.sourceImages[code].height;
            ATI.imageCanvas.getContext("2d").drawImage(ATI.sourceImages[code].imgBuffer, 0, 0);

            ATI.currentSourceImage = ATI.sourceImages[code];

            ATI.applyBrightnessAndContrast();

            // If we just finished loading the scaled image, then start loading
            // the full image.
            if (code === 'scaled') {
                ATI.preloadAndUseSourceImage('full');
            }
        };

        // Image preloading starts as soon as we set this src attribute.
        ATI.sourceImages[code].imgBuffer.src = ATI.sourceImages[code].url;

        // For debugging, it sometimes helps to load an image that
        // (1) has different image content, so you can tell when it's swapped in, and/or
        // (2) is loaded after a delay, so you can zoom in first and then
        //     notice the resolution change when it happens.
        // Here's (2) in action: uncomment the below code and comment out the
        // preload line above to try it.  The second parameter to setTimeout()
        // is milliseconds until the first-parameter function is called.
        // NOTE: only use this for debugging, not for production.
        //setTimeout(function() {
        //    ATI.sourceImages[code].imgBuffer.src = ATI.sourceImages[code].url;
        //}, 10000);
    },

    /* Revert previous brightness/contrast operations, then apply bri/con
       with the new parameters. */
    updateBrightnessAndContrast: function() {
        // If we haven't loaded any image yet, don't do anything.
        if (ATI.currentSourceImage === undefined)
            return;

        // Revert the canvas to pre-image-processing by re-drawing
        // from the source image.
        // (Pixastic has a revert function, but it's not really flexible
        // enough for our purposes, so we're reverting manually.)
        ATI.imageCanvas.getContext("2d").drawImage(ATI.currentSourceImage.imgBuffer, 0, 0);

        ATI.applyBrightnessAndContrast();
    },

    /* Just apply bri/con, no reverting beforehand. */
    applyBrightnessAndContrast: function() {
        // Get the values in the bri/con fields.
        var brightnessValue = ATI.$fields.brightness.val();
        var contrastValue = ATI.$fields.contrast.val();

        // Apply the Pixastic bri/con operations to the canvas.
        // TODO: Don't hang the browser while doing this.
        // TODO: Have some progress text as this goes: "Applying..."
        ATI.imageCanvas = Pixastic.process(
            ATI.imageCanvas,
            'brightness',
            {'brightness': brightnessValue, 'contrast': contrastValue}
        );
    }
};
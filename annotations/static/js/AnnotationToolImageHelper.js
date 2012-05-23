var ATI = {

    $applyButton: undefined,

    form: undefined,
    fields: undefined,

    sourceImages: {},
    currentSourceImage: undefined,
    imageCanvas: undefined,

    nowApplyingProcessing: false,
    redrawSignal: false,

    init: function(sourceImages) {
        ATI.$applyButton = $('#applyImageOptionsButton');

        ATI.form = util.Form({
            brightness: util.Field(
                $('#id_brightness'),
                'signedInt',
                [util.validators.inNumberRange.curry(-150, 150)]
            ),
            contrast: util.Field(
                $('#id_contrast'),
                'signedFloat',
                [util.validators.inNumberRange.curry(-1.0, 3.0)]
            )
        });
        ATI.fields = ATI.form.fields;

        ATI.sourceImages = sourceImages;

        ATI.imageCanvas = $("#imageCanvas")[0];

        // When the show image tools button is clicked, show image tools;
        // when the hide image tools button is clicked, hide image tools.
        $('#id_button_show_image_tools').click(ATI.showImageTools);
        $('#id_button_hide_image_tools').click(ATI.hideImageTools);

        // Initialize fields.
        for (var fieldName in ATI.fields) {
            if (!ATI.fields.hasOwnProperty(fieldName)){ continue; }

            var field = ATI.fields[fieldName];

            // Initialize the stored field value.
            field.updateValue();
            // When the element's value is changed, update the stored field value
            // (or revert the element's value if the value is invalid).
            field.$element.change(field.updateValue);
        }

        if (ATI.sourceImages.hasOwnProperty('scaled')) {
            ATI.preloadAndUseSourceImage('scaled');
        }
        else {
            ATI.preloadAndUseSourceImage('full');
        }

        // When the Apply button is clicked, re-draw the source image
        // and re-apply bri/con operations.
        ATI.$applyButton.click( function(){
            ATI.redrawImage();
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

            ATI.currentSourceImage = ATI.sourceImages[code];
            ATI.redrawImage();

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

    /* Redraw the source image, and apply brightness and contrast operations. */
    redrawImage: function() {
        // If we haven't loaded any image yet, don't do anything.
        if (ATI.currentSourceImage === undefined)
            return;

        // If processing is currently going on, emit the redraw signal to
        // tell it to stop processing and re-call this function.
        if (ATI.nowApplyingProcessing === true) {
            ATI.redrawSignal = true;
            return;
        }

        // Redraw the source image.
        // (Pixastic has a revert function that's supposed to do this,
        // but it's not really flexible enough for our purposes, so
        // we're reverting manually.)
        ATI.imageCanvas.getContext("2d").drawImage(ATI.currentSourceImage.imgBuffer, 0, 0);

        // bri == 0 and con == 0 means it's just the original image, so return.
        if (ATI.fields.brightness.value === 0 && ATI.fields.contrast.value === 0) {
            return;
        }

        // TODO: Have some progress text as this goes: "Applying..."

        // TODO: Work on reducing browser memory usage.
        // Abandoning Pixastic.process() was probably a good start, since that
        // means we no longer create a new canvas.  What else can be done though?

        /* Divide the canvas into rectangles.  We'll operate on one
           rectangle at a time, and do a timeout between rectangles.
           That way we don't lock up the browser for a really long
           time when processing a large image. */

        var X_MAX = ATI.imageCanvas.width - 1;
        var Y_MAX = ATI.imageCanvas.height - 1;

        // TODO: Make the rect size configurable somehow.
        var RECT_SIZE = 1400;

        var x1 = 0, y1 = 0, xRanges = [], yRanges = [];
        while (x1 <= X_MAX) {
            var x2 = Math.min(x1 + RECT_SIZE - 1, X_MAX);
            xRanges.push([x1, x2]);
            x1 = x2 + 1;
        }
        while (y1 <= Y_MAX) {
            var y2 = Math.min(y1 + RECT_SIZE - 1, Y_MAX);
            yRanges.push([y1, y2]);
            y1 = y2 + 1;
        }

        var rects = [];
        for (var i = 0; i < xRanges.length; i++) {
            for (var j = 0; j < yRanges.length; j++) {
                rects.push({
                    'left': xRanges[i][0],
                    'top': yRanges[j][0],
                    'width': xRanges[i][1] - xRanges[i][0] + 1,
                    'height': yRanges[j][1] - yRanges[j][0] + 1
                });
            }
        }

        ATI.nowApplyingProcessing = true;

        ATI.applyBrightnessAndContrastToRects(
            ATI.fields.brightness.value,
            ATI.fields.contrast.value,
            rects
        )
    },

    applyBrightnessAndContrastToRects: function(brightness, contrast, rects) {
        if (ATI.redrawSignal === true) {
            ATI.nowApplyingProcessing = false;
            ATI.redrawSignal = false;
            ATI.redrawImage();
            return;
        }

        // "Pop" the first element from rects.
        var rect = rects.shift();

        var params = {
            image: undefined,  // unused?
            canvas: ATI.imageCanvas,
            width: undefined,  // unused?
            height: undefined,  // unused?
            useData: true,
            options: {
                'brightness': brightness,
                'contrast': contrast,
                'rect': rect    // apply the effect to this region only
            }
        };

        // This is a call to an "internal" Pixastic function, sort of.
        // The intended API function Pixastic.process() includes a
        // drawImage() of the entire image, so that's not good for
        // operations that require many calls to Pixastic!
        Pixastic.Actions.brightness.process(params);

        // Now that we've computed the processed-image data, put that
        // data on the canvas.
        // This code block is based on code near the end of the
        // Pixastic core's applyAction().
        if (params.useData) {
            if (Pixastic.Client.hasCanvasImageData()) {
                ATI.imageCanvas.getContext("2d").putImageData(params.canvasData, params.options.rect.left, params.options.rect.top);

                // Opera doesn't seem to update the canvas until we draw something on it, lets draw a 0x0 rectangle.
                // Is this still so?
                ATI.imageCanvas.getContext("2d").fillRect(0,0,0,0);
            }
        }

        if (rects.length > 0) {
            // Slightly delay the processing of the next rect, so we
            // don't lock up the browser for an extended period of time.
            // Note the use of curry() to produce a function.
            setTimeout(
                ATI.applyBrightnessAndContrastToRects.curry(brightness, contrast, rects),
                50
            );
        }
        else {
            ATI.nowApplyingProcessing = false;
        }
    }
};
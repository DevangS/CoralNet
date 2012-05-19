var ATI = {

    $fields: {
        brightness: undefined,
        contrast: undefined
    },
    sourceImages: {
        full: undefined,
        scaled: undefined
    },
    sourceImgElmt: undefined,
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
        // Set the number of pixels the canvas should hold.
        // TODO: Might want to make this equal to the size of the
        // actual img src, not the size of the img src if it were
        // the full-res image.
        //ATI.imageCanvas.width = $(ATI.sourceImgElmt).width();
        //ATI.imageCanvas.height = $(ATI.sourceImgElmt).height();
        ATI.imageCanvas.width = ATI.sourceImages.scaled.width;
        ATI.imageCanvas.height = ATI.sourceImages.scaled.height;

        // Create a new img element.
        ATI.sourceImgElmt = new Image();
        // When the img element's src has loaded, draw it onto the image canvas.
        ATI.sourceImgElmt.onload = function(){
            ATI.imageCanvas.getContext("2d").drawImage(ATI.sourceImgElmt, 0, 0);
        };
        // Set the img element's src to make it start loading.
        ATI.sourceImgElmt.src = ATI.sourceImages.scaled.url;

        ATI.$fields.brightness.change( function() {
            ATI.changeBrightnessOrContrast();
        });
        ATI.$fields.contrast.change( function() {
            ATI.changeBrightnessOrContrast();
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
        var fullImagePreloader = new Image();

        // When image preloading is done, swap images.
        fullImagePreloader.onload = function() {
            ATH.imageCanvas.src = fullImagePreloader.src;
        };

        // Image preloading starts as soon as we set this src attribute.
        fullImagePreloader.src = ATI.sourceImages.full.url;

        // For debugging, it helps to load an image that is
        // (1) totally different, so you can tell when it's swapped in, and
        // (2) remotely hosted, in case loading a local image is not satisfactory for testing.
        // Remember to refresh + clear cache (Ctrl+Shift+R in Firefox) on subsequent test runs.
        // Uncomment the image of your choice:
        //fullImagePreloader.src = "http://farm6.staticflickr.com/5015/5565696408_8819b64a61_b.jpg"; // 740 KB
        //fullImagePreloader.src = "http://farm6.staticflickr.com/5018/5565067643_1c9686d932_o.jpg"; // 1,756 KB
        //fullImagePreloader.src = "http://farm6.staticflickr.com/5015/5565696408_9849980bdb_o.jpg"; // 2,925 KB
    },

    changeBrightnessOrContrast: function() {
        // Get the values in the brightness and contrast fields.
        var brightnessValue = ATI.$fields.brightness.val();
        var contrastValue = ATI.$fields.contrast.val();

        // TODO: Maintain the zoom level as you change bri/con.

        // TODO: Make the resulting canvas the same resolution as the source image.
        // To do this, change the image into an appropriately-sized canvas before applying
        // image processing.
        // (1) Change imageElmt back to imageCanvas, a canvas element.
        // (2) Make the canvas appropriately sized.
        // (3) Have ATH.init() (or ATI.init()?) take the image src as a parameter.
        // (4) Use the following pattern to draw the image on the canvas:
        //    var img = new Image();   // Create new img element
        //    img.onload = function(){
        //        // execute drawImage statements here
        //    };
        //    img.src = 'myImage.png'; // Set source path

        // First, revert previous Pixastic operations, so we get the
        // imageCanvas with the original image in it.
        Pixastic.revert(ATI.imageCanvas);

        // After the revert, #imageCanvas is now a different DOM object,
        // so re-assign ATI.imageCanvas.
        ATI.imageCanvas = $('#imageCanvas')[0];

        // Apply the new Pixastic operations.
        ATI.imageCanvas = Pixastic.process(
            ATI.imageCanvas,
            'brightness',
            {'brightness': brightnessValue, 'contrast': contrastValue}
        );
    }
};
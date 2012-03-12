var AAH = {
    // jQuery objects
    $box: undefined,
    $image: undefined,
    $imageContainer: undefined,

    // HTML elements
    fields: {
        min_x: undefined,
        max_x: undefined,
        min_y: undefined,
        max_y: undefined
    },

    // Other
    dimensions: {
        displayWidth: undefined,
        displayHeight: undefined,
        fullWidth: undefined,
        fullHeight: undefined,
        widthScaleFactor: undefined,
        heightScaleFactor: undefined
    },
    savedFormValues: {
        min_x: undefined,
        max_x: undefined,
        min_y: undefined,
        max_y: undefined
    },

    init: function(dimensions) {
        AAH.$box = $('#annoarea_box');
        AAH.$image = $('#image');
        AAH.$imageContainer = $('#image_container');
        AAH.fields = {
            min_x: $('#id_min_x')[0],
            max_x: $('#id_max_x')[0],
            min_y: $('#id_min_y')[0],
            max_y: $('#id_max_y')[0]
        };
        AAH.dimensions = dimensions;

        AAH.$image.css({
            'width': AAH.dimensions.displayWidth,
            'height': AAH.dimensions.displayHeight
        });
        AAH.$imageContainer.css({
            'width': AAH.dimensions.displayWidth,
            'height': AAH.dimensions.displayHeight
        });

        // Initialize the remembered form values.
        AAH.rememberFormValues();

        // Initialize the box's position and dimensions.
        AAH.formToBoxUpdate();

        // Make the box resizable with jQuery UI.
        AAH.$box.resizable({
            // Only allowed to resize within the bounds of #image_container.
            containment: '#image_container',

            // Be able to resize in all 8 directions.
            handles: 'all',

            // We want the minimum size to be practically 0, but exactly 0
            // results in very odd behavior.
            minHeight: 0.01,
            minWidth: 0.01,

            // Event handler to call upon resize.
            resize: AAH.boxToFormUpdate
        });

        // Form field event handlers:
        // When a field is typed into and changed, and then unfocused.
        for (var key in AAH.fields) {
            if (!AAH.fields.hasOwnProperty(key)){ continue; }

            $(AAH.fields[key]).change(function() {
                AAH.checkFormValues();
                AAH.rememberFormValues();
                AAH.formToBoxUpdate();
            });
        }
    },

    /* Update the form to match the box. */
    boxToFormUpdate: function() {
        var d = AAH.getBoxValues();
        AAH.fields.min_x.value = d['min_x'];
        AAH.fields.max_x.value = d['max_x'];
        AAH.fields.min_y.value = d['min_y'];
        AAH.fields.max_y.value = d['max_y'];
    },
    /* Update the box to match the form field values. */
    formToBoxUpdate: function() {
        var d = AAH.getFormValues();
        var cssScaledToImage = {
            'left': d['min_x'] - 1,
            'top': d['min_y'] - 1,
            'width': d['max_x'] - d['min_x'] + 1,
            'height': d['max_y'] - d['min_y'] + 1
        };
        var cssDict = {};
        cssDict['left'] = Math.round(cssScaledToImage['left'] * AAH.dimensions.widthScaleFactor);
        cssDict['width'] = Math.round(cssScaledToImage['width'] * AAH.dimensions.widthScaleFactor);
        cssDict['top'] = Math.round(cssScaledToImage['top'] * AAH.dimensions.heightScaleFactor);
        cssDict['height'] = Math.round(cssScaledToImage['height'] * AAH.dimensions.heightScaleFactor);
        AAH.$box.css(cssDict);
    },

    /* Check for valid form values.  If invalid, either revert them back to
     * what they were previously, or correct them. */
    checkFormValues: function() {
        var d = AAH.getFormValuesAsStrs();

        // Check that each field value represents an integer.
        for (var fieldName in d) {
            if (!d.hasOwnProperty(fieldName)){ continue; }

            if (!util.isIntStr(d[fieldName])) {
                AAH.revertFormValues([fieldName]);
                return;
            }
        }

        d = AAH.getFormValues();

        // Check that min <= max for both x and y.
        if (d['min_x'] > d['max_x']) {
            AAH.revertFormValues(['min_x','max_x']);
            return;
        }
        if (d['min_y'] > d['max_y']) {
            AAH.revertFormValues(['min_y','max_y']);
            return;
        }

        // Out-of-range values can be easily corrected.
        if (d['min_x'] < 1)
            AAH.fields['min_x'].value = 1;
        if (d['max_x'] > AAH.dimensions.fullWidth)
            AAH.fields['max_x'].value = AAH.dimensions.fullWidth;
        if (d['min_y'] < 1)
            AAH.fields['min_y'].value = 1;
        if (d['max_y'] > AAH.dimensions.fullHeight)
            AAH.fields['max_y'].value = AAH.dimensions.fullHeight;
    },
    /* Save the current form values, in case we get invalid
     * values later and need to revert. */
    rememberFormValues: function() {
        AAH.savedFormValues = AAH.getFormValues();
    },
    /* Revert back to the latest valid form values. */
    revertFormValues: function(fieldsToRevert) {
        if (fieldsToRevert === undefined)
            fieldsToRevert = ['min_x', 'max_x', 'min_y', 'max_y'];

        for (var i = 0; i < fieldsToRevert.length; i++) {
            var fieldName = fieldsToRevert[i];
            AAH.fields[fieldName].value = AAH.savedFormValues[fieldName];
        }
    },

    /* Get the annotation area values represented by the box. */
    getBoxValues: function() {
        var d = {};
        var cssDict = {
            'left': parseInt(AAH.$box.css('left')),
            'top': parseInt(AAH.$box.css('top')),
            'width': parseInt(AAH.$box.css('width')),
            'height': parseInt(AAH.$box.css('height'))
        };
        var cssScaledToImage = {};
        cssScaledToImage['left'] = cssDict['left'] / AAH.dimensions.widthScaleFactor;
        cssScaledToImage['width'] = cssDict['width'] / AAH.dimensions.widthScaleFactor;
        cssScaledToImage['top'] = cssDict['top'] / AAH.dimensions.heightScaleFactor;
        cssScaledToImage['height'] = cssDict['height'] / AAH.dimensions.heightScaleFactor;

        d['min_x'] = Math.round(cssScaledToImage['left']) + 1;
        d['max_x'] = Math.round(cssScaledToImage['left'] + cssScaledToImage['width']);
        d['min_y'] = Math.round(cssScaledToImage['top']) + 1;
        d['max_y'] = Math.round(cssScaledToImage['top'] + cssScaledToImage['height']);
        return d;
    },
    /* Get form values as numbers */
    getFormValues: function() {
        var d = AAH.getFormValuesAsStrs();
        for (var fieldName in d) {
            if (!d.hasOwnProperty(fieldName)){ continue; }
            d[fieldName] = parseInt(d[fieldName]);
        }
        return d;
    },
    /* Get form values as strings */
    getFormValuesAsStrs: function() {
        var d = {};
        d['min_x'] = AAH.fields.min_x.value;
        d['max_x'] = AAH.fields.max_x.value;
        d['min_y'] = AAH.fields.min_y.value;
        d['max_y'] = AAH.fields.max_y.value;
        return d;
    }
};
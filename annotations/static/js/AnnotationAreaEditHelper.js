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
    boxValues: {
        left: undefined,
        right: undefined,
        top: undefined,
        bottom: undefined
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

            // We want the minimum size to be as close to 0 as possible, but:
            // - exactly 0 results in very odd behavior
            // - 0 < min < 0.49-ish allows the low bound to exceed the high bound for some reason
            // - 0.49-ish < 1 has the same effect as 1.
            minHeight: 1,
            minWidth: 1,

            // Event handler to call upon resize.
            resize: AAH.onBoxResize
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

    onBoxResize: function(event, ui) {
        AAH.updateBoxValuesOnResize(event, ui);
        AAH.boxToFormUpdate();
    },
    updateBoxValuesOnResize: function(event, ui) {
        var newAttrs = {
            'left': parseInt(AAH.$box.css('left')),
            'width': parseInt(AAH.$box.css('width')),
            'top': parseInt(AAH.$box.css('top')),
            'height': parseInt(AAH.$box.css('height'))
        };

        // Only update the box value(s) that have changed.
        // Box values derived from the form fields are more exact,
        // and we want to preserve those whenever possible.
        if (Math.round(AAH.boxValues.left) !== newAttrs.left) {
            AAH.boxValues.left = newAttrs.left;
        }
        if (Math.round(AAH.boxValues.right) !== newAttrs.left + newAttrs.width) {
            AAH.boxValues.right = newAttrs.left + newAttrs.width;
        }
        if (Math.round(AAH.boxValues.top) !== newAttrs.top) {
            AAH.boxValues.top = newAttrs.top;
        }
        if (Math.round(AAH.boxValues.bottom) !== newAttrs.top + newAttrs.height) {
            AAH.boxValues.bottom = newAttrs.top + newAttrs.height;
        }
    },
    /* Update the form to match the box. */
    boxToFormUpdate: function() {
        var boxValues = AAH.boxValues;
        var boxScaledToImage = {};
        boxScaledToImage['left'] = boxValues['left'] / AAH.dimensions.widthScaleFactor;
        boxScaledToImage['right'] = boxValues['right'] / AAH.dimensions.widthScaleFactor;
        boxScaledToImage['top'] = boxValues['top'] / AAH.dimensions.heightScaleFactor;
        boxScaledToImage['bottom'] = boxValues['bottom'] / AAH.dimensions.heightScaleFactor;

        AAH.fields.min_x.value = Math.round(boxScaledToImage['left']) + 1;
        AAH.fields.max_x.value = Math.round(boxScaledToImage['right']);
        AAH.fields.min_y.value = Math.round(boxScaledToImage['top']) + 1;
        AAH.fields.max_y.value = Math.round(boxScaledToImage['bottom']);

        AAH.rememberFormValues();
    },
    /* Update the box to match the form field values. */
    formToBoxUpdate: function() {
        var d = AAH.getFormValues();
        var boxScaledToImage = {
            'left': d['min_x'] - 1,
            'right': d['max_x'],
            'top': d['min_y'] - 1,
            'bottom': d['max_y']
        };
        // Save boxValues as floats.
        AAH.boxValues.left = boxScaledToImage.left * AAH.dimensions.widthScaleFactor;
        AAH.boxValues.right = boxScaledToImage.right * AAH.dimensions.widthScaleFactor;
        AAH.boxValues.top = boxScaledToImage.top * AAH.dimensions.heightScaleFactor;
        AAH.boxValues.bottom = boxScaledToImage.bottom * AAH.dimensions.heightScaleFactor;

        // Apply CSS attrs as ints.
        var cssDict = {};
        cssDict.left = Math.round(AAH.boxValues.left);
        cssDict.width = Math.round(AAH.boxValues.right - AAH.boxValues.left);
        cssDict.top = Math.round(AAH.boxValues.top);
        cssDict.height = Math.round(AAH.boxValues.bottom - AAH.boxValues.top);
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
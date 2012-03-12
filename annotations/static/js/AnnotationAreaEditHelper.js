var AAH = {
    // HTML elements
    $box: undefined,
    $image: undefined,
    $imageContainer: undefined,
    fields: undefined,
    dimensions: undefined,
    savedFormValues: undefined,
    scaleFactor: undefined,

    init: function(scaleFactor, dimensions) {
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
        AAH.scaleFactor = scaleFactor;

        AAH.$image.css({
            'width': AAH.dimensions['displayWidth'],
            'height': AAH.dimensions['displayHeight']
        });
        // The imageContainer should contain the box + its borders.
        // Border widths are hard-coded here because using css() seems
        // to get inaccurate border widths (can be 0.5 to 2 px off).
        AAH.$imageContainer.css({
            'width': AAH.dimensions['displayWidth'] + (2*5),
            'height': AAH.dimensions['displayHeight'] + (2*5)
        });

        // Initialize the remembered form values.
        AAH.rememberFormValues();

        // Initialize the box's position and dimensions.
        AAH.formToBoxUpdate();

        // Make the box resizable with jQuery UI.
//        AAH.$box.resizable({
//            containment: '#image_container',
//            handles: 'all',
//            minHeight: 0.01,
//            minWidth: 0.01,
//            resize: AAH.boxToFormUpdate
//        });

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
        var cssDict = {
            'left': d['min_x'] - 1,
            'top': d['min_y'] - 1,
            'width': d['max_x'] - d['min_x'] + 1,
            'height': d['max_y'] - d['min_y'] + 1
        };
        for (var key in cssDict) {
            if (!cssDict.hasOwnProperty(key)){ continue; }
            cssDict[key] = Math.round(cssDict[key] * AAH.scaleFactor);
        }
        AAH.$box.css(cssDict);
    },

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
        if (d['max_x'] > AAH.dimensions['fullWidth'])
            AAH.fields['max_x'].value = AAH.dimensions['fullWidth'];
        if (d['min_y'] < 1)
            AAH.fields['min_y'].value = 1;
        if (d['max_y'] > AAH.dimensions['fullHeight'])
            AAH.fields['max_y'].value = AAH.dimensions['fullHeight'];
    },
    rememberFormValues: function() {
        AAH.savedFormValues = AAH.getFormValues();
    },
    revertFormValues: function(fieldsToRevert) {
        if (fieldsToRevert === undefined)
            fieldsToRevert = ['min_x', 'max_x', 'min_y', 'max_y'];

        for (var i = 0; i < fieldsToRevert.length; i++) {
            var fieldName = fieldsToRevert[i];
            AAH.fields[fieldName].value = AAH.savedFormValues[fieldName];
        }
    },

    getBoxValues: function() {
        var d = {};
        d['min_x'] = parseInt(AAH.$box.css('left')) + 1;
        d['max_x'] = parseInt(AAH.$box.css('left')) + parseInt(AAH.$box.css('width')) + 1;
        d['min_y'] = parseInt(AAH.$box.css('top')) + 1;
        d['max_y'] = parseInt(AAH.$box.css('top')) + parseInt(AAH.$box.css('height')) + 1;
        for (var key in d) {
            if (!d.hasOwnProperty(key)){ continue; }
            d[key] = Math.round(d[key] / AAH.scaleFactor);
        }
        return d;
    },
    // Get form values as numbers
    getFormValues: function() {
        var d = AAH.getFormValuesAsStrs();
        for (var fieldName in d) {
            if (!d.hasOwnProperty(fieldName)){ continue; }
            d[fieldName] = parseInt(d[fieldName]);
        }
        return d;
    },
    // Get form values as strings
    getFormValuesAsStrs: function() {
        var d = {};
        d['min_x'] = AAH.fields.min_x.value;
        d['max_x'] = AAH.fields.max_x.value;
        d['min_y'] = AAH.fields.min_y.value;
        d['max_y'] = AAH.fields.max_y.value;
        return d;
    }
};
var AAH = {
    // HTML elements
    $box: undefined,
    $image: undefined,
    $imageContainer: undefined,
    fields: undefined,
    scaleFactor: undefined,

    init: function(scaleFactor, imageDisplayWidth, imageDisplayHeight) {
        AAH.$box = $('#annoarea_box');
        AAH.$image = $('#image');
        AAH.$imageContainer = $('#image_container');
        AAH.fields = {
            min_x: $('#id_min_x')[0],
            max_x: $('#id_max_x')[0],
            min_y: $('#id_min_y')[0],
            max_y: $('#id_max_y')[0]
        };
        AAH.scaleFactor = scaleFactor;

        AAH.$imageContainer.css({
            'width': imageDisplayWidth,
            'height': imageDisplayHeight
        });
        AAH.$image.css({
            'width': imageDisplayWidth,
            'height': imageDisplayHeight
        });

        // Initialize the box's position and dimensions.
        AAH.formToBoxUpdate();

        // Make the box resizable with jQuery UI.
        AAH.$box.resizable({
            containment: '#image_container',
            handles: 'all',
            minHeight: 1,
            minWidth: 1,
            resize: AAH.boxToFormUpdate
        });

        // Form field event handlers:
        // When a field is typed into and changed, and then unfocused,
        // the box is updated to match the fields.
        for (var key in AAH.fields) {
            if (!AAH.fields.hasOwnProperty(key)){ continue; }

            $(AAH.fields[key]).change(function() {
                AAH.formToBoxUpdate();
            });
        }
    },

    boxToFormUpdate: function() {
        var d = AAH.getBoxValues();
        AAH.fields.min_x.value = d['min_x'];
        AAH.fields.max_x.value = d['max_x'];
        AAH.fields.min_y.value = d['min_y'];
        AAH.fields.max_y.value = d['max_y'];
    },
    formToBoxUpdate: function() {
        var d = AAH.getFormValues();
        var css_dict = {
            'left': d['min_x'] - 1,
            'top': d['min_y'] - 1,
            'width': d['max_x'] - d['min_x'] + 1,
            'height': d['max_y'] - d['min_y'] + 1
        };
        for (var key in css_dict) {
            if (!css_dict.hasOwnProperty(key)){ continue; }
            css_dict[key] = Math.round(css_dict[key] * AAH.scaleFactor);
        }
        AAH.$box.css(css_dict);
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
    getFormValues: function() {
        var d = {};
        d['min_x'] = AAH.fields.min_x.value;
        d['max_x'] = AAH.fields.max_x.value;
        d['min_y'] = AAH.fields.min_y.value;
        d['max_y'] = AAH.fields.max_y.value;
        return d;
    }
};
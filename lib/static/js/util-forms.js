/*
 Form and Field classes. Includes input checking, output formatting,
 and handling of special widgets like sliders.

 See here for basic patterns on writing Javascript 'classes', including
 use of 'that' instead of 'this':
 http://stackoverflow.com/questions/1595611/how-to-properly-create-a-custom-object-in-javascript/1598077#1598077
 */

util.forms = {

    /* A form field class. */
    Field: function(params) {
        var that = {};

        /* Object initialization */
        var requiredParams = ['$element', 'type', 'defaultValue', 'validators'];
        var optionalParams = ['extraWidget'];
        var paramName, i;

        for (i = 0; i < requiredParams.length; i++) {
            paramName = requiredParams[i];
            if (params.hasOwnProperty(paramName))
                that[paramName] = params[paramName];
            else
                console.log("Required parameter missing: {0}".format(paramName));
        }
        for (i = 0; i < optionalParams.length; i++) {
            paramName = optionalParams[i];
            if (params.hasOwnProperty(paramName))
                that[paramName] = params[paramName];
            else
                that[paramName] = null;
        }

        that.value = null;

        that._init = function() {
            if (that.extraWidget !== null) {
                that.extraWidget.$element.bind("slide", that.onExtraWidgetChange);
            }
        };

        that.onFieldChange = function() {
            // Run the validators
            for (var i = 0; i < that.validators.length; i++) {
                var isValid = that.validators[i](that.$element.val());
                if (isValid === false) {
                    that.revertField();
                    return;
                }
            }

            // Update the stored value
            // (the value for calculation, not for display)
            that.updateValue();

            // Update the extraWidget if applicable.
            if (that.extraWidget !== null)
                that.extraWidget.update(that.value);
        };

        that.onExtraWidgetChange = function(event, ui) {
            that.$element.val(ui.value);
            that.updateValue();
        };

        /* Update the stored value
         (the value for calculation, not for display). */
        that.updateValue = function() {
            var type = that.type;

            if (type === 'checkbox')
                that.value = that.$element.prop('checked');
            else if (type === 'color')
                that.value = '#' + that.$element.val();
            else if (type === 'float' || type === 'signedFloat') {
                var unroundedValue = parseFloat(that.$element.val());
                that.value = parseFloat(unroundedValue.toFixed(that.decimalPlaces));
            }
            else if (type === 'int' || type === 'signedInt')
                that.value = parseInt(that.$element.val(), 10);
            else
                that.value = that.$element.val();

            that.formatField();
        };

        /* Transform the display value to a consistent format */
        that.formatField = function() {
            var type = that.type;

            if (type === 'float' || type === 'signedFloat') {
                that.$element.val(that.value.toFixed(that.decimalPlaces))
            }
            else if (type === 'int' || type === 'signedInt') {
                that.$element.val(that.value.toFixed(0))
            }

            if (type === 'signedFloat' || type === 'signedInt') {
                // Add + to front of positive numbers: e.g. 25 becomes +25
                if (that.value > 0) {
                    that.$element.val('+' + that.$element.val())
                }
            }
        };

        /* Revert the field's value to what it was previously
         (i.e. revert it to the saved value in that.value). */
        that.revertField = function() {
            that.$element.val(that.value);
            that.formatField();
        };

        /* Reset the value to the default value. */
        that.reset = function() {
            // Reset the internal value.
            that.value = that.defaultValue;

            // Reset the field display value.
            that.formatField();

            // Reset the extraWidget if applicable.
            if (that.extraWidget !== null)
                that.extraWidget.update(that.value);
        };

        that._init();
        return that;
    },

    FloatField: function(params) {
        var that = util.forms.Field(params);

        var requiredParams = ['decimalPlaces'];
        var paramName, i;

        for (i = 0; i < requiredParams.length; i++) {
            paramName = requiredParams[i];
            if (params.hasOwnProperty(paramName))
                that[paramName] = params[paramName];
            else
                console.log("Required parameter missing: {0}".format(paramName));
        }

        return that;
    },

    /* A form class.
     * fields - an object with the Field names as the keys.
     */
    Form: function(fields) {
        var that = {};

        /* Form initialization */
        that.fields = fields;

        that._init = function() {
            for (var fieldName in that.fields) {
                if (!that.fields.hasOwnProperty(fieldName)){ continue; }

                var field = that.fields[fieldName];

                // For certain field types, the input needs to be validated
                // as representing the correct type.  Add the type validation
                // function as the field's first validator.
                if (field.type === 'int' || field.type === 'signedInt')
                    field.validators.unshift(util.forms.validators.representsInt);
                if (field.type === 'float' || field.type === 'signedFloat')
                    field.validators.unshift(util.forms.validators.representsFloat);
            }
        };

        that._init();
        return that;
    },

    ExtraWidget: function($element, type) {
        var that = {};

        that.$element = $element;
        that.type = type;

        that.update = function(value) {
            console.log("This extra widget doesn't have an implementation of update().  Please add one.\nIn the meantime, the value received was: {0}".format(value));
        };

        return that;
    },

    SliderWidget: function($element, $fieldElement, min, max, step) {
        var that = util.forms.ExtraWidget($element, 'slider');

        $element.slider({
            value: $fieldElement.value,
            min: min,
            max: max,
            step: step
        });

        that.update = function(value) {
            that.$element.slider("value", value);
        };

        return that;
    },

    /*
     * Field validators.
     * For validators that take arguments other than the Field value,
     * the Field value should be the last argument, and the other arguments
     * should be supplied with Function.prototype.curry() when the Field
     * is instantiated.
     */
    validators: {

        representsInt: function(value) {
            return util.representsInt(value);
        },

        representsFloat: function(value) {
            return util.representsNumber(value);
        },

        /*
         Returns true if min <= fieldValue <= max,
         false otherwise.  If either min or max is null,
         then that boundary won't be checked.
         */
        inNumberRange: function(min, max, value) {
            if (min !== null && value < min) {
                return false;
            }
            else if (max !== null && value > max) {
                return false;
            }
            return true;
        }
    }
};
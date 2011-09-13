var ImageDetailFormHelper = {

    init: function() {
        // Add onchange handler to each location-value dropdown field
        for (var i = 1; $("#id_value" + i).length != 0; i++) {

            var valueFieldJQ = $("#id_value" + i);
            //var otherFieldWrapper = $("#id_value" + i + "_other_wrapper");

            // Show/hide this value's Other field right now
            ImageDetailFormHelper.showOrHideOtherField(valueFieldJQ[0]);
            
            // Show/hide this value's Other field when the dropdown value changes
            valueFieldJQ.change( function() {
                ImageDetailFormHelper.showOrHideOtherField(this);
            });
        }
    },


    showOrHideOtherField: function(valueField) {
        var otherFieldWrapperJQ = $("#" + valueField.id + "_other_wrapper");
//    showOrHideOtherField: function(valueNumber) {
//        var valueField = $("#id_value" + valueNumber);
//        var otherFieldWrapper = $("#id_value" + valueNumber + "_other_wrapper");

//        if (valueField[0].value === 'Other') {
        if (valueField.value === 'Other') {
            otherFieldWrapperJQ.show();
        }
        else {
            otherFieldWrapperJQ.hide();
        }
    }
};

util.addLoadEvent(ImageDetailFormHelper.init);

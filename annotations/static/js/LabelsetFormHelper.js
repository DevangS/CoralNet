var LabelsetFormHelper = {

    init: function(showLabelFormInitially, initiallyCheckedLabels) {
        if (showLabelFormInitially) {
            this.showLabelForm();
        }

        for (var i = 0; i < initiallyCheckedLabels.length; i++) {
            checkboxElmt = $("#id_labels_" + initiallyCheckedLabels[i])[0];
            checkboxElmt.checked = true;
        }

        $("#id_button_show_label_form").click( function() {
            LabelsetFormHelper.showLabelForm();
        });
        $("#id_button_cancel_label_form").click( function() {
            LabelsetFormHelper.hideLabelForm();
        });
    },

    hideLabelForm: function() {
        $("#id_new_label_form_wrapper").hide();
        $("#id_button_show_label_form").show();
    },

    showLabelForm: function() {
        $("#id_new_label_form_wrapper").show();
        $("#id_button_show_label_form").hide();
    },

    sendLabelForm: function() {
        alert("Send label form");
    }
};

//util.addLoadEvent(LabelsetFormHelper.init());

var LabelsetFormHelper = {

    isInLabelset: {},
    isInitiallyChecked: {},
    isEditLabelsetForm: null,

    init: function(showLabelFormInitially, allLabels,
                   isInLabelset, isInitiallyChecked,
                   isLabelUnchangeable, isEditLabelsetForm) {

        this.isInLabelset = isInLabelset;
        this.isInitiallyChecked = isInitiallyChecked;
        this.isEditLabelsetForm = isEditLabelsetForm;

        if (showLabelFormInitially) {
            this.showLabelForm();
        }

        var i, checkboxElmt, checkboxRowJQ;
        
        for (i = 0; i < allLabels.length; i++) {

            var labelId = allLabels[i].labelId;
            checkboxRowJQ = $("#id_row_" + labelId);

            if (labelId in isInitiallyChecked && isInitiallyChecked[labelId]) {

                /* If the label should be checked initially, then check it.
                 * (Would be nice to do this through Django instead of through JS,
                 * but I can't figure out how. -Stephen) */
                checkboxElmt = $("#id_labels_" + labelId)[0];
                checkboxElmt.checked = true;
            }

            /* If the label is selected, then apply the appropriate style class */
            LabelsetFormHelper.updateRowAppearance(checkboxRowJQ[0]);

            if (labelId in isLabelUnchangeable && isLabelUnchangeable[labelId]) {
                /* in-labelset status is unchangeable, so apply a style class */
                checkboxRowJQ.addClass("disabled");
            }
            else {
                /* in-labelset status is changeable, so make it change when the
                 * user clicks any of the clickable cells in the row. */
                var clickableCells = checkboxRowJQ.children(".clickable_cell");

                clickableCells.each( function() {
                    // Set the click function for each clickable cell
                    // in this row.
                    $(this).click(function() {
                        // This is a click handler for a cell, so this.parent()
                        // is the row element.
                        LabelsetFormHelper.toggleRow($(this).parent()[0]);
                        LabelsetFormHelper.updateRowAppearance($(this).parent()[0]);
                    });
                });

/*                for (i = 0; i < clickableCells.length; i++) {
                    clickableCells[i].click( function() {
                        // This is a click handler for a cell, so this.parent()
                        // is the row element.
                        LabelsetFormHelper.toggleRow(this.parent());
                        LabelsetFormHelper.updateRowAppearance(this.parent());
                    });
                }*/
            }
        }

        /* Assign click actions to the buttons that show/hide the new-label form */
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

    /* Toggle the "checked" status of a table row corresponding to a label */
    toggleRow: function(checkboxRow) {
        var rowId = checkboxRow.id;
        var checkboxId = rowId.replace("id_row", "id_labels");
        var checkboxElmt = $("#" + checkboxId)[0];

        checkboxElmt.checked = !checkboxElmt.checked;
    },

    /* Update the appearance of a table row based on the row's "checked" status */
    updateRowAppearance: function(checkboxRow) {
        var rowId = checkboxRow.id;
        var labelId = rowId.replace("id_row_", "");
        var checkboxId = rowId.replace("id_row", "id_labels");
        var checkboxElmt = $("#" + checkboxId)[0];

        /* Update the row's style (which may change background color, etc.) */
        if (checkboxElmt.checked) {
            $(checkboxRow).addClass("selected");
        }
        else {
            $(checkboxRow).removeClass("selected");
        }

        /* If this is the Edit Labelset form, update the row's status
         * (added label or deleted label). */
        if (this.isEditLabelsetForm) {
            var statusElmtJQ = $(checkboxRow).find(".change_status");

            statusElmtJQ.empty();

            if (checkboxElmt.checked && !this.isInLabelset[labelId]) {
                statusElmtJQ.text("added");
            }
            else if (!checkboxElmt.checked && this.isInLabelset[labelId]) {
                statusElmtJQ.text("deleted");
            }
        }
    }
};

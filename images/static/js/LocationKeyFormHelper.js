var LocationKeyFormHelper = {

    /*
     Enable/disable the location key fields.
     Key field n is enabled only if key fields up to n-1 are filled in.
     Otherwise, field n is disabled (grayed out and non-interactive).
     */
    changeKeyFields: function() {
        var key1_elmt = document.getElementById("id_key1");
        var key2_elmt = document.getElementById("id_key2");
        var key3_elmt = document.getElementById("id_key3");
        var key4_elmt = document.getElementById("id_key4");
        var key5_elmt = document.getElementById("id_key5");

        // Set each disabled property to true or false
        key2_elmt.disabled = (util.trimSpaces(key1_elmt.value) == "");
        key3_elmt.disabled = (util.trimSpaces(key2_elmt.value) == "" || key2_elmt.disabled);
        key4_elmt.disabled = (util.trimSpaces(key3_elmt.value) == "" || key3_elmt.disabled);
        key5_elmt.disabled = (util.trimSpaces(key4_elmt.value) == "" || key4_elmt.disabled);
    }
};

util.addLoadEvent(LocationKeyFormHelper.changeKeyFields);
var LocationKeyFormHelper = (function() {

    var $key1 = null;
    var $key2 = null;
    var $key3 = null;
    var $key4 = null;
    var $key5 = null;

    /*
     Enable/disable the location key fields.
     Key field n is enabled only if key fields up to n-1 are filled in.
     Otherwise, field n is disabled (grayed out and non-interactive).
     */
    function updateKeyFields() {

        $key2.prop('disabled', util.trimSpaces($key1.val()) == "");
        $key3.prop('disabled', util.trimSpaces($key2.val()) == "" || $key2.prop('disabled'));
        $key4.prop('disabled', util.trimSpaces($key3.val()) == "" || $key3.prop('disabled'));
        $key5.prop('disabled', util.trimSpaces($key4.val()) == "" || $key4.prop('disabled'));
    }

    return {

        /* Initialize the upload form. */
        init: function(){
            $key1 = $('#id_key1');
            $key2 = $('#id_key2');
            $key3 = $('#id_key3');
            $key4 = $('#id_key4');
            $key5 = $('#id_key5');

            updateKeyFields();

            $key1.keyup(function() { updateKeyFields(); });
            $key2.keyup(function() { updateKeyFields(); });
            $key3.keyup(function() { updateKeyFields(); });
            $key4.keyup(function() { updateKeyFields(); });
            $key5.keyup(function() { updateKeyFields(); });
        }
    }
})();

util.addLoadEvent(LocationKeyFormHelper.init);
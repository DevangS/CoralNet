/*
General-purpose JS utility functions can go here.
*/

var util = {

    /*
    Add a JS event that will run when the page is loaded.
    This will just add to the "events to run" list, it won't
    override previously specified events.

    From http://simonwillison.net/2004/May/26/addLoadEvent/
    */
    addLoadEvent: function(func) {
        var oldonload = window.onload;
        if (typeof window.onload != 'function') {
            window.onload = func;
        } else {
            window.onload = function() {
                if (oldonload) {
                    oldonload();
                }
                func();
            }
        }
    },

    /*
    Trim leading and trailing spaces from a string.

    From http://blog.stevenlevithan.com/archives/faster-trim-javascript
    */
    trimSpaces: function(str) {
        return str.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
    }

};

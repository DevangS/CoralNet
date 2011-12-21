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
    Take a mouse event and return "LEFT", "MIDDLE", or "RIGHT" depending
    on which mouse button was clicked.

    From http://unixpapa.com/js/mouse.html
    "The following test works for all browsers except Opera 7."
    As of Aug 17, 2011
    */
    identifyMouseButton: function(event) {
        if (event.which == null)
           /* IE case */
           return (event.button < 2) ? "LEFT" :
                     ((event.button == 4) ? "MIDDLE" : "RIGHT");
        else
           /* All others */
           return (event.which < 2) ? "LEFT" :
                     ((event.which == 2) ? "MIDDLE" : "RIGHT");
    },

    /*
    Trim leading and trailing spaces from a string.

    From http://blog.stevenlevithan.com/archives/faster-trim-javascript
    */
    trimSpaces: function(str) {
        return str.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
    }

};



/*
 * Extensions of standard types can go here.
 * Always make sure these don't conflict with third-party JS files' extensions of standard types.
 */


/* Array indexOf(), in case the browser doesn't have it (hi, IE)
 * Source: https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Array/IndexOf
 */
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function (searchElement /*, fromIndex */ ) {
        "use strict";
        if (this === void 0 || this === null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 0) {
            n = Number(arguments[1]);
            if (n !== n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n !== 0 && n !== Infinity && n !== -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}


/* String format function, similar to printf in C.
 * Example usage: "{0} is dead, but {1} is alive! {0} {2}".format("ASP", "ASP.NET")
 * Example output: ASP is dead, but ASP.NET is alive! ASP {2}
 * 
 * Source: http://stackoverflow.com/questions/610406/javascript-equivalent-to-printf-string-format/4673436#4673436
 */
String.prototype.format = function() {
  var args = arguments;
  return this.replace(/{(\d+)}/g, function(match, number) {
    return typeof args[number] != 'undefined'
      ? args[number]
      : match
    ;
  });
};

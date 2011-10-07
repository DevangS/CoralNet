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



/*
 * Extensions of standard types can go here.
 * Always make sure these don't conflict with third-party JS files' extensions of standard types.
 */


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

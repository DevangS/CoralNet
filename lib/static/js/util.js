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
    Checks a string or number to see if it represents a number.
    Source: http://stackoverflow.com/a/1830844/859858
    */
    representsNumber: function(x) {
        return !isNaN(parseFloat(x)) && isFinite(x);
    },

    /*
    Checks a string or number to see if it represents an integer.
    Based on: http://stackoverflow.com/a/3886106/859858
    */
    representsInt: function(x) {
        return util.representsNumber(x) && parseFloat(x) % 1 === 0;
    },

    /*
    Returns true if the user's OS is Mac, false otherwise.
    */
    osIsMac: function() {
        return (navigator.appVersion.indexOf("Mac") !== -1);
    },

    /*
    Converts an arguments object to an array.
    Source: http://javascriptweblog.wordpress.com/2010/04/05/curry-cooking-up-tastier-functions/
    */
    toArray: function(argumentsObj) {
        return Array.prototype.slice.call(argumentsObj);
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


/* Curry function.
 *
 * Example:
 * function converter(toUnit, factor, offset, input) {
 *     offset = offset || 0;
 *     return [((offset+input)*factor).toFixed(2), toUnit].join(" ");
 * }
 * var fahrenheitToCelsius = converter.curry('degrees C',0.5556, -32);
 * fahrenheitToCelsius(98); //"36.67 degrees C"
 *
 * Source: http://javascriptweblog.wordpress.com/2010/04/05/curry-cooking-up-tastier-functions/
 */
Function.prototype.curry = function() {
    if (arguments.length<1) {
        return this; //nothing to curry with - return function
    }
    var __method = this;
    var args = util.toArray(arguments);
    return function() {
        return __method.apply(this, args.concat(util.toArray(arguments)));
    }
};


/* String format function, similar to Python's.
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



/*
 * jQuery extensions can go here.
 */

/* autoWidth
 *
 * Automatically make a group of elements the same width, by taking the maximum width of all
 * the elements and then setting the whole group to this width.
 *
 * Parameters:
 * limitWidth - Maximum allowed width.  If any element's width is greater than limitWidth,
 *              make the elements use width=limitWidth instead.
 *
 * Side effects:
 * On slow computers, the elements will appear without their width set for the first
 * 0.5 second or so, and then will shift position on the page once they have their
 * widths set.  It can be jarring to see this on nearly every page load.
 *
 * Original source (though it's been slightly modified):
 * http://stackoverflow.com/a/4641390 (http://stackoverflow.com/questions/4641346/css-to-align-label-and-input)
 * http://www.jankoatwarpspeed.com/post/2008/07/09/Justify-elements-using-jQuery-and-CSS.aspx#id_b16cb791-5bd7-4bb3-abc2-dc414fc1bd07
 * - (1 mistake: maxWidth >= settings.limitWidth should be $(this).width >= settings.limitWidth)
 */
jQuery.fn.autoWidth = function(options) {
  var settings = {
      limitWidth: false
  };

  if(options) {
      jQuery.extend(settings, options);
  }

  var maxWidth = 0;

  this.each(function(){
      var thisWidth = $(this).width();
      if (thisWidth > maxWidth){
          if(settings.limitWidth && thisWidth >= settings.limitWidth) {
            maxWidth = settings.limitWidth;
          } else {
            maxWidth = thisWidth;
          }
      }
  });

  this.width(maxWidth);
};

/* changeFontSize
 *
 * Change the font size of an element.
 *
 * Parameters:
 * changeFactor - a number specifying how much to multiply the font size by.
 *   For example, changeFactor = 0.9 will make the font 90% of its original size.
 */
jQuery.fn.changeFontSize = function(changeFactor) {
    this.each( function(){
        var oldFontSize = $(this).css('font-size');
        var oldFontSizeNumber = parseFloat(oldFontSize);
        var fontSizeUnits = oldFontSize.substring(oldFontSizeNumber.toString().length);

        var newFontSizeNumber = oldFontSizeNumber * changeFactor;
        var newFontSize = newFontSizeNumber.toString() + fontSizeUnits;
        $(this).css('font-size', newFontSize);
    });
};

/* Selector - exactlycontains
 *
 * Variation of the jQuery selector 'contains':
 * 'exactlycontains' will match an element if its entire inner text is
 * exactly what is specified in the argument, as opposed to simply
 * finding the argument as a substring.
 * 
 * Source: http://api.jquery.com/contains-selector/ - see comment by Gibran
 */
$.expr[":"].exactlycontains = function(obj, index, meta, stack){
    return (obj.textContent || obj.innerText || $(obj).text() || "").toLowerCase() == meta[3].toLowerCase();
};



/*
 * Dajaxice settings can go here.
 */

if (window.Dajaxice) {

    /* Override Dajaxice's default exception behavior (the "Something goes wrong" alert).
     */
    Dajaxice.setup({'default_exception_callback': function(){
        if (console) {
            console.error("A Dajaxice error occurred.  Are you having Internet connection problems?  If not, this may be a CoralNet bug.  Please let us know about it.");
        }
    }});
}



/*
 * CSS-manipulating JS to run at every page load can go here.
 */

/* Make all labels with class 'form_label' the same width,
 * and figure out this width dynamically (the longest width
 * needed by any field, with a max allowed width of 250px).
 *
 * See previously defined: jQuery.fn.autoWidth
 */
/*util.addLoadEvent( function() {
    $('label.column_form_text_field').autoWidth({limitWidth: 250});
});*/

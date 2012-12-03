/* Take a layout in JSON format, and create a DOM tree that
 * fits the layout. */

var Layouts = {

    createLayout: function createLayout(layout, parentElement) {
        // <funcname>: function <funcname> - why is the funcname there
        // twice?  The first one declares it to be a variable of the
        // containing object.  The second one makes the function visible
        // to itself, which allows for recursion.

        var parentWidth = $(parentElement).width();
        var parentHeight = $(parentElement).height();

        var key;
        var elementCount = 0;
        var direction = null;

        // TODO: Re-work everything here to account for the new list-based
        // structure of the YAML file.
        for (key in layout) {
            if (!layout.hasOwnProperty(key)) {continue;}

            elementCount++;

            var keyTokens = key.split('-');

            if (direction === null) {
                direction = keyTokens[0];
            }
            else {
                if (direction !== keyTokens[0]) {
                    console.log("createLayout(): Direction mismatch");
                    throw new Error("createLayout(): Direction mismatch");
                }
            }

            var element;
            var isLeaf = util.toType(layout[key]) !== 'object';

            if (isLeaf) {
                element = document.getElementById(layout[key]);
            }
            else {
                element = document.createElement('div');
                element.id = '{0}-{1}'.format(parentElement.id, elementCount);
            }

            var sizeToken = keyTokens[1];
            if (sizeToken.endsWith('%')) {
                var percentageStr = sizeToken.substring(0, sizeToken.length-1);
                var percentage = parseInt(percentageStr);

                if (direction === 'x') {
                    $(element).width(parentWidth * (percentage / 100));
                    $(element).height(parentHeight);
                    $(element).css('float', 'left');
                }
                else if (direction === 'y') {
                    $(element).width(parentWidth);
                    $(element).height(parentHeight * (percentage / 100));
                }
                else {
                    console.log("createLayout(): Unrecognized direction");
                    throw new Error("createLayout(): Unrecognized direction");
                }
            }
            else {
                console.log("createLayout(): Unrecognized size token");
                throw new Error("createLayout(): Unrecognized size token");
            }

            if (!isLeaf) {
                createLayout(layout[key], element);
            }
            parentElement.appendChild(element);
        }
    }
};
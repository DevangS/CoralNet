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

        var elmt_i;
        var key;
        var direction = null;

        for (elmt_i = 0; elmt_i < layout.length; elmt_i++) {

            var layout_subtree = layout[elmt_i];

            // TODO: There has to be a better way to just get the one and only key.
            var k;
            for (k in layout_subtree) {
                if (!layout_subtree.hasOwnProperty(k)) {continue;}

                key = k;
            }

            var keyTokens = key.split('-');

            if (direction === null) {
                // The direction of the first element should be the
                // direction of all elements.  On the first element,
                // direction === null.
                direction = keyTokens[0];
            }
            else {
                // On subsequent elements, check that the direction matches
                // that of previous elements.
                if (direction !== keyTokens[0]) {
                    console.log("createLayout(): Direction mismatch");
                    throw new Error("createLayout(): Direction mismatch");
                }
            }

            var element;
            var isLeaf = util.toType(layout_subtree[key]) !== 'array';

            if (isLeaf) {
                element = document.getElementById(layout_subtree[key]);
            }
            else {
                element = document.createElement('div');
                element.id = '{0}-{1}'.format(parentElement.id, elmt_i);
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
                createLayout(layout_subtree[key], element);
            }
            parentElement.appendChild(element);
        }
    }
};
/* Take a layout in JSON format, and create a DOM tree that
 * fits the layout. */

var Layouts = {

    createLayout: function createLayout(layout, parentElement) {
        // <funcname>: function <funcname> - why is the funcname there
        // twice?  The first one declares it to be a variable of the
        // containing object.  The second one makes the function visible
        // to itself, which allows for recursion.

        var i;
        var key;
        var direction = null;

        var sizeDict = {};

        for (i = 0; i < layout.length; i++) {

            var layout_subtree_container = layout[i];
            var sizeEntry = {};
            var current_subtree_level_direction = null;

            // Get the one and only key of layout_subtree_container.
            //
            // Why do we have an object with only one key/value pair?
            // Because it makes the YAML syntax look nice.  The flip
            // side is that the Javascript we have to write to get the
            // only key looks ugly...
            for (var k in layout_subtree_container) {
                if (!layout_subtree_container.hasOwnProperty(k)) {continue;}
                key = k;
            }
            var layout_subtree = layout_subtree_container[key];

            var keyTokens = key.split('-');
            var directionToken = keyTokens[0];
            var sizeToken = keyTokens[1];

            if (current_subtree_level_direction === null) {
                // The direction of the first element should be the
                // direction of all elements.  On the first element,
                // direction === null.
                current_subtree_level_direction = directionToken;
            }
            else {
                // On subsequent elements, check that the direction matches
                // that of previous elements.
                if (current_subtree_level_direction !== directionToken) {
                    console.log("createLayout(): Direction mismatch");
                    throw new Error("createLayout(): Direction mismatch");
                }
            }

            if (directionToken !== 'x' && directionToken !== 'y') {
                console.log("createLayout(): Unrecognized direction");
                throw new Error("createLayout(): Unrecognized direction");
            }

            sizeEntry.direction = directionToken;

            if (sizeToken.endsWith('%')) {
                sizeEntry.type = 'percentage';

                var percentageStr = sizeToken.substring(0, sizeToken.length-1);
                var percentage = parseInt(percentageStr);
                sizeEntry.size = percentage;
            }
            else {
                console.log("createLayout(): Unrecognized size token");
                throw new Error("createLayout(): Unrecognized size token");
            }

            var childElement;
            var isLeaf = util.toType(layout_subtree) !== 'array';

            if (isLeaf) {
                childElement = document.getElementById(layout_subtree);
            }
            else {
                childElement = document.createElement('div');
                childElement.id = '{0}-{1}'.format(parentElement.id, i);
            }

            // Save the sizing information, for reference whenever the
            // layout sizes need to be re-computed later.
            sizeDict[childElement.id] = sizeEntry;

            // Compute the layout subtree of this child element, and update
            // the sizeDict with the entries from the subtree.
            var childSizeDict;
            if (!isLeaf) {
                childSizeDict = createLayout(layout_subtree, childElement);

                for (var csdKey in childSizeDict) {
                    sizeDict[csdKey] = childSizeDict[csdKey];
                }
            }

            // Append the child element to the layout
            parentElement.appendChild(childElement);
        }

        return sizeDict;
    },

    resizeLayout: function resizeLayout(sizeDict, parentElement) {

        var $parentElement = $(parentElement);

        var parentWidth = $parentElement.width();
        var parentHeight = $parentElement.height();

        var i;
        var children = $parentElement.children();

        for (i = 0; i < children.length; i++) {

            var childElement = children[i];

            if (sizeDict.hasOwnProperty(childElement.id)) {

                // We do have a size entry for this element, so compute the
                // element's size, and try computing the size of all of
                // this element's children, too.

                var sizeEntry = sizeDict[childElement.id];

                if (sizeEntry.type === 'percentage') {

                    if (sizeEntry.direction === 'x') {
                        $(childElement).width(parentWidth * (sizeEntry.size / 100));
                        $(childElement).height(parentHeight);
                        $(childElement).css('float', 'left');
                    }
                    else if (sizeEntry.direction === 'y') {
                        $(childElement).width(parentWidth);
                        $(childElement).height(parentHeight * (sizeEntry.size / 100));
                    }
                }

                resizeLayout(sizeDict, childElement);
            }

            // Otherwise, we don't have a size entry for this element.  This
            // means we also won't have size entries for any child elements,
            // so there's nothing left to do.
        }
    }
};
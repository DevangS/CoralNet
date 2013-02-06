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

        var leftover_size_token_count = 0;

        for (i = 0; i < layout.length; i++) {

            var layoutSubtreeContainer = layout[i];
            var sizeEntry = {};
            var currentSubtreeLevelDirection = null;

            // Get the one and only key of layoutSubtreeContainer.
            //
            // Why do we have an object with only one key/value pair?
            // Because it makes the YAML syntax look nice.  The flip
            // side is that the Javascript we have to write to get the
            // only key looks ugly... unless you can assume ECMAScript 5
            // browser support and use Object.keys().
            for (var k in layoutSubtreeContainer) {
                if (!layoutSubtreeContainer.hasOwnProperty(k)) {continue;}
                key = k;
            }
            // The value, layoutSubtree, can either be a subtree of the
            // layout (an array containing more elements), or a leaf of
            // the layout (a string, the id of an element).
            var layoutSubtree = layoutSubtreeContainer[key];

            var keyTokens = key.split('-');
            var directionToken = keyTokens[0];
            var sizeToken = keyTokens[1];

            if (currentSubtreeLevelDirection === null) {
                // The direction of the first element should be the
                // direction of all elements.  On the first element,
                // direction === null.
                currentSubtreeLevelDirection = directionToken;
            }
            else {
                // On subsequent elements, check that the direction matches
                // that of previous elements.
                if (currentSubtreeLevelDirection !== directionToken) {
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
                sizeEntry.size = parseInt(percentageStr);
            }
            else if (sizeToken.endsWith('px')) {
                sizeEntry.type = 'pixel';

                var pixelStr = sizeToken.substring(0, sizeToken.length-2);
                sizeEntry.size = parseInt(pixelStr);
            }
            else if (sizeToken === 'leftover') {
                sizeEntry.type = 'leftover';

                leftover_size_token_count++;
                if (leftover_size_token_count > 1) {
                    console.log("createLayout(): More than one 'leftover' size token in a set");
                    throw new Error("createLayout(): More than one 'leftover' size token in a set");
                }
            }
            else {
                console.log("createLayout(): Unrecognized size token");
                throw new Error("createLayout(): Unrecognized size token");
            }

            var childElement;
            var isLeaf = util.toType(layoutSubtree) !== 'array';
            var genericElementId = '{0}-{1}'.format(parentElement.id, i);

            if (isLeaf) {
                // x-50%: someElement
                var leafElementName = layoutSubtree

                if (leafElementName === 'divider') {
                    childElement = document.createElement('div');
                    childElement.id = genericElementId;
                    $(childElement).css('background-color', 'black');
                }
                else {
                    childElement = document.getElementById(leafElementName);
                }
            }
            else {
                // x-50%:
                childElement = document.createElement('div');
                childElement.id = genericElementId;
            }

            // Save the sizing information, for reference whenever the
            // layout sizes need to be re-computed later.
            sizeDict[childElement.id] = sizeEntry;

            // Compute the layout subtree of this child element, and update
            // the sizeDict with the entries from the subtree.
            var childSizeDict;
            if (!isLeaf) {
                childSizeDict = createLayout(layoutSubtree, childElement);

                for (var csdKey in childSizeDict) {
                    if (!childSizeDict.hasOwnProperty(csdKey)) {continue;}
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
        var childElement, sizeEntry;
        var sizeAllocatedThisLevel = 0;

        for (i = 0; i < children.length; i++) {

            childElement = children[i];
            var width, height;

            if (sizeDict.hasOwnProperty(childElement.id)) {

                // We do have a size entry for this element, so compute the
                // element's size, and try computing the size of all of
                // this element's children, too.

                sizeEntry = sizeDict[childElement.id];

                if (sizeEntry.type === 'pixel') {

                    if (sizeEntry.direction === 'x') {
                        width = sizeEntry.size;
                        $(childElement).width(width);
                        sizeAllocatedThisLevel += width;

                        $(childElement).height(parentHeight);
                        $(childElement).css('float', 'left');

                    }
                    else if (sizeEntry.direction === 'y') {
                        $(childElement).width(parentWidth);

                        height = sizeEntry.size;
                        $(childElement).height(height);
                        sizeAllocatedThisLevel += height;
                    }
                }

                resizeLayout(sizeDict, childElement);
            }
        }

        for (i = 0; i < children.length; i++) {

            childElement = children[i];

            if (sizeDict.hasOwnProperty(childElement.id)) {

                sizeEntry = sizeDict[childElement.id];

                if (sizeEntry.type === 'percentage') {

                    if (sizeEntry.direction === 'x') {
                        width = parentWidth * (sizeEntry.size / 100);
                        $(childElement).width(width);
                        sizeAllocatedThisLevel += width;

                        $(childElement).height(parentHeight);
                        $(childElement).css('float', 'left');
                    }
                    else if (sizeEntry.direction === 'y') {
                        $(childElement).width(parentWidth);

                        height = parentHeight * (sizeEntry.size / 100)
                        $(childElement).height(height);
                        sizeAllocatedThisLevel += height;
                    }
                }

                resizeLayout(sizeDict, childElement);
            }
        }

        for (i = 0; i < children.length; i++) {

            childElement = children[i];

            if (sizeDict.hasOwnProperty(childElement.id)) {

                sizeEntry = sizeDict[childElement.id];

                if (sizeEntry.type === 'leftover') {

                    if (sizeEntry.direction === 'x') {
                        $(childElement).width(parentWidth - sizeAllocatedThisLevel);

                        $(childElement).height(parentHeight);
                        $(childElement).css('float', 'left');
                    }
                    else if (sizeEntry.direction === 'y') {
                        $(childElement).width(parentWidth);

                        $(childElement).height(parentHeight - sizeAllocatedThisLevel);
                    }
                }

                resizeLayout(sizeDict, childElement);
            }
        }
    }
};
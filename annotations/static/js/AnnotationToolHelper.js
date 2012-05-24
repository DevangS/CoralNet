var ATH = {

    // Compatibility
    // If the appVersion contains the substring "Mac", then it's probably a mac...
    mac: util.osIsMac(),

    // TODO: Change all null initializations to undefined.
    // TODO: Change the naming convention of jQuery variables from -JQ to $-

    // HTML elements
    annotationArea: null,
    annotationList: null,
    annotationFieldRows: [],
    annotationFields: [],
    annotationRobotFields: [],
    annotationFieldsJQ: null,
    imageArea: undefined,
    pointsCanvas: null,
    listenerElmt: null,
    saveButton: null,

    // Annotation related
    labelCodes: [],
    labelCodesToNames: {},
    currentLabelButton: null,

    // Canvas related
	context: null,
    canvasPoints: [], imagePoints: null,
    numOfPoints: null,
    NUMBER_FONT_FORMAT_STRING: "bold {0}px sans-serif",

    // Border where the canvas is drawn, but the image is not.
    // This is used to fully show the points that are located near the edge of the image.
	CANVAS_GUTTER: 25,
    CANVAS_GUTTER_COLOR: "#BBBBBB",

    // Related to possible states of each annotation point
    pointContentStates: [],
    pointGraphicStates: [],
    STATE_UNANNOTATED: 0,
    STATE_ROBOT: 1,
    STATE_ANNOTATED: 2,
    STATE_SELECTED: 3,
    STATE_NOTSHOWN: 4,

    // Point number outline color
    OUTLINE_COLOR: "#000000",
    
    // Point viewing mode
    pointViewMode: null,
    POINTMODE_ALL: 0,
    POINTMODE_SELECTED: 1,
    POINTMODE_NONE: 2,

    // The original image's dimensions
    IMAGE_FULL_WIDTH: null,
    IMAGE_FULL_HEIGHT: null,
    // The area that the image is permitted to fill
    IMAGE_AREA_WIDTH: null,
    IMAGE_AREA_HEIGHT: null,
    // The canvas area, where drawing is allowed
    ANNOTATION_AREA_WIDTH: null,
    ANNOTATION_AREA_HEIGHT: null,
    // Label button grid
    BUTTON_GRID_MAX_X: null,
    BUTTON_GRID_MAX_Y: null,
    BUTTONS_PER_ROW: 10,
    LABEL_BUTTON_WIDTH: null,

    // Display parameters of the image.
    // > 1 zoomFactor means larger than original image
    // zoom levels start at 0 (fully zoomed out) and go up like 1,2,3,etc.
    imageDisplayWidth: null,
    imageDisplayHeight: null,
    zoomFactor: null,
    zoomLevel: null,
    ZOOM_FACTORS: {},
    ZOOM_INCREMENT: 1.5,
    HIGHEST_ZOOM_LEVEL: 8,
    // Current display position of the image.
    // centerOfZoom is in terms of raw-image coordinates.
    // < 0 offset means top left corner is not visible.
    centerOfZoomX: null,
    centerOfZoomY: null,
    imageLeftOffset: null,
    imageTopOffset: null,


    init: function(fullHeight, fullWidth,
                   IMAGE_AREA_WIDTH, IMAGE_AREA_HEIGHT,
                   imagePoints, labels) {
        var i, j, n;    // Loop variables...

        /*
         * Initialize styling, sizing, and positioning for various elements
         */

        ATH.IMAGE_FULL_WIDTH = fullWidth;
        ATH.IMAGE_FULL_HEIGHT = fullHeight;
        ATH.IMAGE_AREA_WIDTH = IMAGE_AREA_WIDTH;
        ATH.IMAGE_AREA_HEIGHT = IMAGE_AREA_HEIGHT;

        ATH.ANNOTATION_AREA_WIDTH = ATH.IMAGE_AREA_WIDTH + (ATH.CANVAS_GUTTER * 2);
        ATH.ANNOTATION_AREA_HEIGHT = ATH.IMAGE_AREA_HEIGHT + (ATH.CANVAS_GUTTER * 2);

        var horizontalSpacePerButton = ATH.ANNOTATION_AREA_WIDTH / ATH.BUTTONS_PER_ROW;

        // LABEL_BUTTON_WIDTH will represent a value that can be passed into jQuery's
        // width() and css('width'), and these jQuery functions deal with
        // inner width + padding + border only.
        // So don't count the button's margins... and subtract another pixel or two
        // to be safe, so that slightly imprecise rendering won't cause an overflow.
        // (Chrome seems a bit more prone to this kind of imprecise rendering, compared
        // to Firefox...)
        ATH.LABEL_BUTTON_WIDTH = horizontalSpacePerButton - (
            parseFloat($('#labelButtons button').css('margin-left'))
            + parseFloat($('#labelButtons button').css('margin-right'))
            + 2
        );

        var $labelButton;
        for (i = 0; i < labels.length; i++) {
            $labelButton = $("#labelButtons button:exactlycontains('{0}')".format(labels[i].code));

            /* Set the button's width.  But first, check to see if the
             button text is going to overflow; if so, then shrink the text
             until it doesn't overflow.

             ... never mind that text shrinking thing for now.  Setting the
             height of the button afterward is just not reliable at all, and
             can destroy the layout of buttons below.
             TODO: Need a robust way to support text shrinking in label buttons.
             */

//            var numOfSizeDecreases = 0;
//            var initialButtonHeight = $labelButton.outerHeight();
//            while (parseFloat($labelButton.outerWidth()) > ATH.LABEL_BUTTON_WIDTH) {
//                // Scale the font to 90% size of what it was before.
//                $labelButton.changeFontSize(0.9);
//
//                numOfSizeDecreases++;
//                // Don't shrink the text so much that it'll become totally unreadable.
//                // Just accept the text overflow if we've already shrunk the text a lot.
//                if (numOfSizeDecreases > 8)
//                    break;
//            }
//            // Need to reset the button's height to what it was before,
//            // if we shrunk the button's text.
//            if (numOfSizeDecreases > 0)
//                $labelButton.css('height', initialButtonHeight);

            // Now set the button's width.
            $labelButton.css('width', ATH.LABEL_BUTTON_WIDTH.toString() + "px");
        }

        ATH.BUTTON_GRID_MAX_Y = Math.floor(labels.length / ATH.BUTTONS_PER_ROW);
        ATH.BUTTON_GRID_MAX_X = ATH.BUTTONS_PER_ROW - 1;

        ATH.annotationArea = $("#annotationArea")[0];
        ATH.annotationList = $("#annotationList")[0];
        ATH.pointsCanvas = $("#pointsCanvas")[0];
        ATH.listenerElmt = $("#listenerElmt")[0];
        ATH.saveButton = $("#saveButton")[0];

        ATH.imageArea = $("#imageArea")[0];

        $('#mainColumn').css({
            "width": ATH.ANNOTATION_AREA_WIDTH + "px"
        });

        var annotationListMaxHeight =
            ATH.ANNOTATION_AREA_HEIGHT - parseFloat($("#toolButtonArea").outerHeight(true));

        $(ATH.annotationList).css({
            "max-height": annotationListMaxHeight + "px"
        });

        $(ATH.annotationArea).css({
            "width": ATH.ANNOTATION_AREA_WIDTH + "px",
            "height": ATH.ANNOTATION_AREA_HEIGHT + "px",
            "background-color": ATH.CANVAS_GUTTER_COLOR
        });

        $(ATH.imageArea).css({
            "width": ATH.IMAGE_AREA_WIDTH + "px",
            "height": ATH.IMAGE_AREA_HEIGHT + "px",
            "left": ATH.CANVAS_GUTTER + "px",
            "top": ATH.CANVAS_GUTTER + "px"
        });

        // Set the height for the element containing the two main columns.
        // This ensures that the info below the annotation tool doesn't overlap with
        // the annotation tool.  Overlap is possible because the main column floats,
        // so the main column doesn't contribute to its container element's height.
        //
        // The container element's height will be set to the max of the
        // columns' DOM (computed) heights.
        $('#columnContainer').css({
            "height": Math.max(
                parseFloat($('#mainColumn').height()),
                parseFloat($('#rightSidebar').height())
            ).toString() + "px"
        });

        /* Initialization - Labels and label buttons */

        var groupsWithStyles = [];
        var groupStyles = {};
        var nextStyleNumber = 1;

        for (i = 0; i < labels.length; i++) {
            var label = labels[i];

            // If this label's functional group doesn't have a style yet,
            // then assign this group a style.
            if (groupsWithStyles.indexOf(label.group) === -1) {
                groupStyles[label.group] = 'group'+nextStyleNumber;
                groupsWithStyles.push(label.group);
                nextStyleNumber++;
            }

            // Get the label's button and apply the label's functional group style to it.
            $labelButton = $("#labelButtons button:exactlycontains('{0}')".format(label.code));
            $labelButton.addClass(groupStyles[label.group]);

            // Assign a grid position to the label button.
            // For example, i=0 gets position [0,0], i=13 gets [1,3]
            $labelButton.attr('gridy', Math.floor(i / ATH.BUTTONS_PER_ROW));
            $labelButton.attr('gridx', i % ATH.BUTTONS_PER_ROW);

            // When you mouseover the button, show the label name in a tooltip.
            $labelButton.attr('title', label.name);

            // Add to an array of available label codes, which will
            // be used for input checking purposes (in label fields).
            ATH.labelCodes.push(label.code);

            // Add to a mapping of label codes to names, which will
            // be used to show a label name when you mouse over a
            // label field with a valid code.
            ATH.labelCodesToNames[label.code] = label.name;
        }

        /*
         * Set initial image scaling so the whole image is shown.
         * Also set the allowable zoom factors.
         */

        var widthScaleRatio = ATH.IMAGE_FULL_WIDTH / ATH.IMAGE_AREA_WIDTH;
        var heightScaleRatio = ATH.IMAGE_FULL_HEIGHT / ATH.IMAGE_AREA_HEIGHT;
        var scaleDownFactor = Math.max(widthScaleRatio, heightScaleRatio);

        // If the scaleDownFactor is < 1, then it's scaled up (meaning the image is really small).
        ATH.zoomFactor = 1.0 / scaleDownFactor;

        // Allowable zoom factors/levels:
        // Start with the most zoomed out level, 0.  Level 1 is ZOOM_INCREMENT * level 0.
        // Level 2 is ZOOM_INCREMENT * level 1, etc.  Goes up to level HIGHEST_ZOOM_LEVEL.
        ATH.zoomLevel = 0;
        for (i = 0; i <= ATH.HIGHEST_ZOOM_LEVEL; i++) {
            ATH.ZOOM_FACTORS[i] = ATH.zoomFactor * Math.pow(ATH.ZOOM_INCREMENT, i);
        }

        // Based on the zoom level, set up the image area.
        // (No need to define centerOfZoom since we're not zooming in to start with.)
        ATH.setupImageArea();

        // Set the canvas's width and height properties so the canvas contents don't stretch.
        // Note that this is different from CSS width and height properties.
        ATH.pointsCanvas.width = ATH.ANNOTATION_AREA_WIDTH;
        ATH.pointsCanvas.height = ATH.ANNOTATION_AREA_HEIGHT;
        $(ATH.pointsCanvas).css({
            "left": 0,
		    "top": 0,
            "z-index": 1
        });

        /*
         * Initialize and draw annotation points,
         * and initialize some other variables and elements
         */

        // Create a canvas context
		ATH.context = ATH.pointsCanvas.getContext("2d");

        // Save this fresh context so we can restore it later as needed.
        ATH.context.save();

        // Translate the canvas context to compensate for the gutter and the image offset.
        ATH.resetCanvas();

        // Initialize point coordinates
        ATH.imagePoints = imagePoints;
        ATH.numOfPoints = imagePoints.length;
        ATH.getCanvasPoints();

        ATH.annotationFieldsJQ = $(ATH.annotationList).find('input');
        var annotationFieldRowsJQ = $(ATH.annotationList).find('tr');

        // Create arrays that map point numbers to HTML elements.
        // For example, for point 1:
        // annotationFields = form field with point 1's label code
        // annotationFieldRows = table row containing form field 1
        // annotationRobotFields = hidden form element of value true/false saying whether point 1 is robot annotated
        annotationFieldRowsJQ.each( function() {
            var field = $(this).find('input')[0];
            var pointNum = ATH.getPointNumOfAnnoField(field);
            var robotField = $('#id_robot_' + pointNum)[0];

            ATH.annotationFields[pointNum] = field;
            ATH.annotationFieldRows[pointNum] = this;
            ATH.annotationRobotFields[pointNum] = robotField;
        });

        // Set point annotation statuses,
        // and draw the points
        for (n = 1; n <= ATH.numOfPoints; n++) {
            ATH.pointContentStates[n] = {'label': undefined, 'robot': undefined};
            ATH.pointGraphicStates[n] = ATH.STATE_NOTSHOWN;
        }
        ATH.annotationFieldsJQ.each( function() {
            ATH.onPointUpdate(this, 'initialize');
        });

        // Set the initial point view mode.  This'll trigger a redraw of the points, but that's okay;
        // initialization slowness is a relatively minor worry.
        ATH.changePointMode(ATH.POINTMODE_ALL);

        // Initialize save button
        $(ATH.saveButton).attr('disabled', 'disabled');
        $(ATH.saveButton).text('Saved');

        // Initialize all_done state
        Dajaxice.CoralNet.annotations.ajax_is_all_done(
            ATH.setAllDoneIndicator,
            {'image_id': $('#id_image_id')[0].value}
        );

        /*
         * Set event handlers
         */

        // Instructions show/hide buttons
        $('#id_button_show_instructions').click(ATH.showInstructions);
        $('#id_button_hide_instructions').click(ATH.hideInstructions);

        // Mouse button is pressed and un-pressed on the canvas
		$(ATH.listenerElmt).mouseup( function(e) {

            var mouseButton = util.identifyMouseButton(e);
            var clickType;

            // Get the click type (in Windows terms)...

            if ((!ATH.mac && e.ctrlKey && mouseButton === "LEFT")
                || ATH.mac && e.metaKey && mouseButton === "LEFT")
                // Ctrl-click non-Mac OR Cmd-click Mac
                clickType = "ctrlClick";
            else if (mouseButton === "RIGHT"
                     || (ATH.mac && e.ctrlKey && mouseButton === "LEFT"))
                // Right-click OR Ctrl-click Mac
                clickType = "rightClick";
            else if (mouseButton === "LEFT")
                // Other left click
                clickType = "leftClick";
            else
                // Middle or other click
                clickType = "unknown";


            // Select the nearest point.
            if (clickType === "ctrlClick") {

                // This only works if we're displaying all points.
                if (ATH.pointViewMode !== ATH.POINTMODE_ALL)
                    return;

                var nearestPoint = ATH.getNearestPoint(e);
                ATH.toggle(nearestPoint);
            }

            // Zoom in or out on the image display.
            else if (clickType === "leftClick" || clickType === "rightClick") {

                // Zoom in.
                if (clickType === "leftClick") {
                    ATH.zoomIn(e);
                }
                // Zoom out.
                else if (clickType === "rightClick") {
                    ATH.zoomOut(e);
                }
            }
        });

        // Disable the context menu on the listener element.
        // The menu just gets in the way while trying to zoom out, etc.
        $(ATH.listenerElmt).bind('contextmenu', function(e){
            return false;
        });
        // Same goes for the canvas element, which is sometimes what we end up
        // right clicking on if the image is no longer over that part of the canvas.
        $(ATH.pointsCanvas).bind('contextmenu', function(e){
            return false;
        });
        // Also note that the listener element uses CSS to disable
        // double-click-to-select (it makes the image turn blue, which is annoying).

        // Save button is clicked
        $(ATH.saveButton).click(function() {
            ATH.saveAnnotations();
        });

        // A label button is clicked
        $('#labelButtons').find('button').each( function() {
            $(this).click( function() {
                // Label the selected points with this button's label code
                ATH.labelSelected($(this).text());
                // Set the current label button.
                ATH.setCurrentLabelButton(this);
            });
        });

        // Label field gains focus
        ATH.annotationFieldsJQ.focus(function() {
            var pointNum = ATH.getPointNumOfAnnoField(this);
            ATH.unselectAll();
            ATH.select(pointNum);

            // Shift the center of zoom to the focused point.
            ATH.centerOfZoomX = ATH.imagePoints[pointNum-1].column;
            ATH.centerOfZoomY = ATH.imagePoints[pointNum-1].row;

            // If we're zoomed in at all, complete the center-of-zoom-shift process.
            if (ATH.zoomLevel > 0) {

                // Adjust the image and point coordinates.
                ATH.setupImageArea();
                ATH.getCanvasPoints();

                // Redraw all points.
                ATH.redrawAllPoints();
            }
        });

        // Label field is typed into and changed, and then unfocused.
        // (This does NOT run when a label button changes the label field.)
        ATH.annotationFieldsJQ.change(function() {
            ATH.onLabelFieldTyping(this);
        });

        // Number next to a label field is clicked.
        $(".annotationFormLabel").click(function() {
            var pointNum = parseInt($(this).text());
            ATH.toggle(pointNum);
        });

        // A zoom button is clicked.

        $("#zoomInButton").click(function() {
            ATH.zoomIn();
        });
        $("#zoomOutButton").click(function() {
            ATH.zoomOut();
        });
        $("#zoomFitButton").click(function() {
            ATH.zoomFit();
        });

        // A point mode button is clicked.
        
        $("#pointModeButtonAll").click(function() {
            ATH.changePointMode(ATH.POINTMODE_ALL);
        });
        $("#pointModeButtonSelected").click(function() {
            ATH.changePointMode(ATH.POINTMODE_SELECTED);
        });
        $("#pointModeButtonNone").click(function() {
            ATH.changePointMode(ATH.POINTMODE_NONE);
        });

        // A quick-select button is clicked.

        $("#quickSelectButtonNone").click(function() {
            // Un-select all points.

            ATH.unselectAll();
        });
        $("#quickSelectButtonUnannotated").click(function() {
            // Select only unannotated points.

            var unannotatedPoints = [];

            for (var n = 1; n <= ATH.numOfPoints; n++) {
                var row = ATH.annotationFieldRows[n];
                if (!$(row).hasClass('annotated'))
                    unannotatedPoints.push(n);
            }

            ATH.unselectAll();
            for (var i = 0; i < unannotatedPoints.length; i++) {
                ATH.select(unannotatedPoints[i])
            }
        });
        $("#quickSelectButtonInvert").click(function() {
            // Invert selections. (selected -> unselected, unselected -> selected)

            var unselectedPoints = [];

            for (var n = 1; n <= ATH.numOfPoints; n++) {
                var row = ATH.annotationFieldRows[n];
                if (!$(row).hasClass('selected'))
                    unselectedPoints.push(n);
            }

            ATH.unselectAll();
            for (var i = 0; i < unselectedPoints.length; i++) {
                ATH.select(unselectedPoints[i])
            }
        });

        // Keymap.
        var keymap = [
            ['shift+up', ATH.zoomIn, 'all'],
            ['shift+down', ATH.zoomOut, 'all'],

            ['return', ATH.confirmFieldAndFocusNext, 'field'],
            ['up', ATH.focusPrevField, 'field'],
            ['down', ATH.focusNextField, 'field'],
            ['ctrl+left', ATH.moveCurrentLabelLeft, 'field'],
            ['ctrl+right', ATH.moveCurrentLabelRight, 'field'],
            ['ctrl+up', ATH.moveCurrentLabelUp, 'field'],
            ['ctrl+down', ATH.moveCurrentLabelDown, 'field'],
            ['ctrl', ATH.beginKeyboardLabelling, 'field', 'keydown']
        ];

        // Bind event listeners according to the keymap.
        for (i = 0; i < keymap.length; i++) {
            var keymapping = keymap[i];
            
            var key = keymapping[0];
            var func = keymapping[1];
            var scope = keymapping[2];
            var elementsToBind;

            // Event is keyup unless otherwise specified
            var keyEvent = 'keyup';
            if (keymapping.length >= 4)
                keyEvent = keymapping[3];

            // Bind the event listeners to the documents, the annotation fields, or both.
            if (scope === 'all')
                elementsToBind = [$(document), ATH.annotationFieldsJQ];
            else if (scope === 'field')
                elementsToBind = [ATH.annotationFieldsJQ];

            // Add the event listener.
            for (j = 0; j < elementsToBind.length; j++) {
                elementsToBind[j].bind(keyEvent, key, func);
            }
        }

        // Show/hide certain key instructions depending on whether Mac is the OS.
        if (ATH.mac) {
            $('span.key_mac').show();
            $('span.key_non_mac').hide();
        }
        else {
            $('span.key_non_mac').show();
            $('span.key_mac').hide();
        }
    },

    /*
     * Based on the current zoom level and focus of the zoom, position and
     * set up the image and on-image listener elements.
     */
    setupImageArea: function() {
        ATH.imageDisplayWidth = ATH.IMAGE_FULL_WIDTH * ATH.zoomFactor;
        ATH.imageDisplayHeight = ATH.IMAGE_FULL_HEIGHT * ATH.zoomFactor;

        // Round off imprecision, so that if the display width is supposed to be
        // equal to the image area width, then they will actually be equal.
        ATH.imageDisplayWidth = parseFloat(ATH.imageDisplayWidth.toFixed(3));
        ATH.imageDisplayHeight = parseFloat(ATH.imageDisplayHeight.toFixed(3));

        // Position the image within the image area.
        // Negative offsets means the top-left corner is offscreen.
        // Positive offsets means there's extra space around the image
        // (should prevent this unless the image display is smaller than the image area).

        if (ATH.imageDisplayWidth <= ATH.IMAGE_AREA_WIDTH)
            ATH.imageLeftOffset = (ATH.IMAGE_AREA_WIDTH - ATH.imageDisplayWidth) / 2;
        else {
            var centerOfZoomInDisplayX = ATH.centerOfZoomX * ATH.zoomFactor;
            var leftEdgeInDisplayX = centerOfZoomInDisplayX - (ATH.IMAGE_AREA_WIDTH / 2);
            var rightEdgeInDisplayX = centerOfZoomInDisplayX + (ATH.IMAGE_AREA_WIDTH / 2);
            
            if (leftEdgeInDisplayX < 0)
                ATH.imageLeftOffset = 0;
            else if (rightEdgeInDisplayX > ATH.imageDisplayWidth)
                ATH.imageLeftOffset = -(ATH.imageDisplayWidth - ATH.IMAGE_AREA_WIDTH);
            else
                ATH.imageLeftOffset = -leftEdgeInDisplayX;
        }

        if (ATH.imageDisplayHeight <= ATH.IMAGE_AREA_HEIGHT)
            ATH.imageTopOffset = (ATH.IMAGE_AREA_HEIGHT - ATH.imageDisplayHeight) / 2;
        else {
            var centerOfZoomInDisplayY = ATH.centerOfZoomY * ATH.zoomFactor;
            var topEdgeInDisplayY = centerOfZoomInDisplayY - (ATH.IMAGE_AREA_HEIGHT / 2);
            var bottomEdgeInDisplayY = centerOfZoomInDisplayY + (ATH.IMAGE_AREA_HEIGHT / 2);

            if (topEdgeInDisplayY < 0)
                ATH.imageTopOffset = 0;
            else if (bottomEdgeInDisplayY > ATH.imageDisplayHeight)
                ATH.imageTopOffset = -(ATH.imageDisplayHeight - ATH.IMAGE_AREA_HEIGHT);
            else
                ATH.imageTopOffset = -topEdgeInDisplayY;
        }

        // Round off imprecision, so that we don't have any extremely small offsets
        // that get expressed in scientific notation (that confuses jQuery's number parsing).
        ATH.imageLeftOffset = parseFloat(ATH.imageLeftOffset.toFixed(3));
        ATH.imageTopOffset = parseFloat(ATH.imageTopOffset.toFixed(3));

        // Set styling properties for the image canvas.
        $(ATI.imageCanvas).css({
            "height": ATH.imageDisplayHeight,
            "left": ATH.imageLeftOffset,
            "top": ATH.imageTopOffset,
            "z-index": 0
        });

        // Set styling properties for the listener element:
        // An invisible element that sits on top of the image
        // and listens for mouse events.
        // Since it has to be on top to listen for mouse events,
        // the z-index should be above every other element's z-index.
        $(ATH.listenerElmt).css({
            "width": ATH.imageDisplayWidth,
            "height": ATH.imageDisplayHeight,
            "left": ATH.imageLeftOffset,
            "top": ATH.imageTopOffset,
            "z-index": 100
        });
    },

    /*
     * Clear the canvas and reset the context.
     */
    resetCanvas: function() {
        // Get the original (untranslated) context back.
        ATH.context.restore();
        // And save the context again for the next time we have to translate.
        ATH.context.save();

        // Clear the entire canvas.
        ATH.context.clearRect(0, 0, ATH.pointsCanvas.width, ATH.pointsCanvas.height);

        // Translate the canvas context to compensate for the gutter.
        // This'll allow us to pretend that canvas coordinates = image area coordinates.
        ATH.context.translate(ATH.CANVAS_GUTTER, ATH.CANVAS_GUTTER);
    },
    
    /* Look at a label field, and based on the label, mark the point
     * as (human) annotated, robot annotated, unannotated, or errored.
     *
     * Return true if something changed (label code or robot status).
     * Return false otherwise.
     */
    updatePointState: function(pointNum, robotStatusAction) {
        var field = ATH.annotationFields[pointNum];
        var row = ATH.annotationFieldRows[pointNum];
        var robotField = ATH.annotationRobotFields[pointNum];
        var labelCode = field.value;

        // Has the label text changed?
        var oldState = ATH.pointContentStates[pointNum];
        var labelChanged = (oldState['label'] !== labelCode);

        /*
         * Update style elements and robot statuses accordingly
         */

        if (labelCode === '') {
            // Empty string; if the label field was non-empty before, fill the field back in.
            // (Or if it was empty before, then leave it empty.)
            if (oldState.label !== undefined && oldState.label !== '')
                field.value = oldState.label;
            return false;
        }
        else if (ATH.labelCodes.indexOf(labelCode) === -1) {
            // Error: label is not in the labelset
            $(field).attr('title', 'Label not in labelset');
            $(row).addClass('error');
            $(row).removeClass('annotated');
            ATH.unrobot(pointNum);
        }
        else {
            // No error

            if (robotField.value === 'true') {
                if (robotStatusAction === 'initialize') {
                    // Initializing the page, need to add robot styles as appropriate.
                    $(row).addClass('robot');
                }
                else if (robotStatusAction === 'unrobotOnlyIfChanged') {
                    // We're told to only unrobot the annotation if the label changed.
                    if (labelChanged)
                        ATH.unrobot(pointNum);
                }
                else {
                    // Any other update results in this annotation being un-roboted.
                    ATH.unrobot(pointNum);
                }
            }

            // Set as (human) annotated or not
            if (ATH.isRobot(pointNum)) {
                // Robot annotated
                $(row).removeClass('annotated');
            }
            else {
                $(row).addClass('annotated');
            }

            // Remove error styling, if any
            $(row).removeClass('error');

            // Field's mouseover text = label name
            $(field).attr('title', ATH.labelCodesToNames[labelCode]);
        }

        var robotStatusChanged = (oldState['robot'] !== robotField.value);
        var contentChanged = ((labelChanged || robotStatusChanged) && (robotStatusAction !== 'initialize'));

        // Done assessing change of state, so set the new state.
        ATH.pointContentStates[pointNum] = {'label': labelCode, 'robot': robotField.value};
        return contentChanged;
    },

    onPointUpdate: function(annoField, robotStatusAction) {
        var pointNum = ATH.getPointNumOfAnnoField(annoField);
        var contentChanged = ATH.updatePointState(pointNum, robotStatusAction);
        
        ATH.updatePointGraphic(pointNum);
        
        if (contentChanged)
            ATH.updateSaveButton();
    },

    onLabelFieldTyping: function(field) {
        ATH.onPointUpdate(field);
    },

    updateSaveButton: function() {
        // No errors in annotation form
        if ($(ATH.annotationList).find('tr.error').length === 0) {
            // Enable save button
            $(ATH.saveButton).removeAttr('disabled');
            ATH.setSaveButtonText("Save progress");
        }
        // Errors
        else {
            // Disable save button
            $(ATH.saveButton).attr('disabled', 'disabled');
            ATH.setSaveButtonText("Error");
        }
    },

    setAllDoneIndicator: function(allDone) {
        if (allDone) {
            $('#allDone').append('<span>').text("ALL DONE");
        }
        else {
            $('#allDone').empty();
        }
    },

    /* Wrapper for event handler functions.
     * Call e.preventDefault() and then call the event handler function.
     * TODO: Once there's a use for this, actually make sure this function works. */
    preventDefaultWrapper: function(fn) {
        return function(e) {
            e.preventDefault();
            fn.call(this, e);
        };
    },

    zoomIn: function(e) {
        ATH.zoom('in', e);
    },
    zoomOut: function(e) {
        ATH.zoom('out', e);
    },
    zoomFit: function(e) {
        ATH.zoom('fit', e);
    },
    zoom: function(zoomType, e) {
        var zoomLevelChange;

        if (zoomType === 'in') {
            if (ATH.zoomLevel === ATH.HIGHEST_ZOOM_LEVEL)
                return;

            zoomLevelChange = 1;
        }
        else if (zoomType === 'out') {
            // 0 is the lowest zoom level.
            if (ATH.zoomLevel === 0)
                return;

            zoomLevelChange = -1;
        }
        else if (zoomType === 'fit') {
            // Zoom all the way out, i.e. get the zoom level to 0.
            if (ATH.zoomLevel === 0)
                return;

            zoomLevelChange = -ATH.zoomLevel;
        }

        // (1) Zoom on click: zoom into the part that was clicked.
        // (Make sure to use the old zoom factor for calculating the click position)
        // (2) Zoom with hotkey: don't change the center of zoom, just the zoom level.
        if (e !== undefined && e.type === 'mouseup') {
            var imagePos = ATH.getImagePosition(e);
            ATH.centerOfZoomX = imagePos[0];
            ATH.centerOfZoomY = imagePos[1];
        }

        ATH.zoomLevel += zoomLevelChange;
        ATH.zoomFactor = ATH.ZOOM_FACTORS[ATH.zoomLevel];

        // Adjust the image and point coordinates.
        ATH.setupImageArea();
        ATH.getCanvasPoints();

        // Redraw all points.
        ATH.redrawAllPoints();
    },

    /* Event listener callback: 'this' is an annotation field */
    confirmFieldAndFocusNext: function() {
        // Unrobot/update the field
        ATH.onPointUpdate(this);

        // Switch focus to next point's field.
        // Call ATH.focusNextField() such that the current field becomes the object 'this'
        ATH.focusNextField.call(this);
    },

    select: function(pointNum) {
        $(ATH.annotationFieldRows[pointNum]).addClass('selected');
        ATH.updatePointGraphic(pointNum);
    },

    unselect: function(pointNum) {
        $(ATH.annotationFieldRows[pointNum]).removeClass('selected');
        ATH.updatePointGraphic(pointNum);
    },

    toggle: function(pointNum) {
        if ($(ATH.annotationFieldRows[pointNum]).hasClass('selected'))
            ATH.unselect(pointNum);
        else
            ATH.select(pointNum);
    },

    isRobot: function(pointNum) {
        var robotField = ATH.annotationRobotFields[pointNum];
        return robotField.value === 'true';
    },

    unrobot: function(pointNum) {
        var robotField = ATH.annotationRobotFields[pointNum];
        robotField.value = 'false';

        var row = ATH.annotationFieldRows[pointNum];
        $(row).removeClass('robot');
    },

    /* Optimization of unselect for multiple points.
     */
    unselectMultiple: function(pointList) {
        var pointNum, i;

        if (ATH.pointViewMode === ATH.POINTMODE_SELECTED) {

            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                $(ATH.annotationFieldRows[pointNum]).removeClass('selected');
            }
            ATH.redrawAllPoints();
        }
        else {
            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                ATH.unselect(pointNum);
            }
        }
    },

    unselectAll: function() {
        var selectedPointList = [];
        ATH.getSelectedFieldsJQ().each( function() {
            var pointNum = ATH.getPointNumOfAnnoField(this);
            selectedPointList.push(pointNum);
        });
        ATH.unselectMultiple(selectedPointList);
    },

    // Label button is clicked
    labelSelected: function(labelButtonCode) {
        var selectedFieldsJQ = ATH.getSelectedFieldsJQ();

        // Iterate over selected points' fields.
        selectedFieldsJQ.each( function() {
            // Set the point's label.
            this.value = labelButtonCode;

            // Update the point's annotation status (including unroboting as necessary).
            ATH.onPointUpdate(this);
        });

        // If just 1 field is selected, focus the next field automatically
        if (selectedFieldsJQ.length === 1) {
            // Call ATH.focusNextField() such that the selected field becomes the object 'this'
            ATH.focusNextField.call(selectedFieldsJQ[0]);
        }
    },

    /* Event listener callback: 'this' is an annotation field */
    labelWithCurrentLabel: function() {
        if (ATH.currentLabelButton !== null) {
            this.value = $(ATH.currentLabelButton).text();
            ATH.onPointUpdate(this, 'unrobotOnlyIfChanged');
        }
    },

    setCurrentLabelButton: function(button) {
        $('#labelButtons button').removeClass('current');
        $(button).addClass('current');

        ATH.currentLabelButton = button;
    },

    /* Event listener callback: 'this' is an annotation field */
    beginKeyboardLabelling: function() {
        // If this field already has a valid label code, then the
        // current label button becomes the button with that label code.
        if (ATH.labelCodes.indexOf(this.value) !== -1) {
            ATH.setCurrentLabelButton($("#labelButtons button:exactlycontains('" + this.value + "')"));
        }
        // Otherwise, label the field with the current label.
        else
            ATH.labelWithCurrentLabel.call(this);
    },

    buttonIndexValid: function(gridX, gridY) {
        var buttonIndex = gridY*ATH.BUTTONS_PER_ROW + gridX;
        return (buttonIndex >= 0 && buttonIndex < ATH.labelCodes.length);
    },

    /* Event listener callback: 'this' is an annotation field */
    moveCurrentLabel: function(dx, dy) {
        if (ATH.currentLabelButton === null)
            return;

        // Start with current label button
        var gridX = parseInt($(ATH.currentLabelButton).attr('gridx'));
        var gridY = parseInt($(ATH.currentLabelButton).attr('gridy'));

        // Move one step, check if valid grid position; repeat as needed
        do {
            gridX += dx;
            gridY += dy;

            // May need to wrap around to the other side of the grid
            if (gridX < 0)
                gridX = ATH.BUTTON_GRID_MAX_X;
            if (gridX > ATH.BUTTON_GRID_MAX_X)
                gridX = 0;
            if (gridY < 0)
                gridY = ATH.BUTTON_GRID_MAX_Y;
            if (gridY > ATH.BUTTON_GRID_MAX_Y)
                gridY = 0;
            
            // Need to check for a valid grid position, if the grid isn't a perfect rectangle
        } while (!ATH.buttonIndexValid(gridX, gridY));

        // Current label button is now the button with the x and y we calculated.
        ATH.setCurrentLabelButton($("#labelButtons button[gridx='" + gridX + "'][gridy='" + gridY + "']")[0]);

        // And make sure the current annotation field's
        // label gets changed to the current button's label.
        ATH.labelWithCurrentLabel.call(this);
    },

    moveCurrentLabelLeft: function() {
        ATH.moveCurrentLabel.call(this, -1, 0);
    },
    moveCurrentLabelRight: function() {
        ATH.moveCurrentLabel.call(this, 1, 0);
    },
    moveCurrentLabelUp: function() {
        ATH.moveCurrentLabel.call(this, 0, -1);
    },
    moveCurrentLabelDown: function() {
        ATH.moveCurrentLabel.call(this, 0, 1);
    },

    /* Event listener callback: 'this' is an annotation field */
    focusPrevField: function() {
        var pointNum = ATH.getPointNumOfAnnoField(this);

        // If first point numerically...
        if (pointNum === 1) {
            // Just un-focus from this point's field
            $(this).blur();
        }
        // If not first point...
        else {
            // Focus the previous point's field
            $(ATH.annotationFields[pointNum-1]).focus();
        }
    },

    /* Event listener callback: 'this' is an annotation field */
    focusNextField: function() {
        var pointNum = ATH.getPointNumOfAnnoField(this);
        var lastPoint = ATH.numOfPoints;

        // If last point (numerically)...
        if (pointNum === lastPoint) {
            // Just un-focus from this point's field
            $(this).blur();
        }
        // If not last point...
        else {
            // Focus the next point's field
            $(ATH.annotationFields[pointNum+1]).focus();
        }
    },

    /* Get the mouse position in the canvas element:
	(mouse's position in the HTML document) minus
	(canvas element's position in the HTML document). */
	getImageElmtPosition: function(e) {
	    var x;
		var y;

		/* The method for getting the mouse position in the HTML document
	    varies depending on the browser: can be based on pageX/Y or clientX/Y. */
		if (e.pageX !== undefined && e.pageY !== undefined) {
			x = e.pageX;
			y = e.pageY;
		}
		else {
			x = e.clientX + document.body.scrollLeft +
					document.documentElement.scrollLeft;
			y = e.clientY + document.body.scrollTop +
					document.documentElement.scrollTop;
		}

        // Get the x,y relative to the upper-left corner of the image
        var elmt = ATI.imageCanvas;
        while (elmt !== null) {
            x -= elmt.offsetLeft;
            y -= elmt.offsetTop;
            elmt = elmt.offsetParent;
        }

	    return [x,y];
	},

    getImagePosition: function(e) {
        var imageElmtPosition = ATH.getImageElmtPosition(e);
        var imageElmtX = imageElmtPosition[0];
        var imageElmtY = imageElmtPosition[1];

        var x = imageElmtX / ATH.zoomFactor;
        var y = imageElmtY / ATH.zoomFactor;

        return [x,y];
    },

    getNearestPoint: function(e) {
        // Mouse's position in the canvas element
        var imagePosition = ATH.getImagePosition(e);
        var x = imagePosition[0];
        var y = imagePosition[1];

        var minDistance = Infinity;
        var closestPoint = null;

        for (var i = 0; i < ATH.imagePoints.length; i++) {
            var currPoint = ATH.imagePoints[i];

            // Don't count points that are offscreen.
            if (ATH.pointIsOffscreen(currPoint.point_number))
                continue;

            var xDiff = x - currPoint.column;
            var yDiff = y - currPoint.row;
            var distance = Math.sqrt((xDiff*xDiff) + (yDiff*yDiff));

            if (distance < minDistance) {
                minDistance = distance;
                closestPoint = currPoint.point_number;
            }
        }

        return closestPoint;
    },

    /*
    Raw image coordinates -> Canvas coordinates:
    (1) Scale the raw image coordinates by the image zoom factor.
    (2) Account for image position offset.
    (3) Don't account for gutter offset (translating the canvas context already takes care of this).
     */
    getCanvasPoints: function() {
        for (var i = 0; i < ATH.imagePoints.length; i++) {

            // ATH.imagePoints[num].row: which image pixel it is, from 1 to height
            // ATH.canvasPoints[num].row: offset on the canvas, starting from 0 if the point is visible.
            // Subtract 0.5 so the canvasPoint is in the middle of the point's pixel instead of the bottom-right edge.  Typically won't make much of a difference, but still.
            ATH.canvasPoints[ATH.imagePoints[i].point_number] = {
                num: ATH.imagePoints[i].point_number,
                row: ((ATH.imagePoints[i].row - 0.5) * ATH.zoomFactor) + ATH.imageTopOffset,
                col: ((ATH.imagePoints[i].column - 0.5) * ATH.zoomFactor) + ATH.imageLeftOffset
            };
        }
    },

    drawPointHelper: function(pointNum, color, outlineColor) {
        var canvasPoint = ATH.canvasPoints[pointNum];

        ATH.drawPointMarker(canvasPoint.col, canvasPoint.row,
                             color);
        ATH.drawPointNumber(canvasPoint.num.toString(), canvasPoint.col, canvasPoint.row,
                             color, outlineColor);
    },

    drawPointUnannotated: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATS.settings.unannotatedColor, ATH.OUTLINE_COLOR);
    },
    drawPointRobotAnnotated: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATS.settings.robotAnnotatedColor, ATH.OUTLINE_COLOR);
    },
    drawPointHumanAnnotated: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATS.settings.humanAnnotatedColor, ATH.OUTLINE_COLOR);
    },
    drawPointSelected: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATS.settings.selectedColor, ATH.OUTLINE_COLOR);
    },

    /* Update a point's graphics on the canvas in the correct color.
     * Don't redraw a point unless necessary.
     */
    updatePointGraphic: function(pointNum) {
        // If the point is offscreen, then don't draw
        if (ATH.pointIsOffscreen(pointNum))
            return;

        // Get the current (graphical) state of this point
        var row = ATH.annotationFieldRows[pointNum];
        var newState;

        if ($(row).hasClass('selected'))
            newState = ATH.STATE_SELECTED;
        else if ($(row).hasClass('annotated'))
            newState = ATH.STATE_ANNOTATED;
        else if ($(row).hasClass('robot'))
            newState = ATH.STATE_ROBOT;
        else
            newState = ATH.STATE_UNANNOTATED;

        // Account for point view modes
        if (ATH.pointViewMode === ATH.POINTMODE_SELECTED && newState !== ATH.STATE_SELECTED)
            newState = ATH.STATE_NOTSHOWN;
        if (ATH.pointViewMode === ATH.POINTMODE_NONE)
            newState = ATH.STATE_NOTSHOWN;

        // Redraw if the (graphical) state has changed
        var oldState = ATH.pointGraphicStates[pointNum];

        if (oldState !== newState) {
            ATH.pointGraphicStates[pointNum] = newState;

            if (newState === ATH.STATE_SELECTED)
                ATH.drawPointSelected(pointNum);
            else if (newState === ATH.STATE_ANNOTATED)
                ATH.drawPointHumanAnnotated(pointNum);
            else if (newState === ATH.STATE_ROBOT)
                ATH.drawPointRobotAnnotated(pointNum);
            else if (newState === ATH.STATE_UNANNOTATED)
                ATH.drawPointUnannotated(pointNum);
            else if (newState === ATH.STATE_NOTSHOWN)
                // "Erase" this point.
                // To do this, redraw the canvas with this point marked as not shown.
                // For performance reasons, you'll want to avoid reaching this code whenever
                // possible/reasonable.  One tip: remember to mark all points as NOTSHOWN
                // whenever you clear the canvas of all points.
                ATH.redrawAllPoints();
        }
    },

    /*
     * Return true if the given point's coordinates
     * are not within the image area
     */
    pointIsOffscreen: function(pointNum) {
        return (ATH.canvasPoints[pointNum].row < 0
                || ATH.canvasPoints[pointNum].row > ATH.IMAGE_AREA_HEIGHT
                || ATH.canvasPoints[pointNum].col < 0
                || ATH.canvasPoints[pointNum].col > ATH.IMAGE_AREA_WIDTH
                )
    },

    redrawAllPoints: function() {
        // Reset the canvas and re-translate the context
        // to compensate for the gutters.
        ATH.resetCanvas();

        // Clear the pointGraphicStates.
        for (var n = 1; n <= ATH.numOfPoints; n++) {
            ATH.pointGraphicStates[n] = ATH.STATE_NOTSHOWN;
        }

        // Draw all points.
        ATH.annotationFieldsJQ.each( function() {
            var pointNum = ATH.getPointNumOfAnnoField(this);
            ATH.updatePointGraphic(pointNum);
        });
    },

    changePointMode: function(pointMode) {
        // Outline this point mode button in red (and de-outline the other buttons).
        $(".pointModeButton").removeClass("selected");
        
        if (pointMode == ATH.POINTMODE_ALL)
            $("#pointModeButtonAll").addClass("selected");
        else if (pointMode == ATH.POINTMODE_SELECTED)
            $("#pointModeButtonSelected").addClass("selected");
        else if (pointMode == ATH.POINTMODE_NONE)
            $("#pointModeButtonNone").addClass("selected");

        // Set the new point display mode.
        ATH.pointViewMode = pointMode;

        // Redraw all points.
        ATH.redrawAllPoints();
    },

    saveAnnotations: function() {
        $(ATH.saveButton).attr('disabled', 'disabled');
        $(ATH.saveButton).text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_annotations(
            ATH.ajaxSaveButtonCallback,    // JS callback that the ajax.py method returns to.
            {'annotationForm': $("#annotationForm").serializeArray()}    // Args to the ajax.py method.
        );
    },

    // AJAX callback: cannot use "this" to refer to ATH
    ajaxSaveButtonCallback: function(returnDict) {
        
        if (returnDict.hasOwnProperty('error')) {
            var errorMsg = returnDict['error'];
            ATH.setSaveButtonText("Error");

            // TODO: Handle error cases more elegantly?  Alerts are lame.
            // Though, these errors aren't really supposed to happen unless the annotation tool behavior is flawed.
            alert("Sorry, an error occurred when trying to save your annotations:\n{0}".format(errorMsg));
        }
        else {
            ATH.setSaveButtonText("Saved");

            // Add or remove ALL DONE indicator
            ATH.setAllDoneIndicator(returnDict.hasOwnProperty('all_done'));
        }
    },

    setSaveButtonText: function(buttonText) {
        $(ATH.saveButton).text(buttonText);
    },

    getPointNumOfAnnoField: function(annoField) {
        // Assuming the annotation field's name attribute is "label_<pointnumber>".
        // "label_" is 6 characters.
        return parseInt(annoField.name.substring(6));
    },

    getSelectedFieldsJQ: function() {
        return $(ATH.annotationList).find('tr.selected').find('input');
    },

    /*
    Draw an annotation point marker (crosshair, circle, or whatever)
    which is centered at x,y.
     */
    drawPointMarker: function(x, y, color) {
        var markerType = ATS.settings.pointMarker;
        var radius;

        if (ATS.settings.pointMarkerIsScaled === true)
            // Zoomed all the way out: radius = pointMarkerSize.
            // Zoomed in 1.5x: radius = pointMarkerSize * 1.5. etc.
            // radius must be an integer.
            radius = Math.round(ATS.settings.pointMarkerSize * Math.pow(ATH.ZOOM_INCREMENT, ATH.zoomLevel));
        else
            radius = ATS.settings.pointMarkerSize;

        // Adjust x and y by 0.5 so that straight lines are centered
		// at the halfway point of a pixel, not on a pixel boundary.
		// This ensures that 1-pixel-wide lines are really 1 pixel wide,
		// instead of 2 pixels wide.
        // NOTE: This only applies to odd-width lines.
		x = x+0.5;
		y = y+0.5;

        ATH.context.strokeStyle = color;
        ATH.context.lineWidth = 3;

		ATH.context.beginPath();

        if (markerType === 'crosshair' || markerType === 'crosshair and circle') {
            ATH.context.moveTo(x, y + radius);
            ATH.context.lineTo(x, y - radius);

            ATH.context.moveTo(x - radius, y);
            ATH.context.lineTo(x + radius, y);
        }
        if (markerType === 'circle' || markerType === 'crosshair and circle') {
            ATH.context.arc(x, y, radius, 0, 2.0*Math.PI);
        }
        if (markerType === 'box') {
            ATH.context.moveTo(x + radius, y + radius);
            ATH.context.lineTo(x - radius, y + radius);
            ATH.context.lineTo(x - radius, y - radius);
            ATH.context.lineTo(x + radius, y - radius);
            ATH.context.lineTo(x + radius, y + radius);
        }

        ATH.context.stroke();
	},

    /*
    Draw the number of an annotation point
    which is centered at x,y.
     */
	drawPointNumber: function(num, x, y, color, outlineColor) {
        ATH.context.textBaseline = "bottom";
		ATH.context.textAlign = "left";
		ATH.context.fillStyle = color;
        ATH.context.strokeStyle = outlineColor;
        ATH.context.lineWidth = 1;

        var numberSize = ATS.settings.pointNumberSize;
        if (ATS.settings.pointNumberIsScaled)
            numberSize = Math.round(numberSize * Math.pow(ATH.ZOOM_INCREMENT, ATH.zoomLevel));

	    ATH.context.font = ATH.NUMBER_FONT_FORMAT_STRING.format(numberSize.toString());

		// Offset the number's position a bit so it doesn't overlap with the annotation point.
		// (Unlike the line drawing, 0.5 pixel adjustment doesn't seem to make a difference)
        // TODO: Consider doing offset calculations once each time the settings/zoom level change, not once for each point
        var offset = ATS.settings.pointMarkerSize;

        if (ATS.settings.pointMarker !== 'box')
            // When the pointMarker is a box, line up the number with the corner of the box.
            // When the pointMarker is not a box, line up the number with the corner of a circle instead.
            offset = offset * 0.7;
        if (ATS.settings.pointMarkerIsScaled === true)
            offset = offset * Math.pow(ATH.ZOOM_INCREMENT, ATH.zoomLevel);
        // Compensate for the fact that the number ends up being drawn
        // a few pixels away from the specified baseline point.
        offset = offset - 2;
        offset = Math.round(offset);

        x = x + offset;
        y = y - offset;

        ATH.context.fillText(num, x, y);    // Color in the number
		ATH.context.strokeText(num, x, y);    // Outline the number (make it easier to see)
	},

    
    /*
    Hiding/showing the annotation tool instructions.
    */
    hideInstructions: function() {
        $("#id_instructions_wrapper").hide();
        $("#id_button_show_instructions").show();
    },

    showInstructions: function() {
        $("#id_instructions_wrapper").show();
        $("#id_button_show_instructions").hide();
    }
};

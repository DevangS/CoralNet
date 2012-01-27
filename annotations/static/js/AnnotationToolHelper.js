var ATH = {

    // Compatibility
    // If the appVersion contains the substring "Mac", then it's probably a mac...
    mac: (navigator.appVersion.indexOf("Mac") !== -1),

    // HTML elements
    annotationArea: null,
    annotationList: null,
    annotationFieldRows: [],
    annotationFields: [],
    annotationRobotFields: [],
    annotationFieldsJQ: null,
    coralImage: null,
    pointsCanvas: null,
    listenerElmt: null,
    saveButton: null,

    // Annotation related
    labelCodes: null,
    currentLabelButton: null,
    BUTTON_GRID_MAX_X: null,
    BUTTON_GRID_MAX_Y: null,

    // Canvas related
	context: null,
    canvasPoints: [], imagePoints: null,
    numOfPoints: null,
	POINT_RADIUS: 16,
    NUMBER_FONT: "bold 24px sans-serif",

    // Border where the canvas is drawn, but the coral image is not.
    // This is used to fully show the points that are located near the edge of the image.
	CANVAS_GUTTER: 25,
    CANVAS_GUTTER_COLOR: "#BBBBBB",

    // Related to possible states of each annotation point
    pointContentStates: [],
    pointGraphicStates: [],
    STATE_UNANNOTATED: 0,
    STATE_ANNOTATED: 1,
    STATE_SELECTED: 2,
    STATE_NOTSHOWN: 3,
    UNANNOTATED_COLOR: "#FFFF00",
	UNANNOTATED_OUTLINE_COLOR: "#000000",
	ANNOTATED_COLOR: "#8888FF",
    ANNOTATED_OUTLINE_COLOR: "#000000",
	SELECTED_COLOR: "#00FF00",
    SELECTED_OUTLINE_COLOR: "#000000",
    
    // Point viewing mode
    pointViewMode: null,
    POINTMODE_ALL: 0,
    POINTMODE_SELECTED: 1,
    POINTMODE_NONE: 2,

    // Entire annotation tool (including buttons, text fields, etc.)
    ANNOTATION_TOOL_WIDTH: 980,
    ANNOTATION_TOOL_HEIGHT: 800, // TODO: Make this dynamic according to how many label buttons there are
    // The canvas area, where drawing is allowed
    ANNOTATION_AREA_WIDTH: 850,
    ANNOTATION_AREA_HEIGHT: 650,
    // The area that the image is permitted to fill
    IMAGE_AREA_WIDTH: null,
    IMAGE_AREA_HEIGHT: null,
    // The original image dimensions
	IMAGE_FULL_WIDTH: null,
    IMAGE_FULL_HEIGHT: null,
    // Display parameters of the image.
    // > 1 zoomFactor means larger than original image
    // zoom levels start at 0 (fully zoomed out) and go up like 1,2,3,etc.
    imageDisplayWidth: null,
    imageDisplayHeight: null,
    zoomFactor: null,
    zoomLevel: null,
    ZOOM_FACTORS: {},
    ZOOM_INCREMENT: 1.5,
    HIGHEST_ZOOM_LEVEL: 4,
    // Current display position of the image.
    // centerOfZoom is in terms of raw-image coordinates.
    // < 0 offset means top left corner is not visible.
    centerOfZoomX: null,
    centerOfZoomY: null,
    imageLeftOffset: null,
    imageTopOffset: null,


    init: function(fullHeight, fullWidth,
                   imagePoints, labels) {
        var i;    // Loop variable...

        ATH.IMAGE_AREA_WIDTH = ATH.ANNOTATION_AREA_WIDTH - (ATH.CANVAS_GUTTER * 2),
        ATH.IMAGE_AREA_HEIGHT = ATH.ANNOTATION_AREA_HEIGHT - (ATH.CANVAS_GUTTER * 2),

        ATH.IMAGE_FULL_WIDTH = fullWidth;
        ATH.IMAGE_FULL_HEIGHT = fullHeight;

        /*
         * Initialize styling, sizing, and positioning for various elements
         */

        ATH.annotationArea = $("#annotationArea")[0];
        ATH.annotationList = $("#annotationList")[0];
        ATH.coralImage = $("#coralImage")[0];
        ATH.pointsCanvas = $("#pointsCanvas")[0];
        ATH.listenerElmt = $("#listenerElmt")[0];
        ATH.saveButton = $("#saveButton")[0];

        $('#mainColumn').css({
            "width": ATH.ANNOTATION_AREA_WIDTH + "px",

            /* Spilling beyond this height is fine, but we define the height
               so this element takes up space, thus forcing the rightSidebar to
               stay on the right. */
            "height": ATH.ANNOTATION_TOOL_HEIGHT + "px"
        });
        $('#rightSidebar').css({
            "width": (ATH.ANNOTATION_TOOL_WIDTH - ATH.ANNOTATION_AREA_WIDTH) + "px",
            "height": ATH.ANNOTATION_TOOL_HEIGHT + "px"
        });
        $('#dummyColumn').css({
            "height": ATH.ANNOTATION_TOOL_HEIGHT + "px"
        });

        var annotationListMaxHeight =
            ATH.ANNOTATION_AREA_HEIGHT
            - 2*(24+(2*2)+2)    // toolButtonArea: 2 rows of buttons - 24px buttons, each with 2px top and bottom borders, and another 2px of space below for some reason
            - (5*2);            // toolButtonArea: 5px margins around the area
        $(ATH.annotationList).css({
            "max-height": annotationListMaxHeight + "px"
        });

        $(ATH.annotationArea).css({
            "width": ATH.ANNOTATION_AREA_WIDTH + "px",
            "height": ATH.ANNOTATION_AREA_HEIGHT + "px",
            "background-color": ATH.CANVAS_GUTTER_COLOR
        });

        $('#imageArea').css({
            "width": ATH.IMAGE_AREA_WIDTH + "px",
            "height": ATH.IMAGE_AREA_HEIGHT + "px",
            "left": ATH.CANVAS_GUTTER + "px",
            "top": ATH.CANVAS_GUTTER + "px"
        });

        // Styling label buttons
        var uniqueGroups = [];
        var groupStyles = {};
        var nextStyleNumber = 1;
        var labelButtonJQ;

        for (i = 0; i < labels.length; i++) {
            // Assign a style class for each functional group represented by the buttons.
            if (uniqueGroups.indexOf(labels[i].group) === -1) {
                uniqueGroups.push(labels[i].group);
                groupStyles[labels[i].group] = 'group'+nextStyleNumber;
                nextStyleNumber++;
            }
        }
        for (i = 0; i < labels.length; i++) {
            // Get the label button and assign the group style to it.
            labelButtonJQ = $("#labelButtons button:exactlycontains('" + labels[i].code + "')");
            labelButtonJQ.addClass(groupStyles[labels[i].group]);
        }

        // Assigning 'grid positions' to label buttons
        // TODO: Derive this magic number from the label-button space available, or vice versa.
        ATH.BUTTONS_PER_ROW = 10;
        ATH.BUTTON_GRID_MAX_Y = Math.floor(labels.length / ATH.BUTTONS_PER_ROW);
        ATH.BUTTON_GRID_MAX_X = ATH.BUTTONS_PER_ROW - 1;

        for (i = 0; i < labels.length; i++) {
            // Get the label button and assign the group style to it.
            labelButtonJQ = $("#labelButtons button:exactlycontains('" + labels[i].code + "')");
            // Assign a grid position, e.g. i=0 gets position [0,0], i=13 gets [1,3]
            labelButtonJQ.attr('gridy', Math.floor(i / ATH.BUTTONS_PER_ROW));
            labelButtonJQ.attr('gridx', i % ATH.BUTTONS_PER_ROW);
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

        // Create array of available label codes
        ATH.labelCodes = [];
        for (i = 0; i < labels.length; i++)
            ATH.labelCodes.push(labels[i].code);

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
        for (i = 0; i < ATH.numOfPoints; i++) {
            ATH.pointGraphicStates[i] = ATH.STATE_NOTSHOWN;
        }
        ATH.annotationFieldsJQ.each( function() {
            var pointNum = ATH.getPointNumOfAnnoField(this);
            ATH.updatePointState(pointNum, true);
            ATH.updatePointGraphic(pointNum);
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

            if (ATH.zoomLevel > 0) {

                // If we're zoomed in at all,
                // shift the center of zoom to the focused point.
                ATH.centerOfZoomX = ATH.imagePoints[pointNum-1].column;
                ATH.centerOfZoomY = ATH.imagePoints[pointNum-1].row;

                // Adjust the image and point coordinates.
                ATH.setupImageArea();
                ATH.getCanvasPoints();

                // Redraw all points.
                ATH.redrawAllPoints();
            }
        });

        // Label field is typed into and changed, and then unfocused.
        // (This does NOT run when a click of a label button changes the label field.)
        ATH.annotationFieldsJQ.change(function() {
            ATH.onLabelFieldChange(this);
        });

        // Number next to a label field is clicked.
        $(".annotationFormLabel").click(function() {
            var pointNum = parseInt($(this).text());
            ATH.toggle(pointNum);
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

        // Keymaps
        var globalKeymap = {
            'ctrl+up': ATH.zoomIn,
            'ctrl+down': ATH.zoomOut
        };
        var annotationFieldKeymap = {
            'return': ATH.confirmFieldAndFocusNext,
            'up': ATH.focusPrevField,
            'down': ATH.focusNextField,
            'shift+left': ATH.moveCurrentLabelLeft,
            'shift+right': ATH.moveCurrentLabelRight,
            'shift+up': ATH.moveCurrentLabelUp,
            'shift+down': ATH.moveCurrentLabelDown
        };
        var outOfFieldKeymap = {
        };

        var key;
        for (key in globalKeymap) {
            // If Mac, replace ctrl with meta (which is Cmd).
            // Remember to apply this to the other keymaps if necessary.
            if (ATH.mac)
                key = key.replace('ctrl','meta');

            $(document).bind('keyup', key, globalKeymap[key]);
            ATH.annotationFieldsJQ.bind('keyup', key, globalKeymap[key]);
        }
        for (key in outOfFieldKeymap) {
            $(document).bind('keyup', key, outOfFieldKeymap[key]);
        }
        for (key in annotationFieldKeymap) {
            ATH.annotationFieldsJQ.bind('keyup', key, annotationFieldKeymap[key]);
        }

        // Special case: keydown
        ATH.annotationFieldsJQ.bind('keydown', 'shift', ATH.prepareForShiftLabeling);
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

        // Set styling properties for the image.
        $(ATH.coralImage).css({
            "height": ATH.imageDisplayHeight,
            "left": ATH.imageLeftOffset,
            "top": ATH.imageTopOffset,
            "z-index": 0
        });

        // Set styling properties for the listener element:
        // An invisible element that goes over the coral image
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
     */
    updatePointState: function(pointNum, initializing) {
        var field = ATH.annotationFields[pointNum];
        var row = ATH.annotationFieldRows[pointNum];
        var robotField = ATH.annotationRobotFields[pointNum];
        var labelCode = field.value;

        /*
         * Update style elements and robot statuses accordingly
         */

        // Error: label is not empty string, and not in the labelset
        if (labelCode !== '' && ATH.labelCodes.indexOf(labelCode) === -1) {
            // Error styling
            $(field).attr('title', 'Label not in labelset');
            $(row).addClass('error');
            $(row).removeClass('annotated');
            $(row).removeClass('robot');
        }
        // No error
        else {
            // Set as robot annotation or not
            if (robotField.value === "true" && initializing) {
                // Initializing the page, need to add robot styles as appropriate.
                $(row).addClass('robot');
            }
            else if (robotField.value === "true") {
                // If we're not initializing the page,
                // then we're updating due to a USER ACTION.
                // Therefore, this robot annotation should be un-roboted.
                ATH.unrobot(pointNum);
            }

            // Set as (human) annotated or not
            if (labelCode === '' || ATH.isRobot(pointNum)) {
                // No label, or robot annotated
                $(row).removeClass('annotated');
            }
            else {
                $(row).addClass('annotated');
            }

            // Remove error styling, if any
            $(row).removeClass('error');
            $(field).removeAttr('title');
        }

        /*
         * See if content has changed (label name and robot status)
         */

        // Possible states:
        // Human annotated (and as what), robot annotated (and as what),
        // empty, errored, selected+any of previous
        
        var contentChanged = false;
        var oldState = ATH.pointContentStates[pointNum];
        var newState = {'label': labelCode, 'robot': robotField.value};

        if (initializing) {
            // Initializing this point at page load time
            ATH.pointContentStates[pointNum] = newState;
        }
        else if (oldState['label'] !== newState['label']
                 || oldState['robot'] !== newState['robot']) {
            // Content has changed
            contentChanged = true;
            ATH.pointContentStates[pointNum] = newState;
        }

        return contentChanged;
    },

    onPointUpdate: function(pointNum) {
        var contentChanged = ATH.updatePointState(pointNum, false);
        
        ATH.updatePointGraphic(pointNum);
        
        if (contentChanged)
            ATH.updateSaveButton();
    },

    onLabelFieldChange: function(field) {
        var pointNum = ATH.getPointNumOfAnnoField(field);
        ATH.onPointUpdate(pointNum);
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
    zoom: function(direction, e) {
        var zoomLevelChange;

        if (direction === 'in') {
            if (ATH.zoomLevel === ATH.HIGHEST_ZOOM_LEVEL)
                return;

            zoomLevelChange = 1;
        }
        else if (direction === 'out') {
            // 0 is the lowest zoom level.
            if (ATH.zoomLevel === 0)
                return;

            zoomLevelChange = -1;
        }

        // (1) Zoom on click: zoom into the part that was clicked.
        // (Make sure to use the old zoom factor for calculating the click position)
        // (2) Zoom with hotkey: don't change the center of zoom, just the zoom level.
        if (e.type === 'mouseup') {
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
        // The function is called with a field element as 'this'
        var pointNum = ATH.getPointNumOfAnnoField(this);

        // Unrobot/update the field
        ATH.onPointUpdate(pointNum);

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

            // Update the point's annotation status (including unroboting).
            var pointNum = ATH.getPointNumOfAnnoField(this);
            ATH.onPointUpdate(pointNum);
        });

        // If just 1 field is selected, focus the next field automatically
        if (selectedFieldsJQ.length === 1) {
            // Call ATH.focusNextField() such that the selected field becomes the object 'this'
            ATH.focusNextField.call(selectedFieldsJQ[0]);
        }
    },

    /* Event listener callback: 'this' is an annotation field */
    labelWithCurrentLabel: function() {
        if (ATH.currentLabelButton !== null)
            this.value = $(ATH.currentLabelButton).text();
    },

    setCurrentLabelButton: function(button) {
        $('#labelButtons button').removeClass('current');
        $(button).addClass('current');

        ATH.currentLabelButton = button;
    },

    /* Event listener callback: 'this' is an annotation field */
    prepareForShiftLabeling: function() {
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

        // Get the x,y relative to the upper-left corner of the coral image
        var elmt = ATH.coralImage;
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

            ATH.canvasPoints[ATH.imagePoints[i].point_number] = {
                num: ATH.imagePoints[i].point_number,
                row: (ATH.imagePoints[i].row * ATH.zoomFactor) + ATH.imageTopOffset,
                col: (ATH.imagePoints[i].column * ATH.zoomFactor) + ATH.imageLeftOffset
            };
        }
    },

    drawPointHelper: function(pointNum, color, outlineColor) {
        var canvasPoint = ATH.canvasPoints[pointNum];

        ATH.drawPointSymbol(canvasPoint.col, canvasPoint.row,
                             color);
        ATH.drawPointNumber(canvasPoint.num.toString(), canvasPoint.col, canvasPoint.row,
                             color, outlineColor);
    },

    drawPointUnannotated: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATH.UNANNOTATED_COLOR, ATH.UNANNOTATED_OUTLINE_COLOR);
    },
    drawPointAnnotated: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATH.ANNOTATED_COLOR, ATH.ANNOTATED_OUTLINE_COLOR);
    },
    drawPointSelected: function(pointNum) {
        ATH.drawPointHelper(pointNum, ATH.SELECTED_COLOR, ATH.SELECTED_OUTLINE_COLOR);
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
                ATH.drawPointAnnotated(pointNum);
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
        for (var i = 0; i < ATH.pointGraphicStates.length; i++) {
            ATH.pointGraphicStates[i] = ATH.STATE_NOTSHOWN;
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
    Draw an annotation point symbol (the crosshair, circle, or whatever)
    which is centered at x,y.
     */
    drawPointSymbol: function(x, y, color) {
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
		//context.arc(x, y, POINT_RADIUS, 0, 2.0*Math.PI);    // A circle

		ATH.context.moveTo(x, y + ATH.POINT_RADIUS);
		ATH.context.lineTo(x, y - ATH.POINT_RADIUS);

		ATH.context.moveTo(x - ATH.POINT_RADIUS, y);
		ATH.context.lineTo(x + ATH.POINT_RADIUS, y);

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
	    ATH.context.font = ATH.NUMBER_FONT;

		// Offset the number's position a bit so it doesn't overlap with the annotation point.
		// (Unlike the line drawing, 0.5 pixel adjustment doesn't seem to make a difference)
        x = x + 3, y = y - 3;

        ATH.context.fillText(num, x, y);    // Color in the number
		ATH.context.strokeText(num, x, y);    // Outline the number (make it easier to see)
	},

	/*
	Toggle the points on/off by bringing them in front of or behind the image.
	TODO: Add a button that does this.
	*/
	togglePoints: function() {
        if (ATH.pointsCanvas.style.visibility === 'hidden')
			ATH.pointsCanvas.style.visibility = 'visible';
		else    // 'visible' or ''
			ATH.pointsCanvas.style.visibility = 'hidden';
	}
};

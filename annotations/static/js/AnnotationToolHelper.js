var AnnotationToolHelper = {

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
                   imagePoints, labelCodes) {
        var t = this;  // Alias for less typing
        var i;    // Loop variable...

        t.IMAGE_AREA_WIDTH = t.ANNOTATION_AREA_WIDTH - (t.CANVAS_GUTTER * 2),
        t.IMAGE_AREA_HEIGHT = t.ANNOTATION_AREA_HEIGHT - (t.CANVAS_GUTTER * 2),

        t.IMAGE_FULL_WIDTH = fullWidth;
        t.IMAGE_FULL_HEIGHT = fullHeight;

        /*
         * Initialize styling and sizing for everything
         */

        t.annotationArea = $("#annotationArea")[0];
        t.annotationList = $("#annotationList")[0];
        t.coralImage = $("#coralImage")[0];
        t.pointsCanvas = $("#pointsCanvas")[0];
        t.listenerElmt = $("#listenerElmt")[0];
        t.saveButton = $("#saveButton")[0];

        $('#mainColumn').css({
            "width": t.ANNOTATION_AREA_WIDTH + "px",

            /* Spilling beyond this height is fine, but we define the height
               so this element takes up space, thus forcing the rightSidebar to
               stay on the right. */
            "height": t.ANNOTATION_TOOL_HEIGHT + "px"
        });
        $('#rightSidebar').css({
            "width": (t.ANNOTATION_TOOL_WIDTH - t.ANNOTATION_AREA_WIDTH) + "px",
            "height": t.ANNOTATION_TOOL_HEIGHT + "px"
        });
        $('#dummyColumn').css({
            "height": t.ANNOTATION_TOOL_HEIGHT + "px"
        });

        var annotationListMaxHeight =
            t.ANNOTATION_AREA_HEIGHT
            - (24 + (2*2) + (5*2) );    // pointModeButtonArea: buttons, borders, and margins
        $(t.annotationList).css({
            "max-height": annotationListMaxHeight + "px"
        });

        $(t.annotationArea).css({
            "width": t.ANNOTATION_AREA_WIDTH + "px",
            "height": t.ANNOTATION_AREA_HEIGHT + "px",
            "background-color": t.CANVAS_GUTTER_COLOR
        });

        $('#imageArea').css({
            "width": t.IMAGE_AREA_WIDTH + "px",
            "height": t.IMAGE_AREA_HEIGHT + "px",
            "left": t.CANVAS_GUTTER + "px",
            "top": t.CANVAS_GUTTER + "px"
        });

        /*
         * Set initial image scaling so the whole image is shown.
         * Also set the allowable zoom factors.
         */

        var widthScaleRatio = t.IMAGE_FULL_WIDTH / t.IMAGE_AREA_WIDTH;
        var heightScaleRatio = t.IMAGE_FULL_HEIGHT / t.IMAGE_AREA_HEIGHT;
        var scaleDownFactor = Math.max(widthScaleRatio, heightScaleRatio);

        // If the scaleDownFactor is < 1, then it's scaled up (meaning the image is really small).
        t.zoomFactor = 1.0 / scaleDownFactor;

        // Allowable zoom factors/levels:
        // Start with the most zoomed out level, 0.  Level 1 is ZOOM_INCREMENT * level 0.
        // Level 2 is ZOOM_INCREMENT * level 1, etc.  Goes up to level HIGHEST_ZOOM_LEVEL.
        t.zoomLevel = 0;
        for (i = 0; i <= t.HIGHEST_ZOOM_LEVEL; i++) {
            t.ZOOM_FACTORS[i] = t.zoomFactor * Math.pow(t.ZOOM_INCREMENT, i);
        }

        // Based on the zoom level, set up the image area.
        // (No need to define centerOfZoom since we're not zooming in to start with.)
        t.setupImageArea();

        // Set the canvas's width and height properties so the canvas contents don't stretch.
        // Note that this is different from CSS width and height properties.
        t.pointsCanvas.width = t.ANNOTATION_AREA_WIDTH;
        t.pointsCanvas.height = t.ANNOTATION_AREA_HEIGHT;
        $(t.pointsCanvas).css({
            "left": 0,
		    "top": 0,
            "z-index": 1
        });

        /*
         * Initialize and draw annotation points,
         * and initialize some other variables and elements
         */

        // Create a canvas context
		t.context = t.pointsCanvas.getContext("2d");

        // Save this fresh context so we can restore it later as needed.
        t.context.save();

        // Translate the canvas context to compensate for the gutter and the image offset.
        t.resetCanvas();

        // Initialize point coordinates
        t.imagePoints = imagePoints;
        t.numOfPoints = imagePoints.length;
        t.getCanvasPoints();

        // Possible label codes
        t.labelCodes = labelCodes;

        t.annotationFieldsJQ = $(t.annotationList).find('input');
        var annotationFieldRowsJQ = $(t.annotationList).find('tr');

        // Create arrays that map point numbers to HTML elements.
        // For example, for point 1:
        // annotationFields = form field with point 1's label code
        // annotationFieldRows = table row containing form field 1
        // annotationRobotFields = hidden form element of value true/false saying whether point 1 is robot annotated
        annotationFieldRowsJQ.each( function() {
            var field = $(this).find('input')[0];
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(field);
            var robotField = $('#id_robot_' + pointNum)[0];

            AnnotationToolHelper.annotationFields[pointNum] = field;
            AnnotationToolHelper.annotationFieldRows[pointNum] = this;
            AnnotationToolHelper.annotationRobotFields[pointNum] = robotField;
        });

        // Set point annotation statuses,
        // and draw the points
        for (i = 0; i < t.numOfPoints; i++) {
            t.pointGraphicStates[i] = t.STATE_NOTSHOWN;
        }
        t.annotationFieldsJQ.each( function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.updatePointState(pointNum, true);
            AnnotationToolHelper.updatePointGraphic(pointNum);
        });

        // Set the initial point view mode.  This'll trigger a redraw of the points, but that's okay;
        // initialization slowness is a relatively minor worry.
        t.changePointMode(t.POINTMODE_ALL);

        // Initialize save button
        $(t.saveButton).attr('disabled', 'disabled');
        $(t.saveButton).text('Saved');

        // Initialize all_done state
        Dajaxice.CoralNet.annotations.ajax_is_all_done(
            this.setAllDoneIndicator,
            {'image_id': $('#id_image_id')[0].value}
        );

        /*
         * Set event handlers
         */

        // Mouse button is pressed and un-pressed on the canvas
		$(t.listenerElmt).mouseup( function(e) {

            var ATH = AnnotationToolHelper;
            var mouseButton = util.identifyMouseButton(e);
            var imagePos;

            // Ctrl + left-click / Cmd + left-click on the image:
            // Selects the nearest point.
            if ((e.ctrlKey || e.metaKey) && mouseButton === "LEFT") {

                // This only works if we're displaying all points.
                if (ATH.pointViewMode !== ATH.POINTMODE_ALL)
                    return;

                var nearestPoint = ATH.getNearestPoint(e);
                ATH.toggle(nearestPoint);
            }

            // Left-click / right-click:
            // Zooms in or out on the image display.
            else if (mouseButton === "LEFT" || mouseButton === "RIGHT") {

                // Left-click to zoom in.
                if (mouseButton === "LEFT") {
                    if (ATH.zoomLevel === ATH.HIGHEST_ZOOM_LEVEL)
                        return;

                    // Zoom into the part that was clicked
                    // (Make sure to use the old zoom factor for calculating this)
                    imagePos = ATH.getImagePosition(e);
                    ATH.centerOfZoomX = imagePos[0];
                    ATH.centerOfZoomY = imagePos[1];

                    ATH.zoomLevel += 1;
                }
                // Right-click to zoom out.
                else if (mouseButton === "RIGHT") {
                    // 0 is the lowest zoom level.
                    if (ATH.zoomLevel === 0)
                        return;

                    // Zoom out toward the part that was clicked
                    // (Make sure to use the old zoom factor for calculating this)
                    imagePos = ATH.getImagePosition(e);
                    ATH.centerOfZoomX = imagePos[0];
                    ATH.centerOfZoomY = imagePos[1];

                    ATH.zoomLevel -= 1;
                }

                ATH.zoomFactor = ATH.ZOOM_FACTORS[ATH.zoomLevel];

                // Adjust the image and point coordinates.
                ATH.setupImageArea();
                ATH.getCanvasPoints();

                // Redraw all points.
                ATH.redrawAllPoints();
            }
        });

        // Disable the context menu on the listener element.
        // The menu just gets in the way while trying to zoom out, etc.
        $(t.listenerElmt).bind('contextmenu', function(e){
            return false;
        });
        // Same goes for the canvas element, which is sometimes what we end up
        // right clicking on if the image is no longer over that part of the canvas.
        $(t.pointsCanvas).bind('contextmenu', function(e){
            return false;
        });
        // Also note that the listener element uses CSS to disable
        // double-click-to-select (it makes the image turn blue, which is annoying).

        // Save button is clicked
        $(t.saveButton).click(function() {
            AnnotationToolHelper.saveAnnotations();
        });

        // A label button is clicked
        $('#labelButtons').find('button').each( function() {
            $(this).click( function() {
                // Label the selected points with this button's label code
                // (which is the button's text).
                AnnotationToolHelper.labelSelected($(this).text());
            });
        });

        // Label field gains focus
        t.annotationFieldsJQ.focus(function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.unselectAll();
            AnnotationToolHelper.select(pointNum);
        });

        // Label field is typed into and changed, and then unfocused.
        // (This does NOT run when a click of a label button changes the label field.)
        t.annotationFieldsJQ.change(function() {
            AnnotationToolHelper.onLabelFieldChange(this);
        });

        // Label field is focused and a keyboard key is released
        t.annotationFieldsJQ.keyup(function(e) {
            var ENTER = 13;
            
            if(e.keyCode === ENTER) {
                var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);

                // Unrobot/update the field
                AnnotationToolHelper.onPointUpdate(pointNum);

                // Switch focus to next point's field
                AnnotationToolHelper.focusNextField(pointNum);
            }
        });

        // Number next to a label field is clicked.
        $(".annotationFormLabel").click(function() {
            var pointNum = parseInt($(this).text());
            AnnotationToolHelper.toggle(pointNum);
        });

        // A point mode button is clicked.
        $("#pointModeButtonAll").click(function() {
            AnnotationToolHelper.changePointMode(AnnotationToolHelper.POINTMODE_ALL);
        });
        $("#pointModeButtonSelected").click(function() {
            AnnotationToolHelper.changePointMode(AnnotationToolHelper.POINTMODE_SELECTED);
        });
        $("#pointModeButtonNone").click(function() {
            AnnotationToolHelper.changePointMode(AnnotationToolHelper.POINTMODE_NONE);
        });
    },

    /*
     * Based on the current zoom level and focus of the zoom, position and
     * set up the image and on-image listener elements.
     */
    setupImageArea: function() {
        var t = this;

        t.imageDisplayWidth = t.IMAGE_FULL_WIDTH * t.zoomFactor;
        t.imageDisplayHeight = t.IMAGE_FULL_HEIGHT * t.zoomFactor;

        // Round off imprecision, so that if the display width is supposed to be
        // equal to the image area width, then they will actually be equal.
        t.imageDisplayWidth = parseFloat(t.imageDisplayWidth.toFixed(3));
        t.imageDisplayHeight = parseFloat(t.imageDisplayHeight.toFixed(3));

        // Position the image within the image area.
        // Negative offsets means the top-left corner is offscreen.
        // Positive offsets means there's extra space around the image
        // (should prevent this unless the image display is smaller than the image area).

        if (t.imageDisplayWidth <= t.IMAGE_AREA_WIDTH)
            t.imageLeftOffset = (t.IMAGE_AREA_WIDTH - t.imageDisplayWidth) / 2;
        else {
            var centerOfZoomInDisplayX = t.centerOfZoomX * t.zoomFactor;
            var leftEdgeInDisplayX = centerOfZoomInDisplayX - (t.IMAGE_AREA_WIDTH / 2);
            var rightEdgeInDisplayX = centerOfZoomInDisplayX + (t.IMAGE_AREA_WIDTH / 2);
            
            if (leftEdgeInDisplayX < 0)
                t.imageLeftOffset = 0;
            else if (rightEdgeInDisplayX > t.imageDisplayWidth)
                t.imageLeftOffset = -(t.imageDisplayWidth - t.IMAGE_AREA_WIDTH);
            else
                t.imageLeftOffset = -leftEdgeInDisplayX;
        }

        if (t.imageDisplayHeight <= t.IMAGE_AREA_HEIGHT)
            t.imageTopOffset = (t.IMAGE_AREA_HEIGHT - t.imageDisplayHeight) / 2;
        else {
            var centerOfZoomInDisplayY = t.centerOfZoomY * t.zoomFactor;
            var topEdgeInDisplayY = centerOfZoomInDisplayY - (t.IMAGE_AREA_HEIGHT / 2);
            var bottomEdgeInDisplayY = centerOfZoomInDisplayY + (t.IMAGE_AREA_HEIGHT / 2);

            if (topEdgeInDisplayY < 0)
                t.imageTopOffset = 0;
            else if (bottomEdgeInDisplayY > t.imageDisplayHeight)
                t.imageTopOffset = -(t.imageDisplayHeight - t.IMAGE_AREA_HEIGHT);
            else
                t.imageTopOffset = -topEdgeInDisplayY;
        }

        // Round off imprecision, so that we don't have any extremely small offsets
        // that get expressed in scientific notation (that confuses jQuery's number parsing).
        t.imageLeftOffset = parseFloat(t.imageLeftOffset.toFixed(3));
        t.imageTopOffset = parseFloat(t.imageTopOffset.toFixed(3));

        // Set styling properties for the image.
        $(t.coralImage).css({
            "height": t.imageDisplayHeight,
            "left": t.imageLeftOffset,
            "top": t.imageTopOffset,
            "z-index": 0
        });

        // Set styling properties for the listener element:
        // An invisible element that goes over the coral image
        // and listens for mouse events.
        // Since it has to be on top to listen for mouse events,
        // the z-index should be above every other element's z-index.
        $(t.listenerElmt).css({
            "width": t.imageDisplayWidth,
            "height": t.imageDisplayHeight,
            "left": t.imageLeftOffset,
            "top": t.imageTopOffset,
            "z-index": 100
        });
    },

    /*
     * Clear the canvas and reset the context.
     */
    resetCanvas: function() {
        var t = this;

        // Get the original (untranslated) context back.
        t.context.restore();
        // And save the context again for the next time we have to translate.
        t.context.save();

        // Clear the entire canvas.
        t.context.clearRect(0, 0, t.pointsCanvas.width, t.pointsCanvas.height);

        // Translate the canvas context to compensate for the gutter.
        // This'll allow us to pretend that canvas coordinates = image area coordinates.
        t.context.translate(t.CANVAS_GUTTER, t.CANVAS_GUTTER);
    },
    
    /* Look at a label field, and based on the label, mark the point
     * as (human) annotated, robot annotated, unannotated, or errored.
     */
    updatePointState: function(pointNum, initializing) {
        var t = this;

        var field = t.annotationFields[pointNum];
        var row = t.annotationFieldRows[pointNum];
        var robotField = t.annotationRobotFields[pointNum];
        var labelCode = field.value;

        /*
         * Update style elements and robot statuses accordingly
         */

        // Error: label is not empty string, and not in the labelset
        if (labelCode !== '' && t.labelCodes.indexOf(labelCode) === -1) {
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
                t.unrobot(pointNum);
            }

            // Set as (human) annotated or not
            if (labelCode === '' || t.isRobot(pointNum)) {
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
        var oldState = t.pointContentStates[pointNum];
        var newState = {'label': labelCode, 'robot': robotField.value};

        if (initializing) {
            // Initializing this point at page load time
            t.pointContentStates[pointNum] = newState;
        }
        else if (oldState['label'] !== newState['label']
                 || oldState['robot'] !== newState['robot']) {
            // Content has changed
            contentChanged = true;
            t.pointContentStates[pointNum] = newState;
        }

        return contentChanged;
    },

    onPointUpdate: function(pointNum) {
        var contentChanged = this.updatePointState(pointNum, false);
        
        this.updatePointGraphic(pointNum);
        
        if (contentChanged)
            this.updateSaveButton();
    },

    onLabelFieldChange: function(field) {
        var pointNum = this.getPointNumOfAnnoField(field);
        this.onPointUpdate(pointNum);
    },

    updateSaveButton: function() {
        var t = this;

        // No errors in annotation form
        if ($(t.annotationList).find('tr.error').length === 0) {
            // Enable save button
            $(t.saveButton).removeAttr('disabled');
            t.setSaveButtonText("Save progress");
        }
        // Errors
        else {
            // Disable save button
            $(t.saveButton).attr('disabled', 'disabled');
            t.setSaveButtonText("Error");
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

    select: function(pointNum) {
        $(this.annotationFieldRows[pointNum]).addClass('selected');
        this.updatePointGraphic(pointNum);
    },

    unselect: function(pointNum) {
        $(this.annotationFieldRows[pointNum]).removeClass('selected');
        this.updatePointGraphic(pointNum);
    },

    toggle: function(pointNum) {
        if ($(this.annotationFieldRows[pointNum]).hasClass('selected'))
            this.unselect(pointNum);
        else
            this.select(pointNum);
    },

    isRobot: function(pointNum) {
        var robotField = this.annotationRobotFields[pointNum];
        return robotField.value === 'true';
    },

    unrobot: function(pointNum) {
        var robotField = this.annotationRobotFields[pointNum];
        robotField.value = 'false';

        var row = this.annotationFieldRows[pointNum];
        $(row).removeClass('robot');
    },

    /* Optimization of unselect for multiple points.
     */
    unselectMultiple: function(pointList) {
        var pointNum, i;

        if (this.pointViewMode === this.POINTMODE_SELECTED) {

            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                $(this.annotationFieldRows[pointNum]).removeClass('selected');
            }
            this.redrawAllPoints();
        }
        else {
            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                this.unselect(pointNum);
            }
        }
    },

    unselectAll: function() {
        var selectedPointList = [];
        this.getSelectedFieldsJQ().each( function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            selectedPointList.push(pointNum);
        });
        this.unselectMultiple(selectedPointList);
    },

    // Label button is clicked
    labelSelected: function(labelButtonCode) {
        var selectedFieldsJQ = this.getSelectedFieldsJQ();

        // Iterate over selected points' fields.
        selectedFieldsJQ.each( function() {
            // Set the point's label.
            this.value = labelButtonCode;

            // Update the point's annotation status (including unroboting).
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.onPointUpdate(pointNum);
        });

        // If just 1 field is selected, focus the next field automatically
        if (selectedFieldsJQ.length === 1) {
            var pointNum = this.getPointNumOfAnnoField(selectedFieldsJQ[0]);
            this.focusNextField(pointNum);
        }
    },

    focusNextField: function(pointNum) {
        // Last point numerically
        var lastPoint = this.numOfPoints;

        // If last point...
        if (pointNum === lastPoint) {
            // Just un-focus from this point's field
            $(this.annotationFields[pointNum]).blur();
        }
        // If not last point...
        else {
            // Focus the next point's field
            $(this.annotationFields[pointNum+1]).focus();
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
        var elmt = this.coralImage;
        while (elmt !== null) {
            x -= elmt.offsetLeft;
            y -= elmt.offsetTop;
            elmt = elmt.offsetParent;
        }

	    return [x,y];
	},

    getImagePosition: function(e) {
        var t = this;
        var imageElmtPosition = t.getImageElmtPosition(e);
        var imageElmtX = imageElmtPosition[0];
        var imageElmtY = imageElmtPosition[1];

        var x = imageElmtX / t.zoomFactor;
        var y = imageElmtY / t.zoomFactor;

        return [x,y];
    },

    getNearestPoint: function(e) {
        var t = this;

        // Mouse's position in the canvas element
        var imagePosition = this.getImagePosition(e);
        var x = imagePosition[0];
        var y = imagePosition[1];

        var minDistance = Infinity;
        var closestPoint = null;

        for (var i = 0; i < t.imagePoints.length; i++) {
            var currPoint = t.imagePoints[i];

            // Don't count points that are offscreen.
            if (t.pointIsOffscreen(currPoint.point_number))
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
        var t = this;

        for (var i = 0; i < t.imagePoints.length; i++) {

            t.canvasPoints[t.imagePoints[i].point_number] = {
                num: t.imagePoints[i].point_number,
                row: (t.imagePoints[i].row * t.zoomFactor) + t.imageTopOffset,
                col: (t.imagePoints[i].column * t.zoomFactor) + t.imageLeftOffset
            };
        }
    },

    drawPointHelper: function(pointNum, color, outlineColor) {
        var canvasPoint = this.canvasPoints[pointNum];

        this.drawPointSymbol(canvasPoint.col, canvasPoint.row,
                             color);
        this.drawPointNumber(canvasPoint.num.toString(), canvasPoint.col, canvasPoint.row,
                             color, outlineColor);
    },

    drawPointUnannotated: function(pointNum) {
        this.drawPointHelper(pointNum, this.UNANNOTATED_COLOR, this.UNANNOTATED_OUTLINE_COLOR);
    },
    drawPointAnnotated: function(pointNum) {
        this.drawPointHelper(pointNum, this.ANNOTATED_COLOR, this.ANNOTATED_OUTLINE_COLOR);
    },
    drawPointSelected: function(pointNum) {
        this.drawPointHelper(pointNum, this.SELECTED_COLOR, this.SELECTED_OUTLINE_COLOR);
    },

    /* Update a point's graphics on the canvas in the correct color.
     * Don't redraw a point unless necessary.
     */
    updatePointGraphic: function(pointNum) {
        var t = this;

        // If the point is offscreen, then don't draw
        if (t.pointIsOffscreen(pointNum))
            return;

        // Get the current (graphical) state of this point
        var row = this.annotationFieldRows[pointNum];
        var newState;

        if ($(row).hasClass('selected'))
            newState = t.STATE_SELECTED;
        else if ($(row).hasClass('annotated'))
            newState = t.STATE_ANNOTATED;
        else
            newState = t.STATE_UNANNOTATED;

        // Account for point view modes
        if (t.pointViewMode === t.POINTMODE_SELECTED && newState !== t.STATE_SELECTED)
            newState = t.STATE_NOTSHOWN;
        if (t.pointViewMode === t.POINTMODE_NONE)
            newState = t.STATE_NOTSHOWN;

        // Redraw if the (graphical) state has changed
        var oldState = t.pointGraphicStates[pointNum];

        if (oldState !== newState) {
            t.pointGraphicStates[pointNum] = newState;

            if (newState === t.STATE_SELECTED)
                t.drawPointSelected(pointNum);
            else if (newState === t.STATE_ANNOTATED)
                t.drawPointAnnotated(pointNum);
            else if (newState === t.STATE_UNANNOTATED)
                t.drawPointUnannotated(pointNum);
            else if (newState === t.STATE_NOTSHOWN)
                // "Erase" this point.
                // To do this, redraw the canvas with this point marked as not shown.
                // For performance reasons, you'll want to avoid reaching this code whenever
                // possible/reasonable.  One tip: remember to mark all points as NOTSHOWN
                // whenever you clear the canvas of all points.
                t.redrawAllPoints();
        }
    },

    /*
     * Return true if the given point's coordinates
     * are not within the image area
     */
    pointIsOffscreen: function(pointNum) {
        var t = this;
        return (t.canvasPoints[pointNum].row < 0
                || t.canvasPoints[pointNum].row > t.IMAGE_AREA_HEIGHT
                || t.canvasPoints[pointNum].col < 0
                || t.canvasPoints[pointNum].col > t.IMAGE_AREA_WIDTH
                )
    },

    redrawAllPoints: function() {
        var t = this;

        // Reset the canvas and re-translate the context
        // to compensate for the gutters.
        t.resetCanvas();

        // Clear the pointGraphicStates.
        for (var i = 0; i < t.pointGraphicStates.length; i++) {
            t.pointGraphicStates[i] = t.STATE_NOTSHOWN;
        }

        // Draw all points.
        t.annotationFieldsJQ.each( function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.updatePointGraphic(pointNum);
        });
    },

    changePointMode: function(pointMode) {
        var t = this;

        // Outline this point mode button in red (and de-outline the other buttons).
        $(".pointModeButton").removeClass("selected");
        
        if (pointMode == t.POINTMODE_ALL)
            $("#pointModeButtonAll").addClass("selected");
        else if (pointMode == t.POINTMODE_SELECTED)
            $("#pointModeButtonSelected").addClass("selected");
        else if (pointMode == t.POINTMODE_NONE)
            $("#pointModeButtonNone").addClass("selected");

        // Set the new point display mode.
        t.pointViewMode = pointMode;

        // Redraw all points.
        t.redrawAllPoints();
    },

    saveAnnotations: function() {
        $(this.saveButton).attr('disabled', 'disabled');
        $(this.saveButton).text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_annotations(
            this.ajaxSaveButtonCallback,    // JS callback that the ajax.py method returns to.
            {'annotationForm': $("#annotationForm").serializeArray()}    // Args to the ajax.py method.
        );
    },

    // AJAX callback: cannot use "this" to refer to AnnotationToolHelper
    ajaxSaveButtonCallback: function(returnDict) {
        
        if (returnDict.hasOwnProperty('error')) {
            var errorMsg = returnDict['error'];
            AnnotationToolHelper.setSaveButtonText("Error");

            // TODO: Handle error cases more elegantly?  Alerts are lame.
            // Though, these errors aren't really supposed to happen unless the annotation tool behavior is flawed.
            alert("Sorry, an error occurred when trying to save your annotations:\n{0}".format(errorMsg));
        }
        else {
            AnnotationToolHelper.setSaveButtonText("Saved");

            // Add or remove ALL DONE indicator
            AnnotationToolHelper.setAllDoneIndicator(returnDict.hasOwnProperty('all_done'));
        }
    },

    setSaveButtonText: function(buttonText) {
        $(this.saveButton).text(buttonText);
    },

    getPointNumOfAnnoField: function(annoField) {
        // Assuming the annotation field's name attribute is "label_<pointnumber>".
        // "label_" is 6 characters.
        return parseInt(annoField.name.substring(6));
    },

    getSelectedFieldsJQ: function() {
        return $(this.annotationList).find('tr.selected').find('input');
    },

    /*
    Draw an annotation point symbol (the crosshair, circle, or whatever)
    which is centered at x,y.
     */
    drawPointSymbol: function(x, y, color) {
        var t = this;

		// Adjust x and y by 0.5 so that straight lines are centered
		// at the halfway point of a pixel, not on a pixel boundary.
		// This ensures that 1-pixel-wide lines are really 1 pixel wide,
		// instead of 2 pixels wide.
        // NOTE: This only applies to odd-width lines.
		x = x+0.5;
		y = y+0.5;

        t.context.strokeStyle = color;
        t.context.lineWidth = 3;

		t.context.beginPath();
		//context.arc(x, y, POINT_RADIUS, 0, 2.0*Math.PI);    // A circle

		t.context.moveTo(x, y + t.POINT_RADIUS);
		t.context.lineTo(x, y - t.POINT_RADIUS);

		t.context.moveTo(x - t.POINT_RADIUS, y);
		t.context.lineTo(x + t.POINT_RADIUS, y);

		t.context.stroke();
	},

    /*
    Draw the number of an annotation point
    which is centered at x,y.
     */
	drawPointNumber: function(num, x, y, color, outlineColor) {
        var t = this;

		t.context.textBaseline = "bottom";
		t.context.textAlign = "left";
		t.context.fillStyle = color;
        t.context.strokeStyle = outlineColor;
        t.context.lineWidth = 1;
	    t.context.font = t.NUMBER_FONT;

		// Offset the number's position a bit so it doesn't overlap with the annotation point.
		// (Unlike the line drawing, 0.5 pixel adjustment doesn't seem to make a difference)
        x = x + 3, y = y - 3;

        t.context.fillText(num, x, y);    // Color in the number
		t.context.strokeText(num, x, y);    // Outline the number (make it easier to see)
	},

	/*
	Toggle the points on/off by bringing them in front of or behind the image.
	TODO: Add a button that does this.
	*/
	togglePoints: function() {
        var t = this;

		if (t.pointsCanvas.style.visibility === 'hidden')
			t.pointsCanvas.style.visibility = 'visible';
		else    // 'visible' or ''
			t.pointsCanvas.style.visibility = 'hidden';
	}
};

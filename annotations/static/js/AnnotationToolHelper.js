var AnnotationToolHelper = (function() {

    // Compatibility
    var isMac = util.osIsMac();

    // HTML elements
    var annotationArea = null;
    var annotationList = null;
    var annotationFieldRows = [];
    var annotationFields = [];
    var annotationRobotFields = [];
    var $annotationFields = null;
    var imageArea = undefined;
    var pointsCanvas = null;
    var listenerElmt = null;
    var saveButton = null;

    // Annotation related
    var labelCodes = [];
    var labelCodesToNames = {};
    var currentLabelButton = null;

    // Canvas related
    var context = null;
    var canvasPoints = [], imagePoints = null;
    var numOfPoints = null;
    var NUMBER_FONT_FORMAT_STRING = "bold {0}px sans-serif";

    // Border where the canvas is drawn, but the image is not.
    // This is used to fully show the points that are located near the edge of the image.
    var canvasGutter = null;
    var CANVAS_GUTTER_COLOR = "#BBBBBB";

    // Related to possible states of each annotation point
    var pointContentStates = [];
    var pointGraphicStates = [];
    var STATE_UNANNOTATED = 0;
    var STATE_ROBOT = 1;
    var STATE_ANNOTATED = 2;
    var STATE_SELECTED = 3;
    var STATE_NOTSHOWN = 4;

    // Point number outline color
    var OUTLINE_COLOR = "#000000";

    // Point viewing mode
    var pointViewMode = null;
    var POINTMODE_ALL = 0;
    var POINTMODE_SELECTED = 1;
    var POINTMODE_NONE = 2;

    // The original image's dimensions
    var IMAGE_FULL_WIDTH = null;
    var IMAGE_FULL_HEIGHT = null;
    // The area that the image is permitted to fill
    var imageAreaWidth = null;
    var imageAreaHeight = null;
    // The canvas area, where drawing is allowed
    var annotationAreaWidth = null;
    var annotationAreaHeight = null;
    // Label button grid
    var BUTTON_GRID_MAX_X = null;
    var BUTTON_GRID_MAX_Y = null;
    var BUTTONS_PER_ROW = 10;
    var LABEL_BUTTON_WIDTH = null;

    // Display parameters of the image.
    // > 1 zoomFactor means larger than original image
    // zoom levels start at 0 (fully zoomed out) and go up like 1,2,3,etc.
    var imageDisplayWidth = null;
    var imageDisplayHeight = null;
    var zoomFactor = null;
    var zoomLevel = null;
    var ZOOM_FACTORS = {};
    var ZOOM_INCREMENT = 1.5;
    var HIGHEST_ZOOM_LEVEL = 8;
    // Current display position of the image.
    // centerOfZoom is in terms of raw-image coordinates.
    // < 0 offset means top left corner is not visible.
    var centerOfZoomX = null;
    var centerOfZoomY = null;
    var imageLeftOffset = null;
    var imageTopOffset = null;


    /*
     * Based on the current zoom level and focus of the zoom, position and
     * set up the image and on-image listener elements.
     */
    function setupImageArea() {
        imageDisplayWidth = IMAGE_FULL_WIDTH * zoomFactor;
        imageDisplayHeight = IMAGE_FULL_HEIGHT * zoomFactor;

        // Round off imprecision, so that if the display width is supposed to be
        // equal to the image area width, then they will actually be equal.
        imageDisplayWidth = parseFloat(imageDisplayWidth.toFixed(3));
        imageDisplayHeight = parseFloat(imageDisplayHeight.toFixed(3));

        // Position the image within the image area.
        // Negative offsets means the top-left corner is offscreen.
        // Positive offsets means there's extra space around the image
        // (should prevent this unless the image display is smaller than the image area).

        if (imageDisplayWidth <= imageAreaWidth)
            imageLeftOffset = (imageAreaWidth - imageDisplayWidth) / 2;
        else {
            var centerOfZoomInDisplayX = centerOfZoomX * zoomFactor;
            var leftEdgeInDisplayX = centerOfZoomInDisplayX - (imageAreaWidth / 2);
            var rightEdgeInDisplayX = centerOfZoomInDisplayX + (imageAreaWidth / 2);
            
            if (leftEdgeInDisplayX < 0)
                imageLeftOffset = 0;
            else if (rightEdgeInDisplayX > imageDisplayWidth)
                imageLeftOffset = -(imageDisplayWidth - imageAreaWidth);
            else
                imageLeftOffset = -leftEdgeInDisplayX;
        }

        if (imageDisplayHeight <= imageAreaHeight)
            imageTopOffset = (imageAreaHeight - imageDisplayHeight) / 2;
        else {
            var centerOfZoomInDisplayY = centerOfZoomY * zoomFactor;
            var topEdgeInDisplayY = centerOfZoomInDisplayY - (imageAreaHeight / 2);
            var bottomEdgeInDisplayY = centerOfZoomInDisplayY + (imageAreaHeight / 2);

            if (topEdgeInDisplayY < 0)
                imageTopOffset = 0;
            else if (bottomEdgeInDisplayY > imageDisplayHeight)
                imageTopOffset = -(imageDisplayHeight - imageAreaHeight);
            else
                imageTopOffset = -topEdgeInDisplayY;
        }

        // Round off imprecision, so that we don't have any extremely small offsets
        // that get expressed in scientific notation (that confuses jQuery's number parsing).
        imageLeftOffset = parseFloat(imageLeftOffset.toFixed(3));
        imageTopOffset = parseFloat(imageTopOffset.toFixed(3));

        // Set styling properties for the image canvas.
        $(ATI.imageCanvas).css({
            "height": imageDisplayHeight,
            "left": imageLeftOffset,
            "top": imageTopOffset,
            "z-index": 0
        });

        // Set styling properties for the listener element:
        // An invisible element that sits on top of the image
        // and listens for mouse events.
        // Since it has to be on top to listen for mouse events,
        // the z-index should be above every other element's z-index.
        $(listenerElmt).css({
            "width": imageDisplayWidth,
            "height": imageDisplayHeight,
            "left": imageLeftOffset,
            "top": imageTopOffset,
            "z-index": 100
        });
    }

    /*
     * Clear the canvas and reset the context.
     */
    function resetCanvas() {
        // Get the original (untranslated) context back.
        context.restore();
        // And save the context again for the next time we have to translate.
        context.save();

        // Clear the entire canvas.
        context.clearRect(0, 0, pointsCanvas.width, pointsCanvas.height);

        // Translate the canvas context to compensate for the gutter.
        // This'll allow us to pretend that canvas coordinates = image area coordinates.
        context.translate(canvasGutter, canvasGutter);
    }
    
    /* Look at a label field, and based on the label, mark the point
     * as (human) annotated, robot annotated, unannotated, or errored.
     *
     * Return true if something changed (label code or robot status).
     * Return false otherwise.
     */
    function updatePointState(pointNum, robotStatusAction) {
        var field = annotationFields[pointNum];
        var row = annotationFieldRows[pointNum];
        var robotField = annotationRobotFields[pointNum];
        var labelCode = field.value;

        // Has the label text changed?
        var oldState = pointContentStates[pointNum];
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
        else if (labelCodes.indexOf(labelCode) === -1) {
            // Error: label is not in the labelset
            $(field).attr('title', 'Label not in labelset');
            $(row).addClass('error');
            $(row).removeClass('annotated');
            unrobot(pointNum);
        }
        else {
            // No error

            if (robotField.value === 'true') {
                if (robotStatusAction === 'unrobotOnlyIfChanged') {
                    // We're told to only unrobot the annotation if the label changed.
                    if (labelChanged)
                        unrobot(pointNum);
                }
                else {
                    // Any other update results in this annotation being un-roboted.
                    unrobot(pointNum);
                }
            }

            // Set as (human) annotated or not
            if (isRobot(pointNum)) {
                // Robot annotated
                $(row).removeClass('annotated');
            }
            else {
                $(row).addClass('annotated');
            }

            // Remove error styling, if any
            $(row).removeClass('error');

            // Field's mouseover text = label name
            $(field).attr('title', labelCodesToNames[labelCode]);
        }

        var robotStatusChanged = (oldState['robot'] !== robotField.value);
        var contentChanged = (labelChanged || robotStatusChanged);

        // Done assessing change of state, so set the new state.
        pointContentStates[pointNum] = {'label': labelCode, 'robot': robotField.value};
        return contentChanged;
    }

    function onPointUpdate(annoField, robotStatusAction) {
        var pointNum = getPointNumOfAnnoField(annoField);
        var contentChanged = updatePointState(pointNum, robotStatusAction);
        
        updatePointGraphic(pointNum);
        
        if (contentChanged)
            updateSaveButton();
    }

    function onLabelFieldTyping(field) {
        onPointUpdate(field);
    }

    function updateSaveButton() {
        // No errors in annotation form
        if ($(annotationList).find('tr.error').length === 0) {
            // Enable save button
            $(saveButton).removeAttr('disabled');
            setSaveButtonText("Save progress");
        }
        // Errors
        else {
            // Disable save button
            $(saveButton).attr('disabled', 'disabled');
            setSaveButtonText("Error");
        }
    }

    function setAllDoneIndicator(allDone) {
        if (allDone) {
            $('#allDone').append('<span>').text("ALL DONE");
        }
        else {
            $('#allDone').empty();
        }
    }

    /* Wrapper for event handler functions.
     * Call e.preventDefault() and then call the event handler function.
     * TODO: Once there's a use for this, actually make sure this function works. */
    function preventDefaultWrapper(fn) {
        return function(e) {
            e.preventDefault();
            fn.call(this, e);
        };
    }

    function zoomIn(e) {
        zoom('in', e);
    }
    function zoomOut(e) {
        zoom('out', e);
    }
    function zoomFit(e) {
        zoom('fit', e);
    }
    function zoom(zoomType, e) {
        var zoomLevelChange;

        if (zoomType === 'in') {
            if (zoomLevel === HIGHEST_ZOOM_LEVEL)
                return;

            zoomLevelChange = 1;
        }
        else if (zoomType === 'out') {
            // 0 is the lowest zoom level.
            if (zoomLevel === 0)
                return;

            zoomLevelChange = -1;
        }
        else if (zoomType === 'fit') {
            // Zoom all the way out, i.e. get the zoom level to 0.
            if (zoomLevel === 0)
                return;

            zoomLevelChange = -zoomLevel;
        }

        // (1) Zoom on click: zoom into the part that was clicked.
        // (Make sure to use the old zoom factor for calculating the click position)
        // (2) Zoom with hotkey: don't change the center of zoom, just the zoom level.
        if (e !== undefined && e.type === 'mouseup') {
            var imagePos = getImagePosition(e);
            centerOfZoomX = imagePos[0];
            centerOfZoomY = imagePos[1];
        }

        zoomLevel += zoomLevelChange;
        zoomFactor = ZOOM_FACTORS[zoomLevel];

        // Adjust the image and point coordinates.
        setupImageArea();
        getCanvasPoints();

        // Redraw all points.
        redrawAllPoints();
    }

    /* Event listener callback: 'this' is an annotation field */
    function confirmFieldAndFocusNext() {
        // Unrobot/update the field
        onPointUpdate(this);

        // Switch focus to next point's field.
        // Call focusNextField() such that the current field becomes the object 'this'
        focusNextField.call(this);
    }

    function select(pointNum) {
        $(annotationFieldRows[pointNum]).addClass('selected');
        updatePointGraphic(pointNum);
    }

    function unselect(pointNum) {
        $(annotationFieldRows[pointNum]).removeClass('selected');
        updatePointGraphic(pointNum);
    }

    function toggle(pointNum) {
        if ($(annotationFieldRows[pointNum]).hasClass('selected'))
            unselect(pointNum);
        else
            select(pointNum);
    }

    function isRobot(pointNum) {
        var robotField = annotationRobotFields[pointNum];
        return robotField.value === 'true';
    }

    function unrobot(pointNum) {
        var robotField = annotationRobotFields[pointNum];
        robotField.value = 'false';

        var row = annotationFieldRows[pointNum];
        $(row).removeClass('robot');
    }

    /* Optimization of unselect for multiple points.
     */
    function unselectMultiple(pointList) {
        var pointNum, i;

        if (pointViewMode === POINTMODE_SELECTED) {

            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                $(annotationFieldRows[pointNum]).removeClass('selected');
            }
            redrawAllPoints();
        }
        else {
            for (i = 0; i < pointList.length; i++) {
                pointNum = pointList[i];
                unselect(pointNum);
            }
        }
    }

    function unselectAll() {
        var selectedPointList = [];
        get$selectedFields().each( function() {
            var pointNum = getPointNumOfAnnoField(this);
            selectedPointList.push(pointNum);
        });
        unselectMultiple(selectedPointList);
    }

    // Label button is clicked
    function labelSelected(labelButtonCode) {
        var $selectedFields = get$selectedFields();

        // Iterate over selected points' fields.
        $selectedFields.each( function() {
            // Set the point's label.
            this.value = labelButtonCode;

            // Update the point's annotation status (including unroboting as necessary).
            onPointUpdate(this);
        });

        // If just 1 field is selected, focus the next field automatically
        if ($selectedFields.length === 1) {
            // Call focusNextField() such that the selected field becomes the object 'this'
            focusNextField.call($selectedFields[0]);
        }
    }

    /* Event listener callback: 'this' is an annotation field */
    function labelWithCurrentLabel() {
        if (currentLabelButton !== null) {
            this.value = $(currentLabelButton).text();
            onPointUpdate(this, 'unrobotOnlyIfChanged');
        }
    }

    function setCurrentLabelButton(button) {
        $('#labelButtons button').removeClass('current');
        $(button).addClass('current');

        currentLabelButton = button;
    }

    /* Event listener callback: 'this' is an annotation field */
    function beginKeyboardLabelling() {
        // If this field already has a valid label code, then the
        // current label button becomes the button with that label code.
        if (labelCodes.indexOf(this.value) !== -1) {
            setCurrentLabelButton($("#labelButtons button:exactlycontains('" + this.value + "')"));
        }
        // Otherwise, label the field with the current label.
        else
            labelWithCurrentLabel.call(this);
    }

    function buttonIndexValid(gridX, gridY) {
        var buttonIndex = gridY*BUTTONS_PER_ROW + gridX;
        return (buttonIndex >= 0 && buttonIndex < labelCodes.length);
    }

    /* Event listener callback: 'this' is an annotation field */
    function moveCurrentLabel(dx, dy) {
        if (currentLabelButton === null)
            return;

        // Start with current label button
        var gridX = parseInt($(currentLabelButton).attr('gridx'));
        var gridY = parseInt($(currentLabelButton).attr('gridy'));

        // Move one step, check if valid grid position; repeat as needed
        do {
            gridX += dx;
            gridY += dy;

            // May need to wrap around to the other side of the grid
            if (gridX < 0)
                gridX = BUTTON_GRID_MAX_X;
            if (gridX > BUTTON_GRID_MAX_X)
                gridX = 0;
            if (gridY < 0)
                gridY = BUTTON_GRID_MAX_Y;
            if (gridY > BUTTON_GRID_MAX_Y)
                gridY = 0;
            
            // Need to check for a valid grid position, if the grid isn't a perfect rectangle
        } while (!buttonIndexValid(gridX, gridY));

        // Current label button is now the button with the x and y we calculated.
        setCurrentLabelButton($("#labelButtons button[gridx='" + gridX + "'][gridy='" + gridY + "']")[0]);

        // And make sure the current annotation field's
        // label gets changed to the current button's label.
        labelWithCurrentLabel.call(this);
    }

    function moveCurrentLabelLeft() {
        moveCurrentLabel.call(this, -1, 0);
    }
    function moveCurrentLabelRight() {
        moveCurrentLabel.call(this, 1, 0);
    }
    function moveCurrentLabelUp() {
        moveCurrentLabel.call(this, 0, -1);
    }
    function moveCurrentLabelDown() {
        moveCurrentLabel.call(this, 0, 1);
    }

    /* Event listener callback: 'this' is an annotation field */
    function focusPrevField() {
        var pointNum = getPointNumOfAnnoField(this);

        // If first point numerically...
        if (pointNum === 1) {
            // Just un-focus from this point's field
            $(this).blur();
        }
        // If not first point...
        else {
            // Focus the previous point's field
            $(annotationFields[pointNum-1]).focus();
        }
    }

    /* Event listener callback: 'this' is an annotation field */
    function focusNextField() {
        var pointNum = getPointNumOfAnnoField(this);
        var lastPoint = numOfPoints;

        // If last point (numerically)...
        if (pointNum === lastPoint) {
            // Just un-focus from this point's field
            $(this).blur();
        }
        // If not last point...
        else {
            // Focus the next point's field
            $(annotationFields[pointNum+1]).focus();
        }
    }

    /* Get the mouse position in the canvas element:
	(mouse's position in the HTML document) minus
	(canvas element's position in the HTML document). */
    function getImageElmtPosition(e) {
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
	}

    function getImagePosition(e) {
        var imageElmtPosition = getImageElmtPosition(e);
        var imageElmtX = imageElmtPosition[0];
        var imageElmtY = imageElmtPosition[1];

        var x = imageElmtX / zoomFactor;
        var y = imageElmtY / zoomFactor;

        return [x,y];
    }

    function getNearestPoint(e) {
        // Mouse's position in the canvas element
        var imagePosition = getImagePosition(e);
        var x = imagePosition[0];
        var y = imagePosition[1];

        var minDistance = Infinity;
        var closestPoint = null;

        for (var i = 0; i < imagePoints.length; i++) {
            var currPoint = imagePoints[i];

            // Don't count points that are offscreen.
            if (pointIsOffscreen(currPoint.point_number))
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
    }

    /*
    Raw image coordinates -> Canvas coordinates:
    (1) Scale the raw image coordinates by the image zoom factor.
    (2) Account for image position offset.
    (3) Don't account for gutter offset (translating the canvas context already takes care of this).
     */
    function getCanvasPoints() {
        for (var i = 0; i < imagePoints.length; i++) {

            // imagePoints[num].row: which image pixel it is, from 1 to height
            // canvasPoints[num].row: offset on the canvas, starting from 0 if the point is visible.
            // Subtract 0.5 so the canvasPoint is in the middle of the point's pixel instead of the bottom-right edge.  Typically won't make much of a difference, but still.
            canvasPoints[imagePoints[i].point_number] = {
                num: imagePoints[i].point_number,
                row: ((imagePoints[i].row - 0.5) * zoomFactor) + imageTopOffset,
                col: ((imagePoints[i].column - 0.5) * zoomFactor) + imageLeftOffset
            };
        }
    }

    function drawPointHelper(pointNum, color, outlineColor) {
        var canvasPoint = canvasPoints[pointNum];

        drawPointMarker(canvasPoint.col, canvasPoint.row,
                             color);
        drawPointNumber(canvasPoint.num.toString(), canvasPoint.col, canvasPoint.row,
                             color, outlineColor);
    }

    function drawPointUnannotated(pointNum) {
        drawPointHelper(pointNum, ATS.settings.unannotatedColor, OUTLINE_COLOR);
    }
    function drawPointRobotAnnotated(pointNum) {
        drawPointHelper(pointNum, ATS.settings.robotAnnotatedColor, OUTLINE_COLOR);
    }
    function drawPointHumanAnnotated(pointNum) {
        drawPointHelper(pointNum, ATS.settings.humanAnnotatedColor, OUTLINE_COLOR);
    }
    function drawPointSelected(pointNum) {
        drawPointHelper(pointNum, ATS.settings.selectedColor, OUTLINE_COLOR);
    }

    /* Update a point's graphics on the canvas in the correct color.
     * Don't redraw a point unless necessary.
     */
    function updatePointGraphic(pointNum) {
        // If the point is offscreen, then don't draw
        if (pointIsOffscreen(pointNum))
            return;

        // Get the current (graphical) state of this point
        var row = annotationFieldRows[pointNum];
        var newState;

        if ($(row).hasClass('selected'))
            newState = STATE_SELECTED;
        else if ($(row).hasClass('annotated'))
            newState = STATE_ANNOTATED;
        else if ($(row).hasClass('robot'))
            newState = STATE_ROBOT;
        else
            newState = STATE_UNANNOTATED;

        // Account for point view modes
        if (pointViewMode === POINTMODE_SELECTED && newState !== STATE_SELECTED)
            newState = STATE_NOTSHOWN;
        if (pointViewMode === POINTMODE_NONE)
            newState = STATE_NOTSHOWN;

        // Redraw if the (graphical) state has changed
        var oldState = pointGraphicStates[pointNum];

        if (oldState !== newState) {
            pointGraphicStates[pointNum] = newState;

            if (newState === STATE_SELECTED)
                drawPointSelected(pointNum);
            else if (newState === STATE_ANNOTATED)
                drawPointHumanAnnotated(pointNum);
            else if (newState === STATE_ROBOT)
                drawPointRobotAnnotated(pointNum);
            else if (newState === STATE_UNANNOTATED)
                drawPointUnannotated(pointNum);
            else if (newState === STATE_NOTSHOWN)
                // "Erase" this point.
                // To do this, redraw the canvas with this point marked as not shown.
                // For performance reasons, you'll want to avoid reaching this code whenever
                // possible/reasonable.  One tip: remember to mark all points as NOTSHOWN
                // whenever you clear the canvas of all points.
                redrawAllPoints();
        }
    }

    /*
     * Return true if the given point's coordinates
     * are not within the image area
     */
    function pointIsOffscreen(pointNum) {
        return (canvasPoints[pointNum].row < 0
                || canvasPoints[pointNum].row > imageAreaHeight
                || canvasPoints[pointNum].col < 0
                || canvasPoints[pointNum].col > imageAreaWidth
                )
    }

    function redrawAllPoints() {
        // Reset the canvas and re-translate the context
        // to compensate for the gutters.
        resetCanvas();

        // Clear the pointGraphicStates.
        for (var n = 1; n <= numOfPoints; n++) {
            pointGraphicStates[n] = STATE_NOTSHOWN;
        }

        // Draw all points.
        $annotationFields.each( function() {
            var pointNum = getPointNumOfAnnoField(this);
            updatePointGraphic(pointNum);
        });
    }

    function changePointMode(pointMode) {
        // Outline this point mode button in red (and de-outline the other buttons).
        $(".pointModeButton").removeClass("selected");
        
        if (pointMode == POINTMODE_ALL)
            $("#pointModeButtonAll").addClass("selected");
        else if (pointMode == POINTMODE_SELECTED)
            $("#pointModeButtonSelected").addClass("selected");
        else if (pointMode == POINTMODE_NONE)
            $("#pointModeButtonNone").addClass("selected");

        // Set the new point display mode.
        pointViewMode = pointMode;

        // Redraw all points.
        redrawAllPoints();
    }

    function saveAnnotations() {
        $(saveButton).attr('disabled', 'disabled');
        $(saveButton).text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_annotations(
            ajaxSaveButtonCallback,    // JS callback that the ajax.py method returns to.
            {'annotationForm': $("#annotationForm").serializeArray()}    // Args to the ajax.py method.
        );
    }

    // AJAX callback.
    function ajaxSaveButtonCallback(returnDict) {
        
        if (returnDict.hasOwnProperty('error')) {
            var errorMsg = returnDict['error'];
            setSaveButtonText("Error");

            // TODO: Handle error cases more elegantly?  Alerts are lame.
            // Though, these errors aren't really supposed to happen unless the annotation tool behavior is flawed.
            alert("Sorry, an error occurred when trying to save your annotations:\n{0}".format(errorMsg));
        }
        else {
            setSaveButtonText("Saved");

            // Add or remove ALL DONE indicator
            setAllDoneIndicator(returnDict.hasOwnProperty('all_done'));
        }
    }

    function setSaveButtonText(buttonText) {
        $(saveButton).text(buttonText);
    }

    function getPointNumOfAnnoField(annoField) {
        // Assuming the annotation field's name attribute is "label_<pointnumber>".
        // "label_" is 6 characters.
        return parseInt(annoField.name.substring(6));
    }

    function get$selectedFields() {
        return $(annotationList).find('tr.selected').find('input');
    }

    /*
    Draw an annotation point marker (crosshair, circle, or whatever)
    which is centered at x,y.
     */
    function drawPointMarker(x, y, color) {
        var markerType = ATS.settings.pointMarker;
        var radius;

        if (ATS.settings.pointMarkerIsScaled === true)
            // Zoomed all the way out: radius = pointMarkerSize.
            // Zoomed in 1.5x: radius = pointMarkerSize * 1.5. etc.
            // radius must be an integer.
            radius = Math.round(ATS.settings.pointMarkerSize * Math.pow(ZOOM_INCREMENT, zoomLevel));
        else
            radius = ATS.settings.pointMarkerSize;

        // Adjust x and y by 0.5 so that straight lines are centered
		// at the halfway point of a pixel, not on a pixel boundary.
		// This ensures that 1-pixel-wide lines are really 1 pixel wide,
		// instead of 2 pixels wide.
        // NOTE: This only applies to odd-width lines.
		x = x+0.5;
		y = y+0.5;

        context.strokeStyle = color;
        context.lineWidth = 3;

		context.beginPath();

        if (markerType === 'crosshair' || markerType === 'crosshair and circle') {
            context.moveTo(x, y + radius);
            context.lineTo(x, y - radius);

            context.moveTo(x - radius, y);
            context.lineTo(x + radius, y);
        }
        if (markerType === 'circle' || markerType === 'crosshair and circle') {
            context.arc(x, y, radius, 0, 2.0*Math.PI);
        }
        if (markerType === 'box') {
            context.moveTo(x + radius, y + radius);
            context.lineTo(x - radius, y + radius);
            context.lineTo(x - radius, y - radius);
            context.lineTo(x + radius, y - radius);
            context.lineTo(x + radius, y + radius);
        }

        context.stroke();
	}

    /*
    Draw the number of an annotation point
    which is centered at x,y.
     */
    function drawPointNumber(num, x, y, color, outlineColor) {
        context.textBaseline = "bottom";
		context.textAlign = "left";
		context.fillStyle = color;
        context.strokeStyle = outlineColor;
        context.lineWidth = 1;

        var numberSize = ATS.settings.pointNumberSize;
        if (ATS.settings.pointNumberIsScaled)
            numberSize = Math.round(numberSize * Math.pow(ZOOM_INCREMENT, zoomLevel));

	    context.font = NUMBER_FONT_FORMAT_STRING.format(numberSize.toString());

		// Offset the number's position a bit so it doesn't overlap with the annotation point.
		// (Unlike the line drawing, 0.5 pixel adjustment doesn't seem to make a difference)
        // TODO: Consider doing offset calculations once each time the settings/zoom level change, not once for each point
        var offset = ATS.settings.pointMarkerSize;

        if (ATS.settings.pointMarker !== 'box')
            // When the pointMarker is a box, line up the number with the corner of the box.
            // When the pointMarker is not a box, line up the number with the corner of a circle instead.
            offset = offset * 0.7;
        if (ATS.settings.pointMarkerIsScaled === true)
            offset = offset * Math.pow(ZOOM_INCREMENT, zoomLevel);
        // Compensate for the fact that the number ends up being drawn
        // a few pixels away from the specified baseline point.
        offset = offset - 2;
        offset = Math.round(offset);

        x = x + offset;
        y = y - offset;

        context.fillText(num, x, y);    // Color in the number
		context.strokeText(num, x, y);    // Outline the number (make it easier to see)
	}

    
    /*
    Hiding/showing the annotation tool instructions.
    */
    function hideInstructions() {
        $("#id_instructions_wrapper").hide();
        $("#id_button_show_instructions").show();
    }

    function showInstructions() {
        $("#id_instructions_wrapper").show();
        $("#id_button_show_instructions").hide();
    }


    function resizeElements() {

        // TODO: Compute the entire annotation tool height from the window
        // height; not just the annotation area height.

        // TODO: Note how the columnContainer is the outermost element
        // and its dimensions are set last.  Can we make the rest of
        // this function go from innermost to outermost to make it easier
        // to follow?  Or is this in general not possible?

        var windowHeight = $(window).height();

        $('#columnContainer').height(windowHeight);

        annotationAreaWidth = $(annotationArea).width();
        //annotationAreaHeight = windowHeight;
        //$(annotationArea).height(annotationAreaHeight);
        annotationAreaHeight = $(annotationArea).height();

        canvasGutter = Math.min(
            Math.round(annotationAreaWidth / 30),
            Math.round(annotationAreaHeight / 30)
        );

        imageAreaWidth = annotationAreaWidth - (canvasGutter*2);
        imageAreaHeight = annotationAreaHeight - (canvasGutter*2);

        $(imageArea).width(imageAreaWidth);
        $(imageArea).height(imageAreaHeight);
        $(imageArea).css({
            "left": canvasGutter + "px",
            "top": canvasGutter + "px"
        });

        // Set the canvas's width and height properties so the canvas contents don't stretch.
        // Note that this is different from CSS width and height properties.
        pointsCanvas.width = annotationAreaWidth;
        pointsCanvas.height = annotationAreaHeight;

        var annotationListMaxHeight =
            annotationAreaHeight - parseFloat($("#toolButtonArea").outerHeight(true));

        $(annotationList).css({
            "max-height": annotationListMaxHeight + "px"
        });

        // Set the height for the element containing the two main columns.
        // This ensures that the info below the annotation tool doesn't overlap with
        // the annotation tool.  Overlap is possible because the main column floats,
        // so the main column doesn't contribute to its container element's height.
        //
        // The container element's height will be set to the max of the
        // columns' DOM (computed) heights.
//        $('#columnContainer').height(
//            Math.max(
//                parseFloat($('#mainColumn').height()),
//                parseFloat($('#rightSidebar').height())
//            ).toString() + "px"
//        );

        // Set initial image scaling so the whole image is shown.
        // Also set the allowable zoom factors.

        var widthScaleRatio = IMAGE_FULL_WIDTH / imageAreaWidth;
        var heightScaleRatio = IMAGE_FULL_HEIGHT / imageAreaHeight;
        var scaleDownFactor = Math.max(widthScaleRatio, heightScaleRatio);

        // If the scaleDownFactor is < 1, then it's scaled up (meaning the image is really small).
        zoomFactor = 1.0 / scaleDownFactor;

        // Allowable zoom factors/levels:
        // Start with the most zoomed out level, 0.  Level 1 is ZOOM_INCREMENT * level 0.
        // Level 2 is ZOOM_INCREMENT * level 1, etc.  Goes up to level HIGHEST_ZOOM_LEVEL.
        zoomLevel = 0;
        for (i = 0; i <= HIGHEST_ZOOM_LEVEL; i++) {
            ZOOM_FACTORS[i] = zoomFactor * Math.pow(ZOOM_INCREMENT, i);
        }

        // Based on the zoom level, set up the image area.
        // (No need to define centerOfZoom since we're not zooming in to start with.)
        setupImageArea();

        // Whenever the image area's set up, the points need to be
        // recomputed and redrawn.
        getCanvasPoints();
        redrawAllPoints();
    }


    /* Public methods.
     * These are the only methods that need to be referred to as
     * AnnotationToolHelper.methodname. */
    return {

        /* Params:
         * fullHeight, fullWidth, imagePoints, labels, layout */
        init: function(params) {
            var i, j, n;    // Loop variables...

            /*
             * Initialize styling, sizing, and positioning for various elements
             */

            IMAGE_FULL_WIDTH = params.fullWidth;
            IMAGE_FULL_HEIGHT = params.fullHeight;

//            var horizontalSpacePerButton = ANNOTATION_AREA_WIDTH / BUTTONS_PER_ROW;
            // TODO: Compute this properly.
            var horizontalSpacePerButton = 40;

            // LABEL_BUTTON_WIDTH will represent a value that can be passed into jQuery's
            // width() and css('width'), and these jQuery functions deal with
            // inner width + padding + border only.
            // So don't count the button's margins... and subtract another pixel or two
            // to be safe, so that slightly imprecise rendering won't cause an overflow.
            // (Chrome seems a bit more prone to this kind of imprecise rendering, compared
            // to Firefox...)
            LABEL_BUTTON_WIDTH = horizontalSpacePerButton - (
                parseFloat($('#labelButtons button').css('margin-left'))
                    + parseFloat($('#labelButtons button').css('margin-right'))
                    + 2
                );

            var $labelButton;
            for (i = 0; i < params.labels.length; i++) {
                $labelButton = $("#labelButtons button:exactlycontains('{0}')".format(params.labels[i].code));

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
    //            while (parseFloat($labelButton.outerWidth()) > LABEL_BUTTON_WIDTH) {
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
                $labelButton.css('width', LABEL_BUTTON_WIDTH.toString() + "px");
            }

            BUTTON_GRID_MAX_Y = Math.floor(params.labels.length / BUTTONS_PER_ROW);
            BUTTON_GRID_MAX_X = BUTTONS_PER_ROW - 1;

            annotationArea = $("#annotationArea")[0];
            annotationList = $("#annotationList")[0];
            pointsCanvas = $("#pointsCanvas")[0];
            listenerElmt = $("#listenerElmt")[0];
            saveButton = $("#saveButton")[0];

            imageArea = $("#imageArea")[0];

            $(annotationArea).css({
                "background-color": CANVAS_GUTTER_COLOR
            });

            /* Initialization - Labels and label buttons */

            var groupsWithStyles = [];
            var groupStyles = {};
            var nextStyleNumber = 1;

            for (i = 0; i < params.labels.length; i++) {
                var label = params.labels[i];

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
                $labelButton.attr('gridy', Math.floor(i / BUTTONS_PER_ROW));
                $labelButton.attr('gridx', i % BUTTONS_PER_ROW);

                // When you mouseover the button, show the label name in a tooltip.
                $labelButton.attr('title', label.name);

                // Add to an array of available label codes, which will
                // be used for input checking purposes (in label fields).
                labelCodes.push(label.code);

                // Add to a mapping of label codes to names, which will
                // be used to show a label name when you mouse over a
                // label field with a valid code.
                labelCodesToNames[label.code] = label.name;
            }

            $(pointsCanvas).css({
                "left": 0,
                "top": 0,
                "z-index": 1
            });

            /*
             * Initialize and draw annotation points,
             * and initialize some other variables and elements
             */

            // Create a canvas context
            context = pointsCanvas.getContext("2d");

            // Save this fresh context so we can restore it later as needed.
            context.save();

            // Translate the canvas context to compensate for the gutter and the image offset.
            resetCanvas();

            // Initialize point coordinates
            imagePoints = params.imagePoints;
            numOfPoints = imagePoints.length;
            getCanvasPoints();

            $annotationFields = $(annotationList).find('input');
            var $annotationFieldRows = $(annotationList).find('tr');

            // Create arrays that map point numbers to HTML elements.
            // For example, for point 1:
            // annotationFields = form field with point 1's label code
            // annotationFieldRows = table row containing form field 1
            // annotationRobotFields = hidden form element of value true/false saying whether point 1 is robot annotated
            $annotationFieldRows.each( function() {
                var field = $(this).find('input')[0];
                var pointNum = getPointNumOfAnnoField(field);
                var robotField = $('#id_robot_' + pointNum)[0];

                annotationFields[pointNum] = field;
                annotationFieldRows[pointNum] = this;
                annotationRobotFields[pointNum] = robotField;

                if (robotField.value === 'true') {
                    $(this).addClass('robot');
                }
            });

            // Set point annotation statuses,
            // and draw the points
            for (n = 1; n <= numOfPoints; n++) {
                pointContentStates[n] = {'label': undefined, 'robot': undefined};
                pointGraphicStates[n] = STATE_NOTSHOWN;
            }
            // TODO: Confirm whether this is no longer necessary, due to
            // us now initializing robot class rows in an earlier for loop.
//            $annotationFields.each( function() {
//                onPointUpdate(this, 'initialize');
//            });

            Layouts.createLayout(params.layout);

            // Compute sizing of everything.
            resizeElements();

            // Recompute element sizes when the browser window is resized.
            $(window).resize(function() {
                resizeElements();
            });

            // Set the initial point view mode.  This'll trigger a redraw of the points, but that's okay;
            // initialization slowness is a relatively minor worry.
            changePointMode(POINTMODE_ALL);

            // Initialize save button
            $(saveButton).attr('disabled', 'disabled');
            $(saveButton).text('Saved');

            // Initialize all_done state
            Dajaxice.CoralNet.annotations.ajax_is_all_done(
                setAllDoneIndicator,
                {'image_id': $('#id_image_id')[0].value}
            );

            /*
             * Set event handlers
             */

            // Instructions show/hide buttons
            $('#id_button_show_instructions').click(showInstructions);
            $('#id_button_hide_instructions').click(hideInstructions);

            // Mouse button is pressed and un-pressed on the canvas
            $(listenerElmt).mouseup( function(e) {

                var mouseButton = util.identifyMouseButton(e);
                var clickType;

                // Get the click type (in Windows terms)...

                if ((!isMac && e.ctrlKey && mouseButton === "LEFT")
                    || isMac && e.metaKey && mouseButton === "LEFT")
                // Ctrl-click non-Mac OR Cmd-click Mac
                    clickType = "ctrlClick";
                else if (mouseButton === "RIGHT"
                    || (isMac && e.ctrlKey && mouseButton === "LEFT"))
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
                    if (pointViewMode !== POINTMODE_ALL)
                        return;

                    var nearestPoint = getNearestPoint(e);
                    toggle(nearestPoint);
                }

                // Zoom in or out on the image display.
                else if (clickType === "leftClick" || clickType === "rightClick") {

                    // Zoom in.
                    if (clickType === "leftClick") {
                        zoomIn(e);
                    }
                    // Zoom out.
                    else if (clickType === "rightClick") {
                        zoomOut(e);
                    }
                }
            });

            // Disable the context menu on the listener element.
            // The menu just gets in the way while trying to zoom out, etc.
            $(listenerElmt).bind('contextmenu', function(e){
                return false;
            });
            // Same goes for the canvas element, which is sometimes what we end up
            // right clicking on if the image is no longer over that part of the canvas.
            $(pointsCanvas).bind('contextmenu', function(e){
                return false;
            });
            // Also note that the listener element uses CSS to disable
            // double-click-to-select (it makes the image turn blue, which is annoying).

            // Save button is clicked
            $(saveButton).click(function() {
                saveAnnotations();
            });

            // A label button is clicked
            $('#labelButtons').find('button').each( function() {
                $(this).click( function() {
                    // Label the selected points with this button's label code
                    labelSelected($(this).text());
                    // Set the current label button.
                    setCurrentLabelButton(this);
                });
            });

            // Label field gains focus
            $annotationFields.focus(function() {
                var pointNum = getPointNumOfAnnoField(this);
                unselectAll();
                select(pointNum);

                // Shift the center of zoom to the focused point.
                centerOfZoomX = imagePoints[pointNum-1].column;
                centerOfZoomY = imagePoints[pointNum-1].row;

                // If we're zoomed in at all, complete the center-of-zoom-shift process.
                if (zoomLevel > 0) {

                    // Adjust the image and point coordinates.
                    setupImageArea();
                    getCanvasPoints();

                    // Redraw all points.
                    redrawAllPoints();
                }
            });

            // Label field is typed into and changed, and then unfocused.
            // (This does NOT run when a label button changes the label field.)
            $annotationFields.change(function() {
                onLabelFieldTyping(this);
            });

            // Number next to a label field is clicked.
            $(".annotationFormLabel").click(function() {
                var pointNum = parseInt($(this).text());
                toggle(pointNum);
            });

            // A zoom button is clicked.

            $("#zoomInButton").click(function() {
                zoomIn();
            });
            $("#zoomOutButton").click(function() {
                zoomOut();
            });
            $("#zoomFitButton").click(function() {
                zoomFit();
            });

            // A point mode button is clicked.

            $("#pointModeButtonAll").click(function() {
                changePointMode(POINTMODE_ALL);
            });
            $("#pointModeButtonSelected").click(function() {
                changePointMode(POINTMODE_SELECTED);
            });
            $("#pointModeButtonNone").click(function() {
                changePointMode(POINTMODE_NONE);
            });

            // A quick-select button is clicked.

            $("#quickSelectButtonNone").click(function() {
                // Un-select all points.

                unselectAll();
            });
            $("#quickSelectButtonUnannotated").click(function() {
                // Select only unannotated points.

                var unannotatedPoints = [];

                for (var n = 1; n <= numOfPoints; n++) {
                    var row = annotationFieldRows[n];
                    if (!$(row).hasClass('annotated'))
                        unannotatedPoints.push(n);
                }

                unselectAll();
                for (var i = 0; i < unannotatedPoints.length; i++) {
                    select(unannotatedPoints[i])
                }
            });
            $("#quickSelectButtonInvert").click(function() {
                // Invert selections. (selected -> unselected, unselected -> selected)

                var unselectedPoints = [];

                for (var n = 1; n <= numOfPoints; n++) {
                    var row = annotationFieldRows[n];
                    if (!$(row).hasClass('selected'))
                        unselectedPoints.push(n);
                }

                unselectAll();
                for (var i = 0; i < unselectedPoints.length; i++) {
                    select(unselectedPoints[i])
                }
            });

            // Keymap.
            var keymap = [
                ['shift+up', zoomIn, 'all'],
                ['shift+down', zoomOut, 'all'],

                ['return', confirmFieldAndFocusNext, 'field'],
                ['up', focusPrevField, 'field'],
                ['down', focusNextField, 'field'],
                ['ctrl+left', moveCurrentLabelLeft, 'field'],
                ['ctrl+right', moveCurrentLabelRight, 'field'],
                ['ctrl+up', moveCurrentLabelUp, 'field'],
                ['ctrl+down', moveCurrentLabelDown, 'field'],
                ['ctrl', beginKeyboardLabelling, 'field', 'keydown']
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
                    elementsToBind = [$(document), $annotationFields];
                else if (scope === 'field')
                    elementsToBind = [$annotationFields];

                // Add the event listener.
                for (j = 0; j < elementsToBind.length; j++) {
                    elementsToBind[j].bind(keyEvent, key, func);
                }
            }

            // Show/hide certain key instructions depending on whether Mac is the OS.
            if (isMac) {
                $('span.key_mac').show();
                $('span.key_non_mac').hide();
            }
            else {
                $('span.key_non_mac').show();
                $('span.key_mac').hide();
            }
        },

        redrawAllPoints: function() {
            redrawAllPoints();
        }
    }
})();

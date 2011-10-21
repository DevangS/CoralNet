var AnnotationToolHelper = {

    // HTML elements
    annotationArea: null,
    annotationList: null,
    annotationFieldRows: [],
    annotationFields: [],
    annotationRobotFields: [],
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

    drawnPointStates: [],
    STATE_UNANNOTATED: 0,
    STATE_ANNOTATED: 1,
    STATE_SELECTED: 2,
    UNANNOTATED_COLOR: "#FFFF00",
	UNANNOTATED_OUTLINE_COLOR: "#000000",
	ANNOTATED_COLOR: "#8888FF",
    ANNOTATED_OUTLINE_COLOR: "#000000",
	SELECTED_COLOR: "#00FF00",
    SELECTED_OUTLINE_COLOR: "#000000",

    ANNOTATION_TOOL_WIDTH: 980,
    ANNOTATION_TOOL_HEIGHT: 800, // TODO: Make this dynamic according to how many label buttons there are
    ANNOTATION_AREA_WIDTH: 850,
    ANNOTATION_AREA_HEIGHT: 650,

    IMAGE_AREA_WIDTH: null,
    IMAGE_AREA_HEIGHT: null,
    IMAGE_DISPLAY_HEIGHT: null,
    IMAGE_DISPLAY_WIDTH: null,
    IMAGE_FULL_HEIGHT: null,
	IMAGE_FULL_WIDTH: null,

    init: function(fullHeight, fullWidth,
                   imagePoints, labelCodes) {
        var t = this;  // Alias for less typing

        t.IMAGE_AREA_WIDTH = t.ANNOTATION_AREA_WIDTH - (t.CANVAS_GUTTER * 2),
        t.IMAGE_AREA_HEIGHT = t.ANNOTATION_AREA_HEIGHT - (t.CANVAS_GUTTER * 2),

        t.IMAGE_FULL_WIDTH = fullWidth;
        t.IMAGE_FULL_HEIGHT = fullHeight;

        var widthScaleRatio = t.IMAGE_FULL_WIDTH / t.IMAGE_AREA_WIDTH;
        var heightScaleRatio = t.IMAGE_FULL_HEIGHT / t.IMAGE_AREA_HEIGHT;

        // Note that for small images, the scaleDownFactor may be < 1; in that case, the image is scaled up
        var scaleDownFactor = Math.max(widthScaleRatio, heightScaleRatio);
        t.IMAGE_DISPLAY_WIDTH = t.IMAGE_FULL_WIDTH / scaleDownFactor;
        t.IMAGE_DISPLAY_HEIGHT = t.IMAGE_FULL_HEIGHT / scaleDownFactor;
        
        t.annotationArea = $("#annotationArea")[0];
        t.annotationList = $("#annotationList")[0];
        t.coralImage = $("#coralImage")[0];
        t.pointsCanvas = $("#pointsCanvas")[0];
        t.listenerElmt = $("#listenerElmt")[0];
        t.saveButton = $("#saveButton")[0];

        t.labelCodes = labelCodes;

        // Initialize styling for everything

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

        $(t.annotationList).css({
            "height": t.ANNOTATION_AREA_HEIGHT + "px"
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

        var imageLeftOffset = (t.IMAGE_AREA_WIDTH - t.IMAGE_DISPLAY_WIDTH) / 2;
        var imageTopOffset = (t.IMAGE_AREA_HEIGHT - t.IMAGE_DISPLAY_HEIGHT) / 2;

        $(t.coralImage).css({
            "height": t.IMAGE_DISPLAY_HEIGHT + "px",
            "left": imageLeftOffset + "px",
            "top": imageTopOffset + "px",
            "z-index": 0
        });

        // Invisible element that goes over the coral image
        // and listens for mouseclicks.
        // z-index should be above everything else.
        $(t.listenerElmt).css({
            "width": t.IMAGE_DISPLAY_WIDTH + "px",
            "height": t.IMAGE_DISPLAY_HEIGHT + "px",
            "left": imageLeftOffset + "px",
            "top": imageTopOffset + "px",
            "z-index": 100
        });

        // Note that the canvas's width and height elements are different from the
        // canvas style's width and height. We're interested in the canvas width and height,
        // so the canvas contents don't stretch.
        t.pointsCanvas.width = t.ANNOTATION_AREA_WIDTH;
        t.pointsCanvas.height = t.ANNOTATION_AREA_HEIGHT;
        $(t.pointsCanvas).css({
            "left": 0,
		    "top": 0,
            "z-index": 1
        });

		t.context = t.pointsCanvas.getContext("2d");

        // Be able to specify all x,y coordinates in (scaled) image coordinates,
        // instead of the coordinates of the entire canvas (which includes the gutter).
        t.context.translate(t.CANVAS_GUTTER + imageLeftOffset,
                            t.CANVAS_GUTTER + imageTopOffset);

		// Mouse button is pressed and un-pressed
		$(t.listenerElmt).mouseup( function(e) {
            // TODO: This shouldn't happen if the points display is toggled off
            if(e.ctrlKey) {
                var nearestPoint = AnnotationToolHelper.getNearestPoint(e);
                AnnotationToolHelper.toggle([nearestPoint]);
            }
        });

        // Initialize points
        t.imagePoints = imagePoints;
        t.numOfPoints = imagePoints.length;
        t.getCanvasPoints();
        t.drawAllPoints();

        // Initialize save button
        $(t.saveButton).removeAttr('disabled');  // Firefox might cache this attribute between page loads
        $(t.saveButton).click(function() {
            AnnotationToolHelper.saveAnnotations();
        });

        // Label button handler
        $('#labelButtons').find('button').each( function() {
            $(this).click( function() {
                // The button's text is the label code
                AnnotationToolHelper.labelSelected($(this).text());
            });
        });

        var annotationFieldsJQ = $(t.annotationList).find('input');
        var annotationFieldRowsJQ = $(t.annotationList).find('tr');

        annotationFieldRowsJQ.each( function() {
            var field = $(this).find('input')[0];
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(field);
            var robotField = $('#id_robot_' + pointNum)[0];

            // Create arrays that map point numbers to HTML elements:
            // annotationFields = form field with name "label_1"
            // annotationFieldRows = form row containing field 1
            // annotationRobotFields = hidden form element of value true/false saying whether the field is robot annotated
            AnnotationToolHelper.annotationFieldRows[pointNum] = this;
            AnnotationToolHelper.annotationFields[pointNum] = field;
            AnnotationToolHelper.annotationRobotFields[pointNum] = robotField;

            // Add robot-annotation styling
            if (robotField.value === "true") {
                $(this).addClass('robot');
            }
        });

        annotationFieldsJQ.each( function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.updatePointStyle(pointNum);
        });

        // Runs when label field gains focus
        annotationFieldsJQ.focus(function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.unselectAll();
            AnnotationToolHelper.select([pointNum]);
        });

        // Runs when label field is typed into and changed, and then unfocused
        annotationFieldsJQ.change(function() {
            AnnotationToolHelper.onLabelFieldChange(this);
        });

        // Runs when label field is focused and a keyboard key is released
        annotationFieldsJQ.keyup(function(e) {
            var ENTER = 13;
            
            if(e.keyCode === ENTER) {
                // Un-robot the current field
                var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
                AnnotationToolHelper.unrobot(pointNum);

                // Switch focus to next point's field
                AnnotationToolHelper.focusNextField(pointNum);
            }
        });

        // Click the number next to a form field to select/unselect that point
        $(".annotationFormLabel").click(function() {
            //var pointNum = parseInt($(this).children(".annotationFormLabel").text());
            var pointNum = parseInt($(this).text());
            AnnotationToolHelper.toggle([pointNum]);
        });
    },

    updatePointStyle: function(pointNum) {
        var t = this;

        var field = t.annotationFields[pointNum];
        var row = t.annotationFieldRows[pointNum];
        var robotField = t.annotationRobotFields[pointNum];
        var labelCode = field.value;

        // Error: label is not empty string, and not in the labelset
        if (labelCode !== '' && t.labelCodes.indexOf(labelCode) === -1) {
            // Error styling
            $(field).attr('title', 'Label not in labelset');
            $(row).addClass('error');
            $(row).removeClass('annotated');
        }
        else {
            // Label is empty or robot annotated
            if (labelCode === '' || robotField.value === 'true') {
                $(row).removeClass('annotated');
            }
            // Label is in the labelset
            else {
                $(row).addClass('annotated');
            }

            // Remove error styling, if any
            if ($(row).hasClass('error')) {
                $(row).removeClass('error');
            }
            if ($(field).attr('title')) {
                $(field).removeAttr('title');
            }
        }

        this.redrawPoint(pointNum);
    },

    onLabelFieldChange: function(field) {
        var t = this;
        var pointNum = t.getPointNumOfAnnoField(field);

        t.updatePointStyle(pointNum);

        // No longer a robot annotation if we've changed it
        t.unrobot(pointNum);

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

    focusNextField: function(pointNum) {
        var lastPoint = this.numOfPoints;
        if (pointNum !== lastPoint) {
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

        var x = imageElmtX * (t.IMAGE_FULL_WIDTH / t.IMAGE_DISPLAY_WIDTH);
        var y = imageElmtY * (t.IMAGE_FULL_HEIGHT / t.IMAGE_DISPLAY_HEIGHT);

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
            var xDiff = x - t.imagePoints[i].column;
            var yDiff = y - t.imagePoints[i].row;
            var distance = Math.sqrt((xDiff*xDiff) + (yDiff*yDiff));

            if (distance < minDistance) {
                minDistance = distance;
                closestPoint = t.imagePoints[i].point_number;
            }
        }

        return closestPoint;
    },

    /*
    To get the points in canvas coordinates,
    scale the coordinates to match the scaling of the image.
     */
    getCanvasPoints: function() {
        var t = this;

        // Apparently JavaScript uses decimal division by default, which we want in this case.
        var scaleFactor = t.IMAGE_DISPLAY_WIDTH / t.IMAGE_FULL_WIDTH;

        for (var i = 0; i < t.imagePoints.length; i++) {

            t.canvasPoints[t.imagePoints[i].point_number] = {
                num: t.imagePoints[i].point_number,
                row: t.imagePoints[i].row * scaleFactor,
                col: t.imagePoints[i].column * scaleFactor
            };
        }
    },

    drawAllPoints: function() {
        var t = this;
        
        for (var pointNum in t.canvasPoints) {

            // hasOwnProperty() is a safety check that's useful when using for...in
            if (t.canvasPoints.hasOwnProperty(pointNum)) {

                t.drawnPointStates[pointNum] = t.STATE_UNANNOTATED;
                t.drawPointUnannotated(pointNum);
            }
        }
    },

    drawCanvasPoint: function(pointNum, color, outlineColor) {
        var canvasPoint = this.canvasPoints[pointNum];

        this.drawPointSymbol(canvasPoint.col, canvasPoint.row,
                             color);
        this.drawPointNumber(canvasPoint.num.toString(), canvasPoint.col, canvasPoint.row,
                             color, outlineColor);
    },

    drawPointUnannotated: function(pointNum) {
        this.drawCanvasPoint(pointNum, this.UNANNOTATED_COLOR, this.UNANNOTATED_OUTLINE_COLOR);
    },
    drawPointAnnotated: function(pointNum) {
        this.drawCanvasPoint(pointNum, this.ANNOTATED_COLOR, this.ANNOTATED_OUTLINE_COLOR);
    },
    drawPointSelected: function(pointNum) {
        this.drawCanvasPoint(pointNum, this.SELECTED_COLOR, this.SELECTED_OUTLINE_COLOR);
    },

    redrawPoint: function(pointNum) {
        var t = this;
        var row = this.annotationFieldRows[pointNum];
        var newState;

        if ($(row).hasClass('selected'))
            newState = t.STATE_SELECTED;
        else if ($(row).hasClass('annotated'))
            newState = t.STATE_ANNOTATED;
        else
            newState = t.STATE_UNANNOTATED;

        var oldState = t.drawnPointStates[pointNum];

        // Only redraw when we have to
        if (oldState !== newState) {
            t.drawnPointStates[pointNum] = newState;

            if (newState === t.STATE_SELECTED)
                t.drawPointSelected(pointNum);
            else if (newState === t.STATE_ANNOTATED)
                t.drawPointAnnotated(pointNum);
            else if (newState === t.STATE_UNANNOTATED)
                t.drawPointUnannotated(pointNum);
        }
    },

    /*
    Draw an annotation point (the crosshair, circle, or whatever)
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
	},

    saveAnnotations: function() {
        $(this.saveButton).attr('disabled', 'disabled');
        $(this.saveButton).text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_annotations(
            this.ajaxStatusToSaved,    // JS callback that the ajax.py method returns to.
            {'annotationForm': $("#annotationForm").serializeArray()}    // Args to the ajax.py method.
        );
    },

    // AJAX callback: cannot use "this" to refer to AnnotationToolHelper
    ajaxStatusToSaved: function(errorMsg) {
        if (errorMsg) {
            AnnotationToolHelper.setSaveButtonText("Error");
            // TODO: Handle error cases more elegantly?  Alerts are lame.
            // Though, these errors aren't really supposed to happen unless hackery is involved.
            alert("Sorry, an error occurred when trying to save your annotations:\n{0}".format(errorMsg));
        }
        else {
            AnnotationToolHelper.setSaveButtonText("Saved");
        }
    },

    setSaveButtonText: function(buttonText) {
        $(this.saveButton).text(buttonText);
    },

    getPointNumOfAnnoField: function(annoField) {
        // Assuming the annotation field's name attribute is "label_<pointnumber>"
        return parseInt(annoField.name.substring(6));
    },

    getSelectedFieldsJQ: function() {
        return $(this.annotationList).find('tr.selected').find('input');
    },

    select: function(points) {

        for (var i = 0; i < points.length; i++) {
            $(this.annotationFieldRows[points[i]]).addClass('selected');
            this.redrawPoint(points[i]);
        }
    },

    unselect: function(points) {

        for (var i = 0; i < points.length; i++) {
            $(this.annotationFieldRows[points[i]]).removeClass('selected');
            this.redrawPoint(points[i]);
        }
    },

    toggle: function(points) {
        for (var i = 0; i < points.length; i++) {
            if ($(this.annotationFieldRows[points[i]]).hasClass('selected'))
                this.unselect([points[i]]);
            else
                this.select([points[i]]);
        }
    },

    unrobot: function(pointNum) {
        var robotField = this.annotationRobotFields[pointNum];

        if (robotField.value === "true") {
            robotField.value = "false";

            var row = this.annotationFieldRows[pointNum];
            $(row).removeClass('robot');

            this.updatePointStyle(pointNum);
        }
    },

    unselectAll: function() {
        this.getSelectedFieldsJQ().each( function() {
            var pointNum = AnnotationToolHelper.getPointNumOfAnnoField(this);
            AnnotationToolHelper.unselect([pointNum]);
        });
    },

    labelSelected: function(labelCode) {
        this.getSelectedFieldsJQ().each( function() {
            var oldValue = this.value;
            this.value = labelCode;
            
            if (oldValue !== this.value) {
                AnnotationToolHelper.onLabelFieldChange(this);
            }
        });
    }
};

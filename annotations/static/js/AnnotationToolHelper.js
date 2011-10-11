var AnnotationToolHelper = {

    annotationArea: null,
    annotationList: null,
    coralImage: null,
    pointsCanvas: null,

	context: null,
    points: null, imagePoints: null,
	POINT_RADIUS: 16,
    NUMBER_FONT: "bold 24px sans-serif",

    // Border where the canvas is drawn, but the coral image is not.
    // This is used to fully show the points that are located near the edge of the image.
	CANVAS_GUTTER: 25,
    CANVAS_GUTTER_COLOR: "#888888",

	// Color for unselected points (point selection to be implemented)
    UNANNOTATED_COLOR: "#FFFF00",
	UNANNOTATED_COLOR_OUTLINE: "#000000",
	ANNOTATED_COLOR: "#FF0000",
	SELECTED_COLOR: "#888888",

	// We should automatically match the coral image's width/height ratio and support up to a maximum width/height.
	IMAGE_DISPLAY_HEIGHT: null,
	IMAGE_DISPLAY_WIDTH: null,
    IMAGE_FULL_HEIGHT: null,
	IMAGE_FULL_WIDTH: null,

    init: function(initialHeight, initialWidth,
                   fullHeight, fullWidth,
                   points) {
        var t = this;  // Alias for less typing

        t.IMAGE_DISPLAY_HEIGHT = initialHeight;
        t.IMAGE_DISPLAY_WIDTH = initialWidth;
        t.IMAGE_FULL_HEIGHT = fullHeight;
        t.IMAGE_FULL_WIDTH = fullWidth;

        t.annotationArea = $("#annotationArea")[0];
        t.annotationList = $("#annotationList")[0];
        t.coralImage = $("#coralImage")[0];
        t.pointsCanvas = $("#pointsCanvas")[0];
        t.saveButton = $("#saveButton")[0];

        // Initialize styling for everything

        $(t.annotationArea).css({
            "width": t.IMAGE_DISPLAY_WIDTH + (t.CANVAS_GUTTER * 2),
            "height": t.IMAGE_DISPLAY_HEIGHT + (t.CANVAS_GUTTER * 2),
            "background-color": t.CANVAS_GUTTER_COLOR
        });

        $(t.annotationList).css({
            "height": $(t.annotationArea).css("height")
        });

        $(t.coralImage).css({
            "height": t.IMAGE_DISPLAY_HEIGHT + "px",
            "left": t.CANVAS_GUTTER + "px",
            "top": t.CANVAS_GUTTER + "px",
            "z-index": 0
        });

        $(t.pointsCanvas).css({
            "left": 0,
		    "top": 0,
            "z-index": 1
        });

        // Note that the canvas's width and height elements are different from the
        // canvas style's width and height. We're interested in the canvas width and height,
        // so the canvas contents don't stretch.
        t.pointsCanvas.width = t.IMAGE_DISPLAY_WIDTH + (t.CANVAS_GUTTER * 2);
        t.pointsCanvas.height = t.IMAGE_DISPLAY_HEIGHT + (t.CANVAS_GUTTER * 2);

		t.context = t.pointsCanvas.getContext("2d");

        // Be able to specify all x,y coordinates in (scaled) image coordinates,
        // instead of the coordinates of the entire canvas (which includes the gutter).
        t.context.translate(t.CANVAS_GUTTER, t.CANVAS_GUTTER);

		// Mouse button is pressed and un-pressed
		t.pointsCanvas.addEventListener("mouseup", t.onMouseup, false);

        // Initialize points
        t.imagePoints = points;
        t.points = new Array(points.length);
        t.getCanvasPoints();
        t.drawPoints();

        // Initialize save button
        $(t.saveButton).removeAttr('disabled');  // Firefox might cache this attribute between page loads
        $(t.saveButton).click(function() {
            t.saveAnnotations();
        });
    },

    /* Get the mouse position in the canvas element:
	(mouse's position in the HTML document) minus
	(canvas element's position in the HTML document).
	The method for getting the mouse position in the HTML document
	varies depending on the browser: can be based on pageX/Y or clientX/Y. */
	getMousePosition: function(e) {
	    var x;
		var y;
		if (e.pageX != undefined && e.pageY != undefined) {
			x = e.pageX;
			y = e.pageY;
		}
		else {
			x = e.clientX + document.body.scrollLeft +
					document.documentElement.scrollLeft;
			y = e.clientY + document.body.scrollTop +
					document.documentElement.scrollTop;
		}

		x -= this.pointsCanvas.offsetLeft;
		y -= this.pointsCanvas.offsetTop;

	    return [x,y];  // Return an array
	},

    /*
    TODO: Implement point-selection and other mouseclick functionality here.
     */
	onMouseup: function(e) {

	},

    /*
    To get the points in canvas coordinates,
    scale the coordinates to match the scaling of the image.
     */
    getCanvasPoints: function() {
        var t = this;

        // Apparently JavaScript uses decimal division by default, which we want in this case.
        var scaleFactor = t.IMAGE_DISPLAY_WIDTH / t.IMAGE_FULL_WIDTH;

        for (var i = 0; i < t.points.length; i++) {
            t.points[i] = {
                num: t.imagePoints[i].point_number,
                row: t.imagePoints[i].row * scaleFactor,
                col: t.imagePoints[i].column * scaleFactor
            };
        }
    },

    drawPoints: function() {
        var t = this;
        
        for (var i = 0; i < t.points.length; i++) {
            t.drawAnnotationPoint(t.points[i].col, t.points[i].row);
            t.drawNumber(t.points[i].num.toString(), t.points[i].col, t.points[i].row);
        }
    },

    /*
    Draw an annotation point (the crosshair, circle, etc.)
    which is centered at x,y.
     */
    drawAnnotationPoint: function(x,y) {
        var t = this;

		// Adjust x and y by 0.5 so that straight lines are centered
		// at the halfway point of a pixel, not on a pixel boundary.
		// This ensures that 1-pixel-wide lines are really 1 pixel wide,
		// instead of 2 pixels wide.
        // NOTE: This only applies to odd-width lines.
		x = x+0.5;
		y = y+0.5;

        t.context.strokeStyle = t.UNANNOTATED_COLOR;
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
	drawNumber: function(num, x, y) {
        var t = this;

		t.context.textBaseline = "bottom";
		t.context.textAlign = "left";
		t.context.fillStyle = t.UNANNOTATED_COLOR;
        t.context.strokeStyle = t.UNANNOTATED_COLOR_OUTLINE;
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

		if (t.pointsCanvas.style.visibility == 'hidden')
			t.pointsCanvas.style.visibility = 'visible';
		else    // 'visible' or ''
			t.pointsCanvas.style.visibility = 'hidden';
	},

    saveAnnotations: function() {
        $(this.saveButton).attr('disabled', 'disabled');
        $(this.saveButton).text("Now saving...");
        Dajaxice.CoralNet.annotations.ajax_save_annotations(
            this.ajaxStatusToSaved,    // JS callback that the ajax.py method returns to.
            {'annotations': []}    // Args to the ajax.py method.
        );
    },

    // AJAX callback: cannot use "this" to refer to AnnotationToolHelper
    ajaxStatusToSaved: function() {
        AnnotationToolHelper.statusToSaved();
    },

    statusToSaved: function() {
        $(this.saveButton).text("Saved");
    }
};

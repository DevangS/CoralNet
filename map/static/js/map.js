var CNMap = (function() {

    var map = null;
    var markers = [];
    var sources = [];

    var markerInfoElmt = null;

    var $markerInfoName = null;
    var $markerInfoDescription = null;
    var $markerInfoNumOfImages = null;
    var $markerInfoCoordinates = null;

    var infoWindow = null;

    function showMarkerDialog(source, sourceLatLon) {

        if (infoWindow === null) {
            infoWindow = new google.maps.InfoWindow();
        }

        infoWindow.setPosition(sourceLatLon);

        // Source name, with a link to the source if provided
        $markerInfoName.empty();
        var $boldName = $('<strong>');
        $boldName.text(source.name);

        if (source.url) {

            var $sourceLink = $('<a>');
            $sourceLink.append($boldName);
            $sourceLink.attr('href', source.url);

            $markerInfoName.append($sourceLink);
        }
        else {
            $markerInfoName.append($boldName);
        }

        $markerInfoDescription.text(source.description);
        $markerInfoNumOfImages.text("Number of images: {0}".format(source.num_of_images));
        $markerInfoCoordinates.text("Lat/Lon: {0}, {1}".format(source.latitude, source.longitude));

        infoWindow.setContent(markerInfoElmt);

        infoWindow.open(map);
    }

    return {

        init: function(params) {

            console.log(params.mapSources.length);

            if (!google) {
                console.log("Couldn't load the Google API.");
                return;
            }

            // https://developers.google.com/maps/documentation/javascript/tutorial#MapOptions
            var mapOptions = {

                center: new google.maps.LatLng(0.0, 0.0),

                zoom: 2,

                mapTypeId: google.maps.MapTypeId.SATELLITE
            };

            map = new google.maps.Map(
                document.getElementById("map-canvas"),
                mapOptions
            );

            var markerInfoElmtId = 'marker-info';
            markerInfoElmt = document.getElementById(markerInfoElmtId);

            $markerInfoName = $('#{0} .name'.format(markerInfoElmtId));
            $markerInfoDescription = $('#{0} .description'.format(markerInfoElmtId));
            $markerInfoNumOfImages = $('#{0} .num-of-images'.format(markerInfoElmtId));
            $markerInfoCoordinates = $('#{0} .coordinates'.format(markerInfoElmtId));


            var i;

            for (i = 0; i < params.mapSources.length; i++) {

                var source = params.mapSources[i];
                var sourceLatLon = new google.maps.LatLng(source.latitude, source.longitude);
                var markerColor = source.color;
		var markerSize = null
		

		if (source.num_of_images < 5) {
		    markerSize = new google.maps.Size(15, 24);
		}
		else if(source.num_of_images < 50){
		    markerSize = new google.maps.Size(20, 32);
		}
		else if(source.num_of_images < 500){
		    markerSize = new google.maps.Size(25, 40);		
		}
		else {
		    markerSize = new google.maps.Size(30, 48);
		}

                var marker = new google.maps.Marker({
                    position: sourceLatLon,
		    draggable:true,
		    icon: new google.maps.MarkerImage(
                        'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|' + markerColor, 
                        null,
		        null,
		        null,
		        markerSize
                    )
                });

                google.maps.event.addListener(marker, 'click', showMarkerDialog.curry(source, sourceLatLon));
                sources.push(source);
                markers.push(marker);
            }
            var markerCluster = new MarkerClusterer(map, markers,{maxZoom : 18});

        }
    }
})();

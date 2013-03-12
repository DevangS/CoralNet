var CNMap = (function() {

    var map;
    var markers = [];

    function showMarkerDialog() {

        $("#marker-info").dialog(
            createModalWindowOptions({
                title: "Marker information"
            })
        );
    }

    return {

        init: function() {

            // https://developers.google.com/maps/documentation/javascript/tutorial#MapOptions
            var mapOptions = {
                center: new google.maps.LatLng(-34.397, 150.644),
                zoom: 2,
                mapTypeId: google.maps.MapTypeId.SATELLITE
            };
            map = new google.maps.Map(
                document.getElementById("map-canvas"),
                mapOptions
            );

            markers.push(new google.maps.Marker({
                position: new google.maps.LatLng(-34.397, 150.644),
                map: map,
                title:"Hello World!"
            }));
            markers.push(new google.maps.Marker({
                position: new google.maps.LatLng(-54.397, 120.644),
                map: map,
                title:"Hello World!"
            }));

            var i;
            for (i = 0; i < markers.length; i++) {
                google.maps.event.addListener(markers[i], 'click', showMarkerDialog);
            }
        }
    }
})();
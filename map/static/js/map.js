var Map = (function() {

    var map;

    return {

        init: function() {
            var mapOptions = {
                center: new google.maps.LatLng(-34.397, 150.644),
                zoom: 8,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            };
            map = new google.maps.Map(
                document.getElementById("map-canvas"),
                mapOptions
            );
        }
    }
})();
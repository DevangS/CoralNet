var PointGenFormHelper = {

    /*
    Depending on the point generation type that was picked, different
    fields are going to be relevant or not. Identify the relevant fields
    and hide the rest of the fields (by setting style.display = 'none').
    */
    showOnlyRelevantFields: function() {
        var point_generation_type = document.getElementById("id_point_generation_type");
        var simple_number_of_points_wrapper = document.getElementById("id_simple_number_of_points_wrapper");
        var number_of_cell_rows_wrapper = document.getElementById("id_number_of_cell_rows_wrapper");
        var number_of_cell_columns_wrapper = document.getElementById("id_number_of_cell_columns_wrapper");
        var stratified_points_per_cell_wrapper = document.getElementById("id_stratified_points_per_cell_wrapper");

        var fields = [simple_number_of_points_wrapper,
                  number_of_cell_rows_wrapper,
                  number_of_cell_columns_wrapper,
                  stratified_points_per_cell_wrapper];

        // Hide or show each field as appropriate.
        // First, hide all fields...
        var i;
        for (i = 0; i < fields.length; i++) {
            fields[i].style.display = 'none';
        }

        // Then, show the relevant fields
        // TODO: Get rid of nasty magic values
        var fields_to_show = [];

        if (point_generation_type.value == "m") {
            fields_to_show.push(simple_number_of_points_wrapper);
        }
        else if (point_generation_type.value == "t") {
            fields_to_show.push(number_of_cell_rows_wrapper);
            fields_to_show.push(number_of_cell_columns_wrapper);
            fields_to_show.push(stratified_points_per_cell_wrapper);
        }
        else if (point_generation_type.value == "u") {
            fields_to_show.push(number_of_cell_rows_wrapper);
            fields_to_show.push(number_of_cell_columns_wrapper);
        }

        for (i = 0; i < fields_to_show.length; i++) {
            fields_to_show[i].style.display = 'block';
        }
    }
};

util.addLoadEvent(PointGenFormHelper.showOnlyRelevantFields);

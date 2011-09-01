import datetime
import math, random

# This file contains general utility methods that do NOT directly reference model classes.
# (models.py may use these utility methods, so having this file reference model classes
# would create a circular import dependency.)

class PointGen():
    """
    Utility class for point generation, including:
    - Generating points.
    - Going between human-readable format and DB-friendly encoding
    of the point generation method.

    Examples of the DB-friendly encoding:
    m_80 -> Simple random, 80 points
    t_8_6_4 -> Stratified random, 8x6 cells, 4 points per cell
    u_10_8 -> Uniform grid, 10x8 grid
    i -> Imported
    """
    class Types():
        SIMPLE = 'm'
        SIMPLE_VERBOSE = 'Simple Random (Each point position is random within the entire image)'
        STRATIFIED = 't'
        STRATIFIED_VERBOSE = 'Stratified Random (Each point position is random within a cell of the image)'
        UNIFORM = 'u'
        UNIFORM_VERBOSE = 'Uniform Grid'
        IMPORTED = 'i'
        IMPORTED_VERBOSE = 'Imported'

    @staticmethod
    def args_to_db_format(point_generation_type=None,
                          simple_number_of_points=None,
                          number_of_cell_rows=None,
                          number_of_cell_columns=None,
                          stratified_points_per_cell=None):

        # Make sure we have strings, not ints
        simple_number_of_points = str(simple_number_of_points)
        number_of_cell_rows = str(number_of_cell_rows)
        number_of_cell_columns = str(number_of_cell_columns)
        stratified_points_per_cell = str(stratified_points_per_cell)

        if point_generation_type == PointGen.Types.SIMPLE:
            return '_'.join([
                point_generation_type,
                simple_number_of_points,
            ])
        elif point_generation_type == PointGen.Types.STRATIFIED:
            return '_'.join([
                point_generation_type,
                number_of_cell_rows,
                number_of_cell_columns,
                stratified_points_per_cell,
            ])
        elif point_generation_type == PointGen.Types.UNIFORM:
            return '_'.join([
                point_generation_type,
                number_of_cell_rows,
                number_of_cell_columns,
            ])

    @staticmethod
    def args_to_readable_format(point_generation_type=None,
                                simple_number_of_points=None,
                                number_of_cell_rows=None,
                                number_of_cell_columns=None,
                                stratified_points_per_cell=None):
        if point_generation_type == PointGen.Types.SIMPLE:
            return "Simple random, %s points" % simple_number_of_points
        elif point_generation_type == PointGen.Types.STRATIFIED:
            return "Stratified random, %s rows x %s columns of cells, %s points per cell (total of %s points)" % (
                   number_of_cell_rows, number_of_cell_columns, stratified_points_per_cell,
                   number_of_cell_rows*number_of_cell_columns*stratified_points_per_cell
                )
        elif point_generation_type == PointGen.Types.UNIFORM:
            return "Uniform grid, %s rows x %s columns (total of %s points)" % (
                   number_of_cell_rows, number_of_cell_columns,
                   number_of_cell_rows*number_of_cell_columns
                )

    @staticmethod
    def db_to_args_format(db_format):
        tokens = db_format.split('_')

        if tokens[0] == PointGen.Types.SIMPLE:
            return dict(point_generation_type=tokens[0],
                        simple_number_of_points=int(tokens[1]))

        elif tokens[0] == PointGen.Types.STRATIFIED:
            return dict(point_generation_type=tokens[0],
                        number_of_cell_rows=int(tokens[1]),
                        number_of_cell_columns=int(tokens[2]),
                        stratified_points_per_cell=int(tokens[3]))

        elif tokens[0] == PointGen.Types.UNIFORM:
            return dict(point_generation_type=tokens[0],
                        number_of_cell_rows=int(tokens[1]),
                        number_of_cell_columns=int(tokens[2]))

    @staticmethod
    def db_to_readable_format(db_format):
        return PointGen.args_to_readable_format(**PointGen.db_to_args_format(db_format))

    @staticmethod
    def generate_points(img,
                        point_generation_type=None,
                        simple_number_of_points=None,
                        number_of_cell_rows=None,
                        number_of_cell_columns=None,
                        stratified_points_per_cell=None
    ):
        """
        Generate points for this image. This doesn't actually
        insert anything in the database; it just generates the
        row, column for each point number.

        Returns the points as a list of dicts; each dict
        represents a point, and has keys "row", "column",
        and "point_number".
        """

        points = []

        if point_generation_type == PointGen.Types.SIMPLE:

            simple_random_points = []

            for i in range(simple_number_of_points):
                row = int(math.floor(random.random()*(img.original_height+1)))  # 0 to img.original_height
                column = int(math.floor(random.random()*(img.original_width+1)))  # 0 to img.original_width

                simple_random_points.append({'row': row, 'column': column})

            # For ease of finding consecutive points, impose cell rows and cols, then
            # make consecutive points fill the cells one by one.
            NUM_OF_CELL_ROWS = 5
            NUM_OF_CELL_COLUMNS = 5
            cell = {}
            for r in range(NUM_OF_CELL_ROWS):
                cell[r] = {}
                for c in range(NUM_OF_CELL_COLUMNS):
                    cell[r][c] = []

            for p in simple_random_points:
                r = int(math.floor( (p['row'] * NUM_OF_CELL_ROWS) / (img.original_height+1) ))
                c = int(math.floor( (p['column'] * NUM_OF_CELL_COLUMNS) / (img.original_width+1) ))
                if r >= 5 or c >= 5:
                    print r, c
                cell[r][c].append(p)

            point_num = 1
            for r in range(NUM_OF_CELL_ROWS):
                for c in range(NUM_OF_CELL_COLUMNS):
                    for p in cell[r][c]:

                        points.append(dict(row=p['row'], column=p['column'], point_number=point_num))
                        point_num += 1

        elif point_generation_type == PointGen.Types.STRATIFIED:

            point_num = 1

            for row_num in range(0, number_of_cell_rows):
                row_min = (row_num * img.original_height) / number_of_cell_rows
                row_max = (((row_num+1) * img.original_height) / number_of_cell_rows) - 1

                for col_num in range(0, number_of_cell_columns):
                    col_min = (col_num * img.original_width) / number_of_cell_columns
                    col_max = (((col_num+1) * img.original_width) / number_of_cell_columns) - 1

                    for cell_point_num in range(0, stratified_points_per_cell):
                        row = row_min + int(math.floor(random.random()*(row_max - row_min +1)))  # row_min to row_max
                        column = col_min + int(math.floor(random.random()*(col_max - col_min +1)))  # col_min to col_max

                        points.append(dict(row=row, column=column, point_number=point_num))
                        point_num += 1

        elif point_generation_type == PointGen.Types.UNIFORM:

            point_num = 1

            for row_num in range(0, number_of_cell_rows):
                row_mid = ((row_num+0.5) * img.original_height) / number_of_cell_rows

                for col_num in range(0, number_of_cell_columns):
                    col_mid = ((col_num+0.5) * img.original_width) / number_of_cell_columns

                    points.append(dict(row=row_mid, column=col_mid, point_number=point_num))
                    point_num += 1

        return points


def filename_to_metadata(filenameWithoutExt, source):
    """
    Takes an image filename without the extension.

    Returns a dict of the location values, and the photo year, month, and day.
    {'values': ['Shore3', 'Reef 5', 'Loc10'],
     'year': 2007, 'month': 8, 'day': 15}
    """

    metadataDict = dict()

    parseError = ValueError('Could not properly extract metadata from the filename "%s".' % filenameWithoutExt)
    dateError = ValueError('Invalid date format or values.')
    numOfKeys = source.num_of_keys()

    # value1_value2_..._YYYY-MM-DD
    tokensFormat = ['value'+str(i) for i in range(1, numOfKeys+1)]
    tokensFormat += ['date']
    numTokensExpected = len(tokensFormat)

    # Make a list of the metadata 'tokens' from the filename
    tokens = filenameWithoutExt.split('_')
    if len(tokens) != numTokensExpected:
        raise parseError

    # Encode the filename data into a dictionary: {'value1':'Shore2', 'date':'2008-12-18', ...}
    filenameData = dict(zip(tokensFormat, tokens))

    valueList = [filenameData['value'+str(i)] for i in range(1, numOfKeys+1)]
    dateToken = filenameData['date']

    try:
        year, month, day = dateToken.split("-")
    except ValueError:
        raise dateError
    # YYYYMMDD parsing:
#    if len(dateToken) != 8:
#        raise dateError
#    year, month, day = dateToken[:4], dateToken[4:6], dateToken[6:8]

    try:
        datetime.date(int(year), int(month), int(day))
    except ValueError:
        # Either non-integer date params, or date params are
        # out of valid range (e.g. month 13)
        raise dateError

    metadataDict['values'] = valueList

    metadataDict['year'] = year
    metadataDict['month'] = month
    metadataDict['day'] = day

    return metadataDict


def metadata_to_filename(values=None,
                         year=None, month=None, day=None):
    """
    Takes metadata arguments and returns a filename (without the extension)
    which would generate these arguments.
    """

    dateStr = '-'.join([year, month, day])
    filename = '_'.join(values + [dateStr])

    return filename

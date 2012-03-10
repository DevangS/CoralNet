# Utility methods used by models.py.
#
# These methods should not import anything from models.py.  Otherwise,
# there will be circular import dependencies.  Utility functions
# that use models.py should go in the general utility functions
# file, utils.py.
from decimal import Decimal
from exceptions import ValueError
import math


class AnnotationAreaUtils():

    # Percentages are decimals.
    # Pixels are integers.
    # Database (db) format:
    #     percentages - "5.7;94.5;10;90"
    #     pixels - "125,1880,80,1600"

    IMPORTED_STR = 'imported'
    IMPORTED_DISPLAY = "(Imported points; not specified)"
    TYPE_PERCENTAGES = 'percentages'
    TYPE_PIXELS = 'pixels'
    TYPE_IMPORTED = 'imported'

    @staticmethod
    def percentages_to_db_format(min_x, max_x, min_y, max_y):
        return ';'.join([
            str(min_x), str(max_x), str(min_y), str(max_y)
        ])

    @staticmethod
    def pixels_to_db_format(min_x, max_x, min_y, max_y):
        return ','.join([
            str(min_x), str(max_x), str(min_y), str(max_y)
        ])

    @staticmethod
    def db_format_to_numbers(s):
        d = dict()
        if s == AnnotationAreaUtils.IMPORTED_STR:
            d['type'] = AnnotationAreaUtils.TYPE_IMPORTED
        elif s.find(';') != -1:
            # percentages
            d['min_x'], d['max_x'], d['min_y'], d['max_y'] = [Decimal(dec_str) for dec_str in s.split(';')]
            d['type'] = AnnotationAreaUtils.TYPE_PERCENTAGES
        elif s.find(',') != -1:
            # pixels
            d['min_x'], d['max_x'], d['min_y'], d['max_y'] = [int(int_str) for int_str in s.split(',')]
            d['type'] = AnnotationAreaUtils.TYPE_PIXELS
        else:
            raise ValueError("Annotation area isn't in a valid DB format.")
        return d

    @staticmethod
    def db_format_to_percentages(s):
        d = AnnotationAreaUtils.db_format_to_numbers(s)
        if d['type'] == AnnotationAreaUtils.TYPE_PERCENTAGES:
            return d
        else:
            raise ValueError("Annotation area type is '{0}' expected {1}.".format(
                d['type'], AnnotationAreaUtils.TYPE_PERCENTAGES))

    @staticmethod
    def db_format_to_display(s):
        d = AnnotationAreaUtils.db_format_to_numbers(s)

        if d['type'] == AnnotationAreaUtils.TYPE_IMPORTED:
            return AnnotationAreaUtils.IMPORTED_DISPLAY
        elif d['type'] == AnnotationAreaUtils.TYPE_PERCENTAGES:
            return "X: {0} - {1}% / Y: {2} - {3}%".format(
                d['min_x'], d['max_x'], d['min_y'], d['max_y']
            )
        elif d['type'] == AnnotationAreaUtils.TYPE_PIXELS:
            return "X: {0} - {1} pixels / Y: {2} - {3} pixels".format(
                d['min_x'], d['max_x'], d['min_y'], d['max_y']
            )

    @staticmethod
    def percentages_to_pixels(min_x, max_x, min_y, max_y, width, height):
        d = dict()

        # The percentages are Decimals.
        # Decimal / int = Decimal, and Decimal * int = Decimal
        d['min_x'] = (min_x / 100) * width
        d['max_x'] = (max_x / 100) * width
        d['min_y'] = (min_y / 100) * height
        d['max_y'] = (max_y / 100) * height

        for key in d.keys():
            # Convert to integer pixel values.
            # Round up (could just as well round down, need to pick one or the other).
            d[key] = int(math.ceil(d[key]))

            # Corner case
            if d[key] == 0:
                d[key] = 1

        return d
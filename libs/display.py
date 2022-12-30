"""Sets the values for displaying supported chars on a Waveshare RGB LED Pico hat (in landscape)"""

import re

from wsgi_web_app_helpers import get_json_wsgi_input, bad_request


class TooManyCharsException(Exception):
    """Oh no, there are too many characters"""


# The index of the nested list is the digit it represents
digits = {
    0: [
        [44, 45, 59, 62, 75, 78, 91, 94, 107, 110, 123, 126, 140, 141], # 0
        [44, 45, 46, 61, 77, 93, 109, 125, 126, 141], # 1
        [43, 44, 45, 46, 62, 77, 92, 107, 123, 126, 140, 141], # 2
        [44, 45, 59, 62, 75, 92, 93, 107, 123, 126, 140, 141],  # 3....
        [44, 60, 76, 91, 92, 93, 94, 108, 110, 124, 126, 140, 142],
        [44, 45, 46, 59, 75, 92, 93, 94, 110, 126, 139, 140, 141, 142],
        [44, 45, 59, 62, 75, 78, 92, 93, 94, 110, 125, 140],
        [45, 61, 77, 93, 108, 123, 139, 140, 141, 142],
        [44, 45, 59, 62, 75, 78, 92, 93, 107, 110, 123, 126, 140, 141],
        [43, 59, 75, 91, 92, 93, 107, 110, 123, 126, 140, 141],
        [92, 93, 94]  # minus
    ],
    1: [
        [121, 136, 135, 118, 102, 70, 54, 57, 40, 39, 73, 105, 89, 86], # 0
        [40, 41, 42, 57, 73, 89, 105, 121, 122, 137], # 1
        [39, 40, 41, 42, 58, 73, 88, 103, 119, 122, 136, 137], # 2
        [40, 41, 55, 58, 71, 88, 89, 103, 119, 122, 136, 137],  # 3....
        [41, 57, 73, 88, 89, 90, 91, 105, 107, 121, 123, 137, 139],
        [40, 41, 42, 55, 71, 88, 89, 90, 106, 122, 135, 136, 137, 138],
        [40, 41, 55, 58, 71, 74, 88, 89, 90, 106, 121, 136],
        [41, 57, 73, 89, 104, 119, 135, 136, 137, 138],
        [39, 40, 54, 57, 70, 73, 87, 88, 102, 105, 118, 121, 135, 136],
        [39, 55, 71, 87, 88, 89, 103, 106, 119, 122, 136, 137],
        [88, 89, 90]  # minus
    ]
}


def gen_char_values(chars):
    """
    Generates the character pixel lists for supported characters.

    params:
      - chars (str): the chars to display on the RGB screen

    returns:
      - list[int]
    """
    num_chars = len(chars)
    max_chars = len(list(digits.keys()))  # the list typecast is due to MicroPython awfulness
    if num_chars > max_chars:
        raise TooManyCharsException("'%s' exceeds the character limit: %s" % (chars, max_chars))

    active_pixels = []
    # We will set the character positions from left to right
    for index, char in enumerate(chars):
        if char == "-":
            char = 10
        else:
            # allow a ValueError to be thrown if we aren't int'able.
            char = int(char)

        active_pixels.extend(digits[index][char])

    return active_pixels


def clear(neo):
    """Clears the screen"""
    neo.fill([0, 0, 0])
    neo.show()
    return None, None


class BaseDisplayHandler:
    """Base class for handling display controls from JSON POST request data."""

    def __init__(self, json_request, neo, num_px):
        self.response = None
        self.status_code = None
        self.req_data = get_json_wsgi_input(json_request, bad_request)
        self.neo = neo
        self.num_px = num_px

    def clear(self):
        return clear(self.neo)

    def set(self):
        raise NotImplementedError("set method needs implementing.")


class SetPx(BaseDisplayHandler):

    def set(self):
        if not isinstance(self.req_data, dict):  # Something bad has happened here.
            return self.req_data

        self.clear()
        for rgb, pixels in self.req_data.items():
            if re.match("\d\d\d", rgb) and isinstance(pixels, list):
                for px in pixels:
                    try:
                        px_int = int(px)
                    except Exception:
                        return bad_request("Pixel numbers from list must be integers")
                    if px_int > self.num_px:
                        return bad_request(
                            "Cannot set value to pixel  %s. Max supported: %s" % (px_int, self.num_px)
                        )

                    self.neo[int(px)] = [int(x * 200) for x in rgb]
            else:
                return bad_request('Input did not match schema. Example: {"010": [1,2,3,4,5], "011": [16,60]}')

        self.neo.show()
        return self.response, self.status_code


class SetTemp(BaseDisplayHandler):

    def set(self):
        if not isinstance(self.req_data, dict):  # Something bad has happened here.
            return self.req_data

        for rgb, temp_value in self.req_data.items():
            # make sure we are a string
            temp_value = str(temp_value)
            # simple regex for temp. "--" is a valid value for null, \d- is clearly just nonsense.
            # regex's are a little hideous as MicroPython's regex engine isn't too glamorous...
            if re.match("\d\d\d", rgb) and re.match("(--)|(^-\d)|(\d\d)|(\d)", temp_value):
                try:
                    rgb_temp_vals = gen_char_values(temp_value)
                except Exception as exc:
                    return bad_request(repr(exc))

                self.clear() # only clearing the screen now as success seems likely
                for px in rgb_temp_vals:
                    self.neo[int(px)] = [int(x * 200) for x in rgb]
            else:
                return bad_request(
                    "Input value %s doesn't appear to match the expected format: \{'001': '-3'\}." % self.req_data
                )

        self.neo.show()
        return self.response, self.status_code

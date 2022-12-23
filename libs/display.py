"""Sets the values for displaying supported chars on a Waveshare RGB LED Pico hat (in landscape)"""


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
    max_chars = len(digits.keys())
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


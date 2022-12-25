"""Pico-temp-display - CircuitPython - W5100s-evb-pico SBC

This depends on the following being present in the Pico's 'lib' DIR:

    --- Circuit Python bundle ---
        - adafruit_wiznet5k
        - adafruit_bus_device
        - adafruit_requests.mpy

    --- Circuit-python-utils (submodule) ---
        - wiznet5keth.py (W5100s-evb-pico)
        - config_utils.py (utils)

config.json needs to exist in the root (with this file).
The value of "mac" must not be an empty string.
A mac address can be generated via circuit-python-utils.networking.generate_mac_addr.py

"""

import time
import re

import board
import neopixel

from wiznet5keth import NetworkConfig, config_eth, wsgi_web_server
from wsgi_web_app_helpers import web_response_wrapper, get_json_wsgi_input, bad_request
from config_utils import get_config_from_json_file

# _local_ imports
from display import gen_char_values


# NeoPixel config
PX_PIN = board.GP6
NUM_PX = 160
ORDER = neopixel.GRB
AUTO_WRITE = False

# Network config file
eth_interface = config_eth(NetworkConfig(**get_config_from_json_file()))
# WSGI and Web App
wsgi_server, web_app = wsgi_web_server(eth_interface)
wsgi_server.start()

neo = neopixel.NeoPixel(PX_PIN, NUM_PX, auto_write=AUTO_WRITE, pixel_order=ORDER, brightness=0.01)


@web_app.route("/clear", methods=["GET"])
def clear(_):
    """Clears the RGB screen"""
    def _clear():
        neo.fill([0, 0, 0])
        neo.show()
        return None, None

    return web_response_wrapper(_clear)


@web_app.route("/set-rgb", methods=["POST"])
def set_px(request):
    """Set a X number of pixels to a value"""
    def _set_px(req):
        response = None
        status_code = None
        req = get_json_wsgi_input(request, bad_request)
        if not isinstance(req, dict):  # Something bad has happened here.
            return req

        for rgb, pixels in req.items():
            if re.match("\d\d\d", rgb) and isinstance(pixels, list):
                for px in pixels:
                    try:
                        px_int = int(px)
                    except Exception:
                        return bad_request("Pixel numbers from list must be integers")

                    if px_int > NUM_PX:
                        return bad_request(f"Cannot set value to pixel {px_int}. Max supported: {NUM_PX}")

                    neo[int(px)] = [int(x * 200) for x in rgb]
            else:
                return bad_request('Input did not match schema. Example: {"010": [1,2,3,4,5], "011": [16,60]}')

        neo.show()
        return response, status_code

    return web_response_wrapper(_set_px, request)


@web_app.route("/set-temp", methods=["POST"])
def set_px(request):
    """
    Sets the temperature value on the display. Only supports and int (positive or negative) value represented as a str.
    Len of 2 chars (i.e "-1", "32", "9").

    Validates the input against the supported char list.

    The key is the RGB value you want the text to be. The below example sets the -1 display text to blue.
    Example: {"001": "-1"}
    """
    def _set_values():
        # TODO: there will be a lot of code here we should be sharing with above ^^^^^^^
        response = None
        status_code = None
        req = get_json_wsgi_input(request, bad_request)
        if not isinstance(req, dict):  # Something bad has happened here.
            return req

        for rgb, temp_value in req.items():
            # make we sure are a string
            temp_value = str(temp_value)
            # simple regex for temp "--" is a valid value for null, \d- is clearly just nonsense.
            # regex's are a little hideous as MicroPython's regex engine isn't too glamorous...
            if re.match("\d\d\d", rgb) and re.match("(--)|(^-\d)|(\d\d)|(\d)", temp_value):
                try:
                    rgb_temp_vals = gen_char_values(temp_value)
                except Exception as exc:
                    return bad_request(repr(rgb_temp_vals))
                for px in rgb_temp_vals:
                    neo[int(px)] = [int(x * 200) for x in rgb]
            else:
                return bad_request("Input value %s doesn't appear to match the expected format: \{'001': '-3'\}." % req)

        neo.show()
        return response, status_code

    return web_response_wrapper(_set_values, request)


while True:
    wsgi_server.update_poll()
    time.sleep(0.1)
    eth_interface.maintain_dhcp_lease()

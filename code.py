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


def _clear():
    """Clears the screen"""
    neo.fill([0, 0, 0])
    neo.show()
    return None, None


class BaseDisplayHandler:
    """Base class for handling display controls from JSON POST request data."""

    def __init__(self, json_request):
        self.response = None
        self.status_code = None
        self.req_data = get_json_wsgi_input(json_request, bad_request)

    @staticmethod
    def clear():
        return _clear()

    def set(self):
        raise NotImplementedError("set method needs implementing.")


@web_app.route("/clear", methods=["GET"])
def clear(_):
    """API call. Clears the RGB screen"""
    return web_response_wrapper(_clear)


@web_app.route("/set-rgb", methods=["POST"])
def set_px(request):
    """API call. Set a X number of pixels to a value"""
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
                        if px_int > NUM_PX:
                            return bad_request(f"Cannot set value to pixel {px_int}. Max supported: {NUM_PX}")

                        neo[int(px)] = [int(x * 200) for x in rgb]
                else:
                    return bad_request('Input did not match schema. Example: {"010": [1,2,3,4,5], "011": [16,60]}')
            neo.show()
            return self.response, self.status_code


    set_px_handler = SetPx(request)
    return web_response_wrapper(set_px_handler.set)


@web_app.route("/set-temp", methods=["POST"])
def set_temp(request):
    """
    API call.
    Sets the temperature value on the display. Only supports and int (positive or negative) value represented as a str.
    Len of 2 chars (i.e "-1", "32", "9").

    Validates the input against the supported char list.

    The key is the RGB value you want the text to be. The below example sets the -1 display text to blue.
    Example: {"001": "-1"}
    """
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
                        neo[int(px)] = [int(x * 200) for x in rgb]
                else:
                    return bad_request(
                        "Input value %s doesn't appear to match the expected format: \{'001': '-3'\}." % self.req_data
                    )
            neo.show()
            return self.response, self.status_code


    set_temp_handler = SetTemp(request)
    return web_response_wrapper(set_temp_handler.set)


while True:
    wsgi_server.update_poll()
    time.sleep(0.1)
    eth_interface.maintain_dhcp_lease()

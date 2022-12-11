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
import json
import re

import board
import neopixel

from wiznet5keth import NetworkConfig, config_eth, wsgi_web_server
from wsgi_web_app_helpers import web_response_wrapper, get_json_wsgi_input, bad_request
from config_utils import get_config_from_json_file


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


@web_app.route("/set", methods=["POST"])
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


while True:
    wsgi_server.update_poll()
    time.sleep(0.1)
    eth_interface.maintain_dhcp_lease()

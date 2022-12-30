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

import board
import neopixel

from wiznet5keth import NetworkConfig, config_eth, wsgi_web_server
from wsgi_web_app_helpers import web_response_wrapper, internal_server_error, HTTPStatusCodes, ErrorCodes
from config_utils import get_config_from_json_file

# _local_ imports
from display import SetPx, SetTemp, clear


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

display_update_event = None


def clear_global():
    global display_update_event
    display_update_event = None


@web_app.route("/clear", methods=["GET"])
def clear_screen(_):
    """API call. Clears the RGB screen"""
    clear_global()
    return web_response_wrapper(clear, neo)


@web_app.route("/set-rgb", methods=["POST"])
def set_px(request):
    """API call. Set a X number of pixels to a value"""
    clear_global()
    set_px_handler = SetPx(request, neo, NUM_PX)
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
    try:
        global display_update_event
        set_temp_handler = SetTemp(request, neo, NUM_PX).set()
        display_update_event = set_temp_handler.set
        status_code = HTTPStatusCodes.OK
        response = {"error": ErrorCodes.OK}
    except Exception as exc:
        response, status_code = internal_server_error(repr(exc))

    return (
        status_code,
        [("Content-type", "application/json; charset=utf-8")],
        [json.dumps(response).encode("UTF-8")]
    )

# Since we can't run the screen update asynchronously (see the text block in display.SetTemp.set), we will add a
# simple counter to stop the update rate from being insane...
madness_counter = 0
while True:
    wsgi_server.update_poll()
    if madness_counter == 5:
        if callable(display_update_event):
            display_update_event()
        madness_counter = 0
    else:
        time.sleep(0.1)
    madness_counter += 1
    eth_interface.maintain_dhcp_lease()

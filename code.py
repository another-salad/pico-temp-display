"""Pico-temp-display - CircuitPython - W5100s-evb-pico SBC

This depends on the following being present in the Pico's 'lib' DIR:

    --- Circuit Python bundle ---
        - adafruit_wiznet5k
        - adafruit_bus_device
        - adafruit_requests.mpy
        - asyncio
        - adafruit_ticks.mpy

    --- Circuit-python-utils (submodule) ---
        - wiznet5keth.py (W5100s-evb-pico)
        - config_utils.py (utils)

config.json needs to exist in the root (with this file).
The value of "mac" must not be an empty string.
A mac address can be generated via circuit-python-utils.networking.generate_mac_addr.py

"""

import time
import json

import asyncio

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

current_display_text = None
background_event = asyncio.Event()
server_event = asyncio.Event()


def clear_global():
    global background_event
    global current_display_text
    current_display_text = None
    background_event.set()
    time.sleep(0.2)
    # Create a new event
    background_event = asyncio.Event()


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
        global current_display_text
        set_temp_handler = SetTemp(request, neo, NUM_PX).set()
        if set_temp_handler.display_text != current_display_text:
            clear_global()  # resets the pertinent global variables to default, sets the old background event
            current_display_text = set_temp_handler.display_text
            asyncio.create_task(run_async_task(set_temp_handler.set, background_event, 1))
        status_code = HTTPStatusCodes.OK
        response = {"error": ErrorCodes.OK}
    except Exception as exc:
        response, status_code = internal_server_error(repr(exc))

    return (
        status_code,
        [("Content-type", "application/json; charset=utf-8")],
        [json.dumps(response).encode("UTF-8")]
    )


def run_server(wsgi_server, eth_interface):
    wsgi_server.update_poll()
    eth_interface.maintain_dhcp_lease()


async def run_async_task(callable_func, stop_event, sleep_val, *args, **kwargs):
    while not stop_event.is_set():
        callable_func(*args, **kwargs)
        await asyncio.sleep(sleep_val)


async def main(wsgi_server, eth_interface, server_event):
    """Entry point"""
    server_task = asyncio.create_task(run_async_task(run_server, server_event, 0.1, wsgi_server, eth_interface))
    await asyncio.gather(server_task)


asyncio.run(main(wsgi_server, eth_interface, server_event))
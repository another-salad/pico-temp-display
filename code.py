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
print(dir(board))
neo.fill([0, 0, 150])
neo[0] = (0, 170, 40)
neo[1] = (0, 0, 0)
neo[2] = (150, 150, 150)

@web_app.route("/hi", methods=["GET"])
def get_readings(_):
    """Gets the current sensor readings"""
    neo.show()
    return (
        "200 OK",
        [("Content-type", "application/json; charset=utf-8")],
        [json.dumps({"success": True}).encode("UTF-8")]
    )

while True:
    wsgi_server.update_poll()
    time.sleep(0.1)
    eth_interface.maintain_dhcp_lease()
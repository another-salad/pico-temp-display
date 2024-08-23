"""
Runtime script (can be triggered by cron, etc) for collecting the temp from a sensor and setting it on the
Pico display
"""

from argparse import ArgumentParser
from urllib import request
import json


class Args(ArgumentParser):
    """Arg parser"""

    def __init__(self, description="Gets the temp from a networked sensor and sets it on a networked pico display"):
        super().__init__(description=description)
        self.add_argument("--sensor", type=str, required=False)
        self.add_argument("--temp", type=int, required=False, default=0)
        self.add_argument("--pico", type=str)


def get_web_req(dest: str):
    with request.urlopen(dest) as req:
        data = req.read()
        return json.loads(data.decode("utf-8"))


def set_web_req(dest: str, temp_val: int):
    if temp_val < 15:
        text_colour = "100" # Red
    elif 15 <= temp_val < 30:
        text_colour = "000" # black
    else:
        text_colour = "111" # white
    data = json.dumps({text_colour: temp_val}).encode("utf-8")
    web_req = request.Request(dest, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(web_req) as req:
        resp = json.loads(req.read().decode("utf-8"))
        if resp["error"] != 0:
            print(resp)


def temp_setter(pico: str, sensor: str | None = None, temp: int = 0):
    if sensor:
        sensor_temp = int(get_web_req(sensor)["temp"])
    else:
        sensor_temp = temp
    set_web_req(pico, sensor_temp)


def main():
    """Entry point"""
    args, _ = Args().parse_known_args()
    temp_setter(args.pico, args.sensor, args.temp)


if __name__ == "__main__":
    main()

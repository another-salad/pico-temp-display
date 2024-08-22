"""
Runtime script (can be triggered by cron, etc)
"""

from argparse import ArgumentParser
from urllib import request
import json


class Args(ArgumentParser):
    """Arg parser"""

    def __init__(self, description="Sets the pico display to the colour cycle"):
        super().__init__(description=description)
        self.add_argument("--pico", type=str)


def req(dest: str):
    web_req = request.Request(dest, headers={"Content-Type": "application/json"}, method="get")
    with request.urlopen(web_req) as req:
        resp = json.loads(req.read().decode("utf-8"))
        print(resp)
        if resp["error"] != 0:
            print(resp)

def main():
    """Entry point"""
    args, _ = Args().parse_known_args()
    req(args.pico)


if __name__ == "__main__":
    main()

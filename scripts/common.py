from argparse import ArgumentParser
from urllib import request
import json


class Args(ArgumentParser):
    """Arg parser"""

    def __init__(self, description="Give me a http endpoint for your pico please"):
        super().__init__(description=description)
        self.add_argument("--pico", type=str)


def req(dest: str, method: str = "get"):
    web_req = request.Request(dest, headers={"Content-Type": "application/json"}, method=method)
    with request.urlopen(web_req) as req:
        return json.loads(req.read().decode("utf-8"))

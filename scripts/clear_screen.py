"""
Runtime script (can be triggered by cron, etc)
"""

if __name__ == "__main__":
    from common import Args, req
    arg, _ = Args().parse_known_args()
    req(f"http://{arg.pico}/clear")

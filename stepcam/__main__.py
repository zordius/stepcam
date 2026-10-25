import argparse

from .app import run
from .devices import list_cameras


def main():
    p = argparse.ArgumentParser(prog="stepcam", description="Webcam virtual dance pad")
    p.add_argument(
        "--source",
        help="camera index, part of a camera name (case-insensitive), or video file; "
        "exits with an error if nothing matches (default: first camera that delivers a frame)",
    )
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--mirror", action="store_true", help="flip the image horizontally")
    p.add_argument("--exposure", type=float, help="raw CAP_PROP_EXPOSURE value for your backend")
    p.add_argument("--auto-exposure", type=float, help="raw CAP_PROP_AUTO_EXPOSURE value for your backend")
    p.add_argument("--config", default="config.json")
    p.add_argument("--keys", action="store_true", help="start with key output on")
    p.add_argument("--headless", action="store_true", help="no window; needs a saved calibration")
    p.add_argument("--seconds", type=float, help="stop after this many seconds")
    p.add_argument("--list-cameras", action="store_true", help="print camera indexes and names, then exit")
    args = p.parse_args()
    if args.list_cameras:
        cameras = list_cameras()
        for index, name in cameras:
            print(f"[{index}] {name}")
        if not cameras:
            print("no camera names available (macOS with pyobjc-framework-AVFoundation only)")
    else:
        run(args)


if __name__ == "__main__":
    main()

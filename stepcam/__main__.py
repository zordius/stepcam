import argparse

from .app import run


def main():
    p = argparse.ArgumentParser(prog="stepcam", description="Webcam virtual dance pad")
    p.add_argument("--source", help="camera index or video file (default: first camera that delivers a frame)")
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
    run(p.parse_args())


if __name__ == "__main__":
    main()

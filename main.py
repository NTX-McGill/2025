#UPDATED


import datetime
from backend import CSVDataRecorder
from backend import MarkerOutlet

from frontend_pygame.master_front_end import runPyGame
import numpy as np
import logging

import pathlib

collector = CSVDataRecorder(find_streams=False)
marker_outlet = MarkerOutlet()

log_path = pathlib.Path(f"logs/data_collection_platform.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_path,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def on_start():
    collector.find_streams()

    if collector.ready:
        name = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
        collector.start(filename=f"{name}.csv")

    else:
        print("Data not ready - quit and try again.")


def on_stop():
    collector.stop()


def on_home_screen():
    marker_outlet.send_marker("Home Screen")


def on_baseline():
    marker_outlet.send_marker("Baseline")


def on_imagine():
    marker_outlet.send_marker("Imagine Object")


def on_blank_white():
    marker_outlet.send_marker("Blank White")


def on_rest():
    marker_outlet.send_marker("Rest")


def on_look_at_image():
    marker_outlet.send_marker("Look at Image")


def on_close_eyes_imagine():
    marker_outlet.send_marker("Close Eyes and Imagine")


np.random.seed(4)

def create_train_sequence():
    return [
        "baseline",
        "imagine",
        "blank_white",
        "rest",
        "look_at_image",
        "rest",
        "close_eyes_imagine",
        "blank_white",
        "rest",
    ]


def main():
    sequence = create_train_sequence()
    print("Sequence: ", sequence)
    runPyGame(
        train_sequence=sequence,
        on_start=on_start,
        on_stop=on_stop,
        on_home_screen=on_home_screen,
        on_baseline=on_baseline,
        on_imagine=on_imagine,
        on_blank_white=on_blank_white,
        on_rest=on_rest,
        on_look_at_image=on_look_at_image,
        on_close_eyes_imagine=on_close_eyes_imagine,
        rest_duration=5,
        work_duration=10,
    )


if __name__ == "__main__":
    main()

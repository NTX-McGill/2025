import datetime
from backend.csv_data_recorder import CSVDataRecorder
from backend.marker_outlet import MarkerOutlet
from master_front_end import runPyGame
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
    marker_outlet.send_transition("Home Screen")


def on_baseline():
    marker_outlet.send_transition("Baseline")


def on_imagine():
    marker_outlet.send_transition("Imagine Object")


def on_blank_white():
    marker_outlet.send_transition("Blank White")


def on_rest():
    marker_outlet.send_transition("Rest")


def on_look_at_image(image):
    marker_outlet.send_new_image(f"Look at Image: {image}")


def on_close_eyes_imagine():
    marker_outlet.send_transition("Close Eyes and Imagine")


def on_cycle_complete(cycle):
    marker_outlet.send_transition(f"Cycle {cycle} Complete")


def create_train_sequence():
    return [
        "baseline",
        "imagine",
        "white_screen_1",
        "rest_1",
        "look_at_image",
        "rest_2",
        "close_eyes_imagine",
        "white_screen_2",
        "rest_3",
    ]


def main():
    sequence = create_train_sequence()
    print("Sequence: ", sequence)

    image_list = [
        "bci_images/Apple.png",
        "bci_images/McGill Arts Building.png",
        "bci_images/Door Handle.png",
        "bci_images/Obama.png",
    ]

    # Pass parameters directly to runPyGame
    runPyGame(
        train_sequence=sequence,
        work_duration=10,
        rest_duration=5,
        image_list=image_list,
        on_home_screen=on_home_screen,
        on_baseline=on_baseline,
        on_imagine=on_imagine,
        on_white_screen=on_blank_white,
        on_rest=on_rest,
        on_look_at_image=on_look_at_image,
        on_close_eyes_imagine=on_close_eyes_imagine,
        on_cycle_complete=on_cycle_complete,
        on_stop=on_stop,
    )


if __name__ == "__main__":
    main()

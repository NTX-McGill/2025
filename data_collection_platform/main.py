import datetime
import logging
import pathlib
import random
from backend.csv_data_recorder import CSVDataRecorder
from backend.marker_outlet import MarkerOutlet
from master_front_end import runPyGame
from constants import *

# Initialize data recorder and marker outlet
collector = CSVDataRecorder(find_streams=False)
marker_outlet = MarkerOutlet()

# Logging configuration
log_path = pathlib.Path(f"logs/data_collection_platform.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_path,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


# Callback functions for different stages
def on_start():
    collector.find_streams()

    if collector.ready:
        name = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
        collector.start(filename=f"{name}.csv")
    else:
        print("Data not ready - quit and try again.")


def on_stop():
    """Handles stopping the session from the checkpoint."""
    print("Stopping session... Saving data and closing streams.")

    # Save all recorded EEG data
    #collector.save_and_close()
    collector.stop()

    # Stop OpenBCI streaming
    try:
        from bci_streamer import BCIStreamer

        bci_streamer = BCIStreamer()
        bci_streamer.stop_stream()
    except Exception as e:
        print(f"Warning: Unable to stop EEG stream properly: {e}")

    # Send LSL stop marker
    #marker_outlet.send_stop_marker()

    print("Session successfully stopped.")


def on_home_screen():
    marker_outlet.send_transition(STATUS_TRANSITION)


def on_baseline():
    marker_outlet.send_transition(STATUS_BASELINE)


def on_imagine(image_id: int):
    marker_outlet.send(new_image=image_id, new_status=STATUS_IMAGINE)


def on_white_screen():
    marker_outlet.send_transition(STATUS_TRANSITION)


def on_rest():
    marker_outlet.send_transition(STATUS_TRANSITION)


def on_look_at_image():
    marker_outlet.send_transition(STATUS_LOOK)


def on_close_eyes_imagine():
    marker_outlet.send_transition(STATUS_IMAGINE_EYES_CLOSED)


def on_cycle_complete():
    collector.pause()


def on_cycle_start():
    collector.unpause()


def create_train_sequence():
    #add list of random trials here
    # if none is provided random sequence of 6 trials is generated
    sequence = None

    return sequence

def create_priming_sequence():
    return ["baseline",
        "imagine",
        "white_screen_1",
        #"rest_1",
        "look_at_image",
        #"rest_2",
        #"close_eyes_imagine",
        #"white_screen_2",
        #"rest_3",
    ]


# Main data collection function
def main():
    # Prompt user to enter CSV filename
    filename = input("Enter the name of the CSV file (without extension): ") + ".csv"

    # Start recording EEG data
    collector.find_streams()
    if collector.ready:
        print(f"Starting data recording... Saving to: {filename}")
        collector.start(filename=filename)
    else:
        print(
            "LSL streams not ready. Please ensure EEG and Marker streams are running."
        )
        return

    sequence = create_priming_sequence()
    random_sequence = create_train_sequence()
    print("Sequence: ", sequence)

    image_list = [
        "bci_images/Apple.png",
        "bci_images/McGill Arts Building.png",
        "bci_images/Door Handle.png",
    ]

    runPyGame(
        train_sequence=sequence,
        random_sequence=random_sequence,
        work_duration=15,
        rest_duration=10,
        image_list=image_list,
        on_home_screen=on_home_screen,
        on_baseline=on_baseline,
        on_imagine=on_imagine,
        on_white_screen=on_white_screen,
        on_rest=on_rest,
        on_look_at_image=on_look_at_image,
        on_close_eyes_imagine=on_close_eyes_imagine,
        on_cycle_complete=on_cycle_complete,  # The checkpoint is inside this function
        on_cycle_start=on_cycle_start,
        on_stop=on_stop,  # Now properly saves and stops EEG
    )


# Entry point
if __name__ == "__main__":
    main()

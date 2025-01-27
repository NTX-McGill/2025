import pathlib
import logging

from marker_outlet import MarkerOutlet, decode_status
from csv_data_recorder import CSVDataRecorder
from constants import *


log_path = pathlib.Path(f"logs/cli.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_path,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

title_string = """

██████╗░░█████╗░████████╗░█████╗░  ░█████╗░░█████╗░██╗░░░░░██╗░░░░░███████╗░█████╗░████████╗██╗░█████╗░███╗░░██╗
██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗  ██╔══██╗██╔══██╗██║░░░░░██║░░░░░██╔════╝██╔══██╗╚══██╔══╝██║██╔══██╗████╗░██║
██║░░██║███████║░░░██║░░░███████║  ██║░░╚═╝██║░░██║██║░░░░░██║░░░░░█████╗░░██║░░╚═╝░░░██║░░░██║██║░░██║██╔██╗██║
██║░░██║██╔══██║░░░██║░░░██╔══██║  ██║░░██╗██║░░██║██║░░░░░██║░░░░░██╔══╝░░██║░░██╗░░░██║░░░██║██║░░██║██║╚████║
██████╔╝██║░░██║░░░██║░░░██║░░██║  ╚█████╔╝╚█████╔╝███████╗███████╗███████╗╚█████╔╝░░░██║░░░██║╚█████╔╝██║░╚███║
╚═════╝░╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝  ░╚════╝░░╚════╝░╚══════╝╚══════╝╚══════╝░╚════╝░░░░╚═╝░░░╚═╝░╚════╝░╚═╝░░╚══╝

░█████╗░██╗░░░░░██╗
██╔══██╗██║░░░░░██║
██║░░╚═╝██║░░░░░██║
██║░░██╗██║░░░░░██║
╚█████╔╝███████╗██║
░╚════╝░╚══════╝╚═╝
"""


def cli():
    # Create a marker outlet
    marker_outlet = MarkerOutlet()

    # Create a data recorder
    data_recorder = CSVDataRecorder(find_streams=False)

    print(title_string)

    while True:
        user_input = input(
            "\nPress 0 to exit."
            "\nPress 1 to send a new state"
            "\nPress 2 to send a new image."
            "\nPress 3 to start recording."
            "\nPress 4 to stop recording."
            "\nPress 5 to connect to streams."
            "\nEnter a command: \n > "
        )

        if user_input == "0":
            print("Exiting the data collection platform.")
            break

        elif user_input == "1":
            marker = input(
              "\nPress -2 for done."
              "\nPress -1 for transition."
              "\nPress 0 for baseline."
              "\nPress 1 for imagine."
              "\nPress 2 for look."
              "\nPress 3 for imagine with eyes closed."
              "\n > "
            )

            try:
                x = int(marker)
                name = decode_status(x)
                if name == "UNKNOWN":
                    print("Invalid input.")
                    continue
                print(f"Sending marker: {name}")
                marker_outlet.send_transition(x)

            except ValueError:
                continue

        elif user_input == "2":
            image = input(
                "\nPress 0 for no image."
                "\nPress 1 for an apple."
                "\nPress 2 for a banana."
                "\nPress 3 for a cherry."
                "\nPress 4 for a grape."
                "\nPress 5 for a lemon."
                "\nPress 6 for an orange."
                "\nPress 7 for a pear."
                "\nPress 8 for a pineapple."
                "\nPress 9 for a strawberry."
                "\n > "
            )

            try:
                x = int(image)
                if x < 0 or x > 9:
                    print("Invalid input.")
                    continue

                print(f"Sending image: {x}")
                marker_outlet.send_new_image(x)

            except ValueError:
                continue

        elif user_input == "3":
            if not data_recorder.ready:
                print(
                    "EEG or marker stream not found. Please use option 4 to connect to streams first."
                )
                continue

            filename = input("Enter the filename for the recording: ")
            data_recorder.start(filename)
            print("Recording data...")

        elif user_input == "4":
            if not data_recorder.recording:
                print("No recording in progress.")
                continue

            data_recorder.stop()
            print(
                "Data collection finished. Your data should be written in the collected_data folder."
            )

        elif user_input == "5":
            print("Looking for streams...")
            data_recorder.find_streams()
            print("Found streams. Ready to start recording.")


if __name__ == "__main__":
    cli()

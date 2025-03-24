import pylsl
import os
import time
import threading

import pandas as pd
import numpy as np
import typing
import logging

from pathlib import Path

from constants import *


# sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

# # from siggy_ml.models.diffusion.classification_heads import EEGNetHead
# # Edited from NTX McGill 2021 stream.py, lines 16-23
# # https://github.com/NTX-McGill/NeuroTechX-McGill-2021/blob/main/software/backend/dcp/bci/stream.py
logger = logging.getLogger(__name__)


def find_bci_inlet(debug=False):
    """Find an EEG stream and return an inlet to it.

    Args:
        debug (bool, optional): Print extra info. Defaults to False.

    Returns:
        pylsl.StreamInlet: Inlet to the EEG stream
    """

    logger.info("Looking for an EEG stream...")
    streams = pylsl.resolve_stream("type", "EEG")
    # Block until stream found
    inlet = pylsl.StreamInlet(
        streams[0], processing_flags=pylsl.proc_dejitter | pylsl.proc_clocksync
    )

    logger.info(
        f"Connected to stream: {streams[0].name()}, Stream channel_count: {streams[0].channel_count()}"
    )

    if debug:
        logger.info(f"Stream info dump:\n{streams[0].as_xml()}")

    return inlet


def find_marker_inlet(debug=False):
    """Find a marker stream and return an inlet to it.

    Args:
        debug (bool, optional): Print extra info. Defaults to False.

    Returns:
        pylsl.StreamInlet: Inlet to the marker stream
    """

    logger.info("Looking for a marker stream...")
    streams = pylsl.resolve_stream("type", "Markers")
    # Block until stream found
    inlet = pylsl.StreamInlet(
        streams[0], processing_flags=pylsl.proc_dejitter | pylsl.proc_clocksync
    )

    logger.info(f"Found {len(streams)} streams")
    logger.info(f"Connected to stream: {streams[0].name()}")

    if debug:
        logger.info(f"Stream info dump:\n{streams[0].as_xml()}")

    return inlet


class CSVDataRecorder:
    """Class to record EEG and marker data to a CSV file."""

    def __init__(self, find_streams=True, num_imgs=20):
        self.eeg_inlet = find_bci_inlet() if find_streams else None
        self.marker_inlet = find_marker_inlet() if find_streams else None

        self.recording = False
        self.paused = False
        self.ready = self.eeg_inlet is not None and self.marker_inlet is not None

        if self.ready:
            logger.info("Ready to start recording.")

        self.num_imgs = num_imgs

    def find_streams(self):
        """Find EEG and marker streams. Updates the ready flag."""
        self.find_eeg_inlet()
        self.find_marker_inlet()
        self.ready = self.eeg_inlet is not None and self.marker_inlet is not None

    def find_eeg_inlet(self):
        """Find the EEG stream and update the inlet."""
        self.eeg_inlet = find_bci_inlet(debug=False)
        logger.info(f"EEG Inlet found:{self.eeg_inlet}")

    def find_marker_inlet(self):
        """Find the marker stream and update the inlet."""
        self.marker_inlet = find_marker_inlet(debug=False)
        logger.info(f"Marker Inlet found:{self.marker_inlet}")

        self.ready = self.eeg_inlet is not None and self.marker_inlet is not None

    def start(self, filename="test_data_0.csv"):
        """Start recording data to a CSV file. The recording will continue until stop() is called.
        The filename is the name of the file to save the data to. If the file already exists, it will be overwritten.
        If the LSL streams are not available, the function will print a message and return without starting the recording.
        Note that the output file will only be written to disk when the recording is stopped.
        """

        if not self.ready:
            logger.error("Error: not ready to start recording")
            logger.info(f"EEG Inlet:{self.eeg_inlet}")
            logger.info(f"Marker Inlet:{self.marker_inlet}")
            return

        self.recording = True

        worker_args = [filename]
        t = threading.Thread(target=self._start_recording_worker, args=worker_args)
        t.start()

    def _start_recording_worker(self, filename):
        """Worker function to record the data to a CSV file.
        This function should not be called directly. Use start() instead.
        """

        eeg_timestamp_list = np.array([])
        channel_lists: typing.List[np.ndarray] = list()
        for i in range(8):
            channel_lists.append(np.array([]))

        marker_timestamp_list = np.array([])
        has_new_image_list = np.array([])
        new_image_list = np.array([])
        has_new_status_list = np.array([])
        new_status_list = np.array([])

        eeg_buffer_size = 0

        # Flush the inlets to remove old data
        self.eeg_inlet.flush()
        self.marker_inlet.flush()

        self._save_buffer(
            filename,
            eeg_timestamp_list,
            marker_timestamp_list,
            channel_lists,
            has_new_image_list,
            new_image_list,
            has_new_status_list,
            new_status_list,
        )

        while self.recording:
            # PROBLEM - we need to merge the two (EEG and Marker) LSL streams into one
            # Assume we never get two markers for one EEG sample
            # Therefore when we pull a marker, we can attach it to the next pulled EEG sample
            # This effectively discards the marker timestamps but the EEG is recorded so quickly that it doesn't matter (?)

            if self.paused:
                continue

            eeg_sample, eeg_timestamp = self.eeg_inlet.pull_sample()
            marker_sample, marker_timestamp = self.marker_inlet.pull_sample(0.0)

            if marker_sample is not None:
                # print("recieved", self.t+marker_timestamp)
                print(
                    f"eeg_timestamp: {eeg_timestamp}, marker_timestamp: {marker_timestamp}, delta={eeg_timestamp-marker_timestamp}"
                )

            if marker_sample is not None and marker_sample[0] is not None:
                has_new_image, new_image, has_new_status, new_status = marker_sample

                marker_timestamp_list = np.append(
                    marker_timestamp_list, marker_timestamp
                )
                has_new_image_list = np.append(has_new_image_list, has_new_image)
                new_image_list = np.append(new_image_list, new_image)
                has_new_status_list = np.append(has_new_status_list, has_new_status)
                new_status_list = np.append(new_status_list, new_status)

            # If there is a marker sample available after we already pulled one, then the assuption that there is only one marker sample per EEG sample has been broken.
            if self.marker_inlet.samples_available():
                print("warning: multiple marker samples found for 1 eeg sample")

            eeg_timestamp_list = np.append(eeg_timestamp_list, eeg_timestamp)
            for i in range(8):
                channel_lists[i] = np.append(channel_lists[i], eeg_sample[i])

            eeg_buffer_size += 1
            if eeg_buffer_size >= 16384:
                threading.Thread(
                    target=self._save_buffer,
                    args=[
                        filename,
                        eeg_timestamp_list,
                        marker_timestamp_list,
                        channel_lists,
                        has_new_image_list,
                        new_image_list,
                        has_new_status_list,
                        new_status_list,
                    ],
                ).start()

                eeg_buffer_size = 0

                eeg_timestamp_list = np.array([])
                channel_lists: typing.List[np.ndarray] = list()
                for i in range(8):
                    channel_lists.append(np.array([]))

                marker_timestamp_list = np.array([])
                has_new_image_list = np.array([])
                new_image_list = np.array([])
                has_new_status_list = np.array([])
                new_status_list = np.array([])

                print(eeg_timestamp_list)
        self._save_buffer(
            filename,
            eeg_timestamp_list,
            marker_timestamp_list,
            channel_lists,
            has_new_image_list,
            new_image_list,
            has_new_status_list,
            new_status_list,
        )

        filepath_eeg = Path(f"collected_data/eeg_{filename}")
        filepath_marker = Path(f"collected_data/markers_{filename}")
        filepath_merged = Path(f"collected_data/{filename}")

        eeg_df = pd.read_csv(filepath_eeg)
        marker_df = pd.read_csv(filepath_marker)

        merged = self.merge_eeg_and_marker_dfs(eeg_df, marker_df)
        merged.to_csv(filepath_merged, index=False)

    def _save_buffer(
        self,
        filename,
        eeg_timestamp_list,
        marker_timestamp_list,
        channel_lists,
        has_new_image_list,
        new_image_list,
        has_new_status_list,
        new_status_list,
    ):
        eeg_df = pd.DataFrame(
            columns=[
                "timestamp",
                "ch1",
                "ch2",
                "ch3",
                "ch4",
                "ch5",
                "ch6",
                "ch7",
                "ch8",
            ]
        )

        marker_df = pd.DataFrame(
            columns=[
                "timestamp",
                "has_new_image",
                "new_image",
                "has_new_status",
                "new_status",
            ]
        )

        eeg_df["timestamp"] = eeg_timestamp_list
        for i in range(8):
            eeg_df[f"ch{i+1}"] = channel_lists[i]

        marker_df["timestamp"] = marker_timestamp_list
        marker_df["has_new_image"] = has_new_image_list.astype("int")
        marker_df["new_image"] = new_image_list.astype("int")
        marker_df["has_new_status"] = has_new_status_list.astype("int")
        marker_df["new_status"] = new_status_list.astype("int")

        filepath_eeg = Path(f"collected_data/eeg_{filename}")
        filepath_marker = Path(f"collected_data/markers_{filename}")

        filepath_eeg.parent.mkdir(parents=True, exist_ok=True)

        eeg_df.to_csv(
            filepath_eeg,
            mode="a",
            index=False,
            header=(not os.path.exists(filepath_eeg)),
        )

        marker_df.to_csv(
            filepath_marker,
            mode="a",
            index=False,
            header=(not os.path.exists(filepath_marker)),
        )

    # TODO: write buffered version of function
    def merge_eeg_and_marker_dfs(self, eeg_df: pd.DataFrame, marker_df: pd.DataFrame):
        merged = pd.DataFrame(
            columns=[
                "timestamp",
                "ch1",
                "ch2",
                "ch3",
                "ch4",
                "ch5",
                "ch6",
                "ch7",
                "ch8",
                "status",
                "image_id",
            ]
        )

        merged["timestamp"] = eeg_df["timestamp"]
        for i in range(8):
            merged[f"ch{i+1}"] = eeg_df[f"ch{i+1}"]

        merged["status"] = np.repeat(-100, len(merged["timestamp"]))
        merged["image_id"] = np.repeat(-100, len(merged["timestamp"]))
        merged = merged.reset_index()
        marker_new_image_rows = marker_df[marker_df["has_new_image"] == 1]
        marker_new_status_rows = marker_df[marker_df["has_new_status"] == 1]

        current_image = IMAGE_NONE
        prev_eeg_index = 0
        for row in marker_new_image_rows.itertuples():
            timestamp = row.timestamp
            eeg_index = merged[merged["timestamp"] > timestamp].iloc[0]["index"]
            merged.loc[prev_eeg_index : eeg_index - 1, "image_id"] = current_image
            prev_eeg_index = eeg_index
            current_image = row.new_image
        merged.loc[eeg_index:, "image_id"] = current_image

        current_status = STATUS_TRANSITION
        prev_eeg_index = 0
        for row in marker_new_status_rows.itertuples():
            timestamp = row.timestamp
            eeg_index = merged[merged["timestamp"] > timestamp].iloc[0]["index"]
            merged.loc[prev_eeg_index : eeg_index - 1, "status"] = current_status
            prev_eeg_index = eeg_index
            current_status = row.new_status
        merged.loc[eeg_index:, "image_id"] = current_status

        merged["transition"] = (merged["status"] == STATUS_TRANSITION).astype(int)
        merged["baseline"] = (merged["status"] == STATUS_BASELINE).astype(int)
        merged["imagine"] = (merged["status"] == STATUS_IMAGINE).astype(int)
        merged["look"] = (merged["status"] == STATUS_LOOK).astype(int)
        merged["imagine_eyes_closed"] = (
            merged["status"] == STATUS_IMAGINE_EYES_CLOSED
        ).astype(int)
        merged["done"] = (merged["status"] == STATUS_DONE).astype(int)

        for i in range(self.num_imgs):
            merged[f"image_{i}"] = (merged["image_id"] == i).astype(int)
        merged["image_none"] = (merged["image_id"] == IMAGE_NONE).astype(int)

        return merged

    def pause(self):
        self.paused = True

    def unpause(self):
        # Flush the inlets to remove old data
        self.eeg_inlet.flush()
        self.marker_inlet.flush()
        self.paused = False

    def stop(self):
        """Finish recording data to a CSV file."""
        self.recording = False


def test_recorder():
    collector = CSVDataRecorder(find_streams=True)

    # mock collect for 3 seconds, then sleep for 1 second 5 times
    for i in range(5):
        print(f"Starting test run {i+1}")

        collector.start(filename=f"test_data_{i+1}.csv")
        time.sleep(3)
        collector.stop()
        print(f"Finished test run {i+1}")
        time.sleep(1)

    def save_and_close(self):
        """Save remaining data and close the file properly."""
        print("Saving EEG data before exiting...")
        self.file.flush()
        os.fsync(self.file.fileno())  # Ensure data is written to disk
        self.file.close()
        print("Data saved. Session closed.")

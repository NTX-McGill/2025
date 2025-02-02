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

        # Flush the inlets to remove old data
        self.eeg_inlet.flush()
        self.marker_inlet.flush()

        timestamp_list = np.array([])
        channel_lists: typing.List[np.ndarray] = list()
        image_id_list = np.array([], dtype=np.int8)
        status_list = np.array([], dtype=np.int8)

        for i in range(8):
            channel_lists.append(np.array([]))

        buffer_size = 0
        status = STATUS_TRANSITION
        image = IMAGE_NONE

        while self.recording:
            # PROBLEM - we need to merge the two (EEG and Marker) LSL streams into one
            # Assume we never get two markers for one EEG sample
            # Therefore when we pull a marker, we can attach it to the next pulled EEG sample
            # This effectively discards the marker timestamps but the EEG is recorded so quickly that it doesn't matter (?)

            eeg_sample, eeg_timestamp = self.eeg_inlet.pull_sample()
            marker_sample, _ = self.marker_inlet.pull_sample(0.0)

            if marker_sample is not None and marker_sample[0] is not None:
                has_new_image, new_image, has_new_status, new_status = marker_sample
                if has_new_image:
                    image = new_image
                if has_new_status:
                    status = new_status

            image_id_list = np.append(image_id_list, image)
            status_list = np.append(status_list, status)
            timestamp_list = np.append(timestamp_list, eeg_timestamp)
            for i in range(8):
                channel_lists[i] = np.append(channel_lists[i], eeg_sample[i])

            buffer_size += 1
            if buffer_size >= 16384:
                threading.Thread(
                    target=self._save_buffer,
                    args=[
                        filename,
                        timestamp_list,
                        channel_lists,
                        image_id_list,
                        status_list,
                    ],
                ).start()
                buffer_size = 0
                timestamp_list = np.array([])
                channel_lists: typing.List[np.ndarray] = list()
                image_id_list = np.array([], dtype=np.int8)
                status_list = np.array([], dtype=np.int8)
                for i in range(8):
                    channel_lists.append(np.array([]))

        print(timestamp_list)
        self._save_buffer(
            filename, timestamp_list, channel_lists, image_id_list, status_list
        )

    def _save_buffer(
        self, filename, timestamp_list, channel_lists, image_id_list, status_list
    ):

        df = pd.DataFrame(
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
                "image_id",
                "status",
            ]
        )

        df["timestamp"] = timestamp_list
        for i in range(8):
            df[f"ch{i+1}"] = channel_lists[i]

        df["transition"] = status_list == STATUS_TRANSITION
        df["baseline"] = status_list == STATUS_BASELINE
        df["imagine"] = status_list == STATUS_IMAGINE
        df["look"] = status_list == STATUS_LOOK
        df["imagine_eyes_closed"] = status_list == STATUS_IMAGINE_EYES_CLOSED
        df["done"] = status_list == STATUS_DONE

        for i in range(self.num_imgs):
            df[f"image_{i}"] = image_id_list == i
        df["image_none"] = image_id_list == IMAGE_NONE

        filepath = Path(f"collected_data/{filename}")
        filepath.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(
            filepath, mode="a", index=False, header=(not os.path.exists(filepath))
        )

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

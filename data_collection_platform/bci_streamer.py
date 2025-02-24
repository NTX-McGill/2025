from OpenBCI_LSL.lib.open_bci_v3 import OpenBCIBoard
import threading
import time


class BciStreamer:
    """Class to interface with the OpenBCI board for streaming EEG data."""

    def __init__(self, port=None):
        """Initialize the BCI streamer. Finds the board by default or uses a specified port."""
        if port is None:
            self.board = OpenBCIBoard()
        else:
            self.board = OpenBCIBoard(port=port)

    def start_streaming(self, on_sample):
        """Start streaming data from the OpenBCI board."""
        print("Streaming started.\n")
        board_thread = threading.Thread(
            target=self.board.start_streaming, args=(on_sample, -1)
        )
        board_thread.daemon = True  # Will stop on exit
        board_thread.start()

    def stop_streaming(self):
        """Stop streaming data and clean up the serial port."""
        self.board.stop()

        # Clean up any leftover bytes from the serial port
        time.sleep(0.1)
        line = ""
        while self.board.ser.inWaiting():
            c = self.board.ser.read().decode("utf-8", errors="replace")
            line += c
            time.sleep(0.001)
            if c == "\n":
                line = ""
        print("Streaming paused.\n")


    def stop_stream(self):
        """Stop streaming EEG data gracefully."""
        print("Stopping EEG stream...")
        self.inlet.close_stream()
        print("EEG stream stopped.")

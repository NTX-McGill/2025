from constants import *
import pylsl
import logging

logger = logging.getLogger(__name__)


def decode_status(status: int) -> str:
    """Decode a marker from the LSL stream."""

    if status == STATUS_TRANSITION:
        return "transition"
    elif status == STATUS_BASELINE:
        return "baseline"
    elif status == STATUS_IMAGINE:
        return "imagine"
    elif status == STATUS_LOOK:
        return "look"
    elif status == STATUS_IMAGINE_EYES_CLOSED:
        return "imagine-eyes-closed"
    elif status == STATUS_DONE:
        return "done"
    else:
        return "UNKNOWN"


class MarkerOutlet:
    """This class creates and sends markers to an LSL stream."""

    def __init__(self):
        info = pylsl.StreamInfo(
            "Neurotech markers", "Markers", 4, 0, "int32", "data-collection-markers"
        )
        self.outlet = pylsl.StreamOutlet(info)

    def send(self, new_image=None, new_status=None):
        """Send a marker to the LSL stream."""
        sample = [
            SHOULD_UPDATE if new_image is not None else NO_UPDATE,
            new_image if new_image is not None else IMAGE_NONE,
            SHOULD_UPDATE if new_status is not None else NO_UPDATE,
            new_status if new_status is not None else NO_UPDATE,
        ]
        self.outlet.push_sample(sample)
        logger.debug(f"Sent update: {sample}")

    def send_new_image(self, new_image):
        """Send a new image marker to the LSL stream."""
        self.send(new_image=new_image)

    def send_transition(self, new_status):
        """Send a transition marker to the LSL stream."""
        self.send(new_status=new_status)

"""File containing constants used in the project
"""

STATUS_BASELINE = 0
"""Status code for baseline, i.e. doing nothing
"""

STATUS_IMAGINE = 1
"""Status code for imagine state, i.e. imagining an apple
"""

STATUS_LOOK = 2
"""Status code for looking at image state, i.e. looking at an image of an apple
"""

STATUS_IMAGINE_EYES_CLOSED = 3
"""Status code for imagine state with eyes closed, i.e. imagining an apple with eyes closed
"""

STATUS_TRANSITION = -1
"""Status code for transition state, i.e. transitioning between states
"""

STATUS_DONE = -2
"""Status code for done state, i.e. data collection is done
"""

IMAGE_NONE = -1
"""Status code for no image, i.e. no image is being displayed
"""

TIME_ACTIVE = 30
"""How long the active states last in seconds
"""

TIME_COUNTDOWN = 5
"""How long the countdown states last in seconds
"""

TIME_REST = 5
"""How long the rest state lasts in seconds
"""

NO_UPDATE = 0
"""Code if state (image or experiment) has not been updated
"""

SHOULD_UPDATE = 1
"""Code if state (image or experiment) has been updated
"""

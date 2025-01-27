import sys
import pygame
from pygame.locals import *
import threading
import os  # To extract the image name from the file path


class Context:
    def __init__(
        self,
        train_sequence,
        work_duration,
        rest_duration,
        image_list,
        on_home_screen,
        on_baseline,
        on_imagine,
        on_white_screen_1,
        on_rest_1,
        on_look_at_image,
        on_rest_2,
        on_close_eyes_imagine,
        on_white_screen_2,
        on_rest_3,
        on_cycle_complete,
        on_stop,
    ):
        self.train_sequence = train_sequence
        self.current_stage = ""
        self.train_index = 0
        self.cycle_count = 0  # Counter for completed cycles
        self.image_index = 0  # Index to track the current image
        self.image_list = image_list  # List of images
        self.work_duration = work_duration
        self.rest_duration = rest_duration
        self.baseline_done = False  # Ensure baseline happens only once

        # Callbacks for each stage
        self._on_home_screen = on_home_screen
        self._on_baseline = on_baseline
        self._on_imagine = on_imagine
        self._on_white_screen_1 = on_white_screen_1
        self._on_rest_1 = on_rest_1
        self._on_look_at_image = on_look_at_image
        self._on_rest_2 = on_rest_2
        self._on_close_eyes_imagine = on_close_eyes_imagine
        self._on_white_screen_2 = on_white_screen_2
        self._on_rest_3 = on_rest_3
        self._on_cycle_complete = on_cycle_complete
        self._on_stop = on_stop

    def on_home_screen(self):
        self.current_stage = "home_screen"
        self._on_home_screen()

    def on_baseline(self):
        if not self.baseline_done:  # Ensure baseline happens only once
            self.current_stage = "baseline"
            self._on_baseline()
            self.baseline_done = True
            threading.Timer(10, self.on_next_stage).start()  # Proceed to the first stage after baseline

    def on_imagine(self):
        self.current_stage = "imagine"
        self._on_imagine()
        threading.Timer(3, self.on_next_stage).start()

    def on_white_screen_1(self):
        self.current_stage = "white_screen_1"
        self._on_white_screen_1()
        threading.Timer(10, self.on_next_stage).start()

    def on_rest_1(self):
        self.current_stage = "rest_1"
        self._on_rest_1()
        threading.Timer(5, self.on_next_stage).start()

    def on_look_at_image(self):
        self.current_stage = "look_at_image"
        if self.image_index < len(self.image_list):
            self._on_look_at_image(self.image_list[self.image_index])
            threading.Timer(10, self.on_next_stage).start()
        else:
            self.on_stop()  # If no images left,

    def on_rest_2(self):
        self.current_stage = "rest_2"
        self._on_rest_2()
        threading.Timer(5, self.on_next_stage).start()

    def on_close_eyes_imagine(self):
        self.current_stage = "close_eyes_imagine"
        self._on_close_eyes_imagine()
        threading.Timer(3, self.on_next_stage).start()

    def on_white_screen_2(self):
        self.current_stage = "white_screen_2"
        self._on_white_screen_2()
        threading.Timer(10, self.on_next_stage).start()

    def on_rest_3(self):
        self.current_stage = "rest_3"
        self._on_rest_3()
        threading.Timer(5, self.on_next_cycle).start()  # Conclude the cycle and start the next one

    def on_next_stage(self):
        # Get the next stage from the train_sequence
        if self.train_index >= len(self.train_sequence):
            return  # No more stages in the current cycle

        next_stage = self.train_sequence[self.train_index]
        self.train_index += 1

        print(f"Transitioning to: {next_stage}, train_index: {self.train_index}")

        # Move to the next stage
        if next_stage == "imagine":
            self.on_imagine()
        elif next_stage == "white_screen_1":
            self.on_white_screen_1()
        elif next_stage == "rest_1":
            self.on_rest_1()
        elif next_stage == "look_at_image":
            self.on_look_at_image()
        elif next_stage == "rest_2":
            self.on_rest_2()
        elif next_stage == "close_eyes_imagine":
            self.on_close_eyes_imagine()
        elif next_stage == "white_screen_2":
            self.on_white_screen_2()
        elif next_stage == "rest_3":
            self.on_rest_3()

    def on_next_cycle(self):
        self.train_index = 0  # Reset the train sequence index
        self.image_index += 1  # Move to the next image
        self.cycle_count += 1  # Increment cycle count

        if self.image_index < len(self.image_list):
            self.current_stage = "cycle_complete"
            print(f"Cycle ({self.cycle_count}) Complete")
            self._on_cycle_complete(self.cycle_count)
            threading.Timer(5, self.on_imagine).start()  # Start next cycle
        else:
            print("No more images")
            self._on_stop()  # End if no more images


def update(on_start_cb):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and on_start_cb:
                on_start_cb()
                return


def show_text(screen, text, font_size=40, color=(0, 0, 100)):
    font = pygame.font.SysFont("Times New Roman", font_size, True, False)
    surface = font.render(text, True, color)
    text_rect = surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(surface, text_rect)


def draw(screen, ctx, current_image=None):
    screen.fill((255, 255, 255))  # Default white background

    if ctx.current_stage == "home_screen":
        show_text(screen, "Press SPACE to Start", font_size=40, color=("#d7d3d2"))
        show_text(screen, "NTech Data Collection Interface 2025", font_size=30, color=(0, 0, 0))

    elif ctx.current_stage == "baseline":
        show_text(screen, "Baseline", font_size=40)

    elif ctx.current_stage == "imagine":
        # Display the name of the image for "Imagine"
        if current_image:
            image_name = os.path.splitext(os.path.basename(current_image))[0]
            show_text(screen, f"Imagine: {image_name}", font_size=40)

    elif ctx.current_stage == "white_screen_1":
        screen.fill((255, 255, 255))

    elif ctx.current_stage == "rest_1":
        screen.fill((173, 216, 230))  # Light blue

    elif ctx.current_stage == "look_at_image":
        if current_image:
            try:
                image = pygame.image.load(current_image)
                image = pygame.transform.scale(image, (200, 200))
                screen.blit(image, (screen.get_width() // 2 - 100, screen.get_height() // 2 - 100))
            except pygame.error:
                show_text(screen, "Image not found", font_size=40)

    elif ctx.current_stage == "rest_2":
        screen.fill((173, 216, 230))

    elif ctx.current_stage == "close_eyes_imagine":
        # Display the name of the image for "Close Eyes and Imagine"
        if current_image:
            image_name = os.path.splitext(os.path.basename(current_image))[0]
            show_text(screen, f"Close Eyes and Imagine: {image_name}", font_size=40)

    elif ctx.current_stage == "white_screen_2":
        screen.fill((255, 255, 255))

    elif ctx.current_stage == "rest_3":
        screen.fill((173, 216, 230))

    elif ctx.current_stage == "cycle_complete":
        screen.fill((0, 0, 128))  # Navy blue background
        show_text(screen, f"Cycle ({ctx.cycle_count}) Complete", font_size=50, color=(255, 255, 255))

    elif ctx.current_stage == "complete":
        screen.fill((0, 0, 128))  # Navy blue background
        show_text(screen, "No more images. Task Complete.", font_size=40, color=(255, 255, 255))

    pygame.display.flip()


def runPyGame(
    train_sequence,
    work_duration,
    rest_duration,
    image_list,
    on_home_screen,
    on_baseline,
    on_imagine,
    on_white_screen,
    on_rest,
    on_look_at_image,
    on_close_eyes_imagine,
    on_cycle_complete,
    on_stop,
):
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Data Collection UI")

    # Create the Context object with passed parameters
    ctx = Context(
        train_sequence=train_sequence,
        work_duration=work_duration,
        rest_duration=rest_duration,
        image_list=image_list,
        on_home_screen=on_home_screen,
        on_baseline=on_baseline,
        on_imagine=on_imagine,
        on_white_screen_1=on_white_screen,
        on_rest_1=on_rest,
        on_look_at_image=on_look_at_image,
        on_rest_2=on_rest,
        on_close_eyes_imagine=on_close_eyes_imagine,
        on_white_screen_2=on_white_screen,
        on_rest_3=on_rest,
        on_cycle_complete=on_cycle_complete,
        on_stop=on_stop,
    )

    # Start the UI
    ctx.on_home_screen()

    while True:
        update(ctx.on_baseline)
        current_image = ctx.image_list[ctx.image_index] if ctx.image_index < len(ctx.image_list) else None
        draw(screen, ctx, current_image)



if __name__ == "__main__":
    runPyGame()


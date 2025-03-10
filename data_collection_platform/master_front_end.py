import sys
import pygame
from pygame.locals import *
import time
import threading
import random
import os  # To extract the image name from the file path

screen_width = 1200  # Set your desired width
screen_height = 800  # Set your desired height
screen = pygame.display.set_mode((screen_width, screen_height))  # Windowed mode


class Context:
    def __init__(
        self,
        train_sequence,
        random_sequence,
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
        on_cycle_start,
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
        self.random_trial_count = 0
        self.in_random_cycle=False
        self.image_indices = []
        self.random_sequence = random_sequence

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
        self._on_next_cycle = on_cycle_start
        self._on_stop = on_stop

    def on_home_screen(self):
        self.current_stage = "home_screen"
        # self._on_home_screen()
        # no work to be done for LSL since the state starts in STATUS_TRANSITION

    def on_instruction_screen(self):
        self.current_stage = "instruction_screen"

    def on_baseline(self,time=10):
        if not self.baseline_done:  # Ensure baseline happens only once
            self.current_stage = "baseline"
            self._on_baseline()
            # self._on_baseline()
            self.baseline_done = True
            # Immediately proceed to the next stage
            self.train_index += 1
            thread = threading.Timer(
                time,
                self.on_next_stage,
            )  # Proceed to the next stage
            thread.daemon = True
            thread.start()

    def on_imagine(self,time=4):
        self.current_stage = "imagine"
        self._on_imagine(self.image_index)
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_white_screen_1(self,time=2):
        self.current_stage = "white_screen_1"
        self._on_white_screen_1()
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_rest_1(self, time=5):
        self.current_stage = "rest_1"
        self._on_rest_1()
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_look_at_image(self,time=6):
        self.current_stage = "look_at_image"
        if self.image_index < len(self.image_list):
            self._on_look_at_image()
            thread = threading.Timer(time, self.on_next_stage)
            thread.daemon = True
            thread.start()
        else:
            self.on_stop()  # If no images left,

    def on_rest_2(self,time=5):
        self.current_stage = "rest_2"
        self._on_rest_2()
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_close_eyes_imagine(self,time=4):
        self.current_stage = "close_eyes_imagine"
        self._on_close_eyes_imagine()
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_white_screen_2(self,time=2):
        self.current_stage = "white_screen_2"
        self._on_white_screen_2()
        thread = threading.Timer(time, self.on_next_stage)
        thread.daemon = True
        thread.start()

    def on_rest_3(self,time=5):
        self.current_stage = "rest_3"
        self._on_rest_3()
        thread = threading.Timer(
            time, self.on_next_stage
        )  # Conclude the cycle and start the next one
        thread.daemon = True
        thread.start()

    def on_next_stage(self):
        # Check if we have more stages left
        if self.train_index >= len(self.train_sequence):
            self.on_next_cycle()
            return  # No more stages in the current cycle
        
        next_stage = self.train_sequence[self.train_index]
        self.train_index += 1  # Increment train index for the next stage

        #update image if in random trial
        if self.in_random_cycle:
            self.image_index = self.image_indices[self.random_trial_count]
            if (next_stage == "rest_1" or next_stage == "rest_2" or next_stage == "rest_3"):
                self.random_trial_count+=1

            print(f"Transitioning to: {next_stage}, train_index: {self.train_index}")

            if next_stage == "imagine":
                self.on_imagine(3)
            elif next_stage == "white_screen_1":
                self.on_white_screen_1(1)
            elif next_stage == "rest_1":
                self.on_rest_1(5)
            elif next_stage == "look_at_image":
                self.on_look_at_image(3)
            elif next_stage == "rest_2":
                self.on_rest_2()
            elif next_stage == "close_eyes_imagine":
                self.on_close_eyes_imagine(3)
            elif next_stage == "white_screen_2":
                self.on_white_screen_2(1)
            elif next_stage == "rest_3":
                self.on_rest_3(5)

        else:
            print(f"Transitioning to: {next_stage}, train_index: {self.train_index}")

            # Call the appropriate stage function
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

        self.train_index = 1  # Reset to 'imagine'
        self.image_index += 1
        self.cycle_count += 1

        if not self.in_random_cycle  and self.image_index < len(self.image_list):
            
            #self.current_stage = "cycle_complete"
            #ctx._on_next_cycle()
            self.on_next_stage()
            #self._on_cycle_complete()
            #print(f"Cycle ({self.cycle_count}) Complete - Waiting for User Input")

            # Now, the main event loop (update function) will handle user input (Y/N)
        elif self.in_random_cycle == False:
            self.current_stage = "priming_complete"
            self._on_cycle_complete()
            print("Priming phase complete. Continue to random trials?")
            
            
        else:
            self.current_stage = "complete"
            self._on_stop()


    def random_cycle(self,num_trials=6,seed=1):
        self.train_sequence = []
        self.image_indices = []

        stages = [["imagine", "white_screen_1","rest_1"],
        ["look_at_image","rest_2"],
        #["close_eyes_imagine","white_screen_2","rest_3"],
        ]
        random.seed(seed)

        if self.random_sequence == None:
            for i in range(num_trials):
                self.image_indices.append(random.randint(0,len(self.image_list)-1))
                self.train_sequence.extend(random.choice(stages))
        else:
            self.train_sequence = self.random_sequence
            for stage in self.random_sequence:
                if (stage == "imagine" or stage == "look_at_image" or stage == "close_eyes_imagine"):
                    self.image_indices.append(random.randint(0,len(self.image_list)-1))
        
        print("Ramdom sequence initialized: ",self.train_sequence)
        print("Random image indices: ",self.image_indices)
        
        self.in_random_cycle = True
        self.random_trial_count = 0
        self.train_index = 0
        self.image_index=self.image_indices[0]
        
        self.on_next_stage()




def fade_screen(screen, duration=500):
    fade = pygame.Surface((screen.get_width(), screen.get_height()))
    fade.fill((240, 240, 240))  # Light gray fade
    for alpha in range(0, 255, 10):  # Gradual fade effect
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.update()
        pygame.time.delay(duration // 50)


def show_text(screen, text, font_size=30, color=(51, 51, 51), y_offset=0, align="left"):
    font = pygame.font.SysFont("Arial", font_size, True, False)
    surface = font.render(text, True, color)
    if align == "center":
        text_rect = surface.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 + y_offset)
        )
    else:
        text_rect = surface.get_rect(left=50, top=screen.get_height() // 3 + y_offset)
    screen.blit(surface, text_rect)


def progress_bar(screen, duration):
    bar_width = screen.get_width() - 100
    bar_height = 30  # Smaller height for minimal distraction
    bar_x = (screen.get_width() - bar_width) // 2
    bar_y = screen.get_height() - bar_height - 50  # Higher placement

    start_time = time.time()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        elapsed_time = time.time() - start_time
        progress = min(elapsed_time / duration, 1.0)  # Scale progress correctly

        pygame.draw.rect(
            screen,
            (90, 125, 154),
            pygame.Rect(bar_x, bar_y, bar_width * progress, bar_height),
        )
        pygame.display.flip()

        if elapsed_time >= duration:
            time.sleep(0.3)  # Shorter pause at the end
            running = False


def draw(screen, ctx, current_image=None):
    if ctx.current_stage == "instruction_screen":
        screen.fill((240, 240, 240))  # Soft gray background
        instructions = [
            "• You will go through a sequence of prompts.",
            "• First, a baseline calibration will be recorded.",
            "• Rest periods will be indicated by a LIGHT BLUE screen.",
            "• Each prompt lasts for a few seconds.",
            "• There will be multiple cycles.",
            "• Press SPACE to begin.",
        ]
        for i, line in enumerate(instructions):
            show_text(screen, line, font_size=30, y_offset=i * 40, align="left")

    elif ctx.current_stage == "home_screen":
        screen.fill((240, 240, 240))
        show_text(
            screen,
            "NTech Data Collection Interface 2025",
            font_size=30,
            align="center",
            y_offset=-30,
        )
        show_text(
            screen, "Press SPACE to Start", font_size=35, align="center", y_offset=30
        )

    elif ctx.current_stage == "baseline":
        screen.fill((240, 240, 240))

    elif ctx.current_stage == "imagine":
        screen.fill((240, 240, 240))
        if current_image:
            image_name = os.path.splitext(os.path.basename(current_image))[0]
            show_text(screen, f"Imagine: {image_name}", font_size=40, align="center")
            #progress_bar(screen, 2)

    elif ctx.current_stage == "white_screen_1":
        screen.fill((240, 240, 240))

    elif ctx.current_stage in ["rest_1", "rest_2", "rest_3"]:
        screen.fill((221, 238, 255))  # Soft blue for rest
        progress_bar(screen, 5)

    elif ctx.current_stage == "look_at_image":
        screen.fill((240, 240, 240))
        if current_image:
            try:
                image = pygame.image.load(current_image)
                image = pygame.transform.scale(image, (400, 400))
                image_rect = image.get_rect(
                    center=(screen.get_width() // 2, screen.get_height() // 2)
                )
                screen.blit(image, image_rect)
            except pygame.error:
                show_text(screen, "Image not found", font_size=40, align="center")

    elif ctx.current_stage == "close_eyes_imagine":
        screen.fill((240, 240, 240))
        if current_image:
            image_name = os.path.splitext(os.path.basename(current_image))[0]
            show_text(screen, f"Imagine: {image_name}", font_size=40, align="center")
            #progress_bar(screen, 2)

    elif ctx.current_stage == "white_screen_2":
        screen.fill((240, 240, 240))

    elif ctx.current_stage == "cycle_complete":
        screen.fill((30, 58, 95))  # Keep blue screen
        show_text(
            screen,
            "Continue?",
            font_size=50,
            color=(255, 255, 255),
            align="center",
            y_offset=-30,
        )
        show_text(
            screen,
            "[YES]    [NO]",
            font_size=40,
            color=(255, 255, 255),
            align="center",
            y_offset=30,
        )
    elif ctx.current_stage == "priming_complete":
        screen.fill((30, 58, 95))  # Keep blue screen
        show_text(
            screen,
            "Priming Phase Complete. Continue?",
            font_size=50,
            color=(255, 255, 255),
            align="center",
            y_offset=-30,
        )
        show_text(
            screen,
            "[YES]    [NO]",
            font_size=40,
            color=(255, 255, 255),
            align="center",
            y_offset=30,
        )
    elif ctx.current_stage == "complete":
        screen.fill((0, 0, 128))
        show_text(
            screen,
            "No more images. Task Complete.",
            font_size=40,
            color=(255, 255, 255),
            align="center",
        )

    pygame.display.flip()


def update(ctx):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if ctx.current_stage == "home_screen":
                    ctx.on_instruction_screen()
                elif ctx.current_stage == "instruction_screen":
                    ctx.on_baseline()
                elif ctx.current_stage == "baseline":
                    ctx.on_next_stage()
            elif event.key == pygame.K_y: 
                if ctx.current_stage == "cycle_complete":
                    print("User selected 'Yes'. Continuing to next cycle.")
                    ctx._on_next_cycle()
                    ctx.on_next_stage()
                elif  ctx.current_stage == "priming_complete":
                    print("User selected 'Yes'. Continuing to random trials.")
                    ctx._on_next_cycle()
                    ctx.random_cycle()
            elif event.key == pygame.K_n and (ctx.current_stage == "cycle_complete"or ctx.current_stage == "priming_complete"):
                print("User selected 'No'. Stopping session.")
                ctx._on_stop()

                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()


# Fix for main loop in runPyGame to pass ctx instead of ctx.on_baseline


def runPyGame(
    train_sequence,
    random_sequence,
    work_duration,
    rest_duration,
    image_list,
    on_home_screen,
    on_baseline,
    on_imagine,  # (image_id) -> None
    on_white_screen,
    on_rest,
    on_look_at_image,
    on_close_eyes_imagine,
    on_cycle_complete,
    on_cycle_start,
    on_stop,
):
    pygame.init()
    width, height = 1000, 800
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.RESIZABLE)
    pygame.display.set_caption("Data Collection UI")

    ctx = Context(
        train_sequence=train_sequence,
        random_sequence=random_sequence,
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
        on_cycle_start=on_cycle_start,
        on_stop=on_stop,
    )

    ctx.on_home_screen()

    while True:
        update(ctx)
        current_image = (
            ctx.image_list[ctx.image_index]
            if ctx.image_index < len(ctx.image_list)
            else None
        )
        draw(screen, ctx, current_image)


if __name__ == "__main__":
    train_sequence = [
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
    image_list = [
        "bci_images/Apple.png",
        "bci_images/McGill Arts Building.png",
        "bci_images/Door Handle.png",
    ]

    def on_home_screen():
        print("Home Screen")

    def on_baseline():
        print("Baseline")

    def on_imagine():
        print("Imagine Object")

    def on_white_screen():
        print("White Screen")

    def on_rest():
        print("Rest")

    def on_look_at_image(image):
        print(f"Look at Image: {image}")

    def on_close_eyes_imagine():
        print("Close Eyes and Imagine")

    def on_cycle_complete(cycle):
        print(f"Cycle {cycle} Complete")

    def on_cycle_start():
        print(f"Cycle Starting")

    def on_stop():
        print("Task Complete")
        pygame.quit()
        sys.exit()

    runPyGame(
        train_sequence=train_sequence,
        random_sequence=None,
        work_duration=15,
        rest_duration=5,
        image_list=image_list,
        on_home_screen=on_home_screen,
        on_baseline=on_baseline,
        on_imagine=on_imagine,
        on_white_screen=on_white_screen,
        on_rest=on_rest,
        on_look_at_image=on_look_at_image,
        on_close_eyes_imagine=on_close_eyes_imagine,
        on_cycle_complete=on_cycle_complete,
        on_cycle_start=on_cycle_start,
        on_stop=on_stop,
    )

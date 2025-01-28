from backend.csv_data_recorder import CSVDataRecorder
import pygame
import time
import sys

def main():
    # Prompt the user to enter a filename
    filename = input("Enter the name of the CSV file (without extension): ") + ".csv"

    # Initialize the CSVDataRecorder
    recorder = CSVDataRecorder(find_streams=True)  # Ensure LSL streams are running

    if not recorder.ready:
        print("LSL streams not ready. Please ensure EEG and Marker streams are running.")
        return

    try:
        # Initialize Pygame for key listening
        pygame.init()
        screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption("Recording EEG Data - Press ESC to Stop")

        # Start recording to the specified file
        print(f"Starting data recording... Saving to: {filename}")
        recorder.start(filename=filename)

        # Listen for key events in the Pygame loop
        print("Recording... Press ESC to stop.")
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # Stop recording on ESC key
                        running = False

            time.sleep(0.1)  # Prevent CPU overload

    finally:
        # Stop recording and clean up
        print("Stopping data recording...")
        recorder.stop()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()


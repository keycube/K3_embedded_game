import board
import digitalio
import storage

button = digitalio.DigitalInOut(board.GP16)

button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# If the button pin (GP16) is connected to the ground during PICO's connection to the
# computer (after the led's 3 blinks), the PICO can now write to its storage and the
# computer will be in read only mode. 
storage.remount("/", readonly= not button.value)

import board
import displayio
import framebufferio
import sharpdisplay
import busio

import digitalio
import time

from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from terminalio import FONT

displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Creating root group for display
splash = displayio.Group()
display.root_group = splash

# Setting black-and-white palette
color_palette = displayio.Palette(2)
color_palette[0] = 0x000000
color_palette[1] = 0xFFFFFF

# Setting board button functionality
board_button = digitalio.DigitalInOut(board.GP15)
board_button.switch_to_input(pull=digitalio.Pull.DOWN)


# Loading bitmap
loading_bitmap = displayio.Bitmap(400, 240, 2)
loading_tilegrid = displayio.TileGrid(loading_bitmap, pixel_shader = color_palette)
splash.append(loading_tilegrid)

# Base rectangle
rect = Rect(10, 10, 380, 220, fill=None, outline=color_palette[1])
splash.append(rect)

# Win message
win_label = Label(font=FONT, text="WIN!!!", color=color_palette[0], x=70, y=120, scale=8, line_spacing=1.2)

win_group = displayio.Group()
win_group.hidden = True
win_group.append(win_label)
splash.append(win_group)

# "Game" variables
min_progress = 11
max_progress = 389

progress = min_progress
win = False

# "Game" loop
while not win:
    # If button held, progress
    if board_button.value:
        if progress < max_progress:
            for y in range(11, 229):
                loading_bitmap[progress, y] = 1
                loading_bitmap[progress+1, y] = 1
            progress += 2
        else:
            win = True
    # If button not held, regress
    elif progress >= min_progress:
        for y in range(11, 229):
            loading_bitmap[progress-1, y] = 0
            loading_bitmap[progress-2, y] = 0
        progress -= 2

    time.sleep(1/60)

# Display win message, and finish "game"
win_group.hidden = False

while True:
    pass

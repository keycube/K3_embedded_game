import board
import displayio
import framebufferio
import sharpdisplay
import busio
import time

from adafruit_display_shapes.line import Line

displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)


splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(400, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette)
splash.append(bg_sprite)



gap = 100
lines = []
pos = 0
for i in range (400 / gap):
    x = i*gap

    line = Line(x, 0, x+30, 240, 0xFFFFFF)
    lines.append(line)
    splash.append(line)

def Update(delta : float):
    pos = delta * 15
    for i in range(len(lines)):
        line = lines[i]
        x = int(pos)
        newline = Line(line.x + x, 0,line.x + x+30, 240, 0xFFFFFF)
        splash[i+1] = newline
        lines[i] = newline



TARGETED_FPS = 20
target_frame_time = 1/TARGETED_FPS
time_at_frame_start = time.monotonic()
while True:
    delta = time.monotonic() - time_at_frame_start
    if (delta > target_frame_time):
        time_at_frame_start = time.monotonic()

        Update(delta)

# type: ignore
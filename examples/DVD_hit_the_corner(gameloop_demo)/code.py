import board
import displayio
import framebufferio
import sharpdisplay
import busio
import adafruit_imageload
import time


displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Créer le groupe pour l'affichage
viewport = displayio.Group()
display.root_group = viewport

cursor_group = displayio.Group()
cursor_group.x = 0
cursor_group.y = 0
cursor_group.scale = 1

cursor_bitmap, cursor_palette = adafruit_imageload.load("/cursor.bmp",\
    bitmap=displayio.Bitmap,\
    palette=displayio.Palette)


cursor_tilegrid = displayio.TileGrid(cursor_bitmap, pixel_shader=cursor_palette)

cursor_group.append(cursor_tilegrid)
viewport.append(cursor_group)

x = 0
y = 0
speedx = 100
speedy = 100
maxwidth = 400 - 16 * cursor_group.scale
maxheight = 240 - 16 * cursor_group.scale

TARGETED_FPS = 60
target_frame_time = 1/TARGETED_FPS
time_at_frame_start = time.monotonic()
while True:
    delta = time.monotonic() - time_at_frame_start
    if (delta > target_frame_time):
        time_at_frame_start = time.monotonic()

        x += delta * speedx
        y += delta * speedy

        if (x < 0):
            x = 0
            speedx *= -1
        elif (x > maxwidth):
            x = maxwidth
            speedx *= -1
        if (y < 0):
            y = 0
            speedy *= -1
        elif (y > maxheight):
            y = maxheight
            speedy *= -1

        cursor_group.x = int(x)
        cursor_group.y = int(y)
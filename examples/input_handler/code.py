import board
import displayio
import framebufferio
import sharpdisplay
import busio
import adafruit_imageload
import time

import usb_cdc
usb_cdc.console.timeout = 0

current_inputs = []

def get_line():
    data = usb_cdc.console.readline(-1)

    if data:
        str = data.decode("utf-8")
        if ("Released" in str or "Pressed" in str):
            return str

    return ""

def get_input_from_line(line):
    i = 1
    while (line[i] != ' '):
        i+=1
    key_code = int(line[:i])

    if "Released" in line:
        return (key_code, False)
    if "Pressed" in line:
        return (key_code, True)

    print("Error: Incorrect input line format!")

def update_input(input_info):
    # input_info is a tuple with element 0 being key code and element 1 whether it was pressed or released
    if (input_info[1] and input_info[0] not in current_inputs):
        current_inputs.append(input_info[0])
    elif ((not input_info[1]) and input_info[0] in current_inputs):
        current_inputs.remove(input_info[0])

def update_all_inputs():
    input_line = get_line()
    if (input_line != ""):
        update_input(get_input_from_line(input_line))


displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Créer le groupe pour l'affichage
# viewport = displayio.Group()
# display.root_group = viewport

# cursor_group = displayio.Group()
# cursor_group.x = 0
# cursor_group.y = 0
# cursor_group.scale = 1

# cursor_bitmap, cursor_palette = adafruit_imageload.load("/cursor.bmp",\
#     bitmap=displayio.Bitmap,\
#     palette=displayio.Palette)


# cursor_tilegrid = displayio.TileGrid(cursor_bitmap, pixel_shader=cursor_palette)

# cursor_group.append(cursor_tilegrid)
# viewport.append(cursor_group)

# x = 0
# y = 0
# speedx = 100
# speedy = 100
# maxwidth = 400 - 16 * cursor_group.scale
# maxheight = 240 - 16 * cursor_group.scale

TARGETED_FPS = 5
target_frame_time = 1/TARGETED_FPS
time_at_frame_start = time.monotonic()
while True:
    update_all_inputs()

    delta = time.monotonic() - time_at_frame_start
    if (delta > target_frame_time):
        time_at_frame_start = time.monotonic()

        print(current_inputs)


        # x += delta * speedx
        # y += delta * speedy

        # if (x < 0):
        #     x = 0
        #     speedx *= -1
        # elif (x > maxwidth):
        #     x = maxwidth
        #     speedx *= -1
        # if (y < 0):
        #     y = 0
        #     speedy *= -1
        # elif (y > maxheight):
        #     y = maxheight
        #     speedy *= -1

        # cursor_group.x = int(x)
        # cursor_group.y = int(y)

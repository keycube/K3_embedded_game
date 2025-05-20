import board
import displayio
import framebufferio
import sharpdisplay
import busio
import math


def shader(bitmap):
    branch_count = 1000
    branch_length = 120*120
    core_length = 30*30

    for x in range(400):
        for y in range(240):

            dist_x = x-200
            dist_y = y-120
            angle  = math.atan2(dist_y, dist_x)
            if dist_x*dist_x + dist_y*dist_y < \
            math.sin(angle * branch_count) * branch_length + core_length :
                bitmap[x, y] = 1
            else:
                bitmap[x, y] = 0

displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Créer le groupe pour l'affichage
image = displayio.Group()
display.root_group = image

color_bitmap = displayio.Bitmap(400, 240, 2)
color_palette = displayio.Palette(2)
color_palette[0] = 0x000000
color_palette[1] = 0xFFFFFF

shader(color_bitmap)

# Create a TileGrid to hold the bitmap
tile_grid = displayio.TileGrid(color_bitmap, pixel_shader=color_palette)

image.append(tile_grid)
print("ok")

while True:
    pass

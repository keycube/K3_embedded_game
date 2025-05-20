import board
import displayio
import framebufferio
import sharpdisplay
import busio
import adafruit_imageload

displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Créer le groupe pour l'affichage
viewport = displayio.Group()
display.root_group = viewport

tileset_bitmap, tileset_palette = adafruit_imageload.load("/tileset.bmp",\
    bitmap=displayio.Bitmap,\
    palette=displayio.Palette)

tilemap = displayio.TileGrid(tileset_bitmap, pixel_shader=tileset_palette,
                             width=6, height=3,
                             tile_width=64, tile_height=64,
                             default_tile=0)

map=[0,2,0,1,1,2,
     8,10,8,9,9,10,
     12,13,13,13,14,15]

for i in range(len(map)):
    tilemap[i] = map[i]

viewport.append(tilemap)

while True:
    pass

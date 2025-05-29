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


try:
    with open("/log.txt", "w") as fp:
        for i in range(15):
            for j in range(i):
                fp.write("{0}".format(j+i))
            fp.write("\n")
except OSError as e: 
    print(e.strerror)


while True:
    pass
 # type: ignore
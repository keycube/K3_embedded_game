import board
import displayio
import framebufferio
import sharpdisplay
import busio

import time
import usb_cdc

displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

# Make sure the serial console is enabled and non-blocking
usb_cdc.console.timeout = 0

print("====== STDIN ======")

while True:
    data = usb_cdc.console.readline(-1)
    if data:
        stdin = data.decode("utf-8")
        print(stdin)


    # time.sleep(1/60)
 # type: ignore

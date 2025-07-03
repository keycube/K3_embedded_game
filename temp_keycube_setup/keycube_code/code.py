import time
import board
import keypad
import neopixel
from rainbowio import colorwheel
import board
from analogio import AnalogIn
from LightManager import LightManager
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

class State:
     IDDLE, PRESSED, FOCUSED = range(3)

pixels = neopixel.NeoPixel(board.SDA, 80, brightness=0.1, auto_write=False)
keys = keypad.KeyMatrix(
    row_pins=(board.A0, board.A1, board.A2, board.A3, board.A4, board.A5, board.SCK, board.MOSI, board.MISO, board.RX, board.TX, board.D2),
    column_pins=(board.D9, board.D6, board.D5, board.SCL, board.D13, board.D12, board.D11, board.D10),

    columns_to_anodes=False,
)

kMat = {
    0:48,
    8:55,
    16:56,
    24:63,
    1:49,
    9:54,
    17:57,
    25:62,
    2:50,
    10:53,
    18:58,
    26:61,
    3:51,
    11:52,
    19:59,
    27:60,

    36:0,
    44:7,
    52:8,
    60:15,
    37:1,
    45:6,
    53:9,
    61:14,
    38:2,
    46:5,
    54:10,
    62:13,
    39:3,
    47:4,
    55:11,
    63:12,

    35:35,
    34:34,
    33:33,
    32:32,
    40:39,
    41:38,
    42:37,
    43:36,
    48:40,
    49:41,
    50:42,
    51:43,
    56:47,
    57:46,
    58:45,
    59:44,

    28:31,
    29:30,
    30:29,
    31:28,
    20:24,
    21:25,
    22:26,
    23:27,
    12:23,
    13:22,
    14:21,
    15:20,
    7:19,
    6:18,
    5:17,
    4:16,

    68:64,
    69:65,
    77:66,
    76:67,
    84:68,
    85:69,
    93:70,
    92:71,
    94:72,
    95:73,
    86:74,
    87:75,
    78:76,
    79:77,
    70:78,
    71:79
}
def kToP(key_number):
    return kMat[key_number]

k3Code = {
    0:0,
    1:0,
    2:0,
    3:0,
    4:0,
    5:0,
    6:0,
    7:0,
    8:0,
    9:0,
    10:0,
    11:0,
    12:0,
    13:0,
    14:0,
    15:0,
    16:0,
    17:0,
    18:0,
    19:0,
    20:0,
    21:0,
    22:0,
    23:0,
    24:0,
    25:0,
    26:0,
    27:0,
    28:0,
    29:0,
    30:0,
    31:0,
    32:Keycode.T,
    33:Keycode.G,
    34:Keycode.SPACE,
    35:Keycode.SPACE,
    36:Keycode.Z,
    37:Keycode.X,
    38:Keycode.C,
    39:Keycode.V,
    40:Keycode.F,
    41:Keycode.D,
    42:Keycode.S,
    43:Keycode.A,
    44:Keycode.Q,
    45:Keycode.W,
    46:Keycode.E,
    47:Keycode.R,
    48:Keycode.SPACE,
    49:Keycode.SPACE,
    50:Keycode.SPACE,
    51:Keycode.Y,
    52:Keycode.G,
    53:Keycode.B,
    54:Keycode.N,
    55:Keycode.M,
    56:Keycode.L,
    57:Keycode.K,
    58:Keycode.J,
    59:Keycode.H,
    60:Keycode.U,
    61:Keycode.I,
    62:Keycode.O,
    63:Keycode.P,
    64:Keycode.LEFT_CONTROL,
    65:Keycode.SPACE,
    66:Keycode.SPACE,
    67:Keycode.SPACE,
    68:Keycode.SPACE,
    69:Keycode.FORWARD_SLASH,
    70:Keycode.ENTER,
    71:Keycode.BACKSPACE,
    72:Keycode.SPACE,
    73:Keycode.SPACE,
    74:Keycode.SPACE,
    75:Keycode.SPACE,
    76:Keycode.KEYPAD_PERIOD,
    77:Keycode.QUOTE,
    78:Keycode.COMMA,
    79:Keycode.LEFT_SHIFT,
}

def k3GetCode(k3Num):
    return k3Code[k3Num]

K3State = {
    0:State.IDDLE,
    1:State.IDDLE,
    2:State.IDDLE,
    3:State.IDDLE,
    4:State.IDDLE,
    5:State.IDDLE,
    6:State.IDDLE,
    7:State.IDDLE,
    8:State.IDDLE,
    9:State.IDDLE,
    10:State.IDDLE,
    11:State.IDDLE,
    12:State.IDDLE,
    13:State.IDDLE,
    14:State.IDDLE,
    15:State.IDDLE,
    16:State.IDDLE,
    17:State.IDDLE,
    18:State.IDDLE,
    19:State.IDDLE,
    20:State.IDDLE,
    21:State.IDDLE,
    22:State.IDDLE,
    23:State.IDDLE,
    24:State.IDDLE,
    25:State.IDDLE,
    26:State.IDDLE,
    27:State.IDDLE,
    28:State.IDDLE,
    29:State.IDDLE,
    30:State.IDDLE,
    31:State.IDDLE,
    32:State.IDDLE,
    33:State.IDDLE,
    34:State.IDDLE,
    35:State.IDDLE,
    36:State.IDDLE,
    37:State.IDDLE,
    38:State.IDDLE,
    39:State.IDDLE,
    40:State.IDDLE,
    41:State.IDDLE,
    42:State.IDDLE,
    43:State.IDDLE,
    44:State.IDDLE,
    45:State.IDDLE,
    46:State.IDDLE,
    47:State.IDDLE,
    48:State.IDDLE,
    49:State.IDDLE,
    50:State.IDDLE,
    51:State.IDDLE,
    52:State.IDDLE,
    53:State.IDDLE,
    54:State.IDDLE,
    55:State.IDDLE,
    56:State.IDDLE,
    57:State.IDDLE,
    58:State.IDDLE,
    59:State.IDDLE,
    60:State.IDDLE,
    61:State.IDDLE,
    62:State.IDDLE,
    63:State.IDDLE,
    64:State.IDDLE,
    65:State.IDDLE,
    66:State.IDDLE,
    67:State.IDDLE,
    68:State.IDDLE,
    69:State.IDDLE,
    70:State.IDDLE,
    71:State.IDDLE,
    72:State.IDDLE,
    73:State.IDDLE,
    74:State.IDDLE,
    75:State.IDDLE,
    76:State.IDDLE,
    77:State.IDDLE,
    78:State.IDDLE,
    79:State.IDDLE,
}

def k3GetState(k3Num):
    return K3State[k3Num]

def k3SetState(k3Num, State):
    K3State[k3Num] = State

SIZE = 4
TF = [
        [73, 72, 70, 71],
        [75, 74, 69, 68],
        [77, 76, 66, 67],
        [79, 78, 65, 64]
    ] # Top Face Pattern
NF = [
        [63, 56, 55, 48],
        [62, 57, 54, 49],
        [61, 58, 53, 50],
        [60, 59, 52, 51]
    ] # North Face Pattern
SF = [
        [ 3,  4, 11, 12],
        [ 2,  5, 10, 13],
        [ 1,  6,  9, 14],
        [ 0,  7,  8, 15]
    ] # South Face Pattern
EF = [
        [28, 29, 30, 31],
        [27, 26, 25, 24],
        [20, 21, 22, 23],
        [19, 18, 17, 16]
    ] # East Face Pattern
WF = [
        [44, 45, 46, 47],
        [43, 42, 41, 40],
        [36, 37, 38, 39],
        [35, 34, 33, 32]
    ] # West Face Pattern

cube = LightManager(SIZE, pixels, keys, TF, NF, SF, EF, WF)

cube.p.fill((0, 0, 0))

interpolateColor = cube.interpolate_color((255, 0, 0), (0, 0, 255), 254)

keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)

while True:
        if cube.color == 1: # Raimbow Effect 1
            cube.RAIMBOWDIRECTION = 1
            for i in range(0, len(cube.RP)):
                for j in range(0, len(cube.RP[i])):
                    if k3GetState(cube.RP[i][j]) == State.IDDLE:
                        cube.p[cube.RP[i][j]] = colorwheel((cube.RAIMBOWCOLOR + (i * 10)) % 255)

        key_event = keys.events.get()
        if key_event:
            if key_event.pressed:
                # Switch light effect
                if (kToP(key_event.key_number) == cube.colorSwitch):
                    cube.color = (cube.color + 1) % (cube.colorEffect + 1)
                    cube.p.fill((0, 0, 0))
                    cube.BRIGHTNESS = 0.1

                # Click effect Press
                if cube.color == 1:
                    cube.p[kToP(key_event.key_number)] = (255, 0, 0)
                    print("{keyCode} : Pressed".format(keyCode=kToP(key_event.key_number)))
                    k3SetState(kToP(key_event.key_number), State.PRESSED)
                    # keyboard.press(k3GetCode(kToP(key_event.key_number)))
            else:
                # Click effect Release
                if cube.color == 1:
                    cube.p[kToP(key_event.key_number)] = (0, 0, 0)
                    print("{keyCode} : Released".format(keyCode=kToP(key_event.key_number)))
                    k3SetState(kToP(key_event.key_number), State.IDDLE)
                    # keyboard.release(k3GetCode(kToP(key_event.key_number)))

        cube.brightnessUpdate()
        cube.raimbowColorUpdate()
        cube.p.show()

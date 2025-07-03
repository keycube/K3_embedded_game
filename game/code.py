import gc
import adafruit_bitmap_font.bitmap_font
import board
import displayio
import framebufferio
import sharpdisplay
import busio
import adafruit_imageload
import time
import random
import ulab.numpy as np

from adafruit_display_text.label import Label
import adafruit_bitmap_font
from terminalio import FONT

import usb_cdc
usb_cdc.console.timeout = 0


### NOTE: This script was made with the mindset of not making classes, for optimization purposes.
### We realized too late this wasn't the best idea.
### Sorry if this is a mess to read/modify...


def TEMP_print_memory_usage():
    """Temporary function that prints out the memory usage."""

    gc.collect()  # Run garbage collection to get accurate numbers
    total = gc.mem_alloc() + gc.mem_free()
    used = gc.mem_alloc()
    free = gc.mem_free()

    print(f"RAM used: {used} / {total} ({(used*100) // total}%)")


#######################################
##########--- Input setup ---##########
#######################################


def get_line():
    """NOTE: This is a temporary function that's used to get input with the following setup: Microcontroller and Keycube both plugged in the computer + Python middleware script
    Once the final setup (screen directly on the Keycube) is achieved, this function won't have any use anymore.

    Gets the next line that was printed in the console.

    Returns
    -------
    str
        String that was printed in the microcontroller's console using the Python middleware
    """

    data = usb_cdc.console.readline(-1)

    if data:
        str = data.decode("utf-8")
        if ("Released" in str or "Pressed" in str):
            return str

    return ""

def get_input_from_line(line):
    """NOTE: This is a temporary function that's used to get input with the following setup: Microcontroller and Keycube both plugged in the computer + Python middleware script
    Once the final setup (screen directly on the Keycube) is achieved, this function won't have any use anymore.

    Takes console line and deduces input info.

    Parameters
    ----------
    line : str
        Console line (obtained from get_line())

    Returns
    -------
    tuple
        Input information
            Element 0 is the key code (int)
            Element 1 is a boolean indicating whether the key was just pressed or released
    """

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
    """
    Updates input-related variables.

    Parameters
    ----------
    input_info : tuple
        Input information (obtained from get_input_from_line())
    """

    # input_info is a tuple with element 0 being key code and element 1 whether it was pressed or released
    if (input_info[1] and input_info[0] not in current_inputs):
        current_inputs.append(input_info[0])
        inputs_pressed_this_frame.append(input_info[0])
    elif ((not input_info[1]) and input_info[0] in current_inputs):
        current_inputs.remove(input_info[0])

def update_all_inputs():
    """NOTE: This function heavily relies on temporary functions that work with the following setup: Microcontroller and Keycube both plugged in the computer + Python middleware script
    Once the final setup (screen directly on the Keycube) is achieved, this function will have to be modified.

    Takes console line info and updates input-related variables accordingly."""

    input_line = get_line()
    if (input_line != ""):
        update_input(get_input_from_line(input_line))


#######################################
########--- Game logic setup ---#######
#######################################


FILES_sprites_info_filepath = "assets/sprites/positions.txt"
FILES_sprites_incomplete_path = "assets/sprites/{}/{}.bmp"
FILES_font_filepath = "/assets/font/tahoma-12.bdf"

current_inputs = []
inputs_pressed_this_frame = []

GAME_cube_state = []
# cube_state[0] = Left / cube_state[1] = Right / cube_state[2] = Up / cube_state[3] = Bottom
# cube_state[i][j,k] => i = side, j = row, k = column

def GAME_reset_cube_state():
    """Resets the GAME_cube_state variable to its original state.
    This function must be run before starting an actual game"""

    global GAME_cube_state
    GAME_cube_state = []

    for i in range(4):
        GAME_cube_state.append(np.zeros((4,4), dtype=np.bool))

GAME_reset_cube_state()

GAME_mismatches = {} # Format of a mismatch element -> dictionary, key: coordinates of one of the mismatched tiles (always the one on the left/up side) / value: longevity of mismatch

GAME_blocked_tiles = []

GAME_score = 0
GAME_score_min_increase = 5

GAME_lives_left = 4
GAME_danger = False
GAME_end = False

GAME_longevity_warning = 5
GAME_longevity_death = 10

MENU_current_side = 4

GLOBAL_inputs_activated = True
GLOBAL_in_game = False

def toggle_tile_from_input(input, block = False):
    """Toggles an in-game tile.
    This function is used when the player toggles a tile, but also when the game does a new wave

    Parameters
    ----------
    input : int
        The key code that corresponds to the tile
    block : bool, optional
        If true, adds a cross on top of the tile and prevents player from toggling it after
        This bool is used when the game spawns waves
    """

    side, row, col = input_to_matrix_coord(input)

    # Can't toggle blocked tiles
    if ((side, row, col) in GAME_blocked_tiles):
        return

    tile_previous_state = GAME_cube_state[side][row, col]
    GAME_cube_state[side][row, col] = not tile_previous_state

    fill_tile_tilegrids[side][row][col].hidden = tile_previous_state

    if (block and (side, row, col) not in GAME_mismatches and get_opposite_matrix_coord(side, row, col) not in GAME_mismatches):
        # Adding "X" tilegrid on top of tile
        cross_tile_tilegrids[side][row][col].pixel_shader = common_color_palette if tile_previous_state else invert_color_palette
        cross_tile_tilegrids[side][row][col].hidden = False
        GAME_blocked_tiles.append((side, row, col))

    update_mismatch_status(side, row, col)


def force_correct_tile_pair(coords):
    """Forces a tile and its opposite to be toggled on.
    This function is used when the player leaves a mismatch for too long, in order to correct the mistake

    Parameters
    ----------
    coords : tuple
        The coordinates of the tile to correct (element 0 is cube side, element 1 is row, element 2 is column)
    """

    side, row, col = coords
    opp_side, opp_row, opp_col = get_opposite_matrix_coord(side, row, col)

    GAME_cube_state[side][row, col] = True

    force_remove_mismatch_status(side, row, col)

    fill_tile_tilegrids[side][row][col].hidden = False
    cross_tile_tilegrids[side][row][col].hidden = True
    if ((side, row, col) in GAME_blocked_tiles):
        GAME_blocked_tiles.remove((side, row, col))

    fill_tile_tilegrids[opp_side][opp_row][opp_col].hidden = False
    cross_tile_tilegrids[opp_side][opp_row][opp_col].hidden = True
    if ((opp_side, opp_row, opp_col) in GAME_blocked_tiles):
        GAME_blocked_tiles.remove((opp_side, opp_row, opp_col))

def input_to_matrix_coord(input):
    """Takes a tile's key code and returns tile's matrix coordinates.
    This function is used only for the keys that corresponds to in-game tiles, and must not be used with key codes for the fifth "unused" side

    Parameters
    ----------
    input : int
        The key code that corresponds to the tile

    Returns
    -------
    tuple
        The tile's coordinates (element 0 is cube side, element 1 is row, element 2 is column)
    """

    side: int
    col: int
    row: int
    input_pos_in_side: int = input % 16

    if (0 <= input < 16):
        # Cube side: UP
        side = 2

        col = input // 4
        if (col % 2 == 0):
            row = input % 4
        else:
            row = 3 - (input % 4)
    elif (input < 32):
        # Cube side: RIGHT
        side = 1

        row = input_pos_in_side // 4
        if (row % 2 == 1):
            col = input_pos_in_side % 4
        else:
            col = 3 - (input_pos_in_side % 4)
    elif (input < 48):
        # Cube side: LEFT
        side = 0

        row = input_pos_in_side // 4
        if (row % 2 == 1):
            col = input_pos_in_side % 4
        else:
            col = 3 - (input_pos_in_side % 4)
    elif (input < 64):
        # Cube side: BOTTOM
        side = 3

        col = 3 - (input_pos_in_side // 4)
        if (col % 2 == 0):
            row = input_pos_in_side % 4
        else:
            row = 3 - (input_pos_in_side % 4)

    return (side, row, col)

def input_to_cube_side(input):
    """Takes a tile's key code and returns tile's cube side (a.k.a. the first matrix coordinate).

    Parameters
    ----------
    input : int
        The key code that corresponds to the tile

    Returns
    -------
    int
        The tile's cube side (-1 if invalid input)
    """

    if (0 <= input < 16):
        return 2
    elif (input < 32):
        return 1
    elif (input < 48):
        return 0
    elif (input < 64):
        return 3
    elif (input < 80):
        return 4

    return -1

def get_opposite_matrix_coord(side, row, col):
    """Takes a tile's matrix coordinates and returns the opposite tile's matrix coordinates.

    Parameters
    ----------
    side : int
        Tile's first matrix coordinate.
    row : int
        Tile's second matrix coordinate.
    col : int
        Tile's third matrix coordinate.

    Returns
    -------
    tuple
        The opposite tile's matrix coordinates (element 0 is cube side, element 1 is row, element 2 is column)
    """

    # Tile from left/right side
    if (side < 2):
        return (1 - side, row, 3 - col)
    # Tile from up/bottom side
    else:
        return (5 - side, 3 - row, col)

def update_mismatch_status(side, row, col):
    """Takes the coordinates of a recently toggled tile, and adds/removes a mismatch accordingly.
    A mismatch is defined as a key-value pair in the GAME_mismatches variable, with the key being one of the tile's coordinates, and the value the mismatch's age.

    Parameters
    ----------
    side : int
        Tile's first matrix coordinate.
    row : int
        Tile's second matrix coordinate.
    col : int
        Tile's third matrix coordinate.
    """

    tile_coords: tuple
    opposite_tile_coords: tuple

    # Tiles from the left/up side are considered as the regular tile, while their counterparts are the opposite tile
    if (side == 0 or side == 2):
        tile_coords = (side, row, col)
        opposite_tile_coords = get_opposite_matrix_coord(side, row, col)
    else:
        opposite_tile_coords = (side, row, col)
        tile_coords = get_opposite_matrix_coord(side, row, col)

    if tile_coords in GAME_mismatches:
        # If there was a mismatch, it's resolved, so remove the pair
        tile_longevity = GAME_mismatches.pop(tile_coords)

        # Check if the opposite tile was blocked
        absolute_opposite_tile_coords = get_opposite_matrix_coord(side, row, col)
        if absolute_opposite_tile_coords in GAME_blocked_tiles:
            GAME_blocked_tiles.remove(absolute_opposite_tile_coords)
            cross_tile_tilegrids[absolute_opposite_tile_coords[0]][absolute_opposite_tile_coords[1]][absolute_opposite_tile_coords[2]].hidden = True

            GAME_increment_score(GAME_longevity_death - tile_longevity)
    else:
        # If there was no mismatch, there's one now, so add the pair
        GAME_mismatches[tile_coords] = 0


def force_remove_mismatch_status(side, row, col):
    """Forcefully removes the mismatch associated to a tile.
    This function should only be used for when the game forcefully corrects tiles

    Parameters
    ----------
    side : int
        Tile's first matrix coordinate.
    row : int
        Tile's second matrix coordinate.
    col : int
        Tile's third matrix coordinate.
    """

    tile_coords = (side, row, col)
    opposite_tile_coords = get_opposite_matrix_coord(side, row, col)

    if tile_coords in GAME_mismatches:
        GAME_mismatches.pop(tile_coords)
    if opposite_tile_coords in GAME_mismatches:
        GAME_mismatches.pop(opposite_tile_coords)

def increment_mismatches_longevity():
    """Updates age of all current mismatches, and starts warning/life loss if a mismatch age reaches a certain point."""

    is_in_danger = False

    for coords in GAME_mismatches:
        GAME_mismatches[coords] += 1

        if GAME_mismatches[coords] >= GAME_longevity_death:
            GAME_lose_life()
            force_correct_tile_pair(coords)
            continue

        if GAME_mismatches[coords] >= GAME_longevity_warning:
            is_in_danger = True

    global GAME_danger
    GAME_danger = is_in_danger

def GAME_lose_life():
    """Handles the logic to make the player lose a life.
    Will also call function to end the game if lives have reached 0"""

    if (GAME_end):
        return

    global GAME_lives_left
    SPRITE_life_tilegrids[GAME_lives_left - 1].hidden = True
    GAME_lives_left -= 1

    if (GAME_lives_left <= 0):
        GAME_end_game()

def GAME_end_game():
    """Handles the game over logic."""

    global GAME_end
    GAME_end = True

    SPRITE_white_bg.hidden = False
    SPRITE_game_over_label.hidden = False

def GAME_increment_score(value):
    """Increments the score and updates the in-game score label.

    Parameters
    ----------
    value : int
        How much to add to the score. This value is multiplied by a "minimum score increase" factor
    """

    global GAME_score
    GAME_score += value * GAME_score_min_increase

    str_score = str(GAME_score)
    if (len(str_score) < 6):
        SPRITE_score_val_label.text = (5 - len(str_score))*'0' + str_score
    else:
        SPRITE_score_val_label.text = "99999"

GAME_wave_chosen_tiles = []

GAME_base_count_before_wave = 22
GAME_count_before_wave = GAME_base_count_before_wave
GAME_min_count_wave = 15

def GAME_generate_tile_count_for_wave() -> int:
    """Returns the number of tiles that will be toggled in the incoming wave.

    Returns
    -------
    int
        Number of tiles to toggle
    """

    if (secs_into_game_loop < 30):
        return 1
    elif (secs_into_game_loop < 75):
        return 2
    elif (secs_into_game_loop < 120):
        return 3
    elif (secs_into_game_loop < 210):
        return 4
    elif (secs_into_game_loop < 360):
        return 5
    elif (secs_into_game_loop < 540):
        return 6

    return 7

def GAME_generate_wave():
    """Updates the GAME_wave_chosen_tiles variable to contain tiles that will be toggled in the next updates."""

    possible_inputs = list(range(64))
    tiles_number = GAME_generate_tile_count_for_wave()

    while (len(GAME_wave_chosen_tiles) < tiles_number):
        input = possible_inputs.pop(random.randint(0, len(possible_inputs) - 1))
        coords = input_to_matrix_coord(input)

        # Check if the opposite tile is part of the wave, only add if it's not
        is_opposite_input_absent = True
        for existing_input in GAME_wave_chosen_tiles:
            ex_side, ex_row, ex_col = input_to_matrix_coord(existing_input)
            if (coords == get_opposite_matrix_coord(ex_side, ex_row, ex_col)):
                is_opposite_input_absent = False
                break

        if (is_opposite_input_absent):
            GAME_wave_chosen_tiles.append(input)


def MENU_do_action_from_input(input):
    """Takes a key code and does the corresponding menu action.

    Parameters
    ----------
    input : int
        The input's key code

    Returns
    -------
    bool
        Whether or not an action was actually done using this input
    """

    side = input_to_cube_side(input)

    # Menu doesn't care about bottom/up sides
    if (side == 2 or side == 3):
        return False

    # When clicking on a side that isn't focused on, switch to that side
    if (side != MENU_current_side):
        MENU_change_cube_side(side)
        return True

    # "Play" side
    if (side == 4):
        GLOBAL_setup_game_loop()
        return True

    # "Tutorial" side
    if (side == 1):
        MENU_advance_tutorial()
        return True

    # "Leaderboard" side
    if (side == 0):
        # Not sure if we'll do anything here
        pass

    return False

def MENU_change_cube_side(new_side):
    """Switches the menu cube to the new side (for navigation purposes).
    NOTE: This function was supposed to also do a visual transition between the two sides. However, it's currently commented out as it took up too much memory.

    Parameters
    ----------
    new_side : int
        The cube side to go to
    """

    global GLOBAL_inputs_activated
    GLOBAL_inputs_activated = False

    global MENU_current_side
    MENU_current_side = new_side

    # Visual transition from one side to the other
    # menu_tilegrid.bitmap, _ = adafruit_imageload.load("/assets/sprites/background45/transition.bmp", bitmap=displayio.Bitmap)
    # menu_tilegrid.bitmap, _ = adafruit_imageload.load("/assets/sprites/background_side1/background_side1.bmp", bitmap=displayio.Bitmap)
    # menu_tilegrid.bitmap, _ = adafruit_imageload.load("/assets/sprites/background_side2/background_side2.bmp", bitmap=displayio.Bitmap)

    if (new_side == 0):
        for tilegrid in SPRITE_play_side_tilegrids:
            tilegrid.hidden = True
        SPRITE_score_side_title.hidden = False
    elif (new_side == 1):
        pass
        #menu_tilegrid.bitmap = menu_tutorial
    elif (new_side == 4):
        for tilegrid in SPRITE_play_side_tilegrids:
            tilegrid.hidden = False
        SPRITE_score_side_title.hidden = True

    GLOBAL_inputs_activated = True

def MENU_advance_tutorial():
    """Function that will handle advancing to the next tutorial slide.
    TODO: Implement this function"""
    pass


#######################################
#####--- Visual elements setup ---#####
#######################################


displayio.release_displays()

bus = busio.SPI(board.GP10, board.GP11)
chip_select_pin = board.GP9
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, chip_select_pin, 400, 240)

display = framebufferio.FramebufferDisplay(framebuffer)

SPRITE_delta_x = max(0, (display.width - display.height) // 2)
SPRITE_delta_y = max(0, (display.height - display.width) // 2)

# Creating group for display
viewport = displayio.Group()
display.root_group = viewport ####################### COMMENT THIS LINE IN ORDER TO GET CONSOLE OUTPUT ON THE MICROCONTROLLER'S SCREEN #######################

#--- Common color palette

common_color_palette = displayio.Palette(3)
common_color_palette[0] = 0xFFFFFF
common_color_palette.make_transparent(0)
common_color_palette[1] = 0x000000
common_color_palette[2] = 0xFFFFFF

invert_color_palette = displayio.Palette(3)
invert_color_palette[0] = 0xFFFFFF
invert_color_palette.make_transparent(0)
invert_color_palette[1] = 0xFFFFFF
invert_color_palette[2] = 0x000000

def transform_bitmap_to_common_palette(base_bitmap, base_palette) -> displayio.Bitmap:
    """Transform a bitmap's contents in order to match with the common and inverted color palettes.
    This will only work with bitmaps which use 0xFFFFFF, 0x000000, and 0xFF0000 for transparency.

    Parameters
    ----------
    base_bitmap : displayio.Bitmap
        The base bitmap
    base_bitmap : displayio.Palette
        The base bitmap's color palette

    Returns
    -------
    displayio.Bitmap
        The corrected bitmap
    """

    old_indexes_to_new = {}
    for i in range(len(base_palette)):
        if (base_palette[i] == 0xFF0000):
            old_indexes_to_new[i] = 0
        elif (base_palette[i] == 0x000000):
            old_indexes_to_new[i] = 1
        elif (base_palette[i] == 0xFFFFFF):
            old_indexes_to_new[i] = 2

    # Attributing correct color indexes
    corrected_tile_bitmap = displayio.Bitmap(base_bitmap.width, base_bitmap.height, 3)
    for x in range(corrected_tile_bitmap.width):
        for y in range(corrected_tile_bitmap.height):
            corrected_tile_bitmap[x,y] = old_indexes_to_new[ base_bitmap[x,y] ]

    return corrected_tile_bitmap

#--- Background
menu_play, menu_palette = adafruit_imageload.load("/assets/sprites/background/bg.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)

menu_tilegrid = displayio.TileGrid(menu_play, pixel_shader=menu_palette)
menu_tilegrid.x = SPRITE_delta_x
menu_tilegrid.y = SPRITE_delta_y

viewport.append(menu_tilegrid)

SPRITE_play_side_tilegrids = []
SPRITE_score_side_title = None

SPRITE_pause_button = None

#--- Warning icon

SPRITE_warning_tilegrid = None

def update_warning_icon():
    """Displays/hides the warning icon depending on the situation. Will also display/hide game info to avoid overlap."""

    if (GAME_danger):
        SPRITE_warning_tilegrid.hidden = not SPRITE_warning_tilegrid.hidden
    else:
        SPRITE_warning_tilegrid.hidden = True

    if (SPRITE_warning_tilegrid.hidden):
        SPRITE_score_label.hidden = False
        SPRITE_score_val_label.hidden = False
        SPRITE_time_label.hidden = False
        SPRITE_time_val_label.hidden = False
    else:
        SPRITE_score_label.hidden = True
        SPRITE_score_val_label.hidden = True
        SPRITE_time_label.hidden = True
        SPRITE_time_val_label.hidden = True

#--- Lives

SPRITE_life_tilegrids = {}

#--- Tile sprites

# Storing all tilegrid references
fill_tile_tilegrids = []
for i in range(4):
    fill_tile_tilegrids.append([[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]])

cross_tile_tilegrids = []
for i in range(4):
    cross_tile_tilegrids.append([[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]])

gc.collect()

#--- Retrieving most sprites and positions

### This big code section that follows opens the positions.txt file that gives indications of most sprites' filepaths and in-game positions.
### The logic to read the file assumes a certain order in the positions.txt's sections, therefore switching up sections in the svg exporter may result in issues here.

with open(FILES_sprites_info_filepath) as sprites_info_file:

    # Declaring variables for future use
    filled_tile_folder_name: str
    cross_tile_folder_name: str
    life_bitmap: displayio.Bitmap
    current_palette: displayio.Palette

    current_section = -1
    current_line_in_section = 0

    sprite_info = sprites_info_file.readline()
    sprite_info = sprite_info.rstrip()


    while (sprite_info != ""):
        # Checking if we are in new section
        if (sprite_info[0] == '!' or sprite_info[0] == '?' or sprite_info[0] == '=' or sprite_info[0] == '$'):
            current_section += 1
            current_line_in_section = 0
            section_name = sprite_info[1:]

            sprite_info = sprites_info_file.readline().rstrip()
            continue

        # Separating info
        sprite_info_list = sprite_info.split(" ")

        # Formatting info
        for i in range(1, len(sprite_info_list)):
            sprite_info_list[i] = int(sprite_info_list[i])

        #--- Tiles
        if (current_section == 0):
            # Fetching folder names
            if (current_line_in_section == 0):
                section_name_split = section_name.split(" ")
                filled_tile_folder_name = section_name_split[1]
                cross_tile_folder_name = section_name_split[2]

            #--- Fill tile

            # Loading fill tile bitmap
            fill_tile_bitmap, current_palette = \
                adafruit_imageload.load(FILES_sprites_incomplete_path.format(filled_tile_folder_name, sprite_info_list[0]), bitmap=displayio.Bitmap, palette=displayio.Palette)

            # Adding reference to tilegrid in 3D list
            tile_side, tile_row, tile_col = input_to_matrix_coord(int(sprite_info_list[0]))
            fill_tile_tilegrids[tile_side][tile_row][tile_col] = displayio.TileGrid(transform_bitmap_to_common_palette(fill_tile_bitmap, current_palette), pixel_shader = common_color_palette)
            fill_tile_tilegrids[tile_side][tile_row][tile_col].x = sprite_info_list[1] + SPRITE_delta_x
            fill_tile_tilegrids[tile_side][tile_row][tile_col].y = sprite_info_list[2] + SPRITE_delta_y
            fill_tile_tilegrids[tile_side][tile_row][tile_col].hidden = True

            viewport.append(fill_tile_tilegrids[tile_side][tile_row][tile_col])

            #--- Cross tile

            # Loading cross tile bitmap
            cross_tile_bitmap, current_palette = \
                adafruit_imageload.load(FILES_sprites_incomplete_path.format(cross_tile_folder_name, sprite_info_list[0]), bitmap=displayio.Bitmap, palette=displayio.Palette)

            # Adding reference to tilegrid in 3D list
            tile_side, tile_row, tile_col = input_to_matrix_coord(int(sprite_info_list[0]))
            cross_tile_tilegrids[tile_side][tile_row][tile_col] = displayio.TileGrid(transform_bitmap_to_common_palette(cross_tile_bitmap, current_palette), pixel_shader = common_color_palette)
            cross_tile_tilegrids[tile_side][tile_row][tile_col].x = sprite_info_list[1] + SPRITE_delta_x
            cross_tile_tilegrids[tile_side][tile_row][tile_col].y = sprite_info_list[2] + SPRITE_delta_y
            cross_tile_tilegrids[tile_side][tile_row][tile_col].hidden = True

            viewport.append(cross_tile_tilegrids[tile_side][tile_row][tile_col])

        #--- Hearts
        elif (current_section == 2):
            # On first line, get heart bitmap
            if (current_line_in_section == 0):
                life_bitmap, current_palette = adafruit_imageload.load("/assets/sprites/game/heart0.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette) #adafruit_imageload.load(FILES_sprites_incomplete_path.format(sprite_info_list[0]), bitmap=displayio.Bitmap)
                life_bitmap = transform_bitmap_to_common_palette(life_bitmap, current_palette)

            new_life_tilegrid = displayio.TileGrid(life_bitmap, pixel_shader=common_color_palette)
            new_life_tilegrid.x = sprite_info_list[1] + SPRITE_delta_x
            new_life_tilegrid.y = sprite_info_list[2] + SPRITE_delta_y
            new_life_tilegrid.hidden = True

            viewport.append(new_life_tilegrid)

            SPRITE_life_tilegrids[ int(sprite_info_list[0][-1]) ] = new_life_tilegrid

        #--- Other
        elif (current_section == 3):
            sprite_name = sprite_info_list[0]

            # Sprites linked to play side in menu
            if (sprite_name == "play_text" or sprite_name == "score_text" or sprite_name == "tuto_text"):
                side_sprite_bitmap, current_palette = adafruit_imageload.load(FILES_sprites_incomplete_path.format("game", sprite_name), bitmap=displayio.Bitmap)
                tilegrid = displayio.TileGrid(transform_bitmap_to_common_palette(side_sprite_bitmap, current_palette), pixel_shader=common_color_palette)
                tilegrid.x = sprite_info_list[1] + SPRITE_delta_x
                tilegrid.y = sprite_info_list[2] + SPRITE_delta_y

                viewport.append(tilegrid)
                SPRITE_play_side_tilegrids.append(tilegrid)

            if (sprite_name == "score_text_front"):
                score_title_bitmap, current_palette = adafruit_imageload.load(FILES_sprites_incomplete_path.format("game", sprite_name), bitmap=displayio.Bitmap)
                tilegrid = displayio.TileGrid(transform_bitmap_to_common_palette(score_title_bitmap, current_palette), pixel_shader=common_color_palette)
                tilegrid.x = sprite_info_list[1] + SPRITE_delta_x
                tilegrid.y = sprite_info_list[2] + SPRITE_delta_y
                tilegrid.hidden = True

                viewport.append(tilegrid)
                SPRITE_score_side_title = tilegrid

            if (sprite_name == "pause_button"):
                pause_bitmap, current_palette = adafruit_imageload.load(FILES_sprites_incomplete_path.format("game", sprite_name), bitmap=displayio.Bitmap)
                tilegrid = displayio.TileGrid(transform_bitmap_to_common_palette(pause_bitmap, current_palette), pixel_shader=common_color_palette)
                tilegrid.x = sprite_info_list[1] + SPRITE_delta_x
                tilegrid.y = sprite_info_list[2] + SPRITE_delta_y
                tilegrid.hidden = True

                viewport.append(tilegrid)
                SPRITE_pause_button = tilegrid

            if (sprite_name == "warning"):
                warn_bitmap, current_palette = adafruit_imageload.load(FILES_sprites_incomplete_path.format("game", sprite_name), bitmap=displayio.Bitmap)
                tilegrid = displayio.TileGrid(transform_bitmap_to_common_palette(warn_bitmap, current_palette), pixel_shader=common_color_palette)
                tilegrid.x = sprite_info_list[1] + SPRITE_delta_x
                tilegrid.y = sprite_info_list[2] + SPRITE_delta_y
                tilegrid.hidden = True

                viewport.append(tilegrid)
                SPRITE_warning_tilegrid = tilegrid


        current_line_in_section += 1

        # Getting new line for next iteration
        sprite_info = sprites_info_file.readline().rstrip()

        gc.collect()

#--- Dynamic text display

### NOTE: All of the dynamic text writing is declared here with hardcoded values, even though the objective was to set them up using the positions.txt file.
### This proved too complicated due to the way fonts work in this environment...
### Therefore, if this game is ported to other screen resolutions, the values below will most likely need to be manually adjusted.

SPRITE_game_font = adafruit_bitmap_font.bitmap_font.load_font("/assets/font/tahoma-12.bdf")

SPRITE_score_label = Label(font=SPRITE_game_font, text="SCORE", color = 0x000000, x = 78 + SPRITE_delta_x, y = 81 + SPRITE_delta_y, scale = 1)
SPRITE_score_label.hidden = True
viewport.append(SPRITE_score_label)

SPRITE_score_val_label = Label(font=SPRITE_game_font, text="00000", color = 0x000000, x = 126 + SPRITE_delta_x, y = 81 + SPRITE_delta_y, scale = 1)
SPRITE_score_val_label.hidden = True
viewport.append(SPRITE_score_val_label)

SPRITE_time_label = Label(font=SPRITE_game_font, text="TIME", color = 0x000000, x = 82 + SPRITE_delta_x, y = 102 + SPRITE_delta_y, scale = 1)
SPRITE_time_label.hidden = True
viewport.append(SPRITE_time_label)

SPRITE_time_val_label = Label(font=SPRITE_game_font, text="00000", color = 0x000000, x = 126 + SPRITE_delta_x, y = 102 + SPRITE_delta_y, scale = 1)
SPRITE_time_val_label.hidden = True
viewport.append(SPRITE_time_val_label)

#--- Game over screen
white_palette = displayio.Palette(1)
white_palette[0] = 0xFFFFFF

white_bitmap = displayio.Bitmap(display.width - 2 * SPRITE_delta_x, display.height, 1)
SPRITE_white_bg = displayio.TileGrid(white_bitmap, pixel_shader=white_palette)
SPRITE_white_bg.x = SPRITE_delta_x
SPRITE_white_bg.hidden = True
viewport.append(SPRITE_white_bg)

SPRITE_game_over_label = Label(font=SPRITE_game_font, text="GAMEOVER", color = 0x000000, anchored_position = (display.width//2, display.height//2), anchor_point = (0.5, 0.5), scale = 3)
SPRITE_game_over_label.hidden = True
viewport.append(SPRITE_game_over_label)


#######################################
########--- Game loops setup ---#######
#######################################


TARGETED_FPS = 30
target_frame_time = 1/TARGETED_FPS
time_at_frame_start = time.monotonic()

ONE_S_frequency = 1
ONE_S_time_at_frame_start = time.monotonic()

secs_into_game_loop = 0

HALF_S_frequency = 0.5
HALF_S_time_at_frame_start = time.monotonic()

def GLOBAL_setup_game_loop():
    """Function to call to start the game. Resets all necessary variables, and hides/displays all sprites accordingly."""

    menu_tilegrid.bitmap = menu_play

    SPRITE_pause_button.hidden = False

    SPRITE_score_label.hidden = False
    SPRITE_time_label.hidden = False

    SPRITE_score_val_label.text = "00000"
    SPRITE_score_val_label.hidden = False
    SPRITE_time_val_label.text = "00000"
    SPRITE_time_val_label.hidden = False

    for tilegrid in SPRITE_play_side_tilegrids:
        tilegrid.hidden = True

    SPRITE_score_side_title.hidden = True

    for life_tilegrid in SPRITE_life_tilegrids.values():
        life_tilegrid.hidden = False

    global GAME_danger
    GAME_danger = False

    global GAME_end
    GAME_end = False

    global GAME_lives_left
    GAME_lives_left = 4

    global GAME_score
    GAME_score = 0

    global GAME_wave_chosen_tiles
    GAME_wave_chosen_tiles = []

    global GAME_count_before_wave
    GAME_count_before_wave = GAME_base_count_before_wave

    global GAME_mismatches
    GAME_mismatches = {}

    global GAME_blocked_tiles
    GAME_blocked_tiles = []

    GAME_reset_cube_state()

    global secs_into_game_loop
    secs_into_game_loop = 0

    global GLOBAL_in_game
    GLOBAL_in_game = True

def GLOBAL_setup_menu_loop():
    """Function to call to return to the menu. Resets all necessary variables, and hides/displays all sprites accordingly."""

    menu_tilegrid.bitmap = menu_play
    menu_tilegrid.hidden = False

    SPRITE_pause_button.hidden = True

    SPRITE_score_label.hidden = True
    SPRITE_score_val_label.hidden = True
    SPRITE_time_label.hidden = True
    SPRITE_time_val_label.hidden = True

    SPRITE_warning_tilegrid.hidden = True

    SPRITE_white_bg.hidden = True
    SPRITE_game_over_label.hidden = True

    for tilegrid in SPRITE_play_side_tilegrids:
        tilegrid.hidden = False

    for life_tilegrid in SPRITE_life_tilegrids.values():
        life_tilegrid.hidden = True

    for side in range(len(fill_tile_tilegrids)):
        for row in range(len(fill_tile_tilegrids[0])):
            for col in range(len(fill_tile_tilegrids[0][0])):
                fill_tile_tilegrids[side][row][col].hidden = True
                cross_tile_tilegrids[side][row][col].hidden = True

    global MENU_current_side
    MENU_current_side = 4

    global GLOBAL_in_game
    GLOBAL_in_game = False

def MENU_frame_loop_instance():
    """Contains all logic that must be executed every frame in the menu."""

    for input in inputs_pressed_this_frame:
        if (MENU_do_action_from_input(input)):
            break

def GAME_frame_loop_instance():
    """Contains all logic that must be executed every frame in the game."""

    for input in inputs_pressed_this_frame:
            if (input < 64):
                toggle_tile_from_input(input)
            elif (72 <= input <= 75):
                # TODO: Instead of going straight to main menu, implement pause menu of some kind
                GLOBAL_setup_menu_loop()

def GAME_one_s_loop_instance():
    """Contains all logic that must be executed every second in the game."""

    increment_mismatches_longevity()

    global secs_into_game_loop
    secs_into_game_loop += 1

    time_str = str(secs_into_game_loop)
    SPRITE_time_val_label.text = (5 - len(time_str))*'0' + time_str

def GAME_half_s_loop_instance():
    """Contains all logic that must be executed every half-second in the game."""

    update_warning_icon()

    # Countdown to next wave
    global GAME_count_before_wave
    GAME_count_before_wave -= 1
    if (GAME_count_before_wave < 1):
        GAME_generate_wave()
        GAME_count_before_wave = max((GAME_base_count_before_wave - (secs_into_game_loop // 60)), GAME_min_count_wave)

    if (len(GAME_wave_chosen_tiles) > 0):
        input = GAME_wave_chosen_tiles.pop(0)
        toggle_tile_from_input(input, block=True)


def GAME_game_over_frame_loop_instance():
    """Contains the logic that must be executed every frame on the game over screen."""

    if (len(inputs_pressed_this_frame) > 0):
        GLOBAL_setup_menu_loop()


#######################################
###########--- GAME LOOP ---###########
#######################################


while (True):
    update_all_inputs()

    #--- Main game loop
    delta = time.monotonic() - time_at_frame_start
    if (delta > target_frame_time):
        time_at_frame_start = time.monotonic()

        if (GLOBAL_inputs_activated):
            if (GLOBAL_in_game):
                if (not GAME_end):
                    GAME_frame_loop_instance()
                else:
                    GAME_game_over_frame_loop_instance()
            else:
                MENU_frame_loop_instance()

        # At the end of the frame, reset the list of inputs that were just pressed
        inputs_pressed_this_frame = []

    if (not GLOBAL_in_game or GAME_end):
        continue

    #--- Functions that are called every second (during game only)
    ONE_S_delta = time.monotonic() - ONE_S_time_at_frame_start
    if (ONE_S_delta > ONE_S_frequency):
        ONE_S_time_at_frame_start = time.monotonic()

        GAME_one_s_loop_instance()

    #--- Functions that are called every half-second (during game only)
    HALF_S_delta = time.monotonic() - HALF_S_time_at_frame_start
    if (HALF_S_delta > HALF_S_frequency):
        HALF_S_time_at_frame_start = time.monotonic()

        GAME_half_s_loop_instance()

import os
import copy
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import PurePath
from lxml import etree
import cairosvg

def render_svg_to_png(svg_path, output_folder, data_filepath, width, height, no_bmp, transparent_threshold=100):
	os.makedirs(output_folder, exist_ok=True)

	# Special case: skip and log if path starts with $ or ?
	if (svg_path[0] == "$" or svg_path[0] == "?"):
		with open(data_filepath, "a") as f:
			f.write(svg_path + "\n")
		return
		
	# Extract filename and subfolder from the path
	path_split = PurePath(svg_path).parts
	subfolder = path_split[1]
	filename_without_ext = os.path.splitext(os.path.basename(svg_path))[0]

	# Rasterize the SVG using cairosvg into a PNG in memory
	png_data = BytesIO()
	cairosvg.svg2png(url=svg_path, write_to=png_data, output_width=width, output_height=height)

	# Convert to grayscale (L), then to RGB, and extract the alpha channel separately
	img = Image.open(png_data).convert("L").convert("RGB")
	alpha = Image.open(png_data).convert("RGBA").getchannel("A")

	palette = [
		255, 0, 0,       # index 0 : red (used later to mark transparent zones)
		255, 255, 255,   # index 1 : white
		0, 0, 0          # index 2 : black
	] + [0]*(768-9)

	pal_img = Image.new("P", (1,1))
	pal_img.putpalette(palette)

	# Dithering
	img = img.quantize(3, palette=pal_img, dither=Image.FLOYDSTEINBERG)

	# Crop to bounding box to remove excess transparent padding
	bbox = img.getbbox()
	if bbox:
		img = img.crop(bbox)
	else:
		img = img


	# Replace pixels with low alpha by red index (0 in palette)
	pixels = img.load()
	for y in range(img.height):
		for x in range(img.width):
			if alpha.getpixel((x, y)) <= transparent_threshold:
				pixels[x, y] = 0  # red index


	img_rgb = img.convert("RGB")
	red = (255, 0, 0)
	min_x, min_y = img_rgb.width, img_rgb.height
	max_x, max_y = 0, 0

	# Calculate bounding box of all non-red pixels
	for y in range(img_rgb.height):
		for x in range(img_rgb.width):
			if img_rgb.getpixel((x, y)) != red:
				min_x = min(min_x, x)
				min_y = min(min_y, y)
				max_x = max(max_x, x)
				max_y = max(max_y, y)

	if min_x <= max_x and min_y <= max_y:
		img_rgb = img_rgb.crop((min_x, min_y, max_x + 1, max_y + 1))

	# reconvert to palette mode to keep a 8 bit depth
	img_final = img_rgb.convert("P", palette=pal_img, colors=3)

	# Store position in data file
	with open(data_filepath, "a") as f:
		f.write(f"{filename_without_ext} {min_x} {min_y}\n")

	if (no_bmp):
		return

	# CSave to BMP
	final_file = f'{output_folder}/{subfolder}/{filename_without_ext}.bmp'
	print("Image générée : " + final_file)
	img_final.save(final_file, format="BMP")





# Split one SVG into individual groups and export them into separate SVG files
def split_svg_by_groups(input_svg_filepath, output_folder):
	os.makedirs(output_folder, exist_ok=True)

	# Parse SVG file
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(input_svg_filepath, parser)
	root = tree.getroot()

	nsmap = root.nsmap
	if None in nsmap:
		nsmap['svg'] = nsmap.pop(None)  # Fix du namespace par défaut

	inkscape_ns = nsmap.get('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
	label_attr = f'{{{inkscape_ns}}}label'
	print(label_attr)

	# Find all groups with a label attribute
	groups = [g for g in root.findall('.//svg:g', namespaces=nsmap) if label_attr in g.attrib]

	print(f"Trouvé {len(groups)} groupes avec un inkscapelabel.")
	 
	# contains all generated svg's filename formated as split_svg/groupname.svg, except tiles, 
	# text_position, and stamps, which are stored in the following lists
	lst_classic_images = [] 

	# list of the filename of tiles, formated as split_svg/id.svg
	lst_tile = [] 

	# contains all exported svg, labeled as 'text position' (with _?group_name)
	lst_text_position = ["?pos_only"] # add header entry

	# key is the group name (without '_!'), value is a list of filepath of each split svg using this stamp name
	dict_stamp = {} 


	last_tile_layer = ""
	i = 0
	for group in groups:
		group_id = group.attrib[label_attr]


		if (group_id[0] != '_'):
			# skip group not labeled as export
			continue

		# Find containing layer
		layer = group
		while layer is not None and layer.attrib.get(f'{{{inkscape_ns}}}groupmode') != 'layer':
			layer = layer.getparent()
		layer_name = layer.attrib.get(label_attr, 'Unnamed Layer') if layer is not None else 'No Layer'

		group_name_simple = group_id[1:] # removes only the '_' token
		group_name_token = group_id[2:] # also removes the second token ('!', '?' or '$')
		
		split_svg_export_path = output_folder + "/" + layer_name + "/"
		svg_ext = '.svg'

		if (group_id[1] == '!'):

			if (group_name_token not in dict_stamp):
				dict_stamp[group_name_token] = []

			stamp = dict_stamp[group_name_token]

			filepath = split_svg_export_path + group_name_token + str(len(stamp)) + svg_ext
			stamp.append(filepath)
			extract_group(root, group, filepath)

		elif (group_id[1] == '?'):
			# no rendered bitmap, only position (text_position)
			# still exported as svg to get the position as rendered bitmap

			filepath = split_svg_export_path + group_name_token + svg_ext
			extract_group(root, group, filepath)
			lst_text_position.append(filepath)


		elif (group_id[1] == '$'):
			# ordered image (tiles)
			try:
				int(group_name_token)
			except:
				print(f"error : tile group {group_id} must contain digits only, key = |{group_name_token}|")

			filepath = split_svg_export_path + group_name_token + svg_ext

			extract_group(root, group, filepath)

			if (layer_name != last_tile_layer):
				# insert special entry to write categories' header in the data file
				last_tile_layer = layer_name
				lst_tile.append("$"+layer_name)

			lst_tile.append(filepath)

		else:
			#classic images
			filepath = split_svg_export_path + group_name_simple + svg_ext
			extract_group(root, group, filepath)
			lst_classic_images.append(filepath)
	
	return (lst_classic_images, lst_tile, dict_stamp, lst_text_position)




# Export a group into its own SVG file, keeping the root structure
def extract_group(root, group, output_path):

	# Créer une nouvelle racine SVG avec même dimensions et viewBox
	new_root = copy.deepcopy(root)
	for elem in list(new_root):
		new_root.remove(elem)

	# Insérer uniquement le groupe courant
	new_root.append(copy.deepcopy(group))

	print(f"Fichier généré : {output_path}")
	with open(output_path, "wb") as f:
		f.write(etree.tostring(new_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

# Create folders named after the SVG layers inside each given root
def create_folders_from_layers(svg_path, lst_root):
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(svg_path, parser)
	root = tree.getroot()

	nsmap = root.nsmap
	if None in nsmap:
		nsmap['svg'] = nsmap.pop(None)
	inkscape_ns = nsmap.get('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
	label_attr = f'{{{inkscape_ns}}}label'
	groupmode_attr = f'{{{inkscape_ns}}}groupmode'

	layers = [g for g in root.findall('.//svg:g', namespaces=nsmap)
			  if g.attrib.get(groupmode_attr) == 'layer']

	for layer in layers:
		layer_name = layer.attrib.get(label_attr, 'Unnamed_Layer')
		for root in lst_root:
			folder_path = os.path.join(root, layer_name)
			os.makedirs(folder_path, exist_ok=True)


svg_path = 'main.svg'
split_svg_folder = 'split_svg'
bmp_folder = "export"
data_filepath = "positions.txt"
width = 240  
height = 240
transparent_threshold= 10

create_folders_from_layers(svg_path, [split_svg_folder, bmp_folder])
open(data_filepath, "w").close() # clear the data file

lst_simple_image, lst_tile, dict_stamp, lst_text = split_svg_by_groups(svg_path, split_svg_folder)


# !!! HARDCODED CASE !!!

lst_tile_headers = []

for i in range(len(lst_tile)-1, 0):
	svg = lst_tile[i]
	if (svg[i] == "$"):
		lst_tile_headers.append(svg)
		del lst_tile[i]

lst_tile_headers.reverse()
header_str = "$"

for header in lst_tile_headers:
	header_str += f" {lst_tile_headers[1:]}"
with open(data_filepath, "a") as f:
	f.write(header_str + "\n")

# !!! HARDCODED CASE !!!


#tiles
for tile in lst_tile:
	render_svg_to_png(tile, bmp_folder, data_filepath, width, height, False, transparent_threshold)

#textpos
if (len(lst_text) >= 1):
	for text in lst_text:
		print("position generated for ", text)
		render_svg_to_png(text, bmp_folder, data_filepath, width, height, True, transparent_threshold)

#stamps
for key in dict_stamp.keys():
	with open(data_filepath, "a") as f:
		f.write(f"!{key}\n")
	
	stamp = dict_stamp[key]
	render_svg_to_png(stamp[0], bmp_folder, data_filepath, width, height, False, transparent_threshold)

	for i in range(1, len(stamp)):
		render_svg_to_png(stamp[i], bmp_folder, data_filepath, width, height, True, transparent_threshold)


#simple images
with open(data_filepath, "a") as f:
	f.write("=other\n")

for path in lst_simple_image:
	render_svg_to_png(path, bmp_folder, data_filepath, width, height, False, transparent_threshold)

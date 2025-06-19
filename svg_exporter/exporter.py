import os
import copy
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import PurePath
from lxml import etree
import cairosvg

def render_svg_to_png(svg_path, output_folder, offset_file_path, width, height, transparent_threshold=100):
	os.makedirs(output_folder, exist_ok=True)

	if (svg_path[0] == "$"):
		with open(offset_file_path, "a") as f:
			f.write(svg_path + "\n")
		return

	path_split = PurePath(svg_path).parts

	filename_without_ext = os.path.splitext(os.path.basename(svg_path))[0]
	subfolder = path_split[1]

	png_data = BytesIO()
	cairosvg.svg2png(url=svg_path, write_to=png_data, output_width=width, output_height=height)

	# Conversion en niveaux de gris puis RGB, et récupération de l'alpha
	img = Image.open(png_data).convert("L").convert("RGB")
	alpha = Image.open(png_data).convert("RGBA").getchannel("A")

	# Déclaration de la palette (noir, blanc, rouge réservé pour les transparents)
	palette = [
		255, 0, 0,       # index 0 : rouge (qu'on utilisera après pour transparence)
		255, 255, 255,   # index 1 : blanc
		0, 0, 0          # index 2 : noir
	] + [0]*(768-9)

	pal_img = Image.new("P", (1,1))
	pal_img.putpalette(palette)

	# Quantization avec dithering, vers 3 couleurs (indice 0, 1 et 2)
	img = img.quantize(3, palette=pal_img, dither=Image.FLOYDSTEINBERG)

	# Remplacement des pixels transparents (alpha=0) par l'index rouge (index 0)

	bbox = img.getbbox()
	if bbox:
		img = img.crop(bbox)
	else:
		# Image entièrement transparente
		img = img


	pixels = img.load()
	for y in range(img.height):
		for x in range(img.width):
			if alpha.getpixel((x, y)) <= transparent_threshold:
				pixels[x, y] = 0  # index rouge

	img_rgb = img.convert("RGB")

	red = (255, 0, 0)
	min_x, min_y = img_rgb.width, img_rgb.height
	max_x, max_y = 0, 0

	for y in range(img_rgb.height):
		for x in range(img_rgb.width):
			if img_rgb.getpixel((x, y)) != red:
				min_x = min(min_x, x)
				min_y = min(min_y, y)
				max_x = max(max_x, x)
				max_y = max(max_y, y)

	# Si on a trouvé au moins un pixel non rouge
	if min_x <= max_x and min_y <= max_y:
		img_rgb = img_rgb.crop((min_x, min_y, max_x + 1, max_y + 1))

	with open(offset_file_path, "a") as f:
		f.write(f"{filename_without_ext} {min_x} {min_y}\n")

	# Conversion finale en RGB pour BMP
	final_file = f'{output_folder}/{subfolder}/{filename_without_ext}.bmp'
	print("Image générée : " + final_file)
	img_rgb.save(final_file, format="BMP")

def split_svg_by_groups(input_svg_path, output_folder):
	# Créer le dossier de sortie si besoin
	os.makedirs(output_folder, exist_ok=True)

	# Charger le SVG d'origine
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(input_svg_path, parser)
	root = tree.getroot()

	nsmap = root.nsmap
	if None in nsmap:
		nsmap['svg'] = nsmap.pop(None)  # Fix du namespace par défaut

	inkscape_ns = nsmap.get('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
	label_attr = f'{{{inkscape_ns}}}label'
	print(label_attr)

	# Chercher tous les groupes ayant un ID
	groups = [g for g in root.findall('.//svg:g', namespaces=nsmap) if label_attr in g.attrib]

	print(f"Trouvé {len(groups)} groupes avec un inkscapelabel.")
	 
	# contains all generated svg's filename formated as split_svg/groupname.svg, except tiles, which are store in lst_tile
	lst_classic_images = [] 

	# list of the filename of tiles, formated as split_svg/id.svg
	lst_tile = [] 

	# key is the name of the file, value is the number of instance using this stamp as an image
	dict_stamp = {} 

	 # key is the name of the text
	dict_text = {}

	last_tile_layer = ""
	i = 0
	for group in groups:
		group_id = group.attrib[label_attr]

		filename_no_ext = f"{group_id[1:]}"

		if (group_id[0] != '_'):
			# skip group not labeled as export
			continue

		layer = group
		while layer is not None and layer.attrib.get(f'{{{inkscape_ns}}}groupmode') != 'layer':
			layer = layer.getparent()
		layer_name = layer.attrib.get(label_attr, 'Unnamed Layer') if layer is not None else 'No Layer'

		output_path = os.path.join(output_folder + "/" + layer_name, filename_no_ext + ".svg")

		key = group_id[2:]
		if (group_id[1] == '!'):
			if (key in dict_stamp):
				pass
			else:
				dict_stamp[key] = []
				#dict_stamp[key].append()

		elif (group_id[1] == '?'):
			pass
		elif (group_id[1] == '$'):
			try:
				int(key)
			except:
				print(f"error : tile group {group_id} must contain digits only, key = |{key}|")
			output_path = os.path.join(output_folder + "/" + layer_name, key + ".svg")
			extract_group(root, group, output_path)
			if (layer_name != last_tile_layer):
				last_tile_layer = layer_name
				lst_tile.append("$"+layer_name)
			lst_tile.append(output_path)

		else:
			extract_group(root, group, output_path)
			lst_classic_images.append(output_path)

	
	return (lst_classic_images, lst_tile, dict_stamp, dict_text)

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


# Exemple d'utilisation
svg_path = 'main.svg'
split_svg_folder = 'split_svg'
bmp_folder = "export"
offset_file_path = "positions.txt"
width = 240  
height = 240
transparent_threshold= 10

os.makedirs(split_svg_folder + "/" + "cross", exist_ok=True)
os.makedirs(split_svg_folder + "/" + "filled", exist_ok=True)
os.makedirs(split_svg_folder + "/" + "other", exist_ok=True)

os.makedirs(bmp_folder + "/" + "cross", exist_ok=True)
os.makedirs(bmp_folder + "/" + "filled", exist_ok=True)
os.makedirs(bmp_folder + "/" + "other", exist_ok=True)

lst_results, lst_tile, dict_stamp, dict_text = split_svg_by_groups(svg_path, split_svg_folder)
with open(offset_file_path, "w") as f:
	pass
	# clear the data file

for tile in lst_tile:
	render_svg_to_png(tile, bmp_folder, offset_file_path, width, height, transparent_threshold)


with open(offset_file_path, "a") as f:
	f.write("=other\n")
for path in lst_results:
	render_svg_to_png(path, bmp_folder, offset_file_path, width, height, transparent_threshold)

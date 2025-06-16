import os
import copy
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from lxml import etree
import cairosvg

def render_svg_to_png(svg_path, output_folder, offset_file_path, width, height, transparent_threshold=100):
	os.makedirs(output_folder, exist_ok=True)
	filename_without_ext = os.path.splitext(os.path.basename(svg_path))[0]

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
	img_rgb.save(f'{output_folder}/{filename_without_ext}.bmp', format="BMP")

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
	 
	list_results = []
	i = 0
	for group in groups:
		group_id = group.attrib[label_attr]

		if (group_id[0] != '_'):
			continue
		# Créer une nouvelle racine SVG avec même dimensions et viewBox
		new_root = copy.deepcopy(root)
		for elem in list(new_root):
			new_root.remove(elem)

		# Insérer uniquement le groupe courant
		new_root.append(copy.deepcopy(group))

		# Écrire le fichier SVG correspondant
		filename_no_ext = f"{group_id[1:]}"
		output_path = os.path.join(output_folder, filename_no_ext + ".svg")
		with open(output_path, "wb") as f:
			f.write(etree.tostring(new_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

		print(f"Fichier généré : {output_path}")
		list_results.append(output_path)
	return list_results


# Exemple d'utilisation
svg_path = 'main.svg'
split_svg_folder = 'split_svg'
bmp_folder = "export"
offset_file_path = "positions.txt"
width = 240  
height = 240
transparent_threshold= 10

list_results = split_svg_by_groups(svg_path, split_svg_folder)
with open(offset_file_path, "w") as f:
	pass
for path in list_results:
	render_svg_to_png(path, bmp_folder, offset_file_path, width, height, transparent_threshold)

#!/usr/bin/python

# Python thingie to write a connector lib for KiCad / EeSchem.
# originally written by P. vd Hoeven.
# 2017-06-18
# https://www.compuphase.com/electronics/LibraryFileFormats.pdf
# Adapted by Poeschl Rene to generate different pin numbering schemes.


from collections import namedtuple
################################  Parameters ##################################
reference_designator = 'J'
pin_grid = 100
pin_spacing_y = 100
# Fill: N = None, f = fill background (yellow), F = fill foreground (red)
body_fill = 'f'
body_outline_line_width = 10
inner_graphics_line_width = 6
max_pin_per_row = 10

CONNECTOR = namedtuple("CONNECTOR",[
	'num_rows',
	'pin_per_row_range',
    'symbol_name_format',
	'pin_number_generator',
	'description',
	'keywords',
	'datasheet',
	'default_footprint',
	'footprint_filter',
	'graphic_type'
])

connector_params = {
	'dualrow_odd-even' : CONNECTOR(
		num_rows = 2,
		pin_per_row_range = range(1, max_pin_per_row + 1),
		symbol_name_format = 'conn_02x{num_pins_per_row:02d}_odd-even',
		pin_number_generator = lambda row_idx, pin_idx, pins_per_row:(2*pin_idx if row_idx == 2 else 2*pin_idx - 1),
		description = 'Generic connector, double row, 02x{num_pins_per_row:02d}, odd/even pin numbering scheme (row 1 odd numbers, row 2 even numbers)',
		keywords = 'connector',
		datasheet = '', # generic symbol, no datasheet
		default_footprint = '', # generic symbol, no default footprint
		footprint_filter = None,
		graphic_type = 0 # 0 = neutral, 1 = male, 2 = female
	),
	'dualrow_counter-clockwise' : CONNECTOR(
		num_rows = 2,
		pin_per_row_range = range(1, max_pin_per_row + 1),
		symbol_name_format = 'conn_02x{num_pins_per_row:02d}_counter-clockwise',
		pin_number_generator = lambda row_idx, pin_idx, pins_per_row:(pin_idx if row_idx == 1 else 2*pins_per_row - (pin_idx - 1)),
		description = 'Generic connector, double row, 02x{num_pins_per_row:02d}, counter clockwise pin numbering scheme (similar to DIP packge numbering)',
		keywords = 'connector',
		datasheet = '', # generic symbol, no datasheet
		default_footprint = '', # generic symbol, no default footprint
		footprint_filter = None,
		graphic_type = 0 # 0 = neutral, 1 = male, 2 = female
	),
	'dualrow_top-bottom' : CONNECTOR(
		num_rows = 2,
		pin_per_row_range = range(1, max_pin_per_row + 1),
		symbol_name_format = 'conn_02x{num_pins_per_row:02d}_top-bottom',
		pin_number_generator = lambda row_idx, pin_idx, pins_per_row:(pin_idx if row_idx == 1 else pins_per_row + pin_idx),
		description = 'Generic connector, double row, 02x{num_pins_per_row:02d}, top/bottom pin numbering scheme (row 1: 1...pins_per_row, row2: pins_per_row+1 ... num_pins)',
		keywords = 'connector',
		datasheet = '', # generic symbol, no datasheet
		default_footprint = '', # generic symbol, no default footprint
		footprint_filter = None,
		graphic_type = 0 # 0 = neutral, 1 = male, 2 = female
	),
	'conn_02xPP_row-letter-first' : CONNECTOR(
		num_rows = 2,
		pin_per_row_range = range(1, max_pin_per_row + 1),
		symbol_name_format = 'conn_02x{num_pins_per_row:02d}_row-letter-first',
		pin_number_generator = lambda row_idx, pin_idx, pins_per_row:'{letter}{num:d}'.format(
			letter = 'a' if row_idx == 1 else 'b', num = pin_idx),
		description = 'Generic connector, double row, 02x{num_pins_per_row:02d}, row letter first pin numbering scheme (pin number consists of a letter for the row and a number for the pin index in this row. a1, ..., aN; b1, ..., bN)',
		keywords = 'connector',
		datasheet = '', # generic symbol, no datasheet
		default_footprint = '', # generic symbol, no default footprint
		footprint_filter = None,
		graphic_type = 0 # 0 = neutral, 1 = male, 2 = female
	),
	'conn_02xPP_row-letter-last' : CONNECTOR(
		num_rows = 2,
		pin_per_row_range = range(1, max_pin_per_row + 1),
		symbol_name_format = 'conn_02x{num_pins_per_row:02d}_row-letter-last',
		pin_number_generator = lambda row_idx, pin_idx, pins_per_row:'{letter}{num:d}'.format(
			letter = 'a' if row_idx == 1 else 'b', num = pin_idx),
		description = 'Generic connector, double row, 02x{num_pins_per_row:02d}, row letter last pin numbering scheme (pin number consists of a letter for the row and a number for the pin index in this row. 1a, ..., Na; 1b, ..., Nb))',
		keywords = 'connector',
		datasheet = '', # generic symbol, no datasheet
		default_footprint = '', # generic symbol, no default footprint
		footprint_filter = None,
		graphic_type = 0 # 0 = neutral, 1 = male, 2 = female
	)
}


class Drawing:
	def __init__(self):
		self.rectangle = []
		self.polyline = []
		self.arc = []
		self.pins = []
	def append_pin(self, str):
		self.pins.append(str)
	def append_poly(self, str):
		self.polyline.append(str)
	def append_arc(self, str):
		self.arc.append(str)
	def append_rectangle(self, str):
		self.rectangle.append(str)

	def __str__(self):
		drawing = 'DRAW\n'
		drawing += ''.join(self.arc)
		drawing += ''.join(self.rectangle)
		drawing += ''.join(self.polyline)
		drawing += ''.join(self.pins)
		drawing += 'ENDDRAW\n'
		return drawing


################################ helper functions #############################

def round_to_grid(x, base=pin_grid):
    return int(base * round(float(x)/base))


################################ generate symbols #############################

def generate_pin_marker(drawing, pin_pos_y, body_edge_x, left_side, type=0):
	marker_width = 50
	marker_height = 10
	female_radius = 20
	if type == 0 or type == 1:
		x2 = body_edge_x + (marker_width if left_side else -marker_width)
		drawing.append_rectangle('S {x1:d} {y1:d} {x2:d} {y2:d} 0 1 {line_width} {fill}\n'.format(
			x1 = body_edge_x, y1 = pin_pos_y - marker_height//2,
			x2 = x2, y2 = pin_pos_y + marker_height//2,
			fill='F' if type == 1 else 'N', line_width = inner_graphics_line_width))
	if type == 2:
		if left_side:
			# A -50 -50 20 901 -901 0 1 6 N -50 -30 -50 -70
			# A -50 50 20 901 -901 0 1 6 N -50 70 -50 30
			drawing.append_arc('A {x:d} {pin_y:d} {r:d} 901 -901 0 1 {line_width} N {x:d} {y1:d} {x:d} {y2:d}\n'.format(
					x = body_edge_x+marker_width, pin_y = pin_pos_y,
					r = female_radius, y1 = pin_pos_y + female_radius,
					y2 = pin_pos_y - female_radius,
					line_width = inner_graphics_line_width
				))
			# P 2 0 1 6 -100 50 -70 50 N
			drawing.append_poly('P 2 0 1 {line_width} {x1:d} {pin_y:d} {x2:d} {pin_y:d} N\n'.format(
					x1 = body_edge_x, pin_y = pin_pos_y,
					x2 = body_edge_x + marker_width - female_radius,
					line_width = inner_graphics_line_width
				))
		else:
			# A 50 -50 20 -899 899 0 1 6 N 50 -70 50 -30
			# A 50 50 20 -899 899 0 1 6 N 50 30 50 70
			drawing.append_arc('A {x:d} {pin_y:d} {r:d} -899 899 0 1 {line_width} N {x:d} {y1:d} {x:d} {y2:d}\n'.format(
					x = body_edge_x-marker_width, pin_y = pin_pos_y,
					r = female_radius, y1 = pin_pos_y - female_radius,
					y2 = pin_pos_y + female_radius,
					line_width = inner_graphics_line_width
				))
			# P 2 0 1 6 100 50 70 50 N
			drawing.append_poly('P 2 0 1 {line_width} {x1:d} {pin_y:d} {x2:d} {pin_y:d} N\n'.format(
					x1 = body_edge_x, pin_y = pin_pos_y,
					x2 = body_edge_x - marker_width + female_radius,
					line_width = inner_graphics_line_width
				))


# X name pin X Y length orientation sizenum sizename part dmg type shape
def generate_pin(pin_pos_y, pin_pos_x, left_side, pin_number):
	return 'X P{number} {number} {pos_x} {pos_y} 100 {rot} 50 50 1 1 P\n'.format(
		number=pin_number, pos_x = -pin_pos_x if left_side else pin_pos_x,
		pos_y = pin_pos_y, rot = 'R' if left_side else 'L')

def generate_connector(num_pins_per_row, series_params, lib_file, dcm_file):
	symbol_name = series_params.symbol_name_format.format(num_pins_per_row=num_pins_per_row)
	top_pin_pos_y = round_to_grid(pin_spacing_y * (num_pins_per_row - 1) / 2.0)
	bottom_pin_pos_y = top_pin_pos_y - (num_pins_per_row - 1) * pin_spacing_y
	body_left = -100
	body_right = 100
	pin_pos_x = 200
	# Write 3 comment lines with the symbol name.
	header = '#\n# {name}\n#\n'.format(name=symbol_name)

	# DEF	# Start of symbol definition.
	# name	# If name starts with "~" it is invisible.
	# ref 	# prefix ( J / U / R / C / etc).
	# 0	# Pin name offset in mill from the end-point of a pin
	# YN	# Show/No show for pin numbers.
	# YN	# Show/No show for pin names.
	# 1	# Number of "parts" in a symbol.
	# LF	# "L"ocked or "F" otherwise.
	# PN	" "P"ower symbol or "N" otherwise.
	header += 'DEF {name} {ref} 0 1 Y N 1 F N\n'.format(
		name=symbol_name, ref=reference_designator)

	# F0	# Symoblic prefix text, a mandatory field.
	# ref	# "ref" should be the same as in the "DEF" field.
	# 10 100 50	# X Y & Size of text [mil].
	# HV	# "H"orizonal or "V"ertical Orientation.
	# IV	# "I"nvisible  or "V"isible.
	# Horizontal Alignment	Left Center Right
	# Vertical Alignment	Top Bottom (There are no spaces betweent the last 3 parameters).
	# "I"talic or "N" otherwise.
	# "B"old or "N" otherwise.
	header += 'F0 "{ref}" 0 {pos_y:d} 50 H V C CNN\n'.format(
		ref=reference_designator, pos_y=top_pin_pos_y + 100)

	#F1	# The symbol name text, a mandatory field. The name  parameter must be the same as in the "DEF" line.
	#	See the "F0" definition for the other parameters.
	header +=  'F1 "{value}" 0 {pos_y:d} 50 H V C CNN\n'.format(
		value=symbol_name, pos_y = bottom_pin_pos_y - 100)

	#F2	# Footprint Field
	#	See the "F0" definition for the other parameters.
	header += 'F2 "{value}" 0 {pos_y:d} 50 H I C CNN\n'.format(
		value=series_params.default_footprint, pos_y = bottom_pin_pos_y - 200)

	#F3	# Datasheet Field (Not used, use datasheet link in dcm file.)
	#	See the "F0" definition for the other parameters.
	header += 'F3 "" 0 {pos_y:d} 50 H I C CNN\n'.format(pos_y = bottom_pin_pos_y - 300)

	# Add footprint filters if defined:
	# $FPLIST
	#  Filter 1
	#  Filter 2
	#  ...
	# $ENDFPLIST
	if series_params.footprint_filter is not None:
		header += '$FPLIST\n'
		for filter in series_params.footprint_filter:
			header += ' {}\n'.format(filter)
		header += '$ENDFPLIST\n'
	lib_file.write(header)

	drawing = Drawing()

	drawing.append_rectangle('S {x1:d} {y1:d} {x2:d} {y2:d} 0 1 {line_width} {fill}\n'.format(
		x1 = body_left, y1 = top_pin_pos_y + 50,
		x2 = body_right, y2 = bottom_pin_pos_y - 50,
		fill = body_fill, line_width = body_outline_line_width))
	pins = ''
	for row_idx in range(1, series_params.num_rows + 1):
		for pin_idx in range(1, num_pins_per_row + 1):
			pin_pos_y = top_pin_pos_y - (pin_idx - 1)*pin_spacing_y
			generate_pin_marker(drawing, pin_pos_y, -100 if row_idx == 1 else 100,
				row_idx == 1, series_params.graphic_type)
			drawing.append_pin(generate_pin(
				pin_pos_y, pin_pos_x , row_idx == 1,
				series_params.pin_number_generator(row_idx, pin_idx, num_pins_per_row)))


	lib_file.write(str(drawing))
	lib_file.write('ENDDEF\n')


def generate_connector_series(series_params, lib_file, dcm_file):
	for num_pins_per_row in series_params.pin_per_row_range:
		generate_connector(num_pins_per_row, series_params, lib_file, dcm_file)


if __name__ == '__main__':
	lib_file =open("conn_new.lib", "w")
	lib_file.write("EESchema-LIBRARY Version 2.3\n#encoding utf-8\n")
	dcm_file =open("conn_new.dcm", "w")
	dcm_file.write('EESchema-DOCLIB  Version 2.0')
	for series_name,series_params in connector_params.items():
		generate_connector_series(series_params, lib_file, dcm_file)
	lib_file.write( '#\n#End Library\n')
	lib_file.close()
	dcm_file.write('#End Doc Library\n')
	dcm_file.close()

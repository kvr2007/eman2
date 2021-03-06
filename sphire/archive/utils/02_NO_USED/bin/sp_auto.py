


























































































































































































































































































































































































































































































































































































































from __future__ import print_function
def show_variables():
	with open(__file__) as r:
		lines = r.readlines()
	xxx_comp = re.compile('XXX_SP_[^ \'/]*_XXX')
	matches = []
	for line in lines:
		for match in xxx_comp.findall(line):
			matches.append(match)
	pass#IMPORTIMPORTIMPORT import numpy as np
	for entry in numpy.sort(numpy.unique(matches)):
		print('UNIQUE VAR:', entry)


def get_defaults():
	default_dict = {}
	default_dict['XXX_SP_BOX_SIZE_XXX'] = '352'
	default_dict['XXX_SP_MOL_MASS_XXX'] = '1400'
	default_dict['XXX_SP_PARTICLE_RADIUS_XXX'] = '145'
	default_dict['XXX_SP_PIXEL_SIZE_XXX'] = '1.14'
	default_dict['XXX_SP_SYMMETRY_XXX'] = 'c5'
	default_dict['XXX_SP_VOLTAGE_XXX'] = '300'

	default_dict['XXX_SP_ADJUSTMENT_ADDITION_XXX'] = ''
	default_dict['XXX_SP_ADJUSTMENT_OUTPUT_DIR_XXX'] = '04b_RVIPER_ADJUSTMENT'
	default_dict['XXX_SP_ADJUSTMENT_RESAMPLE_RATIO_XXX'] = '1.0'

	default_dict['XXX_SP_CRYOLO_ADDITION_XXX'] = ''
	default_dict['XXX_SP_CRYOLO_CONFIG_PATH_XXX'] = '/Path/to/cryolo'
	default_dict['XXX_SP_CRYOLO_GPU_XXX'] = '-1'
	default_dict['XXX_SP_CRYOLO_MICROGRAPH_PATTERN_XXX'] = 'bla/*.mrc'
	default_dict['XXX_SP_CRYOLO_OUTPUT_DIR_XXX'] = '02a_CRYOLO_PREDICT'
	default_dict['XXX_SP_CRYOLO_PREDICT_PATH_XXX'] = '/Path/to/cryolo_predict'

	default_dict['XXX_SP_CTER_ADDITION_XXX'] = ''
	default_dict['XXX_SP_CTER_CS_XXX'] = '2.7'
	default_dict['XXX_SP_CTER_MICROGRAPH_PATTERN_XXX'] = ''
	default_dict['XXX_SP_CTER_OUTPUT_DIR_XXX'] = '01a_CTER'
	default_dict['XXX_SP_CTER_WINDOW_SIZE'] = '1024'

	default_dict['XXX_SP_ISAC_ADDITION_XXX'] = ''
	default_dict['XXX_SP_ISAC_IMG_PER_GRP_XXX'] = '100'
	default_dict['XXX_SP_ISAC_OUTPUT_DIR_XXX'] = '03a_ISAC'
	default_dict['XXX_SP_ISAC_STACK_XXX'] = 'bdb:stack'

	default_dict['XXX_SP_MASK_RVIPER_ADDITION_XXX'] = ''
	default_dict['XXX_SP_MASK_RVIPER_NDILAITON_XXX'] = '3'
	default_dict['XXX_SP_MASK_RVIPER_OUTPUT_DIR_XXX'] = '04c_RVIPER_MASK'
	default_dict['XXX_SP_MASK_RVIPER_SOFT_EDGE_XXX'] = '10'

	default_dict['XXX_SP_MERIDIEN_ADDITION_XXX'] = ''
	default_dict['XXX_SP_MERIDIEN_INPUT_STACK_XXX'] = 'bdb:stack'
	default_dict['XXX_SP_MERIDIEN_INPUT_VOLUME_XXX'] = 'input_volume'
	default_dict['XXX_SP_MERIDIEN_OUTPUT_DIR_XXX'] = '05a_MERIDIEN'

	default_dict['XXX_SP_RVIPER_ADDITION_XXX'] = ''
	default_dict['XXX_SP_RVIPER_INPUT_STACK_XXX'] = 'bdb:classes'
	default_dict['XXX_SP_RVIPER_OUTPUT_DIR_XXX'] = '04a_RVIPER'

	default_dict['XXX_SP_SUBSTACK_OUTPUT_DIR_XXX'] = '03b_SUBSTACK'

	default_dict['XXX_SP_UNBLUR_ADDITION_XXX'] = ''
	default_dict['XXX_SP_UNBLUR_EXP_PER_FRAME_XXX'] = '2.5'
	default_dict['XXX_SP_UNBLUR_GAIN_FILE_XXX'] = '/Path/to/Gain'
	default_dict['XXX_SP_UNBLUR_MICROGRAPH_PATTERN_XXX'] = '/PATTERN*.mrc'
	default_dict['XXX_SP_UNBLUR_OUTPUT_DIR_XXX'] = '00a_UNBLUR'
	default_dict['XXX_SP_UNBLUR_PATH_XXX'] = '/Path/to/unblur'

	default_dict['XXX_SP_WINDOW_ADDITION_XXX'] = ''
	default_dict['XXX_SP_WINDOW_BOX_PATTERN_XXX'] = 'box*.box'
	default_dict['XXX_SP_WINDOW_MICROGRAPH_PATTERN_XXX'] = 'mrc*.mrc'
	default_dict['XXX_SP_WINDOW_OUTPUT_DIR_XXX'] = '02b_WINDOW'
	default_dict['XXX_SP_WINDOW_PARTRES_XXX'] = 'Wuhu/partres'
	return default_dict


























































































































































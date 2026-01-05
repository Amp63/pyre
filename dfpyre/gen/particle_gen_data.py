from dfpyre.gen.gen_data import load_data_file


CLASS_NAME = 'Particle'

PARTICLE_CLASS_DEF = load_data_file('particle_class/particle_class_template.py')
PARTICLE_METHOD_TEMPLATE = load_data_file('particle_class/particle_method.txt')


FIELD_PARAMETER_LOOKUP = {
    'Size': [('size', 'float', '1.0', 'The size of each particle.')],
    'Size Variation': [('size_variation', 'int', '0', 'The percentage variation to apply to particle size.')],
    'Motion': [('motion', 'tuple[float, float, float]', '(0.0, 0.0, 0.0)', 'The velocity to apply to the effect.')],
    'Motion Variation': [('motion_variation', 'int', '0', 'The percentage variation to apply to particle motion.')],
    'Color': [('color', 'tuple[int, int, int] | str', '(255, 255, 255)', 'The color of each particle.')],
    'Color Variation': [('color_variation', 'int', '0', 'The percentage variation to apply to particle color.')],
    'Opacity': [('opacity', 'int', '100', 'The opacity of each particle.')],
    'Duration': [('duration', 'int', '5', 'The duration of the effect in ticks.')],
    'Fade Color': [('fade_color', 'tuple[int, int, int] | str', '(255, 255, 255)', 'The color that each particle will fade to.')],
    'Roll': [('roll', 'float', '0.0', 'The rotational roll of each particle in radians.')],
    'Material': [('material', 'str', 'None', 'The block material to apply to each particle.')]
}

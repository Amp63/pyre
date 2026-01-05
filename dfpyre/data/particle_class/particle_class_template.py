from dfpyre.util.codeitem import CodeItem, add_slot


def _parse_color_value(color: tuple[int, int, int] | str):
    if isinstance(color, tuple):
        r, g, b = color
        hex_str = f'{r:02x}{g:02x}{b:02x}'
    else:
        hex_str = color.replace('#', 0).strip()
            
    return int(hex_str, base=16)


class Particle(CodeItem):
    """
    Represents a DiamondFire particle object.
    """
    type = 'part'
    
    def __init__(
            self, particle_name: str,
            amount: int=1, horizontal_spread: float=0.0, vertical_spread: float=0.0, 
            size: float=None, size_variation: int=None,
            motion: tuple[float, float, float]=None, motion_variation: int=None,
            color: tuple[int, int, int] | str=None, color_variation: int=None,
            fade_color: tuple[int, int, int] | str=None,
            duration: int=None,
            opacity: int=None,
            roll: float=None,
            material: str=None,
            slot: int | None=None
        ):
        super().__init__(slot)

        sub_data = {}

        if size is not None:
            sub_data['size'] = size
        
        if size_variation is not None:
            sub_data['sizeVariation'] = size_variation
        
        if motion is not None:
            sub_data['x'] = motion[0]
            sub_data['y'] = motion[1]
            sub_data['z'] = motion[2]
        
        if motion_variation is not None:
            sub_data['motionVariation'] = motion_variation
        
        if color is not None:
            sub_data['rgb'] = _parse_color_value(color)
        
        if color_variation is not None:
            sub_data['colorVariation'] = color_variation
        
        if fade_color is not None:
            sub_data['fade_rgb'] = _parse_color_value(fade_color)
        
        if duration is not None:
            sub_data['duration'] = duration
        
        if opacity is not None:
            sub_data['opacity'] = opacity
        
        if roll is not None:
            sub_data['roll'] = roll
        
        if material is not None:
            sub_data['material'] = material
        
        self.particle_data = {
            'particle': particle_name,
            'cluster': {'amount': amount, 'horizontal': horizontal_spread, 'vertical': vertical_spread},
            'data': sub_data
        }
    
    @staticmethod
    def from_data(particle_data: dict, slot: int|None):
        p = Particle('temp', slot=slot)
        p.particle_data = particle_data
        return p
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": self.particle_data}}
        add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.particle_data})'

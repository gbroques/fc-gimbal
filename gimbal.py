from enum import Enum, unique
from typing import Tuple

import FreeCAD as App
from FreeCAD import Document, Placement, Rotation, Vector


@unique
class Color(Enum):
    RED = (1.0, 0.0, 0.0, 1.0)
    GREEN = (0.0, 1.0, 0.0, 1.0)
    BLUE = (0.0, 0.0, 1.0, 1.0)


class Gimbal:
    """
    Gimbal for visualizing Euler (or Tait-Bryan) angles.

    See Also:
        https://en.wikipedia.org/wiki/Gimbal
    """

    def __init__(self, obj, gimbal):
        """
        Constructor

        Arguments
        ---------
        - obj: an existing document object or an object created with FreeCAD.Document.addObject('Part::FeaturePython', '{name}').
        """

        self.Type = 'Gimbal'
        self.gimbal = gimbal

        obj.Proxy = self
        obj.addProperty('App::PropertyAngle', 'X',
                        'Base', 'X').X = 0
        obj.addProperty('App::PropertyAngle', 'Y',
                        'Base', 'Y').Y = 0
        obj.addProperty('App::PropertyAngle', 'Z',
                        'Base', 'Z').Z = 0

    def execute(self, obj):
        """
        Called on document recompute.
        """
        base = Vector(0, 0, 0)
        x = self.gimbal.Links[0]
        y = self.gimbal.Links[1]
        z = self.gimbal.Links[2]

        x_rotation = Rotation(Vector(1, 0, 0), obj.X)
        y_rotation = Rotation(Vector(0, 1, 0), obj.Y)
        z_rotation = Rotation(Vector(0, 0, 1), obj.Z)

        # TODO: These initial rotations are duplicated in create_gimbal.
        x_initial = Rotation(Vector(0, 1, 0), 90)
        y_initial = Rotation(Vector(1, 0, 0), 90)
        z_initial = Rotation(Vector(0, 0, 1), 0)

        x_prime = x_rotation.multiply(x_initial)
        x.Placement = Placement(base, x_prime)

        y_prime = x_rotation.multiply(y_rotation.multiply(y_initial))
        y.Placement = Placement(base, y_prime)

        z_prime = x_rotation.multiply(y_rotation).multiply(
            z_rotation.multiply(z_initial))
        z.Placement = Placement(base, z_prime)


def create_gimbal(obj_name: str, document: Document) -> object:
    """
    Create a Gimbal.
    """
    gimbal = document.addObject('Part::Compound', 'Compound')

    size = 15
    thickness = 1
    radius2 = thickness / 2

    toruses = [
        {
            'name': 'X',
            'rotation': Rotation(Vector(0, 1, 0), 90),
            'color': Color.RED.value
        },
        {
            'name': 'Y',
            'rotation': Rotation(Vector(1, 0, 0), 90),
            'color': Color.GREEN.value
        },
        {
            'name': 'Z',
            'rotation': Rotation(Vector(0, 0, 1), 0),
            'color': Color.BLUE.value
        }
    ]
    links = []
    for i, torus in enumerate(toruses):
        torus = create_pointed_torus(document,
                                     torus['name'],
                                     size - (thickness * i),
                                     radius2,
                                     torus['color'],
                                     torus['rotation'])
        links.append(torus)

    gimbal.Links = links

    gimbal.ViewObject.ShowInTree = False

    for obj in links:
        obj.ViewObject.Visibility = True

    obj = document.addObject('Part::FeaturePython', obj_name)
    obj.Shape = gimbal.Shape
    Gimbal(obj, gimbal)
    obj.ViewObject.Proxy = 0  # Mandatory unless ViewProvider is coded
    return gimbal


def create_pointed_torus(document: Document,
                         name: str,
                         radius1: float,
                         radius2: float,
                         shape_color: Tuple[float, float, float, float],
                         rotation: Rotation) -> object:
    torus = document.addObject('Part::Torus', name)
    torus.Radius1 = radius1
    torus.Radius2 = radius2
    torus.ViewObject.ShapeColor = shape_color
    torus.ViewObject.ShowInTree = False
    torus.ViewObject.Visibility = True
    torus.Placement = Placement(Vector(0, 0, 0), rotation)

    # TODO: Compound or fusion doesn't seem to work.
    # arrow = document.addObject('Part::Cone', name + 'Arrow')
    # arrow.Radius1 = 0
    # arrow.Radius2 = 0.5
    # height = 2
    # arrow.Height = height
    # z = -radius1 - height
    # arrow.Placement = Placement(Vector(0, 0, z), Vector(0, 0, 1), 0)
    # arrow.ViewObject.ShapeColor = shape_color
    # arrow.ViewObject.ShowInTree = False
    # arrow.ViewObject.Visibility = False

    return torus


document = App.ActiveDocument
if document is None:
    document = App.newDocument('Gimbal')


gimbal = create_gimbal('Gimbal', document)
document.recompute()

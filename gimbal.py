import FreeCAD as App
import Part
from FreeCAD import Document, Placement, Rotation, Vector


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
        
        z_rotation = Rotation(Vector(0, 0, 1), obj.Z)
        y_rotation = Rotation(Vector(0, 1, 0), obj.Y)
        x_rotation = Rotation(Vector(1, 0, 0), obj.X)

        x_initial = Rotation(Vector(0, 1, 0), 90)
        y_initial = Rotation(Vector(1, 0, 0), 90)
        z_initial = Rotation(Vector(0, 0, 1), 0)

        z_prime = z_rotation.multiply(y_rotation).multiply(x_rotation).multiply(z_initial)
        x_r = x_rotation.multiply(x_initial)
        y_r = y_rotation.multiply(y_initial).multiply(x_rotation)
        y.Placement = Placement(base, y_r)
        z.Placement = Placement(base, z_prime)
        x.Placement = Placement(base, x_r)

def create_gimbal(obj_name: str, document: Document) -> object:
    """
    Create a Gimbal.
    """
    gimbal = document.addObject('Part::Compound', 'Compound')

    size = 15
    thickness = 1
    radius2 = thickness / 2

    x = document.addObject('Part::Torus', 'X')
    x.Radius1 = size
    x.Radius2 = radius2
    x.ViewObject.ShapeColor = (1.0, 0.0, 0.0, 1.0)
    x.ViewObject.ShowInTree = False
    x.Placement = Placement(Vector(0, 0, 0), Vector(0, 1, 0), 90)

    y = document.addObject('Part::Torus', 'Y')
    y.Radius1 = size - thickness
    y.Radius2 = radius2
    y.ViewObject.ShapeColor = (0.0, 1.0, 0.0, 1.0)
    y.ViewObject.ShowInTree = False
    y.Placement = Placement(Vector(0, 0, 0), Vector(1, 0, 0), 90)

    z = document.addObject('Part::Torus', 'Z')
    z.Radius1 = size - thickness * 2
    z.Radius2 = radius2
    z.ViewObject.ShapeColor = (0.0, 0.0, 1.0, 1.0)
    z.ViewObject.ShowInTree = False
    z.Placement = Placement(Vector(0, 0, 0), Vector(0, 0, 1), 0)

    gimbal.Links = [x, y, z]

    gimbal.ViewObject.ShowInTree = False

    for obj in [x, y, z]:
        obj.ViewObject.Visibility = True

    obj = document.addObject('Part::FeaturePython', obj_name)
    obj.Shape = gimbal.Shape
    Gimbal(obj, gimbal)
    obj.ViewObject.Proxy = 0  # Mandatory unless ViewProvider is coded
    return gimbal


document = App.ActiveDocument
if document is None:
    document = App.newDocument('Gimbal')


gimbal = create_gimbal('Gimbal', document)
document.recompute()


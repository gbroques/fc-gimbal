from enum import Enum, unique
from typing import Optional, Tuple

import FreeCAD as App
from FreeCAD import Document, DocumentObject, Placement, Rotation, Vector
from FreeCADGui import Selection


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

    def __init__(self,
                 obj: object,
                 gimbal: object,
                 size: float = 15.0,
                 thickness: float = 2.0):
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
                        'Rotation', 'X').X = 0
        obj.addProperty('App::PropertyAngle', 'Y',
                        'Rotation', 'Y').Y = 0
        obj.addProperty('App::PropertyAngle', 'Z',
                        'Rotation', 'Z').Z = 0
        obj.addProperty('App::PropertyLink', 'LinkedObject',
                        'Base', 'Linked object').LinkedObject = None

        read_only = 1
        obj.addProperty('App::PropertyLength', 'Size',
                        'Dimension', 'Size', read_only).Size = size
        obj.addProperty('App::PropertyLength', 'Thickness',
                        'Dimension', 'Thickness of rings', read_only).Thickness = thickness

        hidden = 2
        obj.setEditorMode('Placement', hidden)

    def execute(self, obj):
        """
        Called on document recompute.
        """
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
        y_prime = z_rotation.multiply(y_rotation).multiply(y_initial)
        z_prime = z_rotation.multiply(y_rotation).multiply(
            x_rotation).multiply(z_initial)

        base = Vector(0, 0, 0)
        if obj.LinkedObject is not None:
            p = obj.LinkedObject.Placement
            base = Vector(p.Base.x, p.Base.y, p.Base.z)
            rotation = z_rotation.multiply(y_rotation).multiply(x_rotation)
            set_placement_if_different(
                obj.LinkedObject, Placement(base, rotation))

        set_placement_if_different(x, Placement(base, x_prime))
        set_placement_if_different(y, Placement(base, y_prime))
        set_placement_if_different(z, Placement(base, z_prime))

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state


def set_placement_if_different(obj: object, next_placement: Placement) -> None:
    if not are_placements_equal(obj.Placement, next_placement):
        obj.Placement = next_placement


def are_placements_equal(a: Placement, b: Placement) -> bool:
    precision = 7
    return (
        round(a.Base.x, ndigits=precision) == round(b.Base.x, ndigits=precision) and
        round(a.Base.y, ndigits=precision) == round(b.Base.y, ndigits=precision) and
        round(a.Base.z, ndigits=precision) == round(b.Base.z, ndigits=precision) and
        a.Rotation.Angle == b.Rotation.Angle and
        a.Rotation.Axis == b.Rotation.Axis
    )


def create_gimbal(obj_name: str,
                  document: Document,
                  size: float = 15.0,
                  thickness: float = 1.0,
                  center: Vector = Vector(0, 0, 0)) -> object:
    """
    Create a Gimbal.
    """
    gimbal = document.addObject('Part::Compound', 'Compound')
    radius2 = thickness / 2
    size_padding = thickness * 3

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
                                     (size + size_padding) - (thickness * i),
                                     radius2,
                                     torus['color'],
                                     center,
                                     torus['rotation'])
        links.append(torus)

    gimbal.Links = links

    gimbal.ViewObject.ShowInTree = False

    for obj in links:
        obj.ViewObject.Visibility = True

    obj = document.addObject('Part::FeaturePython', obj_name)
    obj.Shape = gimbal.Shape
    Gimbal(obj, gimbal, size, thickness)
    obj.ViewObject.Proxy = 0  # Mandatory unless ViewProvider is coded
    return obj


def create_pointed_torus(document: Document,
                         name: str,
                         radius1: float,
                         radius2: float,
                         shape_color: Tuple[float, float, float, float],
                         base: Vector,
                         rotation: Rotation) -> object:
    torus = document.addObject('Part::Torus', name)
    torus.Radius1 = radius1
    torus.Radius2 = radius2
    torus.ViewObject.ShapeColor = shape_color
    torus.ViewObject.ShowInTree = False
    torus.ViewObject.Visibility = True
    torus.Placement = Placement(base, rotation)

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


def select_object(document: Document) -> Optional[object]:
    selection = Selection.getSelection()
    if len(selection) > 0:
        return selection[0]
    elif len(document.Objects) > 0:
        return document.Objects[0]
    else:
        return None


class DocumentObserver:
    """
    Detects when a user deletes a Gimbal object,
    to also delete all links to underlying Torus objects.
    """

    def __init__(self, target_document) -> None:
        self.target_document = target_document

    def slotDeletedDocument(self, document: Document):
        if self.target_document == document:
            App.removeDocumentObserver(self)

    def slotDeletedObject(self, document_object: DocumentObject):
        if self.is_gimbal(document_object):
            gimbal = document_object.Proxy.gimbal
            for torus in gimbal.Links:
                self.delete_object_if_exists(torus)
            self.delete_object_if_exists(gimbal)

    def is_gimbal(self, document_object: DocumentObject) -> bool:
        return (
            document_object.TypeId == 'Part::FeaturePython' and
            hasattr(document_object, 'Proxy') and
            document_object.Proxy.Type == 'Gimbal'
        )

    def delete_object_if_exists(self, document_object: DocumentObject) -> None:
        if hasattr(self.target_document, document_object.Name):
            self.target_document.removeObject(document_object.Name)


selected_object = select_object(document)
if selected_object is not None:
    bounding_box = selected_object.Shape.BoundBox
    size = max(bounding_box.XMax, bounding_box.YMax, bounding_box.ZMax)
    center = bounding_box.Center
    gimbal = create_gimbal('Gimbal', document, size=size, center=center)
    gimbal.LinkedObject = selected_object
else:
    create_gimbal('Gimbal', document)

observer = DocumentObserver(document)
App.addDocumentObserver(observer)

document.recompute()

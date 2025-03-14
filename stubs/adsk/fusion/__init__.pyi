"""Type stubs for adsk.fusion module"""

class Design:
    @staticmethod
    def cast(product: object) -> 'Design': ...
    
    @property
    def rootComponent(self) -> Component: ...

class Component:
    @property
    def sketches(self) -> Sketches: ...
    
    @property
    def xYConstructionPlane(self) -> ConstructionPlane: ...

class Sketches:
    def add(self, plane: ConstructionPlane) -> Sketch: ...

class Sketch:
    @property
    def name(self) -> str: ...
    @name.setter
    def name(self, value: str) -> None: ...
    
    @property
    def sketchCurves(self) -> SketchCurves: ...
    
    @property
    def sketchPoints(self) -> SketchPoints: ...
    
    def copy(self, entities: object, transform: object) -> None: ...

class ConstructionPlane:
    pass

class BRepBody:
    @property
    def boundingBox(self) -> BoundingBox: ...

class BoundingBox:
    @property
    def minPoint(self) -> Point3D: ...
    
    @property
    def maxPoint(self) -> Point3D: ...

class Profile:
    @property
    def loops(self) -> ProfileLoops: ...

# Add more classes as needed...

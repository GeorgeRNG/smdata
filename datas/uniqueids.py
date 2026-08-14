from structs import *

class UniqueIds(Struct):
    """
    This has all IDs which count up and that are unique
    Found in the Game table
    """

    def __members__(self):
        self.a                = self.add(INT)
        self.rigidbody        = self.add(INT)
        self.joint            = self.add(INT)
        self.childshape       = self.add(INT)
        self.controller       = self.add(INT)
        self.container        = self.add(INT)
        self.harvestable      = self.add(INT)
        self.b                = self.add(INT)
        self.tool             = self.add(INT)
        self.player           = self.add(INT)
        self.unit             = self.add(INT)
        self.d                = self.add(INT)
        self.portal           = self.add(INT)
        self.e                = self.add(INT)
        self.voxelterrain     = self.add(INT)
        self.scriptableobject = self.add(INT)
        self.shapegroup       = self.add(INT)
        self.f                = self.add(INT)
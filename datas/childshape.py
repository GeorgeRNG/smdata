from structs import *

class ChildShapeHeader(Struct):
    """
    Every part, wedge, and stretch of blocks is its own ChildShape
    Blocks will automatically simplify themself (merge with other blocks to keep the minimum amount of blocks)
    """
    def __members__(self):
        self.header = self.add(STRING(3),"header")
        self.id = self.add(INT,"id")
        self.body_id = self.add(INT,"body")
        self.shape = self.add(BYTE_ID,"shape id")
        self.id_again = self.add(INT,"id_2") # sure why not
        self.x = self.add(SIGNED_SHORT,"x")
        self.y = self.add(SIGNED_SHORT,"y")
        self.z = self.add(SIGNED_SHORT,"z")
        self._a = self.add(BYTE)
        self.color = self.add(STRING(3),"rrggbb")
class ChildShape(Parsable):
    """
    Every part, wedge, and stretch of blocks is its own ChildShape
    Blocks will automatically simplify themself (merge with other blocks to keep the minimum amount of blocks)
    """
    FLAG_CABLEBOT_EATING = 2 ** 0
    FLAG_BURNING = 2 ** 1

    def __parse__(self, data):
        self.header = ChildShapeHeader(data)
        type = self.header.header()
        if type == ChildShapeBlock.header: self.data = ChildShapeBlock(data)
        elif type == ChildShapePart.header: self.data = ChildShapePart(data)
        elif type == ChildShapeWedge.header: self.data = ChildShapeWedge(data)
        self.flags = data.read(BYTE)

    def get_flag(self, flag) -> bool:
        return get_byte(self.flags, flag)
    def set_flag(self, flag, value: bool):
        self.flags = set_byte(self.flags, flag, value)

    def make(self):
        return (
            self.header.make() +
            self.data.make() +
            struct.pack(">B", self.flags)
        )

    def annotate(self) -> Annotations:
        annotations = super().annotate()
        print(self.data)
        annotations.add(self.header, self.data)
        annotations.split()
        annotations.encode("flags", self.flags, BYTE)
        return annotations

class ChildShapeBlock(Struct):
    header = b"\x01\x1f\x01"

    def __members__(self):
        self.x = self.add(SHORT,"x")
        self.y = self.add(SHORT,"y")
        self.z = self.add(SHORT,"z")
class ChildShapePart(Struct):
    header = b"\x01\x20\x01"

    def __members__(self):
        self.rotation = self.add(BYTE,"rotation")
class ChildShapeWedge(Struct):
    header = b"\x01\x28\x01"
    def __members__(self):
        self.x = self.add(SHORT,"x")
        self.y = self.add(SHORT,"y")
        self.z = self.add(SHORT,"z")
        self.rotation = self.add(BYTE,"rotation")

from struct import pack, unpack, calcsize
from structs import *

class RigidBody:
    struct = ">2s B I H 16s H 4f 3f"

    RESTRICT_ERASABLE = 2**0
    """Players cannot break blocks, uses the encryptor's hexagonal shields and sounds when trying"""
    RESTRICT_BUILDABLE = 2**1
    """Players cannot place blocks, see the placing or breaking overlays, or use the weld tool (unless the creation is on a lift, in which case the weld tool can merge neighbouring pieces on joints albeit it with some missing particles)"""
    RESTRICT_PAINTABLE = 2**2
    """Players cannot use the paint gun to paint or unpaint"""
    RESTRICT_CONNECTABLE = 2**3
    """Players cannot see connections or edit connections"""
    RESTRICT_LIFTABLE = 2**4
    """Players cannot put free moving creations on the lift"""
    RESTRICT_USABLE = 2**5
    """Players cannot access the configuration or upgrade screen for parts, but can still use parts"""
    RESTRICT_DESTRUCTABLE = 2**6
    """Explosions, melee, and projectiles cannot damage blocks, and enemies do not consider attacking blocks"""
    RESTRICT_CONVERTIBLE_TO_DYNAMIC = 2**7
    """Breaking the support for these creations do not make them dynamic. If they are split into two different bodies, one will become dynamic"""

    def __init__(self, data: bytes):
        self.header: bytes
        self.a: bytes
        self.id: int
        self.worldid: int
        self.id_b: bytes
        self.pad: int
        self.qA: float
        self.qB: float
        self.qC: float
        self.qD: float
        self.x: float
        """East"""
        self.y: float
        """North"""
        self.z: float
        """Altitude"""
        self.data: RigidBodyData
        start = calcsize(self.struct)
        (self.header,self.a,self.id,self.worldid,self.id_b,self.pad,self.qA,self.qB,self.qC,self.qD,self.x,self.y,self.z) = unpack(self.struct, data[ : start])
        if self.header == RigidBodyStatic.header: self.data = RigidBodyStatic(data[start :])
        if self.header == RigidBodyMobile.header: self.data = RigidBodyMobile(data[start :])

        #                                                             [quaternion rotation              ] [xyz                     ] flags
        # 0002 01 00000043 0000 c27c7d3fc289cbbec1832452c19b954c 0000 3c4e1e8f b932fa16 bbb42435 3f7ff9d2 c1857fbe c2873662 bf89a19e 00    000000000000000000000000000000000000000000000000
        # 0001 01 000000bc 0000 42b17df442b1020c42f7fdf442f7020c 0000 3f800000 00000000 00000000 00000000 42f00000 42b00000 00000000 00    ffffffff

        # 0001 01 00000438 0000 c0304189c03fbe77c2020419c206fbe7 0000 3f800000 00000000 00000000 00000000 c2000000 00000000 00000000 00 ffffffff # default frozen
        # 0002 01 0000043a 0000 c08ddce1c09628ffc1f04c8ac1f844be 0000 bb1565a6 ba19839c bbc04b2c 3f7ffeb1 c1e037ec c07e28c2 be6fe468 00 000000000000000000000000000000000000000000000000 # free
        # 0001 01 00000440 0000 c020406ac0afe573c1b00828c1c3f972 0000 3a6da6fb 3a3745b6 b8a6e3dd 3f7ffff5 c1c00128 c0800000 3c8185d0 00 ffffffff # custom frozen
        # 0001 01 0000046f 0000 bfc08312bfdf7ceec1a60831c1abf7cf 0000 3f800000 00000000 00000000 00000000 c1a00000 00000000 00000000 01 ffffffff

        # 0002010000043a0000c08ddce1c09628ffc1f04c8ac1f844be0000bb1565a6ba19839cbbc04b2c3f7ffeb1c1e037ecc07e28c2be6fe46800000000000000000000000000000000000000000000000000 # free
        # 
        #                                                                                                                       NN
        # 0002010000046e00003dc25460c02f39dbc16b1e8bc1813915000037b8fb24b7b24ac63d245f6b3f7fcb36c1809d95bf7f7026bef7d86a00000000000000000000000000000000000000000000000041 mobile, encrypted

    def make(self) -> bytes:
        return pack(self.struct, self.header,self.a,self.id,self.worldid,self.id_b,self.pad,self.qA,self.qB,self.qC,self.qD,self.x,self.y,self.z) + self.data.make()

class RigidBodyData:
    def __init__(self, data: bytes):
        raise NotImplementedError()
    def make(self) -> bytes:
        raise NotImplementedError()
class RigidBodyStatic(RigidBodyData):
    struct = "B 4s"
    header = b"\x00\x01"
    def __init__(self, data):
        self.restrictions: int
        self.data: bytes
        (self.restrictions,self.data) = unpack(self.struct,data)
    def make(self):
        return pack(self.struct, self.restrictions, self.data)
class RigidBodyMobile(RigidBodyData):
    struct = "24s B"
    header = b"\x00\x02"
    def __init__(self, data):
        self.data: bytes
        self.restrictions: int
        (self.data, self.restrictions) = unpack(self.struct,data)
    def make(self):
        return pack(self.struct, self.data, self.restrictions)

"""
Every part, wedge, and stretch of blocks is its own ChildShape
Blocks will automatically simplify themself (merge with other blocks to keep the minimum amount of blocks)
"""
class ChildShape:
    struct = ">3s I I 16s I 3h B 3s"

    def __init__(self, data: bytes):
        self.header: bytes
        self.id: int
        self.body: int
        self.shape: bytes
        self.id_again: int # yeah sure why not
        self.x: int
        self.y: int
        self.z: int
        self._a: int
        self.color: any
        self.data: ChildShapeData
        self.flags: int
        start = calcsize(self.struct)
        end = start
        (self.header,self.id,self.body,self.shape,self.id_again,self.x,self.y,self.z,self._a,self.color) = unpack(self.struct, data[ : start])
        if self.header == ChildShapeBlock.header: 
            end += calcsize(ChildShapeBlock.struct)
            self.data = ChildShapeBlock(data[start : end])
        elif self.header == ChildShapePart.header:
            end += calcsize(ChildShapePart.struct)
            self.data = ChildShapePart(data[start : end])
        elif self.header == ChildShapeWedge.header:
            end += calcsize(ChildShapeWedge.struct)
            self.data = ChildShapeWedge(data[start : end])
        else:
            print(f"unknown header {self.header.hex()}")
        # if (self.id != self.id_again): print(f"value after shape on childshape {self.id} does not match id ({self.id_again})")

    def make(self) -> bytes:
        return pack(self.struct, self.header, self.id, self.body, self.shape, self.id_again, self.x, self.y, self.z, self._a, self.color) + self.data.make()

class ChildShapeData:
        def __init__(self, data: bytes):
            raise NotImplementedError()
        def make(self) -> bytes:
            raise NotImplementedError()
class ChildShapeBlock:
    header = b"\x01\x1f\x01"
    struct = ">3H B"

    FLAG_CABLEBOT_EATING = 1
    FLAG_BURNING = 2

    def __init__(self, data: bytes):
        self.length: int
        self.width: int
        self.height: int
        self.flags: int
        (self.length,self.width,self.height,self.flags) = unpack(self.struct, data)
    def make(self) -> bytes:
        return pack(self.struct, self.length, self.width, self.height, self.flags)
class ChildShapePart(ChildShapeData):
    header = b"\x01\x20\x01"
    struct = "H"
    def __init__(self, data):
        self.rotation: int
        (self.rotation,) = unpack(self.struct, data)
    def make(self):
        return pack(self.struct, self.rotation)
class ChildShapeWedge(ChildShapeData):
    header = b"\x01\x28\x01"
    struct = "3HH"
    def __init__(self, data: bytes):
        self.length: int
        self.width: int
        self.height: int
        self.rotation: int
        (self.length,self.width,self.height,self.rotation) = unpack(self.struct, data)
    def make(self):
        return pack(self.struct,self.length,self.width,self.height,self.rotation)

class Item(Struct):
    def __members__(self):
        self.id =      self.add(STRING(16))
        self.divider = self.add(STRING(4))
        self.count =   self.add(SHORT)

class ContainerHeader(Struct):
    def __members__(self):
        self.header =  self.add(STRING(3))
        self.id =      self.add(INT)
        self.divider = self.add(STRING(1))
        self.size =    self.add(BYTE)
        self.a =       self.add(STRING(2))

class Container(Parsable):
    def __init__(self, data):
        self.header = ContainerHeader(data)
        offset = self.header.calcsize()
        self.items: list[Item] = []
        for _ in range(self.header.size.value):
            item = Item(data[offset:])
            self.items.append(item)
            offset+=item.calcsize()
        self.a = data[offset:]

    def make(self):
        container = self.header.make()
        for item in self.items:
            container += item.make()
        container += self.a
        return container
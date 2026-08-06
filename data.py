from struct import pack, unpack, calcsize

class RigidBody:
    struct = ">2s B I H 16s H 4f 3f"

    FLAG_DISABLE_BREAKING = 2**0
    """Players cannot break blocks, uses the encryptor's hexagonal shields and sounds when trying"""
    FLAG_DISABLE_PLACING = 2**1
    """Players cannot place blocks, see the placing or breaking overlays, or use the weld tool (unless the creation is on a lift, in which case the weld tool can merge neighbouring pieces on joints albeit it with some missing particles)"""
    FLAG_DISABLE_PAINTING = 2**2
    """Players cannot use the paint gun to paint or unpaint"""
    FLAG_DISABLE_CONNECTION = 2**3
    """Players cannot see connections or edit connections"""
    FLAG_DISABLE_LIFT = 2**4
    """Players cannot put free moving creations on the lift"""
    FLAG_DISABLE_CONFIGURE = 2**5
    """Players cannot access the configuration or upgrade screen for parts, but can still use parts"""
    FLAG_DISABLE_DAMAGE = 2**6
    """Explosions, melee, and projectiles cannot damage blocks, and enemies do not consider attacking blocks"""

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
        self.flags: int
        self.data: bytes
        (self.flags,self.data) = unpack(self.struct,data)
    def make(self):
        return pack(self.struct, self.flags, self.data)
class RigidBodyMobile(RigidBodyData):
    struct = "24s B"
    header = b"\x00\x02"
    def __init__(self, data):
        self.data: bytes
        self.flags: int
        (self.data, self.flags) = unpack(self.struct,data)
    def make(self):
        return pack(self.struct, self.data, self.flags)

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


class Item:
    struct = ">16s 4s H"

    def __init__(self, data: bytes):
        self.id: bytes
        self.count: int
        
        (self.id,_,self.count) = unpack(self.struct, data)

    def make(self) -> bytes:
        return pack(self.struct,
        self.id,
        b"\xff\xff\xff\xff",
        self.count
    )

class ContainerHeader:
    struct = ">3s I 1s B 2s"

    def __init__(self, data):
        self.id: int
        self.size: int
        self.a: bytes

        (_, self.id, _, self.size, self.a) = unpack(self.struct, data)
    def make(self):
        return pack(
            self.struct,
            b"\x04\x00\x01", # Header?
            self.id,
            b"\x00",
            self.size,
            self.a
        )

class Container:

    def __init__(self, data):
        self.header: ContainerHeader
        self.items: list[Item] = []

        offset = calcsize(ContainerHeader.struct)
        self.header = ContainerHeader(data[:offset])
        size = self.header.size
        for _ in range(size):
            end = offset + calcsize(Item.struct)
            item = Item(data[offset:end])
            self.items.append(item)
            offset = end

    def make(self):
        assert len(self.items) == self.header.size, f"len(self.items) = {len(self.items)} but it should be {self.header.size}"
        container = self.header.make()
        for item in self.items:
            container += item.make()
        container += b"\x00\x00"
        return container
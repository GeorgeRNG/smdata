from struct import pack, unpack, calcsize

class RigidBody:
    struct = ">2s B I H 16s H 4f 3f"

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
        """East"""
        self.x: float
        """North"""
        self.y: float
        """Altitude"""
        self.z: float
        self.data: RigidBodyData
        start = calcsize(self.struct)
        (self.header,self.a,self.id,self.worldid,self.id_b,self.pad,self.qA,self.qB,self.qC,self.qD,self.x,self.y,self.z) = list(unpack(self.struct, data[ : start]))
        if self.header == RigidBodyStatic.header: self.data = RigidBodyStatic(data[start :])
        if self.header == RigidBodyMobile.header: self.data = RigidBodyMobile(data[start :])

        #                                                             [quaternion rotation              ] [xyz                     ]
        # 0002 01 00000043 0000 c27c7d3fc289cbbec1832452c19b954c 0000 3c4e1e8f b932fa16 bbb42435 3f7ff9d2 c1857fbe c2873662 bf89a19e 00000000000000000000000000000000000000000000000000
        # 0001 01 000000bc 0000 42b17df442b1020c42f7fdf442f7020c 0000 3f800000 00000000 00000000 00000000 42f00000 42b00000 00000000 00ffffffff

    def make(self) -> bytes:
        return pack(self.struct, self.header,self.a,self.id,self.worldid,self.id_b,self.pad,self.qA,self.qB,self.qC,self.qD,self.x,self.y,self.z) + self.data.make()

class RigidBodyData:
    def __init__(self, data: bytes):
        raise NotImplementedError()
    def make(self) -> bytes:
        raise NotImplementedError()
class RigidBodyStatic(RigidBodyData):
    struct = "25s"
    header = b"\x00\x01"
    def __init__(self, data):
        self.data: bytes = data
    def make(self):
        return self.data
class RigidBodyMobile(RigidBodyData):
    struct = "5s"
    header = b"\x00\x02"
    def __init__(self, data):
        self.data: bytes = data
    def make(self):
        return self.data

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
        self.items: list[Item]

        offset = calcsize(self.header.size)
        self.header = Container(data[slice(offset)])
        size = self.header.size
        for _ in range(size):
            end = offset + calcsize(Item.struct)
            item = Item(data[slice(offset, end)])
            self.items.append(item)
            offset = end

    def make_container(self):
        assert len(self.items) == self.header.size, f"len(self.items) = {len(self.items)} but it should be {self.header.size}"
        container = self.header.make()
        for item in self.items:
            assert(len(item) == calcsize(Item.struct))
            container += item
        container += b"\x00\x00"
        return container
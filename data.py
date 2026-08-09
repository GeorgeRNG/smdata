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
        self.id =      self.add(BYTE_ID)
        self.tool =    self.add(INT)
        """
        If the id refers to a tool, then this points to a relevant entry in the Tool table.
        If not, this is usually FF FF FF FF
        """
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

class Unit(Struct):
    def __members__(self):
        self.header = self.add(STRING(3)) #1
        self.id = self.add(INT) #2
        self.a = self.add(BYTE) #3 # usually 0xff
        self.grid_x = self.add(SIGNED_INT) #4
        """Matches the SQL value"""
        self.grid_y = self.add(SIGNED_INT) #5
        """Matches the SQL value"""
        self.world_id = self.add(SHORT) #6
        self.unit = self.add(BYTE_ID) #7
        self.world_id_target = self.add(SHORT) #8
        """Changing this value seems to send the unit into the given world"""
        self.pos_x = self.add(FLOAT) #9
        """Altitude"""
        self.pos_y = self.add(FLOAT) #9
        """North"""
        self.pos_z = self.add(FLOAT) #9
        """East"""
        self.rotation = self.add(FLOAT) #10
        self.d = self.add(FLOAT) #11 # might be a rotation value in radians
        self.e = self.add(STRING(9)) #12 # usually 9 null bytes

class Tool(Struct):
    """
    This is referenced by a Container's Item's tool field.
    It may be used for storing data on tools for scripts.
    """
    def __members__(self):
        self.header = self.add(STRING(3)) # usually 08 00 01
        self.id =     self.add(INT)
        self.tool =   self.add(BYTE_ID)
        self.owner =      self.add(INT)
        # fdb8b8be-96e7-4de0-85c7-d2f42e4f33ce
        # 080001 00000012 ce334f2ef4d2c785e04de796beb8b8fd 00000001

class Controller(Parsable):
    def __init__(self, data: bytes):
        self.header = ControllerHeader(data)
        offset = self.header.calcsize()

        types = {
            ControllerElectricEngine.header: ControllerElectricEngine,
            ControllerGasEngine.header: ControllerGasEngine,
            ControllerLever.header: ControllerLever,
            ControllerRadio.header: ControllerRadio,
            ControllerLogicGate.header: ControllerLogicGate,
            ControllerSuspension.legacy_header: ControllerSuspension,
            ControllerSpotLight.header: ControllerSpotLight,
            ControllerChest.header: ControllerChest,
            ControllerPiston.legacy_header: ControllerPiston,
            ControllerPiston.header: ControllerPiston,
            ControllerSuspension.header: ControllerSuspension,
        }

        # FIXME: some Containers do not have these, I think. It might be possible to work out if these are needed
        # based on the self.header.type() :pray:
        # Could also put these inside the actual .data
        # Could also make two ControllerData classes with and without this data
        # Could also make these just be None if it's empty
        # however, I feel like the first option is the best.
        self.children_count = data[offset]
        children_struct = f">{self.children_count}I"
        offset += 1
        end = offset + struct.calcsize(children_struct)
        self.children = list(struct.unpack(children_struct,data[offset:end]))
        """
        A list of IDs of other Controllers that are children of this Controller
        Children are output connections
        """
        offset = end
        
        self.bearings_count = data[offset]
        bearings_struct = f">{self.bearings_count}I"
        offset += 1
        end = offset + struct.calcsize(bearings_struct)
        self.bearings = list(struct.unpack(bearings_struct,data[offset:end]))
        """
        A list of IDs of bearings that are children of this Controller
        """
        offset = end

        type = self.header.type()
        print(type)
        if type in types: self.data = types[type](data[offset:])
        else: self.data = data[offset:]

    def __annotations__(self):
        (top, bottom) = self.header.__annotations__()
        top += " BB"
        bottom += f" {struct.pack("B", self.children_count).hex()}"
        for (i,child) in enumerate(self.children):
            top += f" {i}#IIIIIIII"
            bottom += f" {i}#{struct.pack(">I",child).hex()}"
        top += " BB"
        bottom += f" {struct.pack("B", self.bearings_count).hex()}"
        for (i,bearing) in enumerate(self.bearings):
            top += f" {i}#IIIIIIII"
            bottom += f" {i}#{struct.pack(">I",bearing).hex()}"
        top += " "
        bottom += " "
        if isinstance(self.data, bytes):
            top += len(self.data) * 2 * "s"
            bottom += self.data.hex()
        else:
            (data_top, data_bottom) = self.data.__annotations__()
            top += data_top
            bottom += data_bottom

        return (top,bottom)

    def make(self):
        assert self.children_count == len(self.children)
        assert self.bearings_count == len(self.bearings)
        controller = self.header.make()
        controller += struct.pack(f">B{self.children_count}I",self.children_count,*self.children)
        controller += struct.pack(f">B{self.bearings_count}I",self.bearings_count,*self.bearings)
        controller += self.data if isinstance(self.data, bytes) else self.data.make()
        return controller

class ControllerHeader(Struct):
    # he ty a  id       hostid   ht hostid   ht data
    # 03 14 01 000002ba 00001359 01 00001359 01 00 0005
    def __members__(self):
        self.header = self.add(STRING(1)) # 03
        self.type = self.add(BYTE)
        self.a = self.add(STRING(1)) # 01
        self.id = self.add(INT)
        self.hostid = self.add(INT)
        self.hosttype = self.add(BYTE) # 01
        self.hostid2 = self.add(INT)
        self.hosttype2 = self.add(BYTE)
        """
        Number of child connections child
        Children are output connections
        """

    def __init__(self, data):
        super().__init__(data)
        if self.hostid() != self.hostid2():
            print("hostid mismatch in Controller " + str(self.id()))
        if self.hosttype() != self.hosttype2():
            print("hosttype mismatch in Controller" + str(self.id))

class ControllerByteState(Struct):
    def __members__(self):
            self.state = self.add(BYTE)
class ControllerToggleable(ControllerByteState):
    def is_on(self):
        return (self.state & 0x80) != 0
    def set_on(self, on):
        if on:
            self.state |= 0x80
        else:
            self.state &= ~0x80

class ControllerElectricEngine(Struct):
    header = 0x05
    def __members__(self):
        self.power = self.add(BYTE)
class ControllerGasEngine(Struct):
    header = 0x06
    def __members__(self):
        self.power = self.add(BYTE)
class ControllerLever(ControllerToggleable):
    header = 0x0b
class ControllerRadio(ControllerToggleable):
    header = 0x0e
class ControllerLogicGate(ControllerToggleable):
    header = 0x14
    AND = 0
    OR = 1
    XOR = 2
    NAND = 3
    NOR = 4
    XNOR = 5
    def get_type(self):
        return self.state & 0x07
    def set_type(self, type):
        self.state &= ~0x07
        self.state |= type & 0x07
class ControllerSpotLight(Struct):
    header = 0x19
    def __members__(self):
        self.color = self.add(STRING(3))
        """Appears to do nothing"""
        self.alpha = self.add(BYTE)
        """Appears to do nothing"""
        self.brightness = self.add(BYTE)
        """Brightness levels increase in multiples of 10, from 10 to 100"""
class ControllerChest(Struct):
    header = 0x1a
    def __members__(self):
        self.id = self.add(SHORT)
        self.a = self.add(SHORT)
class ControllerPiston(Struct):
    legacy_header = 0x1d
    header = 0x23

    def __members__(self):
        self.range = self.add(BYTE)
        self.speed = self.add(BYTE)
class ControllerSuspension(Struct):
    legacy_header = 0x17
    header = 0x24

    def __members__(self):
        self.strength = self.add(BYTE)
        """Suspension goes from 0 to 12, however legacy suspension goes from 0 to 13"""

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
        self.c                = self.add(INT)
        self.unit             = self.add(INT)
        self.d                = self.add(INT)
        self.portal           = self.add(INT)
        self.e                = self.add(INT)
        self.voxelterrain     = self.add(INT)
        self.scriptableobject = self.add(INT)
        self.shapegroup       = self.add(INT)
        self.f                = self.add(INT)
        
    #         rigidbod joint    childsha controll containe harvesta          tool              unit              portal            voxel    scriptab shapegro
    #00000011 00000602 000002b1 00001ab4 00000583 00000019 00000100 00000100 00001707 00000200 00000400 00000100 00000112 34567800 00000300 0000fd90 00000540 00000001
    #00000011 00000603 000002b1 00001ab5 00000583 00000019 00000100 00000100 00001707 00000200 00000400 00000100 00000112 34567800 00000300 0000fd90 00000540 00000001
    #00000011 00000603 000002b1 00001ab7 00000585 0000001a 00000100 00000100 00001707 00000200 00000400 00000100 00000112 34567800 00000300 0000fd90 00000540 00000001
    #00000011 00000604 000002b1 00001ab8 00000586 0000001a 00000100 00000100 00001708 00000200 00000401 00000100 00000112 34567800 00000300 0000fd90 00000540 00000001
    #00000011 00000605 000002b2 00001ab9 00000586 0000001a 00000100 00000100 00001708 00000200 00000401 00000100 00000112 34567800 00000300 0000fd90 00000540 00000001
    #00000011 00000605 000002b2 00001abc 00000589 0000001d 00000100 00000100 0000170a 00000200 00000401 00000100 00000112 34567800 00000304 0000fd90 00000540 00000001
    #00000011 00000001 00000001 00000001 00000001 00000003 000004fa 00000002 0000000d 00000002 00000001 00000001 00000001 00000001 00000001 0000000d 00000001 40000000
    #00000011 0000004f 00000002 0000026e 0000002c 00000007 0000118f 00000002 00000013 00000002 00000014 00000001 00000001 00000a20 00000001 0000002b 00000001 40000000
    #00000011 000014cd 0000007d 00001d39 0000091d 000000a7 0000610f 00000004 0000002b 00000003 000008a5 00000001 00000005 0003cdca 00000001 000009f9 0000000b 40000027
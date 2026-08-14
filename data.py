from struct import pack, unpack, calcsize
from structs import *
from datas.childshape import *
from datas.tool import *
from datas.uniqueids import *
from datas.unit import *

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



class Controller(Parsable):
    def __parse__(self, data: ByteByByte):
        self.header = ControllerHeader(data)

        types: dict[int,tuple[(type[Parsable]),bool]] = {
            ControllerElectricEngine.header: (ControllerElectricEngine,True),
            ControllerGasEngine.header: (ControllerGasEngine,True),
            ControllerLever.header: (ControllerLever,True),
            ControllerSensor.header_legacy: (ControllerSensor,True),
            ControllerThrusterLegacy.header: (ControllerThrusterLegacy,False),
            ControllerRadio.header: (ControllerRadio,True),
            ControllerTotebot.header: (ControllerTotebot,True),
            ControllerLogicGate.header: (ControllerLogicGate,True),
            ControllerSuspension.legacy_header: (ControllerSuspension,True),
            ControllerSpotLight.header: (ControllerSpotLight,True),
            ControllerChest.header: (ControllerChest,False),
            ControllerSimpleInteractive.header: (ControllerSimpleInteractive,True),
            ControllerThruster.header: (ControllerThruster,False),
            ControllerPiston.legacy_header: (ControllerPiston,True),
            ControllerPiston.header: (ControllerPiston,True),
            ControllerSuspension.header: (ControllerSuspension,True),
            ControllerSensor.header: (ControllerSensor,True)
        }

        type: int = self.header.type()
        type_info = types[type] if type in types else None

        if type_info is None:
            offset = data.offset
            try: self.connections: ControllerConnections = ControllerConnectionsPresent(data)
            except: 
                data.offset = offset
                self.connections = ControllerConnectionsAbsent(data)
        else:
            if type_info[1]: self.connections = ControllerConnectionsPresent(data)
            else: self.connections = ControllerConnectionsAbsent(data)

        if type_info is not None: self.data = type_info[0](data)
        else: self.data = data.get_all()

    def annotate(self) -> Annotations:
        annotations = super().annotate()
        annotations.add("HEADER [",self.header, "] ", self.connections,splitter="")
        annotations.split()
        if (isinstance(self.data, bytes)):
            annotations.cell("data (unknown)","s" * len(self.data) * 2,self.data.hex())
        else:
            annotations.add(self.data)
        return annotations

    def make(self):
        controller = self.header.make()
        controller += self.connections.make()
        controller += self.data if isinstance(self.data, bytes) else self.data.make()
        return controller

class ControllerHeader(Struct):
    # he ty a  id       hostid   ht hostid   ht data
    # 03 14 01 000002ba 00001359 01 00001359 01 00 0005
    def __members__(self):
        self.header = self.add(STRING(1),"header") # 03
        self.type = self.add(BYTE,"type")
        self.a = self.add(STRING(1)) # 01
        self.id = self.add(INT,"id")
        self.hostid = self.add(INT,"hostid")
        self.hosttype = self.add(BYTE,"ht") # 01
        self.hostid2 = self.add(INT,"hostid2")
        self.hosttype2 = self.add(BYTE,"t2")
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

class ControllerConnections(Parsable):
    pass
class ControllerConnectionsAbsent(ControllerConnections):
    def make(self): return b""
    def __parse__(self, data):
        pass
class ControllerConnectionsPresent(ControllerConnections):
    def __parse__(self, data: ByteByByte):
        self.children_count: int = data.read(BYTE)
        children_struct = f">{self.children_count}I"
        self.children = list(struct.unpack(children_struct,data.get(struct.calcsize(children_struct))))
        """
        A list of IDs of other Controllers that are children of this Controller
        Children are output connections
        """
        
        self.bearings_count = data.read(BYTE)
        bearings_struct = f">{self.bearings_count}I"
        self.bearings = list(struct.unpack(bearings_struct,data.get(struct.calcsize(bearings_struct))))
        """
        A list of IDs of bearings that are children of this Controller
        """
    def make(self):
        assert self.children_count == len(self.children)
        assert self.bearings_count == len(self.bearings)
        return (
            struct.pack(f">B{self.children_count}I",self.children_count,*self.children) +
            struct.pack(f">B{self.bearings_count}I",self.bearings_count,*self.bearings)
        )
    def annotate(self):
        annotations = super().annotate()
        annotations.cell("c#","BB",struct.pack("B", self.children_count).hex())
        for (i,child) in enumerate(self.children):
            annotations.split()
            annotations.cell(f"con {i}","IIIIIIII",struct.pack(">I",child).hex())
        annotations.split()
        annotations.cell("b#","BB", struct.pack("B", self.bearings_count).hex())
        for (i,bearing) in enumerate(self.bearings):
            annotations.split()
            annotations.cell(f"bearing {i}","IIIIIIII",struct.pack(">I",bearing).hex())
        return annotations

class ControllerByteState(Struct):
    def __members__(self):
            self.state = self.add(BYTE, "state")
class ControllerToggleable(ControllerByteState):
    def is_on(self):
        return (self.state & 0x80) != 0
    def set_on(self, on):
        if on: self.state |= 0x80
        else: self.state &= ~0x80

class ControllerElectricEngine(Struct):
    header = 0x05
    def __members__(self):
        self.power = self.add(BYTE,"power")
class ControllerGasEngine(Struct):
    header = 0x06
    def __members__(self):
        self.power = self.add(BYTE,"power")
class ControllerLever(ControllerToggleable):
    header = 0x0b
class ControllerThrusterLegacy(Struct):
    header = 0x0d
    def __members__(self):
        self.a = self.add(STRING(10))
        self.power = self.add(BYTE,"power")
class ControllerRadio(ControllerToggleable):
    header = 0x0e
class ControllerTotebot(Struct):
    header = 0x10
    STYLE_RETRO = 0
    STYLE_DANCE = 1
    def __members__(self):
        self.style = self.add(BYTE, "style")
        self.pitch = self.add(FLOAT, "pitch")
        """From 0.0 to 1.0"""
        self.volume = self.add(BYTE, "volume")
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
        self.color = self.add(STRING(3),"rrggbb")
        """Appears to do nothing"""
        self.alpha = self.add(BYTE,"aa")
        """Appears to do nothing"""
        self.brightness = self.add(BYTE,"brightness")
        """Brightness levels increase in multiples of 10, from 10 to 100"""
class ControllerChest(Struct):
    header = 0x1a
    def __members__(self):
        self.container = self.add(INT,"container")
        """Relevant container ID"""
        self.a = self.add(SHORT)
class ControllerSimpleInteractive(ControllerToggleable):
    header = 0x1e
class ControllerThruster(Struct):
    header = 0x22
    def __members__(self):
        self.a = self.add(STRING(8))
        self.container = self.add(INT,"container")
        self.b = self.add(STRING(2))
        self.power = self.add(BYTE,"power")
        self.c = self.add(STRING(4))
class ControllerPiston(Struct):
    legacy_header = 0x1d
    header = 0x23

    def __members__(self):
        self.range = self.add(BYTE,"range")
        self.speed = self.add(BYTE,"speed")
class ControllerSuspension(Struct):
    legacy_header = 0x17
    header = 0x24

    def __members__(self):
        self.strength = self.add(BYTE,"strength")
        """Suspension goes from 0 to 12, however legacy suspension goes from 0 to 13"""
class ControllerSensor(Struct):
    header = 0x26
    header_legacy = 0x0c

    MODE_BUTTON = 0x80
    MODE_SOUND = 0x40
    MODE_COLOR = 0x20

    def __members__(self):
        self.range = self.add(BYTE,"range")
        self.color = self.add(STRING(3),"rrggbb")
        self.options = self.add(BYTE,"options")

    def get_mode_button(self):
        """Returns True if the switch's mode is set to Button"""
        return self.__get_byte__(self.MODE_BUTTON)
    def set_mode_button(self, button: bool):
        """True sets the switch's mode to Button"""
        self.__set_byte__(self.MODE_BUTTON, button)

    def get_mode_sound(self):
        return self.__get_byte__(self.MODE_SOUND)
    def set_mode_sound(self, sound: bool):
        self.__set_byte__(self.MODE_SOUND, sound)

    def get_mode_color(self):
        return self.__get_byte__(self.MODE_COLOR)
    def set_mode_color(self, color: bool):
        self.__set_byte__(self.MODE_COLOR, color)

    def __get_byte__(self, byte: int):
        return (self.state & byte) != 0
    def __set_byte__(self, byte: int, value: bool):
        if value: self.options |= byte
        else: self.options &= ~byte


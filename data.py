from struct import pack, unpack, calcsize
from structs import *
from datas.childshape import *
from datas.tool import *
from datas.uniqueids import *
from datas.unit import *
from datas.rigidbody import *

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


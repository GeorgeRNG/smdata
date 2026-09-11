from structs import *

class ScriptData(Parsable):
    def __parse__(self, data):
        self.uid = data.read(STRING(16))
        self.key_length = data.read(SHORT)
        self.key = data.read(STRING(self.key_length))
        self.worldid = data.read(SHORT)
        self.flags = data.read(BYTE)
        self.data_length = data.read(INT)
        self.data = data.read(STRING(self.data_length))
        self.rest = data.get_all()


    # 0000002b 804c554100000001050500f00f0200000009006b6579436f756e7465725472696767657273050000000000

    def annotate(self):
        annotations = super().annotate()
        annotations.encode("uid",         self.uid,         STRING(16))
        annotations.split()
        annotations.encode("keylength",   self.key_length,  SHORT)
        annotations.split()
        annotations.encode("key",         self.key,         STRING(self.key_length))
        annotations.split()
        annotations.encode("worldid",     self.worldid,     SHORT)
        annotations.split()
        annotations.encode("flags",       self.flags,       BYTE)
        annotations.split()
        annotations.encode("data length", self.data_length, INT)
        annotations.split()
        annotations.encode("data",        self.data,        STRING(self.data_length))
        annotations.bytes(self.rest)
        return annotations

def decodeLZ4(data: ReadableSource) -> bytes:
    input = ByteByByte(data) if isinstance(data, bytes) else data
    output = bytearray()

    while not input.done():
        token = input.read(BYTE)
        literalLength = token >> 4
        matchLength = (token & 0x0F) + 4

        if literalLength == 15:
            length = 0
            while True:
                length = input.read(BYTE)
                literalLength += length
                if length < 255: break
        
        if literalLength > 0:
            output += input.read(STRING(literalLength))

        if input.done():
            break

        offset = input.read(BYTE) + (input.read(BYTE) << 8) # Little endian Short

        if matchLength == 19:
            length = 0
            while True:
                length = input.read(BYTE)
                matchLength += length
                if length < 255: break

        outputLength = len(output)

        for i in range(matchLength):
            matchPos = outputLength - offset + i
            output.append(output[matchPos])

        # return output

    return bytes(output)

class types: 
    BOOLEAN = 2
    FLOAT = 3
    STRING = 4
    OBJECT = 5
    INT = 6
    SHORT = 7
    BYTE = 8
    USERDATA = 100
class userdata_types:
    Uuid = 10001
    Vec3 = 10003
    Quat = 10004
    Color = 10005
    Shape = 10021
    Body = 10022
    Interactable = 10023
    Container = 10024
    Harvestable = 10025
    World = 10027
    Player = 10030
    Character = 10031
    Joint = 10032
    Portal = 10036
    PathNode = 10037
    Lift = 10038
    ScriptableObject = 10039
    Tool = 20002

class BitByBit():
    def __init__(self, bytes: bytes):
        self.bytes = bytes
        self.bit_offset = 0

    def __bytes__(self):
        return self.bytes

    def bit(self):
        offset = self.bit_offset // 8
        shift = self.bit_offset % 8
        self.bit_offset += 1
        return 1 if ((self.bytes[offset] << shift) & 0b1000_0000) != 0 else 0

    def byte(self):
        offset = self.bit_offset // 8
        shift = self.bit_offset % 8
        self.bit_offset += 8
        if shift == 0:
            return self.bytes[offset]
        else:
            return ((self.bytes[offset] << shift) & 0xFF) + (self.bytes[offset+1] >> (8-shift))

    def align(self):
        shift = self.bit_offset % 8
        if shift != 0:
            self.bit_offset += 8 - shift

    def read(self, type: StructMemberType):
        part = bytes([self.byte() for i in range(type.size)])
        return struct.unpack(">" + type.char,part)[0]


def decodeBitstream(data: ReadableSource):
    data = ByteByByte(data) if isinstance(data, bytes) else data

    def parseObject(data: BitByBit):
        type = data.read(BYTE)
        match type:
            case types.BOOLEAN: return data.read(BYTE) != 0
            case types.FLOAT: return data.read(FLOAT)
            case types.STRING:
                size = data.read(INT)
                data.align()
                return data.read(STRING(size))
            case types.OBJECT:
                size = data.read(INT)
                is_array = data.bit() == 1
                if is_array:
                    return [None]*data.read(INT) + [parseObject(data) for i in range(size)]
                else:
                    return dict([([parseObject(data),parseObject(data)]) for i in range(size)])
            case types.INT: return data.read(INT)
            case types.SHORT: return data.read(SHORT)
            case types.BYTE: return data.read(BYTE)
            case types.USERDATA:
                userdataType = data.read(INT)
                result = None
                match userdataType:
                    case userdata_types.Uuid: result = data.read(BYTE_ID)
                    case userdata_types.Vec3: result = [data.read(FLOAT), data.read(FLOAT), data.read(FLOAT)]
                    case userdata_types.Quat | userdata_types.Color: result = [data.read(FLOAT), data.read(FLOAT), data.read(FLOAT), data.read(FLOAT)]
                    case _: data = data.read(INT)
                return {"_userdataType": userdataType, "_data": result}


    magic = data.read(STRING(3))
    version = data.read(INT)
    content = parseObject(BitByBit(data.get_all()))

    result = {
        "magic": magic,
        "version": version,
        "content": content,
    }

    return result
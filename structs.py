"""
structs.py
Classes for easily handling binary data
"""

import struct

def get_byte(input, byte: int):
        return (input & byte) != 0
def set_byte(input, byte: int, value: bool):
    if value: input |= byte
    else: input &= ~byte
    return input

class ByteByByte:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def get(self, amount: int):
        data = self.data[self.offset:self.offset+amount]
        self.offset += amount
        return data

    def get_all(self):
        return self.get(len(self)-self.offset)

    def read(self, type: StructMemberType):
        return struct.unpack(type.char, self.get(type.size))[0]

    def reader(value: ReadableSource):
        return ByteByByte(value) if isinstance(value, bytes) else value

    def __bytes__(self):
        return self.data

    def __len__(self):
        return len(self.data)

ReadableSource = bytes|ByteByByte

class StructMemberType:
    def __init__(self, char, size: int, type: type):
        self.char: str = char
        self.size: int = size
        self.type = type

CHAR = StructMemberType("c",1,bytes)
BYTE = StructMemberType("B",1,int)
SHORT = StructMemberType("H",2,int)
SIGNED_SHORT = StructMemberType("h",2,int)
INT = StructMemberType("I",4,int)
SIGNED_INT = StructMemberType("I",4,int)
LONG = StructMemberType("L",4,int)
LONGLONG = StructMemberType("Q",8,int)
FLOAT = StructMemberType("f",4,float)
DOUBLE = StructMemberType("d",4,float)
def STRING(length: int):
    return StructMemberType(f"{length}s",length,bytes)
BYTE_ID = StructMemberType("16s",16,bytes)


class StructMember:
    def __init__(self, type: StructMemberType, name = ""):
        self.type = type
        self.value = None # typescript when
        self.name = name

    def __call__(self, *args, **kwds):
        if args == ():
            return self.get()
        else:
            self.set(args[0])

    def get(self):
        return self.value
    def set(self, value):
        self.value = value

class Annotations:
    def __init__(self):
        self.names = ""
        self.types = ""
        self.value = ""
    def add(self, *others: StructMember|Parsable|Annotations|str, splitter = " "):
        first = True
        for other in others:
            if first:
                first = False
            else:
                self.add(splitter)
            if isinstance(other, Parsable):
                other = other.annotate()
            if isinstance(other, StructMember):
                self.encode(other.name, other.value, other.type)

            elif isinstance(other, str):
                self.cell(other,other,other)
            elif isinstance(other, Annotations):
                self.cell(other.names, other.types, other.value)
            else: raise TypeError()

    def cell(self, name: str, type: str, value: str):
        assert isinstance(name, str) and isinstance(type, str) and isinstance(value, str) 
        length = len(value)
        assert len(type) == length
        self.names += name.ljust(length)[:length]
        self.types += type
        self.value += value

    def encode(self, names: str, value, type: StructMemberType):
        target_length = type.size * 2
        types = type.char[-1] * (type.size * 2)
        value = struct.pack(">" + type.char, value).hex()
        assert len(types) == target_length and len(value) == target_length
        self.cell(names, types, value)


    def split(self, splitter = " "):
        if not self.empty():
            self.add(splitter)

    def empty(self):
        return len(self) == 0

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return "\n".join([self.names, self.types, self.value])

    def __repr__(self):
        return self.__str__()

class Parsable:
    def __init__(self, data: ReadableSource):
        self.__parse__(ByteByByte.reader(data))
    def __parse__(self, data: ByteByByte) -> None:
        raise NotImplementedError()
    def make(self) -> bytes:
        raise NotImplementedError()

    def annotate(self) -> Annotations:
        return Annotations()
    
class Struct(Parsable):
    def add(self, type: StructMemberType, name: str = "") -> StructMember:
        member = StructMember(type, name)
        self.members.append(member)
        return member

    def __members__(self):
        pass

    def __init__(self, data: ReadableSource):
        self.members: list[StructMember] = []
        self.__members__()
        super().__init__(data)

    def __parse__(self, data: ByteByByte):
        fmt = self.get_fmt()
        length = struct.calcsize(fmt)
        for (i,v) in enumerate(struct.unpack(fmt, data.get(length))):
            self.members[i].value = v

    def calcsize(self) -> int:
        return struct.calcsize(self.get_fmt())

    def make(self) -> bytes:
        return struct.pack(self.get_fmt(), *[member.value for member in self.members])
    
    def get_fmt(self):
        string = ">"
        for member in self.members:
            string += member.type.char
        return string

    def annotate(self) -> Annotations:
        annotations = super().annotate()

        for member in self.members:
            annotations.split(" ")
            annotations.add(member)

        return annotations
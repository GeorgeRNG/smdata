"""
structs.py
Classes for easily handling binary data
"""

import struct

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
LONGLONG = StructMemberType("Q",4,int)
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
    def add(self, *others: StructMember|Parsable|Annotations|tuple[str,str,str]|list[str]|str, splitter = " "):
        first = True
        for other in others:
            if first:
                first = False
            else:
                self.add(splitter)
            if isinstance(other, Parsable):
                other = other.annotate()
            if isinstance(other, StructMember):
                target_length = other.type.size * 2
                names = other.name
                types = other.type.char[-1] * (other.type.size * 2)
                value = struct.pack(">" + other.type.char, other.value).hex()
                assert len(types) == target_length and len(value) == target_length
                self.cell(names, types, value)
            elif isinstance(other, tuple) or isinstance(other, list):
                self.cell(other[0], other[1], other[2])
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
    def __init__(self, data: bytes):
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

    def __init__(self, data: bytes):
        self.members: list[StructMember] = []
        self.__members__()
        fmt = self.get_fmt()
        length = struct.calcsize(fmt)
        for (i,v) in enumerate(struct.unpack(fmt, data[:length])):
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
"""
structs.py
Classes for easily handling binary data
"""

import struct

class StructMemberType:
    def __init__(self, char, size: int, type: type):
        self.char = char
        self.size = size
        self.type = type
    def get_char(self) -> str:
        return self.char
    def get_size(self) -> int:
        return self.size
    def get_type(self) -> type:
        return self.type

CHAR = StructMemberType("c",1,bytes)
BYTE = StructMemberType("B",1,int)
SHORT = StructMemberType("H",2,int)
INT = StructMemberType("I",4,int)
LONG = StructMemberType("L",4,int)
LONGLONG = StructMemberType("Q",4,int)
FLOAT = StructMemberType("f",4,float)
DOUBLE = StructMemberType("d",4,float)
def STRING(length: int):
    return StructMemberType(f"{length}s",length,str)


class StructMember:
    def __init__(self, type: StructMemberType):
        self.type = type
        self.value = None # typescript when

    def get(self):
        return self.value
    def set(self, value):
        self.value = value

class Parsable:
    def __init__(self, data: bytes):
        raise NotImplementedError()
    def make(self) -> bytes:
        raise NotImplementedError()
    
class Struct(Parsable):
    def add(self, type: StructMemberType) -> StructMember:
        member = StructMember(type)
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
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
    def __init__(self, type: StructMemberType):
        self.type = type
        self.value = None # typescript when

    def __call__(self, *args, **kwds):
        if args == ():
            return self.get()
        else:
            self.set(args[0])

    def get(self):
        return self.value
    def set(self, value):
        self.value = value

class Parsable:
    def __init__(self, data: bytes):
        raise NotImplementedError()
    def make(self) -> bytes:
        raise NotImplementedError()

    def __annotations__(self) -> tuple[str,str]:
        top = ""
        bottom = ""
        return (top, bottom)

    def annotate(self) -> str:
        return "\n".join(self.__annotations__())
    
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

    def __annotations__(self):
        (top, bottom) = super().__annotations__()

        for member in self.members:
            if len(top) != 0:
                top += " "
            if len(bottom) != 0:
                bottom += " "
            top += member.type.char[-1] * member.type.size * 2
            bottom += struct.pack(">" + member.type.char, member.value).hex()

        return (top, bottom)
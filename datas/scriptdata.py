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

from structs import *

class Tool(Struct):
    """
    This is referenced by a Container's Item's tool field.
    It may be used for storing data on tools for scripts.
    """
    def __members__(self):
        self.header = self.add(STRING(3),"header") # usually 08 00 01
        self.id =     self.add(INT,"id")
        self.tool =   self.add(BYTE_ID,"tool id")
        self.owner =  self.add(INT,"owner")
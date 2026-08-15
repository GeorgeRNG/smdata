from structs import *

class Item(Struct):
    def __members__(self):
        self.id =      self.add(BYTE_ID,"shape/tool uuid")
        self.tool =    self.add(INT,"tool id")
        """
        If the id refers to a tool, then this points to a relevant entry in the Tool table.
        If not, this is usually FF FF FF FF
        """
        self.count =   self.add(SHORT,"count")

class ContainerHeader(Struct):
    def __members__(self):
        self.header =  self.add(STRING(3),"header")
        self.id =      self.add(INT,"id")
        self.divider = self.add(STRING(1))
        self.slots =   self.add(BYTE,"size")
        self.maxsize = self.add(SHORT,"stack")
class Container(Parsable):
    def __parse__(self, data) -> None:
        self.header = ContainerHeader(data)
        self.items: list[Item] = []
        for _ in range(self.header.slots()):
            self.items.append(Item(data))
        self.filter_count = data.read(SHORT)
        self.filters: list[bytes] = []
        """These are NOT ByteIDs, they are UUIDs without the dashes, they *aren't* backwards."""
        for _ in range(self.filter_count):
            self.filters.append(data.read(STRING(16)))
        self.a = data.get_all()

    def make(self):
        container = self.header.make()
        assert self.header.slots() == len(self.items)
        for item in self.items:
            container += item.make()
        container += self.a
        container += struct.pack(">H" + "16s" * self.filter_count, self.filter_count, *self.filters)
        return container

    def annotate(self):
        annotations = super().annotate()
        annotations.add(self.header)
        annotations.add(" [")
        for (i,item) in enumerate(self.items):
            annotations.add(f" #{i}")
            annotations.add(item)
        annotations.add("]")
        annotations.split()
        annotations.encode("filters",self.filter_count,SHORT)
        annotations.add(" [")
        for (i,filter) in enumerate(self.filters):
            annotations.add(f" #{i}")
            annotations.encode("filter shape id",filter,BYTE_ID)
        annotations.add("]")
        annotations.bytes(self.a)
        return annotations
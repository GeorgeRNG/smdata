from structs import *

class Unit(Struct):
    def __members__(self):
        self.header = self.add(STRING(3)) #1
        self.id = self.add(INT) #2
        self.a = self.add(BYTE) #3 # usually 0xff
        self.grid_x = self.add(SIGNED_INT) #4
        """Matches the SQL value"""
        self.grid_y = self.add(SIGNED_INT) #5
        """Matches the SQL value"""
        self.world_id = self.add(SHORT) #6
        self.unit = self.add(BYTE_ID) #7
        self.world_id_target = self.add(SHORT) #8
        """Changing this value seems to send the unit into the given world"""
        self.pos_x = self.add(FLOAT) #9
        """Altitude"""
        self.pos_y = self.add(FLOAT) #9
        """North"""
        self.pos_z = self.add(FLOAT) #9
        """East"""
        self.rotation = self.add(FLOAT) #10
        self.d = self.add(FLOAT) #11 # might be a rotation value in radians
        self.e = self.add(STRING(9)) #12 # usually 9 null bytes

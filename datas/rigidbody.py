from structs import *

class RigidBodyHeader(Struct):
    def __members__(self):
        self.header = self.add(STRING(2),"header")
        self.a = self.add(BYTE)
        self.id = self.add(INT,"id")
        self.world_id = self.add(SHORT,"worldid")
        self.id_b = self.add(BYTE_ID)
        self.b = self.add(SHORT)
        self.rotation_x = self.add(FLOAT,"x rotation")
        """Quaternion, the order of elements reverse between being static or mobile"""
        self.rotation_y = self.add(FLOAT,"y rotation")
        """Quaternion, the order of elements reverse between being static or mobile"""
        self.rotation_z = self.add(FLOAT,"z rotation")
        """Quaternion, the order of elements reverse between being static or mobile"""
        self.rotation_w = self.add(FLOAT,"w rotation")
        """Quaternion, the order of elements reverse between being static or mobile"""
        self.x = self.add(FLOAT,"x")
        """East"""
        self.y = self.add(FLOAT,"y")
        """North"""
        self.z = self.add(FLOAT,"z")
        """Altitude"""

class RigidBody(Parsable):
    def __parse__(self, data):
        self.header = RigidBodyHeader(data)
        type = self.header.header()
        if   type == RigidBodyStatic.header: self.data = RigidBodyStatic(data)
        elif type == RigidBodyMobile.header: self.data = RigidBodyMobile(data)
        else: self.data = data.get_all()

    def annotate(self):
        annotations = super().annotate()
        annotations.add(self.header)
        annotations.split()
        if isinstance(self.data, bytes): annotations.bytes(self.data)
        else: annotations.add(self.data)
        return annotations

    def make(self):
        return self.header.make() + (self.data if isinstance(self.data, bytes) else self.data.make())

class RigidBodyData(Struct):
    RESTRICT_ERASABLE = 2**0
    """Players cannot break blocks, uses the encryptor's hexagonal shields and sounds when trying"""
    RESTRICT_BUILDABLE = 2**1
    """Players cannot place blocks, see the placing or breaking overlays, or use the weld tool (unless the creation is on a lift, in which case the weld tool can merge neighbouring pieces on joints albeit it with some missing particles)"""
    RESTRICT_PAINTABLE = 2**2
    """Players cannot use the paint gun to paint or unpaint"""
    RESTRICT_CONNECTABLE = 2**3
    """Players cannot see connections or edit connections"""
    RESTRICT_LIFTABLE = 2**4
    """Players cannot put free moving creations on the lift"""
    RESTRICT_USABLE = 2**5
    """Players cannot access the configuration or upgrade screen for parts, but can still use parts"""
    RESTRICT_DESTRUCTABLE = 2**6
    """Explosions, melee, and projectiles cannot damage blocks, and enemies do not consider attacking blocks"""
    RESTRICT_CONVERTIBLE_TO_DYNAMIC = 2**7
    """Breaking the support for these creations do not make them dynamic. If they are split into two different bodies, one will become dynamic"""

    def __init__(self, data) -> None:
        self.restrictions: StructMember
        super().__init__(data)
    def get_restriction(self, restriction: int) -> bool:
        return get_byte(self.restrictions(), restriction)
    def set_restriction(self, restriction: int, value: bool):
        self.restrictions(set_byte(self.restrictions(),restriction,value) )

class RigidBodyStatic(RigidBodyData):
    header = b"\x00\x01"
    def __members__(self):
        self.restrictions = self.add(BYTE,"flags")
        self.lift = self.add(INT,"lift owner")
        """
        The ID of the player who has this creation on a lift
        When it is not on a lift, it is FFFFFFFF
        Setting it to a player id (or 00000000) will make it automatically become a mobile object when loading in.
        """
class RigidBodyMobile(RigidBodyData):
    header = b"\x00\x02"
    def __members__(self):
        self.x_velocity = self.add(FLOAT,"x velocity")
        """East"""
        self.y_velocity = self.add(FLOAT,"y velocity")
        """North"""
        self.z_velocity = self.add(FLOAT,"z velocity")
        """Vertical"""
        self.x_rotation = self.add(FLOAT,"x spin")
        """Velocity of rotation aruond the X axis"""
        self.y_rotation = self.add(FLOAT,"y spin")
        """Velocity of rotation around the Y axis"""
        self.z_rotation = self.add(FLOAT,"z spin")
        """Velocity of rotation around the Z axis"""
        self.restrictions = self.add(BYTE,"flags")
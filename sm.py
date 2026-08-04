from struct import pack, unpack, calcsize
import uuid
from pathlib import Path
import json
import sys


def itemid_from_shapeuuid(uuidstring: str):
    return bytes.fromhex(uuidstring.replace('-',''))[::-1]
def shapeuuid_from_itemid(id: bytes):
    return uuid.UUID(int=int.from_bytes(id, 'little'))

class Paths:
    def __init__(self, game_dir):
        self.data = Path(game_dir,"Data")
        self.survival = Path(game_dir,"Survival")
        self.challenge = Path(game_dir,"ChallengeData")

    def resolve(self, path):
        return Path(path
                        .replace("$GAME_DATA",str(self.data))
                        .replace("$SURVIVAL_DATA",str(self.survival))
                        .replace("$CHALLENGE_DATA",str(self.challenge))
                    )

BLOCKS = 0
PARTS = 1
WEDGES = 2
ITEMS = 3
def load_shapesets(game_dir, data_source):
    paths = Paths(game_dir)

    path = Path(game_dir,data_source,"Objects","Database","shapesets.json")
    shapesetlist = []
    with open(path,"r") as shapesets:
        try:
            shapesetlist = json.loads(shapesets.read())["shapeSetList"]
        except:
            sys.stderr.write(f"shapesets at {path} is not valid json or missing shapeSetList\n")
            exit(1)
    blocks = []
    parts = []
    wedges = []
    items = []
    for shapeset in shapesetlist:
        with open(paths.resolve(shapeset),"r") as shapesetFile:
            data = json.loads(shapesetFile.read())
            if "partList" in data:
                parts.extend(data["partList"])
                items.extend(data["partList"])
            if "blockList" in data:
                blocks.extend(data["blockList"])
                items.extend(data["blockList"])
            if "wedgeList" in data:
                wedges.extend(data["wedgeList"])
                items.extend(data["wedgeList"])
            if ("partList" not in data) and ("blockList" not in data) and ("wedgeList" not in data):
                sys.stderr.write(f"shapesetfile at {shapeset} does not have partList or blockList\n")
    return (blocks, parts, wedges, items)
def shape_from_shapesets_via_item(shapesets, item: bytes):
    return shape_from_shapesets_via_uuid(shapesets, shapeuuid_from_itemid(item))
def shape_from_shapesets_via_uuid(shapesets, _uuid: uuid.UUID):
    for shape in shapesets[ITEMS]:
        if uuid.UUID(shape["uuid"]) == _uuid:
            return shape
def shape_from_shapesets_via_name(shapesets, name: str):
    for shape in shapesets[ITEMS]:
        if "name" in shape and shape["name"] == name:
            return shape

# Maybe only a user's data?
genericdata = ">16s 2s I 2s 9s 3f 4s 2f 4s 20s 4s"
def parse_genericdata(data):
    print("len", len(data))
    (
        uid,    # 16s
        a,      # 2s # 0004
        key,    # I
        b,      # 2s # fffe
        c,      # 9s # data
        x,      # 3f (1) # vertical
        y,      # 3f (2) # north
        z,      # 3f (3) # east
        d,      # 4s # 000100c4
        yaw,    # 2f (1) # radians
        pitch,  # 2f (2) # radians
        _,      # 4s # ffffffff
        e,      # 20s # data
        _,      # 4s # ffffffff
    ) = unpack(genericdata, data)
    # print(f"x: {x} y: {y} z: {z} yaw: {yaw} pitch: {pitch}")

    return (uid,a,key,b,c,x,y,z,d,yaw,pitch,e)
def make_genericdata(uid,a,key,b,c,x,y,z,d,yaw,pitch,e):
    return pack(genericdata, uid, a, key, b, c, x, y, z, d, yaw, pitch, b"\xff\xff\xff\xff", e, b"\xff\xff\xff\xff")

# 67ce7fe2f7564898b8f076080146a358                                       Altitude North    East                   Yaw      Pitch
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|38f7000001[3f38e2ee c19ce720 4114059c] [000100c4] [406edc90 bda222e7] ffffffff 1700f005[01100001140cc6c4]00000001000000|02ffffffff # standing



# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|38f700[0001|3f]38e2eec19ce7204114059c         [000100c4]      406edc90bda222e7[ffffff]ff17          00f005[01100001140cc6c4]00000001000000|02ffffffff # standing
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|31e8  [0001|41]90[0000c3]170000430640         [000100c4]      3d5f42f9bfc73376[000000]01180083            [01100001140cc6c4]140050        |02ffffffff # seat
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|36e8  [0001|41]8d[0000c3]1780004304a0         [000100c4]      40c5f355bf9dd28a[000000]0218          00f005[01100001140cc6c4]00000001000000|02ffffffff # toilet
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|35d9  [0001|41]8d[0000c3]17a0004308           [000100c4]      40c44bf9bf38c0ee[000000]0319          00f005[01100001140cc6c4]00000001000000|02ffffffff # bed
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|36e8  [0001|41]92[0000c3]1960004302a0         [000100c4]      3f5f1930bf0104ed[000000]0518          00f005[01100001140cc6c4]00000001000000|02ffffffff # saddle 5
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|36e8  [0001|41]92[0000c3]1960004304e0         [000100c4]      40960704bfc907db[000000]0618          00f005[01100001140cc6c4]00000001000000|02ffffffff # saddle 4
# 67ce7fe2f7564898b8f076080146a358|0004|01000000|fffe|03000000|45f218[0001|41]98c67cc31b24a6430811e23dc238003f13f800be17e000bff044d6bcd2525b [000000]6700010010010c00f005[01100001140cc6c4]00000001000000|02ffffffff # flyer
# 67ce7fe2f7564898b8f076080146a358|0004|04000000|fffe|03000000|41f318[0001|40]f3adfac4cee7b1c4ea2c0d3820000040453000c0d138003f9083653d490fe0 [ffffff]ff000100f005011000011787f3fa0000001b0000001cff0f5be7 # some guy's save


# 67ce7fe2f7564898b8f076080146a358000401000000fffe0300000031e8000141900000c3170000430640000100c43d5f42f9bfc733760000000118008301100001140cc6c414005002ffffffff # seat
# 67ce7fe2f7564898b8f076080146a358000401000000fffe0300000036e80001418d0000c31780004304a0000100c440c5f355bf9dd28a000000021800f00501100001140cc6c40000000100000002ffffffff # toilet

if __name__ == "__main__":

    print(parse_genericdata(bytes.fromhex("67ce7fe2f7564898b8f076080146a358000401000000fffe0300000038f70000013f38e2eec19ce7204114059c000100c43efa85ee3fc907dbffffffff1700f00501100001140cc6c40000000100000002ffffffff")))

    # nothing = bytes.fromhex("00000000000000000000000000000000")
    # wood = bytes.fromhex("713e220b49f05eafc24a4f239c3d95df")
    # output = make_container(id=1, size=30, a=b"\xff\xff", items=[
    #     make_container_item(wood, 123),
    #     make_container_item(itemid_from_shapeuuid("11805d14-8dc0-4372-b08d-e1c70392cba8"), 1),
    #     make_container_item(itemid_from_shapeuuid("c8ca8731-3af2-4554-9019-6b941affcb16"), 1),
    #     * [make_container_item(nothing, 0)] * 27
    # ])
    # sys.stdout.buffer.write(output)
    # sys.stdout.buffer.flush()

    # sys.stderr.write(bytes.fromhex("04000100000006000affff713e220b49f05eafc24a4f239c3d95dfffffffff003200000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff000000000000000000000000000000000000ffffffff00000000").hex(" ") + "\n")
    # sys.stderr.write(output.hex(" ") + "\n")
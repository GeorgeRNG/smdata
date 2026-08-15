import sqlite3
import sys
from sm import *
import json
import random
import math

def main():
    config = {}
    with open("config.json") as file:
        config = json.loads(file.read())
    game_dir = config["game_dir"]
    data_source = config["data_source"]

    shapesets = ShapeSets(game_dir, data_source)

    path = sys.argv[1] if len(sys.argv) >= 2 else input("Enter save path: ")
    db = sqlite3.connect(path)

    # raise_deadbags(db, shapesets, DEADBAG_RAISE_100)
    freeze_loose_parts(db, shapesets)


def freeze_loose_parts(db: sqlite3.Connection, shapesets: ShapeSets):
    targets = [as_byteid(shapesets.shape_from_name(name)["uuid"]) for name in [
        "obj_interactive_robotbasshead","obj_interactive_robotdrumhead","obj_interactive_robotdrumhead","obj_interactive_robotbliphead01",
        "obj_harvest_stone","obj_harvest_wood","obj_harvest_wood2","obj_harvest_metal","obj_harvest_metal2",
    ]]

    results = []
    for (data,) in db.execute("SELECT data FROM ChildShape GROUP BY bodyId HAVING COUNT(*) = 1"):
        cs = ChildShape(data)
        if cs.header.shape() in targets:
            results.append(cs.header.body_id())

    locked = 0
    for (rowid, data) in db.execute("SELECT rowid, data FROM RigidBody"):
        rb = RigidBody(data)
        if rb.header.id() not in results:
            continue
        if rb.header.header() == RigidBodyMobile.header:
            rb.header.header(RigidBodyStatic.header)
            rb.data = RigidBodyStatic(b"\x00\xFF\xFF\xFF\xFF")
            (x,y,z,w) = [rb.header.rotation_x(),rb.header.rotation_y(),rb.header.rotation_z(),rb.header.rotation_w()]
            rb.header.rotation_x(w)
            rb.header.rotation_y(z)
            rb.header.rotation_z(y)
            rb.header.rotation_w(x)
            locked += 1

        db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
    db.commit()
    print(f"locked {locked} bodies.")

def print_unit_pos(db:sqlite3.Connection):
    for (rowid,data) in db.execute("SELECT rowid,data FROM unit"):
        u = Unit(data)
        print(u.pos_x.get(), u.pos_y.get(), u.pos_z.get(), u.rotation.get())
        # db.execute("UPDATE Unit SET data=? WHERE rowid=?",[u.make(),rowid])
    # if input() == "w":
        # db.commit()

def replace_item(db: sqlite3.Connection, input: ID, input_count: int, output: ID, output_count: int):
    for (rowid,data) in db.execute("SELECT rowid,data FROM Container").fetchall():
        c = Container(data)
        for item in c.items:
            if item.id.get() == as_byteid(input) and (input_count <= 0 or item.count.get() == input_count):
                item.id.set(as_byteid(output))
                item.count.set(output_count)
                print("replaced")
        db.execute("UPDATE Container SET data=? WHERE rowid=?",[c.make(),rowid])
    db.commit()

def inv_size(db: sqlite3.Connection, size: int):
    for (rowid,data) in db.execute("SELECT rowid,data FROM Container").fetchall():
        c = Container(data)
        if size > c.header.size.get():
            c.header.size.set(size)
            c.items.extend([Item(b"\x00" * 16 + b"\xff\xff\xff\xff" + b"\x00\x00")] * (size - len(c.items)))
            db.execute("UPDATE Container SET data=? WHERE rowid=?",[c.make(),rowid])
    db.commit()

def stack(db: sqlite3.Connection, shapesets: ShapeSets, multiplier: int):
    q = db.execute("SELECT rowid,data FROM Container")
    for (rowid,data) in q.fetchall():
        container = Container(data)
        for item in container.items:
            shape = shapesets.shape(item.id.get())
            if shape:
                item.count.set(max(item.count.get(), multiplier))
                if "stackSize" in shape:
                    item.count.set(min(max(10,item.count.get(),shape["stackSize"] * multiplier),0xffff))
                # item.count.set(0xffff)
        db.execute("UPDATE Container SET data=? WHERE rowid=?",[container.make(),rowid])
    db.commit()

def encrypt_everything(db: sqlite3.Connection):
    for (rowid, data) in db.execute("SELECT rowid, data FROM RigidBody").fetchall():
        rb = RigidBody(data)
        rb.data.set_restriction(RigidBodyData.RESTRICT_BUILDABLE,True)
        rb.data.set_restriction(RigidBodyData.RESTRICT_ERASABLE,True)
        rb.data.set_restriction(RigidBodyData.RESTRICT_LIFTABLE,True)

        db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
    db.commit()

DEADBAG_RAISE_10 = 0
DEADBAG_RAISE_50 = 1
DEADBAG_RAISE_100 = 2
DEADBAG_SHIP = 2
DEADBAG_NEWEST = 3
def raise_deadbags(db: sqlite3.Connection, shapesets: ShapeSets, method: int):
    bag = uuid_to_byteid(shapesets.shape_from_name("obj_survivalobject_kobag")["uuid"])

    x = -2354.0
    y = -2622.5
    z = 10

    if method == DEADBAG_NEWEST:
        (data,) = db.execute("SELECT data FROM RigidBody ORDER BY id DESC LIMIT 1").fetchone()
        rb = RigidBody(data)
        x = rb.header.x()
        y = rb.header.y()
        z = rb.header.z() + 2.0
    
    for (bodyId,data) in db.execute("SELECT bodyId, data FROM ChildShape").fetchall():
        cs = ChildShape(data)
        if cs.header.shape() == bag:
            (rowid, data) = db.execute("SELECT rowid, data FROM RigidBody WHERE id=?",[int(bodyId)]).fetchone()
            rb = RigidBody(data)
            (oldx, oldy, oldz) = (rb.header.x(), rb.header.y(), rb.header.z())
            if method in (DEADBAG_RAISE_10, DEADBAG_RAISE_50, DEADBAG_RAISE_100):
                rb.header.z(rb.header.z() + [10,50,100][method])
            elif method == DEADBAG_SHIP or method == DEADBAG_NEWEST:
                rb.header.x(x)
                rb.header.y(y)
                rb.header.z(z)
                z+=2
            else:
                print("raise_deadbags: invalid method")
                exit(2)
                return
            
            print(f"found bag rowid {rowid}\nold {data.hex()}\nnew {rb.make().hex()}\nmoved {math.sqrt((oldx - rb.header.x()) ** 2 + (oldy - rb.header.y()) ** 2 + (oldz - rb.header.z()) ** 2)}")
            db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
    db.commit()

def move_everything_up(db):
    bodies = db.execute("SELECT rowid, data from RigidBody").fetchall()
    
    for (rowid, data) in bodies:
        rb = RigidBody(data)

        rb.header.z(rb.header.z() + 30)

        db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
        db.commit()

def random_colors(db):
    q = db.execute("SELECT rowid, data FROM ChildShape")
    for row in q.fetchall():
        rowid = row[0]
        data = row[1]
        cs = ChildShape(data)
        cs.color = random.randbytes(3)
        # print(cs._a)
        if isinstance(cs.data, ChildShapeBlock): cs.data.flags |= ChildShapeBlock.FLAG_BURNING
        db.execute("UPDATE ChildShape SET data=? WHERE rowid=?",[cs.make(),rowid])
    db.commit()

def read_all_containers(db: sqlite3.Connection, shapesets: ShapeSets):
    q = db.execute("SELECT data FROM Container")
    for (data,) in q.fetchall():
        container = Container(data)
        for item in container.items:
            shape = shapesets.shape(item.id.value)
            if shape is not None:
                print(shape["name"])
            else:
                print(item.id.value.hex(), item.tool.get())

def move_bag_items_into_host_inventory(db: sqlite3.Connection, shapesets: ShapeSets, clues: list[str]):
    rescues: dict[bytes,Item] = {}
    no_stack_tools = 0
    found_bag = False

    for (rowid,data,) in db.execute("SELECT rowid,data FROM Container"):
        container = Container(data)

        found_clues = set()
        for item in container.items:
            shape = shapesets.shape(item.id.get())
            if shape is not None:
                if shape["name"] in clues:
                    found_clues.add(shape["name"])
        bag = set(clues) == found_clues
        if bag or container.header.id.get() == 1:
            print(f"CONTAINER {container.header.id.get()} SIZE {container.header.size.get()}")
            for item in container.items:
                if item.id.get() == b"\x00" * 16:
                    continue
                tool = item.tool.get() != 0xFFFFFFFF
                if tool:
                    no_stack_tools += 1
                rescueid = item.id.get() + struct.pack("2I",item.tool.get(),(no_stack_tools if tool else 0))
                if rescueid in rescues:
                    addupitem = rescues[rescueid]
                    addupitem.count.set(addupitem.count.get() + item.count.get())
                else:
                    rescues[rescueid] = Item(item.make())
                shape = shapesets.shape(item.id.get())
                if shape is not None and shape["name"]:
                    print(shape["name"], item.count.get(), item.tool.get(), tool)
                else:
                    print(item.id.get(), item.tool.get(), tool)
        if bag:
            found_bag = True
            container.items = []
            container.header.size = 0
            db.execute("UPDATE Container SET data=? WHERE rowid=?",[container.make(),rowid])
            pass # Empty the bag

    if not found_bag:
        print("Did not find bag")
        exit(2)
        return
    
    (rowid,data) = db.execute("SELECT rowid,data FROM Container WHERE id=1").fetchone()
    container = Container(data)
    rescues = list(rescues.values())
    if len(rescues) > container.header.size.get():
        print("sorry, too many items to fit into your inventory")
        exit(1)
        return
    print("NEW INVENTORY:")
    for (i,item) in enumerate(container.items):
        if i < len(rescues):
            rescue = rescues[i]
            item.id.set(rescue.id.get())
            item.tool.set(rescue.tool.get())
            item.count.set(rescue.count.get())
            shape = shapesets.shape(item.id.value)
            if shape is not None and shape["name"]:
                print(shape["name"], item.count.get())
            else:
                print(item.id.get(), item.tool.get())
        else:
            item.id.set(b"\x00" * 16)
            item.tool.set(0xFF_FF_FF_FF)
            item.count.set(0)
    db.execute("UPDATE Container SET data=? WHERE rowid=?",[container.make(),rowid])
    db.commit()


def read_userpos(db):
    q = db.execute("SELECT uid,key,data FROM GenericData where worldId = 65534 and flags = 3")
    myuid,mykey,data = q.fetchone()
    print(data.hex())
    (uid,a,key,b,c,x,y,z,d,yaw,pitch,e) = parse_genericdata(data)



    db.execute("UPDATE GenericData SET data=? WHERE worldId = 65534 and flags = 3 and uid=?",[make_genericdata(uid,a,key,bytes.fromhex("0300000038f7000001"),c,x+100.0,y,z,d,yaw,pitch,e),myuid])
    db.commit()


if __name__ == "__main__": main()

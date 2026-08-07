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

    # encrypt_everything(db)
    # inv_size(db, 60)
    stack(db,shapesets,1)
    # read_all_containers(db,shapesets)
    # raise_deadbags(db, shapesets, DEADBAG_NEWEST)
    replace_item(db, "8e61a423-5aa6-4dd3-ac57-ecac313f82f5",1,"5530e6a0-4748-4926-b134-50ca9ecb9dcf",0xffff)

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
        if True:
            rb.data.restrictions = 0xff

            db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
    db.commit()

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
        x = rb.x
        y = rb.y
        z = rb.z + 2
    
    for (bodyId,data) in db.execute("SELECT bodyId, data FROM ChildShape").fetchall():
        cs = ChildShape(data)
        if cs.shape == bag:
            (rowid, data) = db.execute("SELECT rowid, data FROM RigidBody WHERE id=?",[int(bodyId)]).fetchone()
            rb = RigidBody(data)
            (oldx, oldy, oldz) = (rb.x, rb.y, rb.z)
            if method == DEADBAG_RAISE_50 or method == DEADBAG_RAISE_100:
                rb.z += 50 if method == DEADBAG_RAISE_50 else 100
            elif method == DEADBAG_SHIP or method == DEADBAG_NEWEST:
                rb.x = x
                rb.y = y
                rb.z = z
                z+=2
            else:
                print("raise_deadbags: invalid method")
                exit(2)
                return
            
            print(f"found bag rowid {rowid}\nold {data.hex()}\nnew {rb.make().hex()}\nmoved {math.sqrt((oldx - rb.x) ** 2 + (oldy - rb.y) ** 2 + (oldz - rb.z) ** 2)}")
            db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
    db.commit()

def move_everything_up(db):
    bodies = db.execute("SELECT rowid, data from RigidBody").fetchall()
    
    for (rowid, bytess) in bodies:
        print(bytess.hex())
        rb = RigidBody(bytess)

        rb.z += 30

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
                print(item.id.value.hex())

def read_userpos(db):
    q = db.execute("SELECT uid,key,data FROM GenericData where worldId = 65534 and flags = 3")
    myuid,mykey,data = q.fetchone()
    print(data.hex())
    (uid,a,key,b,c,x,y,z,d,yaw,pitch,e) = parse_genericdata(data)



    db.execute("UPDATE GenericData SET data=? WHERE worldId = 65534 and flags = 3 and uid=?",[make_genericdata(uid,a,key,bytes.fromhex("0300000038f7000001"),c,x+100.0,y,z,d,yaw,pitch,e),myuid])
    db.commit()


if __name__ == "__main__": main()

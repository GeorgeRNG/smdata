import sqlite3
import sys
from sm import *
from database import *
import json
import random

def main():
    config = {}
    with open("config.json") as file:
        config = json.loads(file.read())
    game_dir = config["game_dir"]
    data_source = config["data_source"]

    shapesets = load_shapesets(game_dir, data_source)

    path = sys.argv[1] if len(sys.argv) >= 2 else input("Enter save path: ")
    db = sqlite3.connect(path)

    raise_deadbags(db, shapesets)

def raise_deadbags(db: sqlite3.Connection, shapesets):
    bag = itemid_from_shapeuuid(shape_from_shapesets_via_name(shapesets, "obj_survivalobject_kobag")["uuid"])

    for (bodyId,data) in db.execute("SELECT bodyId, data FROM ChildShape").fetchall():
        cs = ChildShape(data)
        if cs.shape == bag:
            print("bag!!")
            (rowid, data) = db.execute("SELECT rowid, data FROM RigidBody WHERE id=?",[int(bodyId)]).fetchone()
            rb = RigidBody(data)
            rb.z += 50
            db.execute("UPDATE RigidBody SET data=? WHERE rowid=?",[rb.make(),rowid])
            db.commit()
            return

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

def read_all_containers(db,shapesets):
    q = db.execute("SELECT data FROM Container")
    for container in q.fetchall():
        container = Container(container[0])
        for item in container.items:
            item = shape_from_shapesets_via_item(shapesets, item[0])
            if item is not None:
                print(item["name"])

def read_userpos(db):
    q = db.execute("SELECT uid,key,data FROM GenericData where worldId = 65534 and flags = 3")
    myuid,mykey,data = q.fetchone()
    print(data.hex())
    (uid,a,key,b,c,x,y,z,d,yaw,pitch,e) = parse_genericdata(data)



    db.execute("UPDATE GenericData SET data=? WHERE worldId = 65534 and flags = 3 and uid=?",[make_genericdata(uid,a,key,bytes.fromhex("0300000038f7000001"),c,x+100.0,y,z,d,yaw,pitch,e),myuid])
    db.commit()


if __name__ == "__main__": main()

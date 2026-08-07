"""
files.py
For parsing all the scrap mechanic game files.
"""

from pathlib import Path
from uuid import UUID
import typing
import json
from files import *

class Paths:
    def __init__(self, game_dir):
        self.data = Path(game_dir,"Data")
        self.survival = Path(game_dir,"Survival")
        self.challenge = Path(game_dir,"ChallengeData")

    def resolve(self, path: str) -> Path:
        return Path(path
                        .replace("$GAME_DATA",str(self.data))
                        .replace("$SURVIVAL_DATA",str(self.survival))
                        .replace("$CHALLENGE_DATA",str(self.challenge))
                    )

type ID = typing.Union[UUID, bytes]
def uuid_to_byteid(uuid: UUID) -> bytes:
    if isinstance(uuid, str): uuid = UUID(uuid)
    return uuid.bytes[::-1]
def byteid_to_uuid(data: bytes) -> UUID:
    return UUID(int=int.from_bytes(data, 'little'))

def as_byteid(id: ID) -> bytes:
    return id if isinstance(id, bytes) else uuid_to_byteid(id)
def as_uuid(id: ID) -> UUID:
    return id if isinstance(id, UUID) else byteid_to_uuid(id)

type Shape = typing.Any
class ShapeSets:
    def __init__(self, game_dir: str, data_source: str):
        paths = Paths(game_dir)
        path = Path(game_dir,data_source,"Objects","Database","shapesets.json")
        shapesetlist = []
        with open(path,"r") as shapesets:
            try:
                shapesetlist = json.loads(shapesets.read())["shapeSetList"]
            except:
                print(f"shapesets at {path} is not valid json or missing shapeSetList")
                exit(1)
        self.blocks: list[Shape] = []
        self.parts: list[Shape] = []
        self.wedges: list[Shape] = []
        self.items: list[Shape] = []
        for shapeset in shapesetlist:
            with open(paths.resolve(shapeset),"r") as shapesetFile:
                data = json.loads(shapesetFile.read())
                if "partList" in data:
                    self.parts.extend(data["partList"])
                    self.items.extend(data["partList"])
                if "blockList" in data:
                    self.blocks.extend(data["blockList"])
                    self.items.extend(data["blockList"])
                if "wedgeList" in data:
                    self.wedges.extend(data["wedgeList"])
                    self.items.extend(data["wedgeList"])
                if ("partList" not in data) and ("blockList" not in data) and ("wedgeList" not in data):
                    print(f"shapesetfile at {shapeset} does not have partList or blockList")

    def shape(self, id: ID) -> Shape:
        for shape in self.items:
            if UUID(shape["uuid"]) == as_uuid(id):
                return shape

    def shape_from_name(self, name: str) -> Shape:
        for shape in self.items:
            if "name" in shape and shape["name"] == name:
                return shape
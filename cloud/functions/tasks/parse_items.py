from dataclasses import dataclass
from typing import List

@dataclass
class Asset:
    name: str
    public_url: str
    id : str

    def serialize(self):
        return {"name": self.name, "public_url": self.public_url, 'id': self.id}


@dataclass
class Subitem:
    id: int
    name: str  # people__1 column
    assets: List[Asset]

    def serialize(self):
        return {
            'id': self.id,
        'name': self.name,
        'assets': [x.serialize() for x in self.assets],
        }


@dataclass
class Item:
    name: str  # text7__1 (client_name)
    id: int
    subitems: List[Subitem]

    @classmethod
    def from_monday_data(
        cls, data: dict
    ) -> "Item":  # Extract client name from column values
        columns = {col["column"]["id"]: col for col in data.get("column_values", [])}
        client_name = columns.get("text7__1")
        item_id = int(data.get("id"))

        # Create subitems
        subitems = []
        for subitem_data in data.get("subitems", []):
            assets = [
                Asset(name=asset["name"], public_url=asset["public_url"], id = asset['id'])
                for asset in subitem_data.get("assets", [])
            ]

            subitem = Subitem(
                id=int(subitem_data["id"]),
                name=subitem_data["name"],
                assets=assets,
            )
            subitems.append(subitem)

        return cls(
            name=client_name.get("text"),
            id=item_id,
            subitems=subitems,
        )

    def serialize(self):
        return  {
            'name': self.name,
        'id': self.id,
        'subitems': [x.serialize() for x in self.subitems],
        }


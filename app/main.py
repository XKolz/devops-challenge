from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="DevOps Challenge API", version="1.0.0")

_items: dict = {}


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ItemResponse(Item):
    id: str


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/items", response_model=list[ItemResponse])
def list_items():
    return list(_items.values())


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: str):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    return _items[item_id]


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: Item):
    item_id = str(uuid.uuid4())
    record = {"id": item_id, **item.model_dump()}
    _items[item_id] = record
    return record

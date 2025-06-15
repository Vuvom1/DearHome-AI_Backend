import uuid
from fastapi import APIRouter, Body, Depends
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from src.services.virtual_room_service import VirtualRoomService

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Position(BaseModel):
    x: float
    y: float
    z: float

class Window(BaseModel):
    position: Position
    width: float
    height: float

class Door(BaseModel):
    position: Position
    width: float
    height: float

class Dimensions(BaseModel):
    width: float
    length: float
    height: float

class Room(BaseModel):
    room_type: str
    width: float
    length: float
    height: float
    wall_color: str
    floor_type: str
    windows: List[Window]
    doors: List[Door]

class Furniture(BaseModel):
    id: uuid.UUID

class Options(BaseModel):
    number_of_designs: int
    style_preference: str
    priority: Literal["functionality", "aesthetics", "balance"]

class VirtualLayoutCreate(BaseModel):
    room: Room
    furniture: List[Furniture]
    prompt: str
    options: Options

class VariantDetails(BaseModel):
    ids: List[uuid.UUID] = Field(..., description="List of variant IDs to fetch details for")

virtualoom_service = VirtualRoomService()

@router.post("/generate_virtual_layout")
async def generate_virtual_layout(layout_request: VirtualLayoutCreate = Body(...)):
    layout_response = await virtualoom_service.get_virtual_room_layout(
        room_info=layout_request.room.dict(),
        furniture_ids=[item.id for item in layout_request.furniture],
        prompt=layout_request.prompt,
        options=layout_request.options.dict()
    )
    
    return layout_response


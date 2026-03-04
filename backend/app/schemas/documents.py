from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    description: Optional[str] = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    cloudinary_public_id: str
    cloudinary_url: str
    cloudinary_secure_url: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentLinkCreate(BaseModel):
    entity_type: str
    entity_id: int


class DocumentLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    entity_type: str
    entity_id: int
    created_at: datetime

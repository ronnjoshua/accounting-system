from typing import List, Optional
import base64
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.core.config import settings
from app.models.user import User
from app.models.document import Document, DocumentLink
from app.schemas.documents import DocumentResponse, DocumentLinkCreate, DocumentLinkResponse

router = APIRouter()

# For now, we'll use a simple file storage. In production, use Cloudinary
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../../uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[int] = Form(None),
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Upload a document"""
    # Validate file size (max 10MB)
    content = await file.read()
    file_size = len(content)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_id = str(uuid.uuid4())
    stored_filename = f"{unique_id}{ext}"

    # Save file locally (in production, upload to Cloudinary)
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        filename=stored_filename,
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        cloudinary_public_id=unique_id,  # Using UUID as ID for local storage
        cloudinary_url=f"/uploads/{stored_filename}",
        cloudinary_secure_url=f"/uploads/{stored_filename}",
        description=description,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(document)
    db.flush()

    # Create link if entity provided
    if entity_type and entity_id:
        link = DocumentLink(
            document_id=document.id,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id
        )
        db.add(link)

    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """List documents, optionally filtered by entity"""
    if entity_type and entity_id:
        # Get documents linked to specific entity
        query = (
            select(Document)
            .join(DocumentLink, Document.id == DocumentLink.document_id)
            .where(and_(
                DocumentLink.entity_type == entity_type,
                DocumentLink.entity_id == entity_id
            ))
        )
    else:
        query = select(Document)

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete physical file
    file_path = os.path.join(UPLOAD_DIR, document.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete links
    db.execute(select(DocumentLink).where(DocumentLink.document_id == document_id))
    links = db.execute(select(DocumentLink).where(DocumentLink.document_id == document_id)).scalars().all()
    for link in links:
        db.delete(link)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/link", response_model=DocumentLinkResponse)
def link_document(
    document_id: int,
    data: DocumentLinkCreate,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Link a document to an entity"""
    document = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if link already exists
    existing = db.execute(
        select(DocumentLink).where(and_(
            DocumentLink.document_id == document_id,
            DocumentLink.entity_type == data.entity_type,
            DocumentLink.entity_id == data.entity_id
        ))
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Document is already linked to this entity")

    link = DocumentLink(
        document_id=document_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/{document_id}/link/{link_id}")
def unlink_document(
    document_id: int,
    link_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Remove a document link"""
    link = db.execute(
        select(DocumentLink).where(and_(
            DocumentLink.id == link_id,
            DocumentLink.document_id == document_id
        ))
    ).scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=404, detail="Document link not found")

    db.delete(link)
    db.commit()

    return {"message": "Document unlinked successfully"}


@router.get("/{document_id}/links", response_model=List[DocumentLinkResponse])
def get_document_links(
    document_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get all links for a document"""
    document = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = db.execute(select(DocumentLink).where(DocumentLink.document_id == document_id))
    return result.scalars().all()

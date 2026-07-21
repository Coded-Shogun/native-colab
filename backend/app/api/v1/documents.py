"""
Documents API
Endpoints for document upload, download, and version management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
import io

from app.db.session import get_db
from app.db.models import (
    User,
    WorkspaceMember,
    Folder,
    Document,
    DocumentVersion,
)
from app.core.organization_context import get_organization_context, OrganizationContext

from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUpdate,
    DocumentVersionResponse,
    DocumentVersionListResponse,
    DocumentVersionCreate,
    FileUploadResponse,
)
from app.core.deps import get_current_user
from app.services import storage_service

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(workspace_id: int, user: User, db: AsyncSession) -> bool:
    """Check if user has access to workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_document_access(document_id: int, user: User, db: AsyncSession) -> Optional[Document]:
    """Check if user has access to document via workspace membership"""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document or document.is_deleted:
        return None

    # Check workspace access
    has_access = await check_workspace_access(document.workspace_id, user, db)
    if not has_access:
        return None

    return document


async def build_document_response(document: Document, db: AsyncSession) -> DocumentResponse:
    """Build document response with nested information"""
    # Load relationships
    stmt = select(Document).options(
        selectinload(Document.created_by),
        selectinload(Document.folder)
    ).where(Document.id == document.id)
    result = await db.execute(stmt)
    document = result.scalar_one()

    # Count versions
    version_stmt = select(func.count(DocumentVersion.id)).where(DocumentVersion.document_id == document.id)
    version_result = await db.execute(version_stmt)
    version_count = version_result.scalar() or 0

    # Count comments (will add later)
    comment_count = 0

    return DocumentResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        folder_id=document.folder_id,
        created_by_id=document.created_by_id,
        project_id=document.project_id,
        task_id=document.task_id,
        name=document.name,
        description=document.description,
        file_type=document.file_type,
        mime_type=document.mime_type,
        file_size=document.file_size,
        current_version=document.current_version,
        storage_path=document.storage_path,
        tags=document.tags,
        is_starred=document.is_starred,
        is_deleted=document.is_deleted,
        deleted_at=document.deleted_at,
        created_at=document.created_at,
        updated_at=document.updated_at,
        creator_name=document.created_by.full_name if document.created_by else None,
        creator_email=document.created_by.email if document.created_by else None,
        folder_name=document.folder.name if document.folder else None,
        version_count=version_count,
        comment_count=comment_count,
    )


# ============================================
# Document Upload/Download Endpoints
# ============================================
@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: int = Query(..., gt=0),
    folder_id: Optional[int] = Query(None, gt=0),
    name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None, gt=0),
    task_id: Optional[int] = Query(None, gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new document.
    File is stored in S3/MinIO and metadata is saved in database.
    """
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Validate file type
    if not storage_service.validate_file_type(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(storage_service.settings.allowed_file_types_list)}"
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size
    if not storage_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {storage_service.settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
        )

    # Generate storage path
    storage_path = storage_service.generate_storage_path(workspace_id, file.filename)

    # Upload to storage
    upload_success = await storage_service.upload_file(
        file_content,
        storage_path,
        file.content_type or "application/octet-stream"
    )

    if not upload_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )

    # Create document record
    file_type = storage_service.get_file_type_from_extension(file.filename)
    document_name = name or file.filename

    new_document = Document(
        workspace_id=workspace_id,
        folder_id=folder_id,
        created_by_id=current_user.id,
        project_id=project_id,
        task_id=task_id,
        name=document_name,
        description=description,
        file_type=file_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        current_version=1,
        storage_path=storage_path,
    )

    db.add(new_document)
    await db.flush()

    # Create initial version
    initial_version = DocumentVersion(
        document_id=new_document.id,
        created_by_id=current_user.id,
        version_number=1,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        change_description="Initial upload",
        is_current=True,
    )

    db.add(initial_version)
    await db.commit()

    return FileUploadResponse(
        document_id=new_document.id,
        name=document_name,
        file_type=file_type,
        file_size=file_size,
        storage_path=storage_path,
        message="File uploaded successfully"
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    version: Optional[int] = Query(None, gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a document or specific version.
    If version is not specified, downloads the current version.
    """
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    # Determine which version to download
    if version:
        # Download specific version
        version_stmt = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        )
        version_result = await db.execute(version_stmt)
        doc_version = version_result.scalar_one_or_none()

        if not doc_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )

        storage_path = doc_version.storage_path
        mime_type = doc_version.mime_type
    else:
        # Download current version
        storage_path = document.storage_path
        mime_type = document.mime_type

    # Download from storage
    file_data = await storage_service.download_file(storage_path)

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file from storage"
        )

    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.name}"'
        }
    )


# ============================================
# Document CRUD Endpoints
# ============================================
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: int = Query(..., gt=0),
    folder_id: Optional[int] = Query(None, gt=0),
    file_type: Optional[str] = Query(None),
    starred_only: bool = Query(False),
    include_deleted: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents in a workspace or folder.
    User must be a workspace member.
    """
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Build query
    conditions = [Document.workspace_id == workspace_id]

    if folder_id:
        conditions.append(Document.folder_id == folder_id)

    if file_type:
        conditions.append(Document.file_type == file_type)

    if starred_only:
        conditions.append(Document.is_starred == True)

    if not include_deleted:
        conditions.append(Document.is_deleted == False)

    stmt = select(Document).where(and_(*conditions))
    stmt = stmt.order_by(desc(Document.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    documents = result.scalars().all()

    # Build responses
    document_responses = []
    for document in documents:
        document_responses.append(await build_document_response(document, db))

    return DocumentListResponse(
        documents=document_responses,
        total=total
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document details"""
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    return await build_document_response(document, db)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata"""
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    # Update fields
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    await db.commit()
    await db.refresh(document)

    return await build_document_response(document, db)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document (soft delete by default)"""
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    if permanent:
        # Delete from storage
        await storage_service.delete_file(document.storage_path)

        # Delete all versions from storage
        versions_stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id)
        versions_result = await db.execute(versions_stmt)
        versions = versions_result.scalars().all()

        for version in versions:
            if version.storage_path != document.storage_path:
                await storage_service.delete_file(version.storage_path)

        # Hard delete from database
        await db.delete(document)
    else:
        # Soft delete
        from datetime import datetime
        document.is_deleted = True
        document.deleted_at = datetime.utcnow()

    await db.commit()


# ============================================
# Version Management Endpoints
# ============================================
@router.post("/{document_id}/versions", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_document_version(
    document_id: int,
    file: UploadFile = File(...),
    version_data: DocumentVersionCreate = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new version of a document"""
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    # Read and validate file
    file_content = await file.read()
    file_size = len(file_content)

    if not storage_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size"
        )

    # Generate storage path for new version
    new_version_number = document.current_version + 1
    storage_path = storage_service.generate_storage_path(
        document.workspace_id,
        f"v{new_version_number}_{file.filename}"
    )

    # Upload to storage
    upload_success = await storage_service.upload_file(
        file_content,
        storage_path,
        file.content_type or document.mime_type
    )

    if not upload_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )

    # Mark all existing versions as not current
    update_stmt = select(DocumentVersion).where(
        DocumentVersion.document_id == document_id,
        DocumentVersion.is_current == True
    )
    update_result = await db.execute(update_stmt)
    current_versions = update_result.scalars().all()
    for ver in current_versions:
        ver.is_current = False

    # Create new version record
    new_version = DocumentVersion(
        document_id=document_id,
        created_by_id=current_user.id,
        version_number=new_version_number,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=file.content_type or document.mime_type,
        change_description=version_data.change_description,
        is_current=True,
    )

    db.add(new_version)

    # Update document
    document.current_version = new_version_number
    document.storage_path = storage_path
    document.file_size = file_size

    await db.commit()

    return FileUploadResponse(
        document_id=document_id,
        name=document.name,
        file_type=document.file_type,
        file_size=file_size,
        storage_path=storage_path,
        message=f"Version {new_version_number} created successfully"
    )


@router.get("/{document_id}/versions", response_model=DocumentVersionListResponse)
async def list_document_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all versions of a document"""
    document = await check_document_access(document_id, current_user, db)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have access"
        )

    # Get all versions
    stmt = select(DocumentVersion).options(
        selectinload(DocumentVersion.created_by)
    ).where(
        DocumentVersion.document_id == document_id
    ).order_by(desc(DocumentVersion.version_number))

    result = await db.execute(stmt)
    versions = result.scalars().all()

    version_responses = []
    for version in versions:
        version_responses.append(DocumentVersionResponse(
            id=version.id,
            document_id=version.document_id,
            created_by_id=version.created_by_id,
            version_number=version.version_number,
            storage_path=version.storage_path,
            file_size=version.file_size,
            mime_type=version.mime_type,
            change_description=version.change_description,
            is_current=version.is_current,
            created_at=version.created_at,
            creator_name=version.created_by.full_name if version.created_by else None,
            creator_email=version.created_by.email if version.created_by else None,
        ))

    return DocumentVersionListResponse(
        versions=version_responses,
        total=len(version_responses)
    )

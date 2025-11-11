"""
Document Schemas
Pydantic schemas for document collaboration features
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.db.models.document import DocumentSharePermission


# ============================================
# Folder Schemas
# ============================================
class FolderBase(BaseModel):
    """Base folder schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class FolderCreate(FolderBase):
    """Schema for creating a folder"""
    workspace_id: int = Field(..., gt=0)
    parent_folder_id: Optional[int] = Field(None, gt=0)


class FolderUpdate(BaseModel):
    """Schema for updating a folder"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    parent_folder_id: Optional[int] = Field(None, gt=0)


class FolderResponse(BaseModel):
    """Schema for folder response"""
    id: int
    workspace_id: int
    parent_folder_id: Optional[int] = None
    created_by_id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    subfolder_count: int = 0
    document_count: int = 0

    model_config = {"from_attributes": True}


class FolderListResponse(BaseModel):
    """Schema for folder list response"""
    folders: List[FolderResponse]
    total: int


# ============================================
# Document Schemas
# ============================================
class DocumentBase(BaseModel):
    """Base document schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[str] = Field(None, max_length=500)


class DocumentCreate(DocumentBase):
    """Schema for creating a document (used after file upload)"""
    workspace_id: int = Field(..., gt=0)
    folder_id: Optional[int] = Field(None, gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[str] = Field(None, max_length=500)
    folder_id: Optional[int] = Field(None, gt=0)
    is_starred: Optional[bool] = None


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    workspace_id: int
    folder_id: Optional[int] = None
    created_by_id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None

    # File metadata
    name: str
    description: Optional[str] = None
    file_type: str
    mime_type: str
    file_size: int

    # Version info
    current_version: int
    storage_path: str

    # Metadata
    tags: Optional[str] = None
    is_starred: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    folder_name: Optional[str] = None
    version_count: int = 0
    comment_count: int = 0

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for document list response"""
    documents: List[DocumentResponse]
    total: int


# ============================================
# Document Version Schemas
# ============================================
class DocumentVersionResponse(BaseModel):
    """Schema for document version response"""
    id: int
    document_id: int
    created_by_id: int
    version_number: int
    storage_path: str
    file_size: int
    mime_type: str
    change_description: Optional[str] = None
    is_current: bool
    created_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentVersionListResponse(BaseModel):
    """Schema for document version list response"""
    versions: List[DocumentVersionResponse]
    total: int


class DocumentVersionCreate(BaseModel):
    """Schema for creating a new document version"""
    change_description: Optional[str] = Field(None, max_length=500)


# ============================================
# Document Share Schemas
# ============================================
class DocumentShareBase(BaseModel):
    """Base document share schema"""
    permission: DocumentSharePermission = Field(default=DocumentSharePermission.VIEW)
    message: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = None


class DocumentShareCreate(DocumentShareBase):
    """Schema for creating a document share"""
    shared_with_user_id: Optional[int] = Field(None, gt=0)
    shared_with_team_id: Optional[int] = Field(None, gt=0)


class DocumentShareUpdate(BaseModel):
    """Schema for updating a document share"""
    permission: Optional[DocumentSharePermission] = None
    expires_at: Optional[datetime] = None


class DocumentShareResponse(BaseModel):
    """Schema for document share response"""
    id: int
    document_id: int
    shared_by_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_team_id: Optional[int] = None
    permission: DocumentSharePermission
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested info
    shared_by_name: Optional[str] = None
    shared_by_email: Optional[str] = None
    shared_with_user_name: Optional[str] = None
    shared_with_user_email: Optional[str] = None
    shared_with_team_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentShareListResponse(BaseModel):
    """Schema for document share list response"""
    shares: List[DocumentShareResponse]
    total: int


# ============================================
# Document Comment Schemas
# ============================================
class DocumentCommentBase(BaseModel):
    """Base document comment schema"""
    content: str = Field(..., min_length=1, max_length=2000)


class DocumentCommentCreate(DocumentCommentBase):
    """Schema for creating a document comment"""
    parent_comment_id: Optional[int] = Field(None, gt=0)


class DocumentCommentUpdate(BaseModel):
    """Schema for updating a document comment"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    is_resolved: Optional[bool] = None


class DocumentCommentResponse(BaseModel):
    """Schema for document comment response"""
    id: int
    document_id: int
    user_id: int
    parent_comment_id: Optional[int] = None
    content: str
    is_resolved: bool
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None
    resolved_by_name: Optional[str] = None
    reply_count: int = 0

    model_config = {"from_attributes": True}


class DocumentCommentListResponse(BaseModel):
    """Schema for document comment list response"""
    comments: List[DocumentCommentResponse]
    total: int


# ============================================
# File Upload Schemas
# ============================================
class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    document_id: int
    name: str
    file_type: str
    file_size: int
    storage_path: str
    message: str


# ============================================
# Document Statistics
# ============================================
class DocumentStats(BaseModel):
    """Schema for document statistics"""
    total_documents: int
    total_folders: int
    total_file_size: int  # in bytes
    documents_by_type: dict
    recent_documents: List[DocumentResponse]

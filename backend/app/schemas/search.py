"""
Search Schemas
Pydantic schemas for comprehensive search functionality
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.search import ContentType


# ============================================
# Search Request Schemas
# ============================================
class SearchFilters(BaseModel):
    """Schema for search filters"""
    content_types: Optional[List[ContentType]] = Field(
        default=None,
        description="Filter by content types"
    )
    workspace_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filter by workspace"
    )
    project_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filter by project"
    )
    user_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filter by author/creator"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags"
    )
    is_public: Optional[bool] = Field(
        default=None,
        description="Filter by public/private"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter by start date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter by end date"
    )


class SearchRequest(BaseModel):
    """Schema for search request"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Search filters"
    )
    limit: int = Field(
        default=20,
        gt=0,
        le=100,
        description="Maximum results to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip"
    )
    sort_by: Optional[str] = Field(
        default="relevance",
        description="Sort field: relevance, date, title"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        description="Sort order: asc, desc"
    )
    highlight: bool = Field(
        default=True,
        description="Highlight search terms in results"
    )


class QuickSearchRequest(BaseModel):
    """Schema for quick autocomplete search"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Quick search query"
    )
    workspace_id: int = Field(..., gt=0)
    limit: int = Field(default=10, gt=0, le=20)


# ============================================
# Search Result Schemas
# ============================================
class SearchResultItem(BaseModel):
    """Schema for individual search result"""
    content_type: ContentType
    content_id: int
    title: str
    content: str
    highlighted_title: Optional[str] = None
    highlighted_content: Optional[str] = None

    # Context
    workspace_id: int
    workspace_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: bool

    # Timestamps
    content_created_at: datetime
    content_updated_at: datetime

    # Relevance
    relevance_score: Optional[float] = None

    # URL/Link
    url: Optional[str] = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str
    results: List[SearchResultItem]
    total: int
    limit: int
    offset: int
    filters: Optional[SearchFilters] = None

    # Search metadata
    search_duration_ms: Optional[int] = None
    has_more: bool = False

    # Suggestions
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Query suggestions"
    )


class QuickSearchResult(BaseModel):
    """Schema for quick search result"""
    content_type: ContentType
    content_id: int
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    url: Optional[str] = None


class QuickSearchResponse(BaseModel):
    """Schema for quick search response"""
    query: str
    results: List[QuickSearchResult]
    total: int


# ============================================
# Search Suggestions Schemas
# ============================================
class SearchSuggestion(BaseModel):
    """Schema for search suggestion"""
    suggestion: str
    count: int
    last_searched: datetime


class SearchSuggestionsResponse(BaseModel):
    """Schema for search suggestions response"""
    suggestions: List[SearchSuggestion]
    total: int


# ============================================
# Search History Schemas
# ============================================
class SearchHistoryResponse(BaseModel):
    """Schema for search history response"""
    id: int
    query: str
    filters: Optional[Dict[str, Any]] = None
    content_types: Optional[List[str]] = None
    results_count: int
    clicked_content_type: Optional[str] = None
    clicked_content_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchHistoryListResponse(BaseModel):
    """Schema for search history list response"""
    history: List[SearchHistoryResponse]
    total: int


# ============================================
# Saved Search Schemas
# ============================================
class SavedSearchCreate(BaseModel):
    """Schema for creating saved search"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    content_types: Optional[List[ContentType]] = None
    is_default: bool = Field(default=False)
    is_shared: bool = Field(default=False)
    notify_on_new_results: bool = Field(default=False)


class SavedSearchUpdate(BaseModel):
    """Schema for updating saved search"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    content_types: Optional[List[ContentType]] = None
    is_default: Optional[bool] = None
    is_shared: Optional[bool] = None
    notify_on_new_results: Optional[bool] = None


class SavedSearchResponse(BaseModel):
    """Schema for saved search response"""
    id: int
    user_id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    query: str
    filters: Optional[Dict[str, Any]] = None
    content_types: Optional[List[str]] = None
    is_default: bool
    is_shared: bool
    notify_on_new_results: bool
    use_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SavedSearchListResponse(BaseModel):
    """Schema for saved search list response"""
    saved_searches: List[SavedSearchResponse]
    total: int


# ============================================
# Search Statistics Schemas
# ============================================
class SearchStats(BaseModel):
    """Schema for search statistics"""
    total_searches_today: int
    total_searches_this_week: int
    total_searches_this_month: int
    most_searched_terms: List[Dict[str, Any]]
    recent_searches: List[SearchHistoryResponse]
    popular_content_types: List[Dict[str, int]]


class ContentTypeStats(BaseModel):
    """Schema for content type statistics"""
    content_type: ContentType
    total_items: int
    searchable_items: int
    last_indexed: Optional[datetime] = None


class SearchIndexStats(BaseModel):
    """Schema for search index statistics"""
    total_indexed: int
    by_content_type: List[ContentTypeStats]
    last_updated: datetime


# ============================================
# Indexing Schemas
# ============================================
class IndexItemRequest(BaseModel):
    """Schema for manually indexing an item"""
    content_type: ContentType
    content_id: int
    workspace_id: int


class IndexBulkRequest(BaseModel):
    """Schema for bulk indexing"""
    content_type: ContentType
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    force_reindex: bool = Field(default=False)


class IndexResponse(BaseModel):
    """Schema for indexing response"""
    success: bool
    indexed_count: int
    failed_count: int
    errors: Optional[List[str]] = None
    duration_ms: Optional[int] = None

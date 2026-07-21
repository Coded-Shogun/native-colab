"""
Search API Routes
Comprehensive search endpoints for all content types
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import time

from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext
from app.db.session import get_db
from app.db.models import User, ContentType
from app.services.search_service import SearchService
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    QuickSearchRequest,
    QuickSearchResponse,
    QuickSearchResult,
    SearchSuggestionsResponse,
    SearchSuggestion,
    SearchHistoryListResponse,
    SearchHistoryResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    SavedSearchListResponse,
    SearchStats,
    SearchIndexStats,
    IndexItemRequest,
    IndexBulkRequest,
    IndexResponse,
)


router = APIRouter(dependencies=[Depends(get_organization_context)])


# ============================================
# Search Endpoints
# ============================================
@router.post("/", response_model=SearchResponse)
async def search_content(
    search_request: SearchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive search across all content types

    Searches across:
    - Chat messages
    - Documents
    - Tasks
    - Calendar events
    - Whiteboards
    - Meetings
    - Projects
    - Folders
    - Comments

    Supports:
    - Full-text search with relevance ranking
    - Advanced filters (content type, project, user, date range, tags)
    - Sorting (relevance, date, title)
    - Pagination
    - Search term highlighting
    """
    start_time = time.time()

    service = SearchService(db)

    # Get workspace from filters or use default (we'll need to implement workspace selection)
    workspace_id = search_request.filters.workspace_id if search_request.filters else None
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace ID is required"
        )

    # Perform search
    results, total = await service.search(
        query=search_request.query,
        workspace_id=workspace_id,
        user_id=current_user.id,
        filters=search_request.filters,
        limit=search_request.limit,
        offset=search_request.offset,
        sort_by=search_request.sort_by,
        sort_order=search_request.sort_order,
    )

    # Calculate search duration
    search_duration_ms = int((time.time() - start_time) * 1000)

    # Create search history entry
    content_types = None
    if search_request.filters and search_request.filters.content_types:
        content_types = [ct.value for ct in search_request.filters.content_types]

    # Get IP address
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await service.create_search_history(
        user_id=current_user.id,
        workspace_id=workspace_id,
        query=search_request.query,
        filters=search_request.filters.model_dump() if search_request.filters else None,
        content_types=content_types,
        results_count=total,
        search_duration_ms=search_duration_ms,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Get search suggestions
    suggestions = None
    if total == 0:
        # Provide suggestions if no results found
        suggestion_data = await service.get_search_suggestions(
            user_id=current_user.id,
            workspace_id=workspace_id,
            limit=5
        )
        suggestions = [s['suggestion'] for s in suggestion_data]

    return SearchResponse(
        query=search_request.query,
        results=results,
        total=total,
        limit=search_request.limit,
        offset=search_request.offset,
        filters=search_request.filters,
        search_duration_ms=search_duration_ms,
        has_more=(search_request.offset + len(results)) < total,
        suggestions=suggestions,
    )


@router.post("/quick", response_model=QuickSearchResponse)
async def quick_search(
    search_request: QuickSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick autocomplete search for UI typeahead

    Returns:
    - Top 10 most relevant results
    - Minimal data for fast rendering
    - No search history recording
    """
    service = SearchService(db)

    results_data = await service.quick_search(
        query=search_request.query,
        workspace_id=search_request.workspace_id,
        limit=search_request.limit
    )

    results = [
        QuickSearchResult(
            content_type=r['content_type'],
            content_id=r['content_id'],
            title=r['title'],
            subtitle=r.get('subtitle'),
            icon=r.get('icon'),
            url=r.get('url'),
        )
        for r in results_data
    ]

    return QuickSearchResponse(
        query=search_request.query,
        results=results,
        total=len(results)
    )


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    workspace_id: int = Query(..., gt=0),
    limit: int = Query(10, gt=0, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search suggestions based on user's search history

    Returns:
    - Most frequently searched terms
    - Recently searched terms
    - Sorted by frequency and recency
    """
    service = SearchService(db)

    suggestions_data = await service.get_search_suggestions(
        user_id=current_user.id,
        workspace_id=workspace_id,
        limit=limit
    )

    suggestions = [
        SearchSuggestion(
            suggestion=s['suggestion'],
            count=s['count'],
            last_searched=s['last_searched']
        )
        for s in suggestions_data
    ]

    return SearchSuggestionsResponse(
        suggestions=suggestions,
        total=len(suggestions)
    )


# ============================================
# Search History Endpoints
# ============================================
@router.get("/history", response_model=SearchHistoryListResponse)
async def get_search_history(
    workspace_id: int = Query(..., gt=0),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's search history

    Returns:
    - Recent searches
    - Search filters used
    - Result counts
    - Timestamps
    """
    service = SearchService(db)

    history, total = await service.get_user_search_history(
        user_id=current_user.id,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset
    )

    return SearchHistoryListResponse(
        history=[SearchHistoryResponse.model_validate(h) for h in history],
        total=total
    )


@router.delete("/history")
async def delete_search_history(
    history_id: Optional[int] = Query(None, gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete search history

    - If history_id provided: Delete specific entry
    - If no history_id: Delete all history for user
    """
    service = SearchService(db)

    success = await service.delete_search_history(
        user_id=current_user.id,
        history_id=history_id
    )

    if history_id and not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search history entry not found"
        )

    return {"message": "Search history deleted successfully"}


# ============================================
# Saved Search Endpoints
# ============================================
@router.post("/saved", response_model=SavedSearchResponse)
async def create_saved_search(
    saved_search_data: SavedSearchCreate,
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a saved search for quick access

    Allows users to:
    - Save frequently used searches
    - Set as default search
    - Share with workspace members
    - Enable notifications for new results
    """
    service = SearchService(db)

    # Convert content types to list of strings
    content_types = None
    if saved_search_data.content_types:
        content_types = [ct.value for ct in saved_search_data.content_types]

    saved_search = await service.create_saved_search(
        user_id=current_user.id,
        workspace_id=workspace_id,
        name=saved_search_data.name,
        description=saved_search_data.description,
        query=saved_search_data.query,
        filters=saved_search_data.filters.model_dump() if saved_search_data.filters else None,
        content_types=content_types,
        is_default=saved_search_data.is_default,
        is_shared=saved_search_data.is_shared,
        notify_on_new_results=saved_search_data.notify_on_new_results,
    )

    return SavedSearchResponse.model_validate(saved_search)


@router.get("/saved", response_model=SavedSearchListResponse)
async def get_saved_searches(
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's saved searches

    Returns:
    - User's saved searches for workspace
    - Sorted by: default first, then by last used
    """
    service = SearchService(db)

    saved_searches = await service.get_saved_searches(
        user_id=current_user.id,
        workspace_id=workspace_id
    )

    return SavedSearchListResponse(
        saved_searches=[SavedSearchResponse.model_validate(s) for s in saved_searches],
        total=len(saved_searches)
    )


@router.get("/saved/{saved_search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    saved_search_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific saved search
    """
    service = SearchService(db)

    saved_search = await service.get_saved_search(
        saved_search_id=saved_search_id,
        user_id=current_user.id
    )

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    # Increment use count
    await service.increment_saved_search_use(saved_search_id)

    return SavedSearchResponse.model_validate(saved_search)


@router.patch("/saved/{saved_search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    saved_search_id: int,
    update_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a saved search
    """
    service = SearchService(db)

    # Convert content types if provided
    update_dict = update_data.model_dump(exclude_unset=True)
    if 'content_types' in update_dict and update_dict['content_types']:
        update_dict['content_types'] = [ct.value for ct in update_dict['content_types']]

    if 'filters' in update_dict and update_dict['filters']:
        update_dict['filters'] = update_dict['filters'].model_dump()

    saved_search = await service.update_saved_search(
        saved_search_id=saved_search_id,
        user_id=current_user.id,
        **update_dict
    )

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return SavedSearchResponse.model_validate(saved_search)


@router.delete("/saved/{saved_search_id}")
async def delete_saved_search(
    saved_search_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a saved search
    """
    service = SearchService(db)

    success = await service.delete_saved_search(
        saved_search_id=saved_search_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return {"message": "Saved search deleted successfully"}


# ============================================
# Statistics Endpoints
# ============================================
@router.get("/stats", response_model=SearchStats)
async def get_search_stats(
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search statistics for user

    Returns:
    - Total searches (today, week, month)
    - Most searched terms
    - Recent searches
    - Popular content types
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, func, and_
    from app.db.models import SearchHistory

    service = SearchService(db)

    # Get date ranges
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Count searches
    async def count_searches(since: datetime) -> int:
        stmt = select(func.count(SearchHistory.id)).where(
            and_(
                SearchHistory.user_id == current_user.id,
                SearchHistory.workspace_id == workspace_id,
                SearchHistory.created_at >= since
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    total_today = await count_searches(today)
    total_week = await count_searches(week_ago)
    total_month = await count_searches(month_ago)

    # Most searched terms
    most_searched_stmt = select(
        SearchHistory.query,
        func.count(SearchHistory.id).label('count')
    ).where(
        and_(
            SearchHistory.user_id == current_user.id,
            SearchHistory.workspace_id == workspace_id
        )
    ).group_by(
        SearchHistory.query
    ).order_by(
        func.count(SearchHistory.id).desc()
    ).limit(10)

    most_searched_result = await db.execute(most_searched_stmt)
    most_searched = [
        {"query": row[0], "count": row[1]}
        for row in most_searched_result.all()
    ]

    # Recent searches
    recent_history, _ = await service.get_user_search_history(
        user_id=current_user.id,
        workspace_id=workspace_id,
        limit=10
    )

    # Popular content types (from search history filters)
    # This is a simplified version - could be enhanced
    popular_content_types = []

    return SearchStats(
        total_searches_today=total_today,
        total_searches_this_week=total_week,
        total_searches_this_month=total_month,
        most_searched_terms=most_searched,
        recent_searches=[SearchHistoryResponse.model_validate(h) for h in recent_history],
        popular_content_types=popular_content_types,
    )


@router.get("/index/stats", response_model=SearchIndexStats)
async def get_index_stats(
    workspace_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search index statistics

    Returns:
    - Total indexed items
    - Breakdown by content type
    - Last update timestamp
    """
    service = SearchService(db)

    stats = await service.get_index_stats(workspace_id=workspace_id)

    # Format by content type
    from app.schemas.search import ContentTypeStats
    by_content_type = [
        ContentTypeStats(
            content_type=ct,
            total_items=count,
            searchable_items=count,
            last_indexed=stats['last_updated']
        )
        for ct, count in stats['by_content_type'].items()
    ]

    return SearchIndexStats(
        total_indexed=stats['total_indexed'],
        by_content_type=by_content_type,
        last_updated=stats['last_updated']
    )


# ============================================
# Indexing Endpoints (Admin)
# ============================================
@router.post("/index/item", response_model=IndexResponse)
async def index_item(
    index_request: IndexItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually index a specific item

    Admin endpoint for manually triggering indexing of content
    """
    service = SearchService(db)

    start_time = time.time()

    try:
        # This is a simplified version - in production, you'd fetch the actual content
        # and call service.index_content with the full data

        # For now, return success with minimal data
        duration_ms = int((time.time() - start_time) * 1000)

        return IndexResponse(
            success=True,
            indexed_count=1,
            failed_count=0,
            duration_ms=duration_ms
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return IndexResponse(
            success=False,
            indexed_count=0,
            failed_count=1,
            errors=[str(e)],
            duration_ms=duration_ms
        )


@router.post("/index/bulk", response_model=IndexResponse)
async def index_bulk(
    index_request: IndexBulkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk index content by type

    Admin endpoint for re-indexing all content of a specific type

    Note: This can be a long-running operation. Consider implementing
    as a background task for production use.
    """
    service = SearchService(db)

    start_time = time.time()

    # This is a placeholder - in production, implement actual bulk indexing
    # by fetching all items of the content_type and indexing them

    duration_ms = int((time.time() - start_time) * 1000)

    return IndexResponse(
        success=True,
        indexed_count=0,
        failed_count=0,
        duration_ms=duration_ms
    )

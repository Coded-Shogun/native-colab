"""
Search Service
Handles comprehensive search functionality using PostgreSQL full-text search
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, or_, and_, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    SearchIndex,
    SearchHistory,
    SavedSearch,
    ContentType,
    User,
    Workspace,
    Project,
    Message,
    Document,
    Task,
    Event,
    Whiteboard,
    Meeting,
    Folder,
    TaskComment,
)
from app.schemas.search import (
    SearchFilters,
    SearchResultItem,
    SearchHistoryResponse,
)


class SearchService:
    """Service for handling all search operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Search Operations
    # ============================================
    async def search(
        self,
        query: str,
        workspace_id: int,
        user_id: int,
        filters: Optional[SearchFilters] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "desc",
    ) -> Tuple[List[SearchResultItem], int]:
        """
        Perform full-text search across all indexed content

        Args:
            query: Search query string
            workspace_id: Workspace to search in
            user_id: User performing search
            filters: Optional filters
            limit: Maximum results to return
            offset: Number of results to skip
            sort_by: Sort field (relevance, date, title)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (results, total_count)
        """
        # Build base query with full-text search
        tsquery = func.plainto_tsquery('english', query)

        stmt = select(
            SearchIndex,
            func.ts_rank(SearchIndex.search_vector, tsquery).label('rank')
        ).where(
            and_(
                SearchIndex.workspace_id == workspace_id,
                SearchIndex.is_deleted == False,
                SearchIndex.search_vector.op('@@')(tsquery)
            )
        )

        # Apply filters
        if filters:
            if filters.content_types:
                stmt = stmt.where(SearchIndex.content_type.in_(filters.content_types))

            if filters.project_id:
                stmt = stmt.where(SearchIndex.project_id == filters.project_id)

            if filters.user_id:
                stmt = stmt.where(SearchIndex.user_id == filters.user_id)

            if filters.is_public is not None:
                stmt = stmt.where(SearchIndex.is_public == filters.is_public)

            if filters.date_from:
                stmt = stmt.where(SearchIndex.content_created_at >= filters.date_from)

            if filters.date_to:
                stmt = stmt.where(SearchIndex.content_created_at <= filters.date_to)

            if filters.tags:
                # Filter by tags (JSON array contains)
                for tag in filters.tags:
                    stmt = stmt.where(
                        func.jsonb_contains(SearchIndex.tags, func.jsonb_build_array(tag))
                    )

        # Count total results
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply sorting
        if sort_by == "relevance":
            stmt = stmt.order_by(desc('rank') if sort_order == "desc" else asc('rank'))
        elif sort_by == "date":
            order_col = desc(SearchIndex.content_created_at) if sort_order == "desc" else asc(SearchIndex.content_created_at)
            stmt = stmt.order_by(order_col)
        elif sort_by == "title":
            order_col = desc(SearchIndex.title) if sort_order == "desc" else asc(SearchIndex.title)
            stmt = stmt.order_by(order_col)

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute search
        result = await self.db.execute(stmt)
        rows = result.all()

        # Build search results with enriched data
        results = []
        for row in rows:
            search_index = row[0]
            relevance_score = row[1]

            # Get enriched data
            enriched = await self._enrich_search_result(search_index, query)

            result_item = SearchResultItem(
                content_type=search_index.content_type,
                content_id=search_index.content_id,
                title=search_index.title,
                content=search_index.content[:500],  # Truncate for preview
                highlighted_title=enriched.get('highlighted_title'),
                highlighted_content=enriched.get('highlighted_content'),
                workspace_id=search_index.workspace_id,
                workspace_name=enriched.get('workspace_name'),
                project_id=search_index.project_id,
                project_name=enriched.get('project_name'),
                user_id=search_index.user_id,
                user_name=enriched.get('user_name'),
                user_avatar=enriched.get('user_avatar'),
                metadata=search_index.extra_data,
                tags=search_index.tags,
                is_public=search_index.is_public,
                content_created_at=search_index.content_created_at,
                content_updated_at=search_index.content_updated_at,
                relevance_score=float(relevance_score) if relevance_score else None,
                url=self._generate_content_url(search_index.content_type, search_index.content_id),
            )
            results.append(result_item)

        return results, total

    async def _enrich_search_result(
        self,
        search_index: SearchIndex,
        query: str
    ) -> Dict[str, Any]:
        """Enrich search result with additional data"""
        enriched = {}

        # Get workspace name
        if search_index.workspace_id:
            workspace_stmt = select(Workspace.name).where(Workspace.id == search_index.workspace_id)
            workspace_result = await self.db.execute(workspace_stmt)
            enriched['workspace_name'] = workspace_result.scalar()

        # Get project name
        if search_index.project_id:
            project_stmt = select(Project.name).where(Project.id == search_index.project_id)
            project_result = await self.db.execute(project_stmt)
            enriched['project_name'] = project_result.scalar()

        # Get user info
        if search_index.user_id:
            user_stmt = select(User.full_name, User.avatar_url).where(User.id == search_index.user_id)
            user_result = await self.db.execute(user_stmt)
            user_row = user_result.first()
            if user_row:
                enriched['user_name'] = user_row[0]
                enriched['user_avatar'] = user_row[1]

        # Generate highlighted snippets using PostgreSQL ts_headline
        try:
            tsquery = func.plainto_tsquery('english', query)

            # Highlight title
            title_headline = await self.db.execute(
                select(func.ts_headline('english', search_index.title, tsquery))
            )
            enriched['highlighted_title'] = title_headline.scalar()

            # Highlight content
            content_headline = await self.db.execute(
                select(func.ts_headline('english', search_index.content, tsquery))
            )
            enriched['highlighted_content'] = content_headline.scalar()
        except Exception:
            # Fallback if highlighting fails
            enriched['highlighted_title'] = search_index.title
            enriched['highlighted_content'] = search_index.content[:200]

        return enriched

    def _generate_content_url(self, content_type: ContentType, content_id: int) -> str:
        """Generate URL for content item"""
        url_map = {
            ContentType.MESSAGE: f"/chat/messages/{content_id}",
            ContentType.DOCUMENT: f"/documents/{content_id}",
            ContentType.TASK: f"/tasks/{content_id}",
            ContentType.EVENT: f"/calendar/events/{content_id}",
            ContentType.WHITEBOARD: f"/whiteboards/{content_id}",
            ContentType.MEETING: f"/meetings/{content_id}",
            ContentType.PROJECT: f"/projects/{content_id}",
            ContentType.FOLDER: f"/folders/{content_id}",
            ContentType.COMMENT: f"/comments/{content_id}",
        }
        return url_map.get(content_type, f"/{content_type}/{content_id}")

    async def quick_search(
        self,
        query: str,
        workspace_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Quick autocomplete search for UI

        Args:
            query: Search query (partial)
            workspace_id: Workspace to search in
            limit: Maximum results

        Returns:
            List of quick search results
        """
        # Use prefix matching for autocomplete
        tsquery = func.to_tsquery('english', f"{query}:*")

        stmt = select(
            SearchIndex.content_type,
            SearchIndex.content_id,
            SearchIndex.title,
            func.ts_rank(SearchIndex.search_vector, tsquery).label('rank')
        ).where(
            and_(
                SearchIndex.workspace_id == workspace_id,
                SearchIndex.is_deleted == False,
                SearchIndex.search_vector.op('@@')(tsquery)
            )
        ).order_by(
            desc('rank')
        ).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                'content_type': row[0],
                'content_id': row[1],
                'title': row[2],
                'subtitle': self._get_content_type_label(row[0]),
                'icon': self._get_content_type_icon(row[0]),
                'url': self._generate_content_url(row[0], row[1]),
            }
            for row in rows
        ]

    def _get_content_type_label(self, content_type: ContentType) -> str:
        """Get human-readable label for content type"""
        labels = {
            ContentType.MESSAGE: "Chat Message",
            ContentType.DOCUMENT: "Document",
            ContentType.TASK: "Task",
            ContentType.EVENT: "Calendar Event",
            ContentType.WHITEBOARD: "Whiteboard",
            ContentType.MEETING: "Meeting",
            ContentType.PROJECT: "Project",
            ContentType.FOLDER: "Folder",
            ContentType.COMMENT: "Comment",
        }
        return labels.get(content_type, str(content_type))

    def _get_content_type_icon(self, content_type: ContentType) -> str:
        """Get icon name for content type"""
        icons = {
            ContentType.MESSAGE: "message-square",
            ContentType.DOCUMENT: "file-text",
            ContentType.TASK: "check-square",
            ContentType.EVENT: "calendar",
            ContentType.WHITEBOARD: "layout",
            ContentType.MEETING: "video",
            ContentType.PROJECT: "folder",
            ContentType.FOLDER: "folder",
            ContentType.COMMENT: "message-circle",
        }
        return icons.get(content_type, "file")

    async def get_search_suggestions(
        self,
        user_id: int,
        workspace_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get search suggestions based on user's search history"""
        stmt = select(
            SearchHistory.query,
            func.count(SearchHistory.id).label('count'),
            func.max(SearchHistory.created_at).label('last_searched')
        ).where(
            and_(
                SearchHistory.user_id == user_id,
                SearchHistory.workspace_id == workspace_id
            )
        ).group_by(
            SearchHistory.query
        ).order_by(
            desc('count'),
            desc('last_searched')
        ).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                'suggestion': row[0],
                'count': row[1],
                'last_searched': row[2],
            }
            for row in rows
        ]

    # ============================================
    # Search History Operations
    # ============================================
    async def create_search_history(
        self,
        user_id: int,
        workspace_id: int,
        query: str,
        filters: Optional[Dict[str, Any]],
        content_types: Optional[List[str]],
        results_count: int,
        search_duration_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SearchHistory:
        """Create search history entry"""
        history = SearchHistory(
            user_id=user_id,
            workspace_id=workspace_id,
            query=query,
            filters=filters,
            content_types=content_types,
            results_count=results_count,
            search_duration_ms=search_duration_ms,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def get_user_search_history(
        self,
        user_id: int,
        workspace_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[SearchHistory], int]:
        """Get user's search history"""
        stmt = select(SearchHistory).where(
            and_(
                SearchHistory.user_id == user_id,
                SearchHistory.workspace_id == workspace_id
            )
        ).order_by(
            desc(SearchHistory.created_at)
        ).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        history = result.scalars().all()

        # Count total
        count_stmt = select(func.count(SearchHistory.id)).where(
            and_(
                SearchHistory.user_id == user_id,
                SearchHistory.workspace_id == workspace_id
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        return list(history), total

    async def delete_search_history(self, user_id: int, history_id: Optional[int] = None) -> bool:
        """Delete search history (specific or all)"""
        if history_id:
            stmt = select(SearchHistory).where(
                and_(
                    SearchHistory.id == history_id,
                    SearchHistory.user_id == user_id
                )
            )
            result = await self.db.execute(stmt)
            history = result.scalar_one_or_none()

            if history:
                await self.db.delete(history)
                await self.db.commit()
                return True
            return False
        else:
            # Delete all history for user
            from sqlalchemy import delete
            stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
            await self.db.execute(stmt)
            await self.db.commit()
            return True

    # ============================================
    # Saved Search Operations
    # ============================================
    async def create_saved_search(
        self,
        user_id: int,
        workspace_id: int,
        name: str,
        query: str,
        description: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        content_types: Optional[List[str]] = None,
        is_default: bool = False,
        is_shared: bool = False,
        notify_on_new_results: bool = False,
    ) -> SavedSearch:
        """Create a saved search"""
        saved_search = SavedSearch(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            query=query,
            filters=filters,
            content_types=content_types,
            is_default=is_default,
            is_shared=is_shared,
            notify_on_new_results=notify_on_new_results,
        )
        self.db.add(saved_search)
        await self.db.commit()
        await self.db.refresh(saved_search)
        return saved_search

    async def get_saved_searches(
        self,
        user_id: int,
        workspace_id: int
    ) -> List[SavedSearch]:
        """Get user's saved searches"""
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.user_id == user_id,
                SavedSearch.workspace_id == workspace_id
            )
        ).order_by(desc(SavedSearch.is_default), desc(SavedSearch.last_used_at))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_saved_search(self, saved_search_id: int, user_id: int) -> Optional[SavedSearch]:
        """Get a specific saved search"""
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.id == saved_search_id,
                SavedSearch.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_saved_search(
        self,
        saved_search_id: int,
        user_id: int,
        **update_data
    ) -> Optional[SavedSearch]:
        """Update a saved search"""
        saved_search = await self.get_saved_search(saved_search_id, user_id)
        if not saved_search:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(saved_search, key):
                setattr(saved_search, key, value)

        await self.db.commit()
        await self.db.refresh(saved_search)
        return saved_search

    async def delete_saved_search(self, saved_search_id: int, user_id: int) -> bool:
        """Delete a saved search"""
        saved_search = await self.get_saved_search(saved_search_id, user_id)
        if not saved_search:
            return False

        await self.db.delete(saved_search)
        await self.db.commit()
        return True

    async def increment_saved_search_use(self, saved_search_id: int) -> None:
        """Increment use count and update last used timestamp"""
        stmt = select(SavedSearch).where(SavedSearch.id == saved_search_id)
        result = await self.db.execute(stmt)
        saved_search = result.scalar_one_or_none()

        if saved_search:
            saved_search.use_count += 1
            saved_search.last_used_at = datetime.utcnow()
            await self.db.commit()

    # ============================================
    # Indexing Operations
    # ============================================
    async def index_content(
        self,
        content_type: ContentType,
        content_id: int,
        workspace_id: int,
        title: str,
        content: str,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        content_created_at: Optional[datetime] = None,
        content_updated_at: Optional[datetime] = None,
    ) -> SearchIndex:
        """Index or update content in search index"""
        # Check if already indexed
        stmt = select(SearchIndex).where(
            and_(
                SearchIndex.content_type == content_type,
                SearchIndex.content_id == content_id,
                SearchIndex.workspace_id == workspace_id
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing index
            existing.title = title
            existing.content = content
            existing.user_id = user_id
            existing.project_id = project_id
            existing.extra_data = metadata
            existing.tags = tags
            existing.is_public = is_public
            existing.content_updated_at = content_updated_at or datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new index
            search_index = SearchIndex(
                content_type=content_type,
                content_id=content_id,
                workspace_id=workspace_id,
                user_id=user_id,
                project_id=project_id,
                title=title,
                content=content,
                metadata=metadata,
                tags=tags,
                is_public=is_public,
                content_created_at=content_created_at or datetime.utcnow(),
                content_updated_at=content_updated_at or datetime.utcnow(),
            )
            self.db.add(search_index)
            await self.db.commit()
            await self.db.refresh(search_index)
            return search_index

    async def delete_from_index(
        self,
        content_type: ContentType,
        content_id: int,
        workspace_id: int,
        soft_delete: bool = True
    ) -> bool:
        """Delete content from search index"""
        stmt = select(SearchIndex).where(
            and_(
                SearchIndex.content_type == content_type,
                SearchIndex.content_id == content_id,
                SearchIndex.workspace_id == workspace_id
            )
        )
        result = await self.db.execute(stmt)
        index = result.scalar_one_or_none()

        if not index:
            return False

        if soft_delete:
            index.is_deleted = True
            await self.db.commit()
        else:
            await self.db.delete(index)
            await self.db.commit()

        return True

    async def get_index_stats(self, workspace_id: int) -> Dict[str, Any]:
        """Get search index statistics"""
        # Total indexed items
        total_stmt = select(func.count(SearchIndex.id)).where(
            and_(
                SearchIndex.workspace_id == workspace_id,
                SearchIndex.is_deleted == False
            )
        )
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0

        # By content type
        by_type_stmt = select(
            SearchIndex.content_type,
            func.count(SearchIndex.id)
        ).where(
            and_(
                SearchIndex.workspace_id == workspace_id,
                SearchIndex.is_deleted == False
            )
        ).group_by(SearchIndex.content_type)

        type_result = await self.db.execute(by_type_stmt)
        by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            'total_indexed': total,
            'by_content_type': by_type,
            'last_updated': datetime.utcnow(),
        }

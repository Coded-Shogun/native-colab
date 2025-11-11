/**
 * Search Page
 * Universal search across all content
 */

import { useState, useEffect } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { searchService, SearchResult } from '../services/search';

export default function Search() {
  const { currentWorkspace } = useWorkspace();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const contentTypes = [
    { value: 'project', label: 'Projects', icon: '📋' },
    { value: 'task', label: 'Tasks', icon: '✓' },
    { value: 'message', label: 'Messages', icon: '💬' },
    { value: 'document', label: 'Documents', icon: '📄' },
    { value: 'event', label: 'Events', icon: '📅' },
    { value: 'user', label: 'People', icon: '👤' },
  ];

  useEffect(() => {
    if (currentWorkspace) {
      loadRecentSearches();
    }
  }, [currentWorkspace]);

  useEffect(() => {
    if (query.length >= 2) {
      const timeoutId = setTimeout(() => {
        performSearch();
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setResults([]);
      setHasSearched(false);
    }
  }, [query, selectedTypes]);

  const loadRecentSearches = async () => {
    if (!currentWorkspace) return;
    try {
      const recent = await searchService.getRecentSearches(currentWorkspace.id);
      setRecentSearches(recent);
    } catch (error) {
      console.error('Failed to load recent searches:', error);
    }
  };

  const performSearch = async () => {
    if (!currentWorkspace || query.length < 2) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const response = await searchService.search({
        workspace_id: currentWorkspace.id,
        query,
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
      });
      setResults(response.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleType = (type: string) => {
    if (selectedTypes.includes(type)) {
      setSelectedTypes(selectedTypes.filter((t) => t !== type));
    } else {
      setSelectedTypes([...selectedTypes, type]);
    }
  };

  const handleRecentSearch = (searchQuery: string) => {
    setQuery(searchQuery);
  };

  const getResultIcon = (type: string) => {
    const icons: Record<string, string> = {
      project: '📋',
      task: '✓',
      message: '💬',
      document: '📄',
      event: '📅',
      user: '👤',
    };
    return icons[type] || '📌';
  };

  const getResultTypeLabel = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      project: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      task: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      message: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      document: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
      event: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
      user: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
    };
    return colors[type] || colors.project;
  };

  const groupedResults = results.reduce((acc, result) => {
    if (!acc[result.type]) {
      acc[result.type] = [];
    }
    acc[result.type].push(result);
    return acc;
  }, {} as Record<string, SearchResult[]>);

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-600 dark:text-slate-400">Please select a workspace</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Search</h1>
        <p className="text-slate-600 dark:text-slate-400">
          Search across projects, tasks, messages, documents, and more
        </p>
      </div>

      {/* Search Input */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for anything..."
            className="w-full px-6 py-4 pl-14 text-lg bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            autoFocus
          />
          <svg
            className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {isSearching && (
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}
        </div>

        {/* Filter by Type */}
        <div className="mt-4 flex flex-wrap gap-2">
          {contentTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => toggleType(type.value)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                selectedTypes.includes(type.value)
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <span className="mr-1.5">{type.icon}</span>
              {type.label}
            </button>
          ))}
          {selectedTypes.length > 0 && (
            <button
              onClick={() => setSelectedTypes([])}
              className="px-3 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Results or Recent Searches */}
      {!hasSearched && recentSearches.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">Recent Searches</h2>
          <div className="space-y-2">
            {recentSearches.map((search, index) => (
              <button
                key={index}
                onClick={() => handleRecentSearch(search)}
                className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {search}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search Results */}
      {hasSearched && (
        <>
          {/* Results Summary */}
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {isSearching ? (
                'Searching...'
              ) : results.length === 0 ? (
                'No results found'
              ) : (
                <>
                  Found <span className="font-semibold text-slate-900 dark:text-white">{results.length}</span>{' '}
                  result{results.length !== 1 ? 's' : ''} for &quot;{query}&quot;
                </>
              )}
            </p>
          </div>

          {results.length === 0 && !isSearching ? (
            <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No results found</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Try different keywords or remove some filters
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedResults).map(([type, typeResults]) => (
                <div key={type}>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center">
                    <span className="mr-2">{getResultIcon(type)}</span>
                    {getResultTypeLabel(type)}s
                    <span className="ml-2 text-sm font-normal text-slate-500 dark:text-slate-400">
                      ({typeResults.length})
                    </span>
                  </h2>
                  <div className="space-y-2">
                    {typeResults.map((result) => (
                      <SearchResultCard
                        key={`${result.type}-${result.id}`}
                        result={result}
                        getTypeColor={getTypeColor}
                        getResultIcon={getResultIcon}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
  getTypeColor: (type: string) => string;
  getResultIcon: (type: string) => string;
}

function SearchResultCard({ result, getTypeColor, getResultIcon }: SearchResultCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1 min-w-0">
          <span className="text-2xl flex-shrink-0">{getResultIcon(result.type)}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-base font-medium text-slate-900 dark:text-white truncate">
                {result.title}
              </h3>
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${getTypeColor(result.type)}`}>
                {result.type}
              </span>
            </div>
            {result.description && (
              <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                {result.description}
              </p>
            )}
            {result.snippet && (
              <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                ...{result.snippet}...
              </p>
            )}
            <div className="flex items-center space-x-4 text-xs text-slate-500 dark:text-slate-400">
              {result.created_at && (
                <span>
                  Created {new Date(result.created_at).toLocaleDateString()}
                </span>
              )}
              {result.updated_at && (
                <span>
                  Updated {new Date(result.updated_at).toLocaleDateString()}
                </span>
              )}
              {result.metadata && Object.keys(result.metadata).length > 0 && (
                <span>
                  {Object.entries(result.metadata).slice(0, 2).map(([key, value], index) => (
                    <span key={key}>
                      {index > 0 && ' • '}
                      {key}: {String(value)}
                    </span>
                  ))}
                </span>
              )}
            </div>
          </div>
        </div>
        <button className="ml-4 p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
          <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

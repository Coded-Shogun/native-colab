/**
 * Whiteboards Page
 * Collaborative whiteboard with drawing tools
 */

import { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { whiteboardsService } from '../services/whiteboards';
import type { Whiteboard } from '../types';

type DrawingTool = 'pen' | 'eraser' | 'line' | 'rectangle' | 'circle' | 'text' | 'select';

interface DrawingPoint {
  x: number;
  y: number;
}

export default function Whiteboards() {
  const { currentWorkspace } = useWorkspace();
  const [whiteboards, setWhiteboards] = useState<Whiteboard[]>([]);
  const [selectedWhiteboard, setSelectedWhiteboard] = useState<Whiteboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (currentWorkspace) {
      loadWhiteboards();
    }
  }, [currentWorkspace]);

  const loadWhiteboards = async () => {
    if (!currentWorkspace) return;
    try {
      setIsLoading(true);
      const data = await whiteboardsService.getWhiteboards({
        workspace_id: currentWorkspace.id,
      });
      setWhiteboards(data);
    } catch (error) {
      console.error('Failed to load whiteboards:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateWhiteboard = async () => {
    if (!currentWorkspace) return;
    const name = prompt('Enter whiteboard name:');
    if (!name) return;

    try {
      const newWhiteboard = await whiteboardsService.createWhiteboard({
        workspace_id: currentWorkspace.id,
        name,
      });
      setWhiteboards([newWhiteboard, ...whiteboards]);
      setSelectedWhiteboard(newWhiteboard);
    } catch (error) {
      console.error('Failed to create whiteboard:', error);
    }
  };

  const handleDeleteWhiteboard = async (whiteboardId: number) => {
    if (!confirm('Are you sure you want to delete this whiteboard?')) return;
    try {
      await whiteboardsService.deleteWhiteboard(whiteboardId);
      setWhiteboards(whiteboards.filter((w) => w.id !== whiteboardId));
      if (selectedWhiteboard?.id === whiteboardId) {
        setSelectedWhiteboard(null);
      }
    } catch (error) {
      console.error('Failed to delete whiteboard:', error);
    }
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-600 dark:text-slate-400">Please select a workspace</p>
      </div>
    );
  }

  if (selectedWhiteboard) {
    return (
      <WhiteboardCanvas
        whiteboard={selectedWhiteboard}
        onClose={() => setSelectedWhiteboard(null)}
      />
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading whiteboards...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Whiteboards</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              {whiteboards.length} whiteboard{whiteboards.length !== 1 ? 's' : ''} in {currentWorkspace.name}
            </p>
          </div>
          <button
            onClick={handleCreateWhiteboard}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            + New Whiteboard
          </button>
        </div>
      </div>

      {/* Whiteboards Grid */}
      {whiteboards.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <div className="text-6xl mb-4">🎨</div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No whiteboards yet</h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">Create your first whiteboard to start collaborating</p>
          <button
            onClick={handleCreateWhiteboard}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            + Create Whiteboard
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {whiteboards.map((whiteboard) => (
            <WhiteboardCard
              key={whiteboard.id}
              whiteboard={whiteboard}
              onOpen={() => setSelectedWhiteboard(whiteboard)}
              onDelete={handleDeleteWhiteboard}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface WhiteboardCardProps {
  whiteboard: Whiteboard;
  onOpen: () => void;
  onDelete: (id: number) => void;
}

function WhiteboardCard({ whiteboard, onOpen, onDelete }: WhiteboardCardProps) {
  return (
    <div
      onClick={onOpen}
      className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer group"
    >
      <div className="aspect-video bg-slate-100 dark:bg-slate-700 rounded-lg mb-3 flex items-center justify-center">
        <span className="text-4xl">🎨</span>
      </div>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate mb-1">
            {whiteboard.name}
          </h3>
          {whiteboard.description && (
            <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
              {whiteboard.description}
            </p>
          )}
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Updated {new Date(whiteboard.updated_at).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(whiteboard.id);
          }}
          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all"
        >
          <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
}

interface WhiteboardCanvasProps {
  whiteboard: Whiteboard;
  onClose: () => void;
}

function WhiteboardCanvas({ whiteboard, onClose }: WhiteboardCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [selectedTool, setSelectedTool] = useState<DrawingTool>('pen');
  const [strokeColor, setStrokeColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [lastPoint, setLastPoint] = useState<DrawingPoint | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Set default styles
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Load saved canvas data if available
    if (whiteboard.canvas_data) {
      try {
        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, 0, 0);
        };
        img.src = whiteboard.canvas_data;
      } catch (error) {
        console.error('Failed to load canvas data:', error);
      }
    }
  }, [whiteboard]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsDrawing(true);
    setLastPoint({ x, y });

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.strokeStyle = selectedTool === 'eraser' ? '#FFFFFF' : strokeColor;
    ctx.lineWidth = selectedTool === 'eraser' ? strokeWidth * 3 : strokeWidth;

    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (selectedTool === 'pen' || selectedTool === 'eraser') {
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    setLastPoint({ x, y });
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    setLastPoint(null);

    // Auto-save canvas data
    const canvas = canvasRef.current;
    if (canvas) {
      const dataUrl = canvas.toDataURL();
      whiteboardsService.saveCanvas(whiteboard.id, dataUrl).catch(console.error);
    }
  };

  const clearCanvas = () => {
    if (!confirm('Are you sure you want to clear the entire canvas?')) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    whiteboardsService.saveCanvas(whiteboard.id, null).catch(console.error);
  };

  const exportCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dataUrl = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `${whiteboard.name}.png`;
    link.href = dataUrl;
    link.click();
  };

  const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FFA500'];

  return (
    <div className="fixed inset-0 bg-slate-50 dark:bg-slate-900 z-50">
      {/* Header */}
      <div className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">{whiteboard.name}</h2>
            {whiteboard.description && (
              <p className="text-sm text-slate-600 dark:text-slate-400">{whiteboard.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={exportCanvas}
            className="px-3 py-1.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            Export PNG
          </button>
          <button
            onClick={clearCanvas}
            className="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-center px-6">
        <div className="flex items-center space-x-6">
          {/* Drawing Tools */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedTool('pen')}
              className={`p-2 rounded-lg transition-colors ${
                selectedTool === 'pen'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
              title="Pen"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button
              onClick={() => setSelectedTool('eraser')}
              className={`p-2 rounded-lg transition-colors ${
                selectedTool === 'eraser'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
              title="Eraser"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="w-px h-8 bg-slate-200 dark:bg-slate-700" />

          {/* Colors */}
          <div className="flex items-center space-x-1">
            {colors.map((color) => (
              <button
                key={color}
                onClick={() => setStrokeColor(color)}
                className={`w-8 h-8 rounded-lg border-2 transition-all ${
                  strokeColor === color
                    ? 'border-blue-600 scale-110'
                    : 'border-slate-300 dark:border-slate-600 hover:scale-105'
                }`}
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>

          <div className="w-px h-8 bg-slate-200 dark:bg-slate-700" />

          {/* Stroke Width */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">Width:</span>
            <input
              type="range"
              min="1"
              max="20"
              value={strokeWidth}
              onChange={(e) => setStrokeWidth(parseInt(e.target.value))}
              className="w-24"
            />
            <span className="text-sm font-medium text-slate-900 dark:text-white w-8">{strokeWidth}px</span>
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-hidden p-4">
        <canvas
          ref={canvasRef}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="w-full h-full bg-white dark:bg-slate-800 rounded-lg shadow-lg cursor-crosshair border border-slate-200 dark:border-slate-700"
        />
      </div>
    </div>
  );
}

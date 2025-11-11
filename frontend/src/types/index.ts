/**
 * TypeScript type definitions for Native Colab
 * Corresponds to backend Pydantic schemas
 */

// ============================================
// Authentication & Users
// ============================================
export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url?: string;
  bio?: string;
  is_active: boolean;
  is_verified: boolean;
  role: 'super_admin' | 'user';
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ============================================
// Workspaces
// ============================================
export interface Workspace {
  id: number;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  owner_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: number;
  workspace_id: number;
  user_id: number;
  role: 'owner' | 'admin' | 'member' | 'guest';
  joined_at: string;
  user?: User;
}

// ============================================
// Projects & Tasks
// ============================================
export interface Project {
  id: number;
  workspace_id: number;
  name: string;
  description?: string;
  status: 'active' | 'on_hold' | 'completed' | 'archived';
  start_date?: string;
  end_date?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to?: number;
  due_date?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// ============================================
// Time Tracking
// ============================================
export interface TimeEntry {
  id: number;
  user_id: number;
  workspace_id: number;
  project_id?: number;
  task_id?: number;
  description?: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  is_billable: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================
// Chat & Messages
// ============================================
export interface Channel {
  id: number;
  workspace_id: number;
  name: string;
  description?: string;
  is_private: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  channel_id: number;
  user_id: number;
  content: string;
  type: 'text' | 'file' | 'image' | 'system';
  edited_at?: string;
  created_at: string;
  user?: User;
}

// ============================================
// Calendar & Events
// ============================================
export interface Event {
  id: number;
  calendar_id: number;
  title: string;
  description?: string;
  location?: string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  type: 'meeting' | 'deadline' | 'reminder' | 'other';
  visibility: 'public' | 'private';
  created_by: number;
  created_at: string;
  updated_at: string;
}

// ============================================
// Documents
// ============================================
export interface Document {
  id: number;
  folder_id?: number;
  workspace_id: number;
  name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  version: number;
  uploaded_by: number;
  created_at: string;
  updated_at: string;
}

export interface Folder {
  id: number;
  workspace_id: number;
  parent_id?: number;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

// ============================================
// Meetings
// ============================================
export interface Meeting {
  id: number;
  workspace_id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time?: string;
  meeting_url: string;
  type: 'video' | 'audio' | 'screen_share';
  status: 'scheduled' | 'in_progress' | 'ended' | 'cancelled';
  max_participants?: number;
  is_recording: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

// ============================================
// Notifications
// ============================================
export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

// ============================================
// Analytics
// ============================================
export interface WorkspaceAnalytics {
  workspace_id: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
  user_metrics: {
    total_users: number;
    active_users: number;
    new_users: number;
  };
  content_metrics: {
    total_projects: number;
    total_tasks: number;
    completed_tasks: number;
    completion_rate: number;
  };
  time_tracking_metrics: {
    total_time_hours: number;
    billable_time_hours: number;
  };
}

// ============================================
// Common Types
// ============================================
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  errors?: Record<string, string[]>;
}

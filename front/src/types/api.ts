export interface User {
  id: string
  name: string
  email: string
  avatarUrl?: string
  createdAt: string
}

export interface Task {
  id: string
  title: string
  description?: string
  start: string
  end: string
  userId: string
  completed: boolean
  createdAt: string
  updatedAt: string
}

export interface Chat {
  id: string
  name: string
  type: 'chat' | 'topic'
  messageCount: number
  participants: string[]
  createdAt: string
  updatedAt: string
}

export interface ChatNode {
  id: string
  label: string
  type: 'chat' | 'user' | 'topic'
  messageCount?: number
  createdAt?: string
}

export interface ChatEdge {
  source: string
  target: string
  type: 'replied' | 'mentioned' | 'related'
  weight?: number
}

export interface GraphData {
  nodes: ChatNode[]
  edges: ChatEdge[]
}

export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface ApiError {
  error: string
  message: string
  statusCode: number
}

export interface TaskCreateDto {
  title: string
  description?: string
  start: string
  end: string
}

export interface TaskUpdateDto {
  title?: string
  description?: string
  start?: string
  end?: string
  completed?: boolean
}

export interface AvatarUploadResponse {
  url: string
  success: boolean
}

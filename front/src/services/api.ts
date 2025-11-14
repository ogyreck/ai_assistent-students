import type {
  ApiResponse,
  Task,
  TaskCreateDto,
  TaskUpdateDto,
  GraphData,
  User,
  AvatarUploadResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`

    const defaultHeaders = {
      'Content-Type': 'application/json',
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'API request failed')
      }

      return await response.json()
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  // User API
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/user/me')
  }

  async updateUser(name?: string, email?: string): Promise<User> {
    const params = new URLSearchParams()
    if (name) params.append('name', name)
    if (email) params.append('email', email)

    return this.request<User>(`/user/me?${params.toString()}`, {
      method: 'PATCH',
    })
  }

  async uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${API_BASE_URL}/user/avatar`
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Failed to upload avatar')
    }

    return await response.json()
  }

  // Tasks API
  async getTasks(): Promise<Task[]> {
    return this.request<Task[]>('/tasks')
  }

  async getTask(id: string): Promise<Task> {
    return this.request<Task>(`/tasks/${id}`)
  }

  async createTask(data: TaskCreateDto): Promise<Task> {
    return this.request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateTask(id: string, data: TaskUpdateDto): Promise<Task> {
    return this.request<Task>(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async deleteTask(id: string): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/tasks/${id}`, {
      method: 'DELETE',
    })
  }

  // Projects API
  async getProjects(): Promise<any[]> {
    return this.request<any[]>('/projects')
  }

  async createProject(name: string): Promise<any> {
    return this.request<any>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  }

  // Chats API
  async getChats(projectId?: string): Promise<any[]> {
    const url = projectId ? `/chats?project_id=${projectId}` : '/chats'
    return this.request<any[]>(url)
  }

  async createChat(projectId: string, name: string): Promise<any> {
    return this.request<any>('/chats', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, name }),
    })
  }

  async getMessages(chatId: string): Promise<any[]> {
    return this.request<any[]>(`/chats/${chatId}/messages`)
  }

  async sendMessage(chatId: string, content: string): Promise<any> {
    return this.request<any>(`/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, role: 'user' }),
    })
  }

  // Chat Graph API
  async getChatGraph(): Promise<GraphData> {
    return this.request<GraphData>('/chats/graph')
  }

  async getChatConnections(chatId: string): Promise<GraphData> {
    return this.request<GraphData>(`/chats/${chatId}/connections`)
  }
}

export const apiService = new ApiService()
export default apiService

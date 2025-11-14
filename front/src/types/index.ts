export interface User {
  id: string
  token: string
}

export interface Project {
  id: string
  name: string
  createdAt: string
}

export interface Chat {
  id: string
  projectId: string
  name: string
  createdAt: string
}

export interface Message {
  id: string
  chatId: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
}

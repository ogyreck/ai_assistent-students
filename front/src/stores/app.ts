import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, Project, Chat, Message } from '@/types'
import {
  getUserId,
  getUserToken,
  getCurrentChatId,
  setCurrentChatId,
  getCurrentProjectId,
  setCurrentProjectId,
} from '@/utils/storage'
import apiService from '@/services/api'

export const useAppStore = defineStore('app', () => {
  // User
  const user = ref<User>({
    id: getUserId(),
    token: getUserToken(),
  })

  // Projects
  const projects = ref<Project[]>([])
  const currentProjectId = ref<string | null>(getCurrentProjectId())

  const currentProject = computed(() => {
    return projects.value.find((p) => p.id === currentProjectId.value) || null
  })

  // Chats
  const chats = ref<Chat[]>([])
  const currentChatId = ref<string | null>(getCurrentChatId())

  const currentChat = computed(() => {
    return chats.value.find((c) => c.id === currentChatId.value) || null
  })

  const currentProjectChats = computed(() => {
    if (!currentProjectId.value) return []
    return chats.value.filter((c) => c.projectId === currentProjectId.value)
  })

  // Messages
  const messages = ref<Message[]>([])

  const currentChatMessages = computed(() => {
    if (!currentChatId.value) return []
    return messages.value.filter((m) => m.chatId === currentChatId.value)
  })

  // Actions
  function selectProject(projectId: string) {
    currentProjectId.value = projectId
    setCurrentProjectId(projectId)
    // При смене проекта сбрасываем текущий чат
    currentChatId.value = null
    localStorage.removeItem('studAssis_currentChatId')
  }

  function selectChat(chatId: string) {
    currentChatId.value = chatId
    setCurrentChatId(chatId)
  }

  function addProject(project: Project) {
    projects.value.push(project)
  }

  function addChat(chat: Chat) {
    chats.value.push(chat)
  }

  function addMessage(message: Message) {
    messages.value.push(message)
  }

  async function loadProjects() {
    try {
      const data = await apiService.getProjects()
      projects.value = data.map((p: any) => ({
        id: p.id,
        name: p.name,
        createdAt: p.created_at,
      }))
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  async function loadChats() {
    try {
      const data = await apiService.getChats()
      chats.value = data.map((c: any) => ({
        id: c.id,
        projectId: c.project_id,
        name: c.name,
        createdAt: c.created_at,
      }))
    } catch (error) {
      console.error('Failed to load chats:', error)
    }
  }

  async function loadMessages(chatId: string) {
    try {
      const data = await apiService.getMessages(chatId)
      const chatMessages = data.map((m: any) => ({
        id: m.id,
        chatId: m.chat_id,
        content: m.content,
        role: m.role,
        timestamp: m.timestamp,
      }))
      // Replace messages for this chat
      messages.value = messages.value.filter((m) => m.chatId !== chatId)
      messages.value.push(...chatMessages)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  async function createNewChat(projectId: string, name: string = 'Новый чат') {
    try {
      const data = await apiService.createChat(projectId, name)
      const newChat: Chat = {
        id: data.id,
        projectId: data.project_id,
        name: data.name,
        createdAt: data.created_at,
      }
      addChat(newChat)
      selectChat(newChat.id)
      return newChat
    } catch (error) {
      console.error('Failed to create chat:', error)
      // Fallback to local creation
      const newChat: Chat = {
        id: 'chat_' + Date.now(),
        projectId,
        name,
        createdAt: new Date().toISOString(),
      }
      addChat(newChat)
      selectChat(newChat.id)
      return newChat
    }
  }

  async function createNewProject(name: string) {
    try {
      const data = await apiService.createProject(name)
      const newProject: Project = {
        id: data.id,
        name: data.name,
        createdAt: data.created_at,
      }
      addProject(newProject)
      selectProject(newProject.id)
      return newProject
    } catch (error) {
      console.error('Failed to create project:', error)
      // Fallback to local creation
      const newProject: Project = {
        id: 'project_' + Date.now(),
        name,
        createdAt: new Date().toISOString(),
      }
      addProject(newProject)
      selectProject(newProject.id)
      return newProject
    }
  }

  async function sendMessage(chatId: string, content: string) {
    try {
      const data = await apiService.sendMessage(chatId, content)
      const message: Message = {
        id: data.id,
        chatId: data.chat_id,
        content: data.content,
        role: data.role,
        timestamp: data.timestamp,
      }
      addMessage(message)
      return message
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    }
  }

  return {
    // State
    user,
    projects,
    currentProjectId,
    currentProject,
    chats,
    currentChatId,
    currentChat,
    currentProjectChats,
    messages,
    currentChatMessages,
    // Actions
    selectProject,
    selectChat,
    addProject,
    addChat,
    addMessage,
    createNewChat,
    createNewProject,
    loadProjects,
    loadChats,
    loadMessages,
    sendMessage,
  }
})

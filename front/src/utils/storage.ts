const STORAGE_KEYS = {
  USER_ID: 'studAssis_userId',
  USER_TOKEN: 'studAssis_userToken',
  CURRENT_CHAT_ID: 'studAssis_currentChatId',
  CURRENT_PROJECT_ID: 'studAssis_currentProjectId',
} as const

// Генерация случайного токена
function generateToken(): string {
  return 'user_' + Math.random().toString(36).substring(2) + Date.now().toString(36)
}

// User ID и Token
export function getUserId(): string {
  let userId = localStorage.getItem(STORAGE_KEYS.USER_ID)
  if (!userId) {
    userId = generateToken()
    localStorage.setItem(STORAGE_KEYS.USER_ID, userId)
  }
  return userId
}

export function getUserToken(): string {
  let token = localStorage.getItem(STORAGE_KEYS.USER_TOKEN)
  if (!token) {
    token = generateToken()
    localStorage.setItem(STORAGE_KEYS.USER_TOKEN, token)
  }
  return token
}

// Current Chat ID
export function getCurrentChatId(): string | null {
  return localStorage.getItem(STORAGE_KEYS.CURRENT_CHAT_ID)
}

export function setCurrentChatId(chatId: string): void {
  localStorage.setItem(STORAGE_KEYS.CURRENT_CHAT_ID, chatId)
}

export function removeCurrentChatId(): void {
  localStorage.removeItem(STORAGE_KEYS.CURRENT_CHAT_ID)
}

// Current Project ID
export function getCurrentProjectId(): string | null {
  return localStorage.getItem(STORAGE_KEYS.CURRENT_PROJECT_ID)
}

export function setCurrentProjectId(projectId: string): void {
  localStorage.setItem(STORAGE_KEYS.CURRENT_PROJECT_ID, projectId)
}

export function removeCurrentProjectId(): void {
  localStorage.removeItem(STORAGE_KEYS.CURRENT_PROJECT_ID)
}

// Clear all data
export function clearAllStorage(): void {
  Object.values(STORAGE_KEYS).forEach((key) => {
    localStorage.removeItem(key)
  })
}

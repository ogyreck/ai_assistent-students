export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  endpoints: {
    auth: {
      login: '/auth/login',
      register: '/auth/register',
      logout: '/auth/logout',
    },
    chat: {
      send: '/chat/send',
      history: '/chat/history',
    },
    projects: {
      list: '/projects',
      create: '/projects',
      get: (id: string) => `/projects/${id}`,
      update: (id: string) => `/projects/${id}`,
      delete: (id: string) => `/projects/${id}`,
    },
  },
} as const

export default API_CONFIG
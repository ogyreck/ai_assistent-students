// Determine WebSocket URL based on current location
const getWsBaseUrl = () => {
  // If we have env variable, use it
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }

  // Otherwise, construct from current location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws`
}

const WS_BASE_URL = getWsBaseUrl()

export interface WSMessage {
  type: 'user_message' | 'assistant_start' | 'assistant_chunk' | 'assistant_end'
  content?: string
  message?: any
  message_id?: string
}

export class ChatWebSocket {
  private ws: WebSocket | null = null
  private chatId: string
  private messageHandlers: ((message: WSMessage) => void)[] = []
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(chatId: string) {
    this.chatId = chatId
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE_URL}/chat/${this.chatId}`
        console.log(`Connecting to WebSocket: ${wsUrl}`)
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log(`✓ WebSocket connected to chat ${this.chatId}`)
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            console.log(`← WS Message:`, message.type)
            this.messageHandlers.forEach((handler) => handler(message))
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('✗ WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.attemptReconnect()
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
        reject(error)
      }
    })
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error)
        })
      }, 1000 * this.reconnectAttempts)
    }
  }

  sendMessage(content: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log(`→ Sending message: ${content.substring(0, 50)}...`)
      this.ws.send(JSON.stringify({ content }))
    } else {
      console.error('✗ WebSocket is not connected')
    }
  }

  onMessage(handler: (message: WSMessage) => void) {
    this.messageHandlers.push(handler)
  }

  removeMessageHandler(handler: (message: WSMessage) => void) {
    this.messageHandlers = this.messageHandlers.filter((h) => h !== handler)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.messageHandlers = []
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export default ChatWebSocket

<template>
  <div class="chat-container">
    <div class="chat-content">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="currentChatMessages.length === 0" class="no-messages">
          <p>Начните диалог с вашим ассистентом</p>
        </div>
        <div
          v-for="message in currentChatMessages"
          :key="message.id"
          :class="['message', message.role]"
        >
          <div class="message-content">
            {{ message.content }}
          </div>
          <div class="message-time">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>

      <div class="input-container">
        <button class="attach-btn" title="Прикрепить файл" disabled>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              d="M12 5v14M5 12h14"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
        <input
          v-model="messageText"
          @keydown.enter="sendMessage()"
          type="text"
          placeholder="Спросите что нибудь"
          class="message-input"
        />
        <button
          class="voice-btn"
          :class="{ recording: isRecording }"
          @click="toggleVoiceRecording"
          :title="isRecording ? 'Остановить запись' : 'Голосовой ввод'"
        >
          <svg v-if="!isRecording" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
            />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
          <span v-else class="recording-indicator">REC</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'
import ChatWebSocket from '@/services/websocket'
import SpeechRecorder, { transcribeAudio } from '@/services/speech'
import type { Message } from '@/types'
import type { WSMessage } from '@/services/websocket'

const store = useAppStore()
const { currentChat, currentChatMessages } = storeToRefs(store)

const messageText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const isRecording = ref(false)
const isTranscribing = ref(false)

let chatWs: ChatWebSocket | null = null
let isConnecting = false
let speechRecorder: SpeechRecorder | null = null

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

async function connectWebSocket(chatId: string) {
  if (chatWs && chatWs.isConnected()) {
    return
  }

  if (isConnecting) return
  isConnecting = true

  try {
    chatWs = new ChatWebSocket(chatId)
    await chatWs.connect()

    let currentAssistantMessageId: string | null = null

    // Handle incoming messages
    chatWs.onMessage((message: WSMessage) => {
      switch (message.type) {
        case 'user_message':
          // User message already added before sending, so skip it here
          break

        case 'assistant_start':
          // Create assistant message at the start of streaming
          const assistantMessage: Message = {
            id: message.message_id || `msg_${Date.now()}`,
            chatId,
            content: '',
            role: 'assistant',
            timestamp: new Date().toISOString(),
          }
          store.addMessage(assistantMessage)
          currentAssistantMessageId = assistantMessage.id
          break

        case 'assistant_chunk':
          if (message.content && currentAssistantMessageId) {
            // Find and update the assistant message in the store
            const assistantMsg = store.messages.find((m) => m.id === currentAssistantMessageId)
            if (assistantMsg) {
              assistantMsg.content += message.content
              nextTick(() => scrollToBottom())
            }
          }
          break

        case 'assistant_end':
          // Update final message content with complete response
          if (message.message && currentAssistantMessageId) {
            const assistantMsg = store.messages.find((m) => m.id === currentAssistantMessageId)
            if (assistantMsg) {
              assistantMsg.content = message.message.content
              assistantMsg.timestamp = message.message.timestamp
            }
          }
          currentAssistantMessageId = null
          nextTick(() => scrollToBottom())
          break
      }
    })

    isConnecting = false
  } catch (error) {
    console.error('Failed to connect WebSocket:', error)
    isConnecting = false
  }
}

async function sendMessage(content?: string) {
  const messageContent = content || messageText.value
  if (!messageContent.trim()) return

  // Если нет текущего чата, создаем новый
  let chatId = currentChat.value?.id
  if (!chatId) {
    // Если нет проекта, создаем проект по умолчанию
    let projectId = store.currentProjectId
    if (!projectId) {
      const newProject = await store.createNewProject('Новый проект')
      projectId = newProject.id
    }
    // Создаем новый чат
    const newChat = await store.createNewChat(projectId, 'Новый чат')
    chatId = newChat.id
  }

  // Добавляем сообщение пользователя локально
  const userMessage: Message = {
    id: `msg_${Date.now()}`,
    chatId: chatId,
    content: messageContent,
    role: 'user',
    timestamp: new Date().toISOString(),
  }
  store.addMessage(userMessage)

  // Очищаем поле ввода
  if (!content) {
    messageText.value = ''
  }

  await nextTick()
  scrollToBottom()

  // Подключаемся к WebSocket если не подключены
  if (!chatWs || !chatWs.isConnected()) {
    await connectWebSocket(chatId)
  }

  // Отправляем сообщение через WebSocket
  if (chatWs && chatWs.isConnected()) {
    chatWs.sendMessage(messageContent)
  } else {
    console.error('WebSocket is not connected')
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Connect to WebSocket when chat changes
watch(
  () => currentChat.value?.id,
  (newChatId) => {
    if (newChatId) {
      connectWebSocket(newChatId)
    }
    nextTick(() => scrollToBottom())
  }
)

async function toggleVoiceRecording() {
  if (!speechRecorder) {
    speechRecorder = new SpeechRecorder({
      onStart: () => {
        isRecording.value = true
        console.log('Recording started...')
      },
      onStop: () => {
        isRecording.value = false
        console.log('Recording stopped')
      },
      onError: (error) => {
        console.error('Recording error:', error)
        isRecording.value = false
      },
    })
  }

  if (!isRecording.value) {
    // Start recording
    await speechRecorder.startRecording()
  } else {
    // Stop recording and transcribe
    isTranscribing.value = true
    const audioBlob = await speechRecorder.stopRecording()

    if (audioBlob) {
      try {
        const apiUrl = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000'
        const transcribedText = await transcribeAudio(audioBlob, apiUrl)

        if (transcribedText.trim()) {
          messageText.value = transcribedText
        }
      } catch (error) {
        console.error('Transcription failed:', error)
      } finally {
        isTranscribing.value = false
      }
    }
  }
}

// Cleanup on unmount
onUnmounted(() => {
  if (chatWs) {
    chatWs.disconnect()
  }
  if (speechRecorder && isRecording.value) {
    speechRecorder.cancelRecording()
  }
})
</script>

<style scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.no-messages {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  gap: 4px;
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.user .message-content {
  background: #1967d2;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #999;
  padding: 0 8px;
}

.message.user .message-time {
  text-align: right;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.attach-btn,
.voice-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f0f0f0;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s;
  flex-shrink: 0;
}

.attach-btn:hover,
.voice-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.voice-btn.recording {
  background: #ff5252;
  color: white;
  animation: pulse 1s infinite;
}

.voice-btn.recording:hover {
  background: #ff1744;
}

.recording-indicator {
  font-size: 11px;
  font-weight: bold;
  letter-spacing: 1px;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(255, 82, 82, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0);
  }
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #1967d2;
}

.message-input::placeholder {
  color: #999;
}
</style>

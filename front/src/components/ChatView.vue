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
  background: #f5f7fa;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.no-messages {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 16px;
  text-align: center;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  gap: 6px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: white;
  color: #2d3748;
  border-bottom-left-radius: 4px;
  border: 1px solid #e2e8f0;
}

.message-time {
  font-size: 11px;
  color: #a0aec0;
  padding: 0 8px;
  font-weight: 500;
}

.message.user .message-time {
  text-align: right;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px 24px;
  background: transparent;
}

.attach-btn,
.voice-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #718096;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.attach-btn:hover,
.voice-btn:hover {
  background: #f7fafc;
  color: #4a5568;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.voice-btn.recording {
  background: #fc8181;
  color: white;
  animation: pulse 1.5s infinite;
}

.voice-btn.recording:hover {
  background: #f56565;
}

.recording-indicator {
  font-size: 11px;
  font-weight: bold;
  letter-spacing: 1px;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(252, 129, 129, 0.7);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(252, 129, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(252, 129, 129, 0);
  }
}

.message-input {
  flex: 1;
  padding: 14px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 24px;
  font-size: 15px;
  outline: none;
  transition: all 0.2s ease;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.message-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1), 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-input::placeholder {
  color: #a0aec0;
}
</style>

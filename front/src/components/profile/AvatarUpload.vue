<template>
  <div class="avatar-upload">
    <div class="avatar-container">
      <div class="avatar-preview">
        <img
          v-if="avatarUrl"
          :src="avatarUrl"
          alt="User Avatar"
          class="avatar-image"
        />
        <div v-else class="avatar-placeholder">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
      </div>

      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        @change="handleFileSelect"
        style="display: none"
      />

      <button @click="triggerFileInput" class="upload-button">
        {{ avatarUrl ? 'Изменить аватар' : 'Загрузить аватар' }}
      </button>

      <div v-if="uploading" class="upload-status">
        Загрузка...
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>

    <div class="user-info">
      <h3>{{ userName || 'Пользователь' }}</h3>
      <p class="user-email">{{ userEmail || 'email@example.com' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiService from '@/services/api'

const avatarUrl = ref<string>('')
const userName = ref<string>('Иван Иванов')
const userEmail = ref<string>('ivan@example.com')
const uploading = ref<boolean>(false)
const error = ref<string>('')
const fileInput = ref<HTMLInputElement | null>(null)

onMounted(async () => {
  try {
    const user = await apiService.getCurrentUser()
    userName.value = user.name
    userEmail.value = user.email
    if (user.avatar_url) {
      avatarUrl.value = user.avatar_url
    }
  } catch (err) {
    console.error('Failed to load user:', err)
  }
})

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    error.value = 'Пожалуйста, выберите изображение'
    return
  }

  // Validate file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Размер файла не должен превышать 5MB'
    return
  }

  error.value = ''
  uploading.value = true

  try {
    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      avatarUrl.value = e.target?.result as string
    }
    reader.readAsDataURL(file)

    // Upload to backend
    const response = await apiService.uploadAvatar(file)
    avatarUrl.value = response.url

    uploading.value = false
  } catch (err) {
    error.value = 'Ошибка при загрузке аватара'
    uploading.value = false
    console.error('Avatar upload error:', err)
  }
}
</script>

<style scoped>
.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  width: 100%;
}

.avatar-preview {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #e0e0e0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.avatar-placeholder svg {
  width: 80px;
  height: 80px;
}

.upload-button {
  padding: 10px 20px;
  background: #333;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  width: 100%;
  max-width: 200px;
  font-weight: 500;
}

.upload-button:hover {
  background: #000;
}

.upload-status {
  color: #666;
  font-size: 14px;
}

.error-message {
  color: #f44336;
  font-size: 14px;
  text-align: center;
}

.user-info {
  text-align: center;
  width: 100%;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.user-info h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 1.2rem;
}

.user-email {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}
</style>

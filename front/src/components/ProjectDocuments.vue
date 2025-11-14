<template>
  <div class="project-documents">
    <!-- Header -->
    <div class="documents-header">
      <h1>📁 Документы проекта</h1>
      <p class="project-name" v-if="currentProject">{{ currentProject.name }}</p>
    </div>

    <!-- Upload Area -->
    <div class="upload-section">
      <div class="upload-box" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
        <div class="upload-icon">📤</div>
        <p class="upload-text">Перетащите файлы сюда или нажмите для загрузки</p>
        <p class="upload-hint">Поддерживаемые форматы: PDF, DOCX, XLSX, CSV, HTML, TXT и другие</p>
        <input
          ref="fileInput"
          type="file"
          multiple
          @change="handleFileSelect"
          style="display: none"
          accept=".pdf,.docx,.xlsx,.csv,.html,.txt,.xml,.odt,.epub,.doc,.rtf"
        />
      </div>

      <!-- Upload Progress -->
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
        <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
        <span>{{ uploadProgress }}%</span>
      </div>
    </div>

    <!-- Documents List -->
    <div class="documents-section">
      <h2>Загруженные документы</h2>
      <div v-if="documents.length === 0" class="no-documents">
        <p>Документы еще не загружены</p>
      </div>
      <div v-else class="documents-list">
        <div v-for="doc in documents" :key="doc.id" class="document-item">
          <div class="document-info">
            <div class="document-icon">📄</div>
            <div class="document-details">
              <h3>{{ doc.filename }}</h3>
              <div class="document-meta">
                <span class="file-size">{{ formatFileSize(doc.file_size) }}</span>
                <span class="upload-date">{{ formatDate(doc.uploaded_at) }}</span>
              </div>
            </div>
          </div>
          <button class="delete-btn" @click="deleteDocument(doc.id)" :disabled="isDeleting">
            🗑️ Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useAppStore } from '../stores/app'
import { apiService } from '../services/api'

const store = useAppStore()
const documents = ref<any[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const uploadProgress = ref(0)
const isDeleting = ref(false)
const isLoading = ref(false)

const currentProjectId = computed(() => store.currentProjectId)
const currentProject = computed(() => {
  return store.projects.find(p => p.id === store.currentProjectId)
})

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const loadDocuments = async () => {
  if (!store.currentProjectId) {
    documents.value = []
    return
  }

  try {
    isLoading.value = true
    documents.value = await apiService.getProjectDocuments(store.currentProjectId)
  } catch (error) {
    console.error('Failed to load documents:', error)
    documents.value = []
  } finally {
    isLoading.value = false
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    await uploadFile(files[i], i, files.length)
  }

  target.value = ''
}

const handleDrop = async (event: DragEvent) => {
  const files = event.dataTransfer?.files

  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    await uploadFile(files[i], i, files.length)
  }
}

const uploadFile = async (file: File, index: number, total: number) => {
  if (!store.currentProjectId) {
    alert('Пожалуйста, выберите проект')
    return
  }

  try {
    uploadProgress.value = Math.round(((index + 1) / total) * 100)
    const newDocument = await apiService.uploadDocument(store.currentProjectId, file)
    documents.value.push(newDocument)
    documents.value = documents.value.sort((a, b) =>
      new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
    )
  } catch (error) {
    console.error(`Failed to upload ${file.name}:`, error)
    alert(`Ошибка при загрузке файла ${file.name}`)
  } finally {
    if (index === total - 1) {
      uploadProgress.value = 0
    }
  }
}

const deleteDocument = async (documentId: string) => {
  if (!store.currentProjectId) return

  if (!confirm('Удалить этот документ?')) return

  try {
    isDeleting.value = true
    await apiService.deleteDocument(store.currentProjectId, documentId)
    documents.value = documents.value.filter(d => d.id !== documentId)
  } catch (error) {
    console.error('Failed to delete document:', error)
    alert('Ошибка при удалении документа')
  } finally {
    isDeleting.value = false
  }
}

onMounted(async () => {
  await store.loadProjects()
  loadDocuments()
})

watch(currentProjectId, () => {
  loadDocuments()
})
</script>

<style scoped>
.project-documents {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 30px;
  background: #f8f9fa;
  overflow-y: auto;
}

.documents-header {
  margin-bottom: 30px;
}

.documents-header h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.project-name {
  margin: 0;
  font-size: 16px;
  color: #666;
}

.upload-section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.upload-box {
  border: 2px dashed #d0d0d0;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.upload-box:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.upload-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.upload-text {
  margin: 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.upload-hint {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #999;
}

.upload-progress {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  height: 8px;
  background: linear-gradient(90deg, #007bff, #0056b3);
  border-radius: 4px;
  flex: 1;
  transition: width 0.3s ease;
}

/* Documents Section */
.documents-section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.documents-section h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.no-documents {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.3s ease;
}

.document-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
}

.document-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
}

.document-icon {
  font-size: 28px;
}

.document-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.document-details h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
  word-break: break-word;
}

.document-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.file-size::before {
  content: '📊 ';
}

.upload-date::before {
  content: '📅 ';
}

.delete-btn {
  padding: 8px 16px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  white-space: nowrap;
  margin-left: 10px;
}

.delete-btn:hover:not(:disabled) {
  background: #c82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2);
}

.delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

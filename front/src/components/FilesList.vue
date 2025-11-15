<template>
  <div class="files-list-container">
    <h2>Файлы проекта</h2>

    <div class="filter-section">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск файлов..."
        class="search-input"
      />
      <select v-model="selectedCategory" class="category-select">
        <option value="">Все файлы</option>
        <option value="images">Изображения</option>
        <option value="styles">Стили</option>
        <option value="scripts">Скрипты</option>
        <option value="documents">Документы</option>
      </select>
    </div>

    <div class="stats">
      <span>Всего файлов: <strong>{{ allFiles.length }}</strong></span>
      <span>Найдено: <strong>{{ filteredFiles.length }}</strong></span>
    </div>

    <div class="files-grid">
      <div
        v-for="(file, index) in filteredFiles"
        :key="index"
        class="file-item"
      >
        <div class="file-icon">
          <span :class="['icon', getFileType(file)]">
            {{ getFileExtension(file) }}
          </span>
        </div>
        <div class="file-info">
          <div class="file-name">{{ getFileName(file) }}</div>
          <div class="file-path">{{ file }}</div>
        </div>
      </div>
    </div>

    <div v-if="filteredFiles.length === 0" class="no-files">
      Файлы не найдены
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const searchQuery = ref('')
const selectedCategory = ref('')
const allFiles = ref<string[]>([])

onMounted(async () => {
  // Получаем все файлы из папки src
  const fileModules = import.meta.glob('@/**/*', { eager: false })

  const files = Object.keys(fileModules)
    .map(path => {
      // Убираем @ и оставляем относительный путь от src
      return path.replace('@/', '')
    })
    .filter(path => {
      // Фильтруем скрытые файлы и папки node_modules
      const parts = path.split('/')
      return !parts.some(part => part.startsWith('.') || part === 'node_modules')
    })
    .sort()

  allFiles.value = files
})

const filteredFiles = computed(() => {
  return allFiles.value.filter(file => {
    const matchesSearch = file.toLowerCase().includes(searchQuery.value.toLowerCase())

    if (!selectedCategory.value) {
      return matchesSearch
    }

    const category = getCategoryByFile(file)
    return matchesSearch && category === selectedCategory.value
  })
})

function getFileExtension(file: string): string {
  const parts = file.split('.')
  if (parts.length > 1) {
    return parts[parts.length - 1].toUpperCase()
  }
  return 'FILE'
}

function getFileName(file: string): string {
  const result = file.split('/').pop()
  return result || file
}

function getFileType(file: string): string {
  const ext = getFileExtension(file).toLowerCase()

  if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
    return 'image'
  } else if (['css', 'scss', 'sass'].includes(ext)) {
    return 'style'
  } else if (['ts', 'tsx', 'js', 'jsx'].includes(ext)) {
    return 'script'
  } else if (['vue'].includes(ext)) {
    return 'vue'
  } else if (['json', 'yaml', 'yml', 'toml'].includes(ext)) {
    return 'config'
  } else if (['md', 'txt'].includes(ext)) {
    return 'document'
  }

  return 'other'
}

function getCategoryByFile(file: string): string {
  const fileType = getFileType(file)

  if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(getFileExtension(file).toLowerCase())) {
    return 'images'
  } else if (['css', 'scss', 'sass', 'vue'].includes(getFileExtension(file).toLowerCase())) {
    return 'styles'
  } else if (['ts', 'tsx', 'js', 'jsx'].includes(getFileExtension(file).toLowerCase())) {
    return 'scripts'
  } else if (['md', 'txt'].includes(getFileExtension(file).toLowerCase())) {
    return 'documents'
  }

  return 'other'
}
</script>

<style scoped>
.files-list-container {
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  max-width: 1200px;
  margin: 20px auto;
}

h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 24px;
}

.filter-section {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input,
.category-select {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.search-input:focus,
.category-select:focus {
  outline: none;
  border-color: #1967d2;
  box-shadow: 0 0 0 3px rgba(25, 103, 210, 0.1);
}

.category-select {
  min-width: 150px;
}

.stats {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
}

.stats strong {
  color: #333;
  font-weight: 600;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #eee;
  transition: all 0.2s;
  cursor: pointer;
}

.file-item:hover {
  border-color: #1967d2;
  box-shadow: 0 2px 8px rgba(25, 103, 210, 0.1);
  transform: translateY(-2px);
}

.file-icon {
  flex-shrink: 0;
}

.icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  color: white;
}

.icon.image {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.icon.style {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.icon.script {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.icon.vue {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.icon.config {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.icon.document {
  background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
}

.icon.other {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
  word-break: break-word;
}

.file-path {
  font-size: 12px;
  color: #999;
  word-break: break-all;
  margin-top: 4px;
  font-family: 'Courier New', monospace;
}

.no-files {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 16px;
}
</style>

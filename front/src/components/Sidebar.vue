<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <img src="@/assets/photo_2025-11-14_16-28-46.jpg" alt="SA Logo" class="logo" />
      <span class="logo-text">SA</span>
    </div>

    <div class="sidebar-navigation">
      <RouterLink to="/" class="nav-item">
        <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span class="nav-label">Чаты</span>
      </RouterLink>
      <RouterLink to="/profile" class="nav-item">
        <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
        <span class="nav-label">Профиль</span>
      </RouterLink>
    </div>

    <div v-if="!hideProjects" class="sidebar-section">
      <div class="section-header">
        <h3>Projects</h3>
        <button @click="createProject" class="add-btn" title="Создать проект">+</button>
      </div>
      <div class="items-list">
        <div
          v-for="project in projects"
          :key="project.id"
          :class="['item', { active: project.id === currentProjectId }]"
          @click="selectProject(project.id)"
        >
          {{ project.name }}
        </div>
        <div v-if="projects.length === 0" class="empty-state">Нет проектов</div>
      </div>
    </div>

    <div v-if="!hideProjects" class="sidebar-section">
      <div class="section-header">
        <h3>Chat:</h3>
        <button
          @click="createChat"
          class="add-btn"
          :disabled="!currentProjectId"
          title="Создать чат"
        >
          +
        </button>
      </div>
      <div class="items-list">
        <div
          v-for="chat in currentProjectChats"
          :key="chat.id"
          :class="['item', { active: chat.id === currentChatId }]"
          @click="selectChat(chat.id)"
        >
          {{ chat.name }}
        </div>
        <div v-if="!currentProjectId" class="empty-state">Выберите проект</div>
        <div v-else-if="currentProjectChats.length === 0" class="empty-state">Нет чатов</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'
import { onMounted } from 'vue'

defineProps<{
  hideProjects?: boolean
}>()

const store = useAppStore()
const { projects, currentProjectId, currentProjectChats, currentChatId } = storeToRefs(store)

onMounted(async () => {
  await store.loadProjects()
  await store.loadChats()
})

function selectProject(projectId: string) {
  store.selectProject(projectId)
}

function selectChat(chatId: string) {
  store.selectChat(chatId)
}

function createProject() {
  const name = prompt('Название проекта:', 'Шагомер на мк')
  if (name) {
    store.createNewProject(name)
  }
}

function createChat() {
  if (!currentProjectId.value) return
  const name = prompt('Название чата:', 'Математический анализ')
  if (name) {
    store.createNewChat(currentProjectId.value, name)
  }
}
</script>

<style scoped>
.sidebar {
  width: 280px;
  height: 100vh;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.logo-text {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.sidebar-navigation {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  gap: 4px;
  border-bottom: 1px solid #e0e0e0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  text-decoration: none;
  color: #666;
  font-size: 14px;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-item:hover {
  background: #f5f5f5;
  color: #333;
}

.nav-item.router-link-active {
  background: #e8f0fe;
  color: #1967d2;
  font-weight: 500;
}

.nav-icon-svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  min-height: 0;
}

.sidebar-section:last-child {
  flex: 1;
  border-bottom: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin: 0;
}

.add-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  color: #666;
  transition: all 0.2s;
}

.add-btn:hover:not(:disabled) {
  background: #e0e0e0;
  color: #333;
}

.add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  min-height: 0;
}

.item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item:hover {
  background: #f5f5f5;
}

.item.active {
  background: #e8f0fe;
  color: #1967d2;
  font-weight: 500;
}

.empty-state {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
}
</style>

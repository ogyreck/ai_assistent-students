<template>
  <div class="main-view">
    <Sidebar />
    <ChatView v-if="currentChatId" />
    <ProjectDocuments v-else-if="currentProjectId" />
    <div v-else class="empty-state">
      <p>Выберите проект чтобы начать работу</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import Sidebar from '@/components/Sidebar.vue'
import ChatView from '@/components/ChatView.vue'
import ProjectDocuments from '@/components/ProjectDocuments.vue'

const store = useAppStore()
const currentChatId = computed(() => store.currentChatId)
const currentProjectId = computed(() => store.currentProjectId)
</script>

<style scoped>
.main-view {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #999;
}

.empty-state p {
  margin: 0;
  font-size: 18px;
}
</style>

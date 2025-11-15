<template>
  <div class="main-view">
    <Sidebar />
    <ChatView v-if="currentChatId" />
    <ProjectDocuments v-else-if="currentProjectId" />
    <FilesList v-else />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import Sidebar from '@/components/Sidebar.vue'
import ChatView from '@/components/ChatView.vue'
import ProjectDocuments from '@/components/ProjectDocuments.vue'
import FilesList from '@/components/FilesList.vue'

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
</style>

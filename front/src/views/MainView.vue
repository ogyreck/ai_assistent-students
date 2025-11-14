<template>
  <div class="main-view">
    <Sidebar />
    <ChatView />
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
import ChatView from '@/components/ChatView.vue'
</script>

<style scoped>
.main-view {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>

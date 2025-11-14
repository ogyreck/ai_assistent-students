<template>
  <div class="profile-view">
    <Sidebar :hide-projects="true" />
    <div class="profile-container">
      <header class="profile-header">
        <h1>Личный кабинет</h1>
      </header>

      <div class="profile-content">
      <!-- Avatar Section -->
      <section class="avatar-section">
        <AvatarUpload />
      </section>

      <!-- Calendar Section -->
      <section class="calendar-section">
        <h2>Календарь задач</h2>
        <CalendarTask />
      </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '../components/Sidebar.vue'
import AvatarUpload from '../components/profile/AvatarUpload.vue'
import CalendarTask from '../components/profile/CalendarTask.vue'
</script>

<style scoped>
.profile-view {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.profile-container {
  flex: 1;
  padding: 30px;
  overflow: hidden;
  background: linear-gradient(135deg, #a8c0d8 0%, #f4d89a 35%, #f9b26d 70%, #ff8c61 100%);
  background-attachment: fixed;
  display: flex;
  flex-direction: column;
}

.profile-header {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.profile-header h1 {
  font-size: 1.75rem;
  color: #333;
  margin: 0;
  font-weight: 600;
}

.profile-content {
  display: grid;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.avatar-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.calendar-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.calendar-section h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

@media (min-width: 1024px) {
  .profile-content {
    grid-template-columns: 300px 1fr;
  }

  .avatar-section {
    grid-column: 1;
  }

  .calendar-section {
    grid-column: 2;
  }
}
</style>

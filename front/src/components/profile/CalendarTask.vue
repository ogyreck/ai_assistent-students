<template>
  <div class="calendar-task">
    <div class="calendar-header">
      <div class="month-selector">
        <button @click="previousMonth" class="nav-btn">&lt;</button>
        <h3>{{ currentMonthYear }}</h3>
        <button @click="nextMonth" class="nav-btn">&gt;</button>
      </div>
      <button @click="() => openNewTaskModal()" class="add-task-btn">+ Добавить задачу</button>
    </div>

    <div class="calendar-grid">
      <div class="weekday-header">
        <div v-for="day in weekDays" :key="day" class="weekday">{{ day }}</div>
      </div>

      <div class="days-grid">
        <div
          v-for="day in calendarDays"
          :key="day.date"
          :class="['day-cell', {
            'other-month': !day.isCurrentMonth,
            'today': day.isToday,
            'has-tasks': day.tasks.length > 0
          }]"
          @click="selectDay(day)"
        >
          <div class="day-number">{{ day.dayNumber }}</div>
          <div v-if="day.tasks.length > 0" class="tasks-list">
            <div
              v-for="task in day.tasks.slice(0, 2)"
              :key="task.id"
              class="task-item"
              @click.stop="editTask(task)"
            >
              {{ task.title }}
            </div>
            <div v-if="day.tasks.length > 2" class="more-tasks">
              +{{ day.tasks.length - 2 }} ещё
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>{{ editingTask ? 'Редактировать задачу' : 'Новая задача' }}</h3>

        <form @submit.prevent="saveTask">
          <div class="form-group">
            <label>Дата</label>
            <input
              v-model="taskForm.date"
              type="date"
              required
            />
          </div>

          <div class="form-group">
            <label>Время</label>
            <input
              v-model="taskForm.time"
              type="time"
              required
            />
          </div>

          <div class="form-group">
            <label>Название задачи</label>
            <input
              v-model="taskForm.title"
              type="text"
              required
              placeholder="Введите название"
            />
          </div>

          <div class="form-group">
            <label>Описание</label>
            <textarea
              v-model="taskForm.description"
              rows="3"
              placeholder="Описание задачи (необязательно)"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="submit" class="save-btn">Сохранить</button>
            <button type="button" @click="closeModal" class="cancel-btn">
              Отмена
            </button>
            <button
              v-if="editingTask"
              type="button"
              @click="deleteTask"
              class="delete-btn"
            >
              Удалить
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import apiService from '@/services/api'

interface Task {
  id: string
  title: string
  description?: string
  date: string
  time: string
}

interface CalendarDay {
  date: string
  dayNumber: number
  isCurrentMonth: boolean
  isToday: boolean
  tasks: Task[]
}

const currentDate = ref(new Date())
const showModal = ref(false)
const editingTask = ref<Task | null>(null)
const selectedDate = ref<string>('')

const tasks = ref<Task[]>([])

onMounted(async () => {
  try {
    const data = await apiService.getTasks()
    tasks.value = data
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
})

const taskForm = reactive<Omit<Task, 'id'>>({
  title: '',
  description: '',
  date: '',
  time: '09:00',
})

const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const currentMonthYear = computed(() => {
  return currentDate.value.toLocaleDateString('ru-RU', {
    month: 'long',
    year: 'numeric',
  })
})

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  const firstDayWeekday = firstDay.getDay() === 0 ? 7 : firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const days: CalendarDay[] = []

  // Previous month days
  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = firstDayWeekday - 1; i > 0; i--) {
    const date = new Date(year, month - 1, prevMonthLastDay - i + 1)
    const dateStr = date.toISOString().split('T')[0]!
    days.push({
      date: dateStr,
      dayNumber: prevMonthLastDay - i + 1,
      isCurrentMonth: false,
      isToday: false,
      tasks: getTasksForDate(dateStr),
    })
  }

  // Current month days
  const today = new Date().toISOString().split('T')[0]!
  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i)
    const dateStr = date.toISOString().split('T')[0]!
    days.push({
      date: dateStr,
      dayNumber: i,
      isCurrentMonth: true,
      isToday: dateStr === today,
      tasks: getTasksForDate(dateStr),
    })
  }

  // Next month days
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(year, month + 1, i)
    const dateStr = date.toISOString().split('T')[0]!
    days.push({
      date: dateStr,
      dayNumber: i,
      isCurrentMonth: false,
      isToday: false,
      tasks: getTasksForDate(dateStr),
    })
  }

  return days
})

function getTasksForDate(date: string): Task[] {
  return tasks.value.filter(task => task.date === date)
}

function previousMonth() {
  currentDate.value = new Date(
    currentDate.value.getFullYear(),
    currentDate.value.getMonth() - 1,
    1
  )
}

function nextMonth() {
  currentDate.value = new Date(
    currentDate.value.getFullYear(),
    currentDate.value.getMonth() + 1,
    1
  )
}

function selectDay(day: CalendarDay) {
  if (!day.isCurrentMonth) return
  selectedDate.value = day.date
  openNewTaskModal(day.date)
}

function openNewTaskModal(date?: string) {
  taskForm.title = ''
  taskForm.description = ''
  taskForm.date = date || selectedDate.value || new Date().toISOString().split('T')[0]!
  taskForm.time = '09:00'
  editingTask.value = null
  showModal.value = true
}

function editTask(task: Task) {
  taskForm.title = task.title
  taskForm.description = task.description || ''
  taskForm.date = task.date
  taskForm.time = task.time
  editingTask.value = task
  showModal.value = true
}

async function saveTask() {
  if (!taskForm.title || !taskForm.date || !taskForm.time) return

  try {
    if (editingTask.value) {
      // Update existing task
      const updatedTask = await apiService.updateTask(editingTask.value.id, {
        id: editingTask.value.id,
        title: taskForm.title,
        description: taskForm.description,
        date: taskForm.date,
        time: taskForm.time,
      })
      const index = tasks.value.findIndex(t => t.id === editingTask.value!.id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
    } else {
      // Create new task
      const newTask = await apiService.createTask({
        id: Date.now().toString(),
        title: taskForm.title,
        description: taskForm.description,
        date: taskForm.date,
        time: taskForm.time,
      })
      tasks.value.push(newTask)
    }

    closeModal()
  } catch (error) {
    console.error('Error saving task:', error)
  }
}

async function deleteTask() {
  if (!editingTask.value) return

  try {
    await apiService.deleteTask(editingTask.value.id)
    tasks.value = tasks.value.filter(t => t.id !== editingTask.value!.id)

    closeModal()
  } catch (error) {
    console.error('Error deleting task:', error)
  }
}

function closeModal() {
  showModal.value = false
  editingTask.value = null
}
</script>

<style scoped>
.calendar-task {
  width: 100%;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.month-selector {
  display: flex;
  align-items: center;
  gap: 20px;
}

.month-selector h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
  color: #333;
  text-transform: capitalize;
  min-width: 200px;
  text-align: center;
}

.nav-btn {
  background: transparent;
  border: 1px solid #ddd;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.add-task-btn {
  background: transparent;
  border: 1px solid #333;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.add-task-btn:hover {
  background: #333;
  color: white;
}

.calendar-grid {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
}

.weekday {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: white;
}

.day-cell {
  min-height: 100px;
  padding: 8px;
  border-right: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.day-cell:hover {
  background: #f9f9f9;
}

.day-cell.other-month {
  background: #fafafa;
  color: #ccc;
}

.day-cell.other-month:hover {
  background: #f5f5f5;
}

.day-cell.today {
  background: #fff8e1;
}

.day-cell.today .day-number {
  background: #333;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.other-month .day-number {
  color: #ccc;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.task-item {
  background: #e3f2fd;
  border-left: 3px solid #2196F3;
  padding: 4px 6px;
  border-radius: 2px;
  font-size: 11px;
  color: #1976D2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition: all 0.2s;
}

.task-item:hover {
  background: #bbdefb;
}

.more-tasks {
  font-size: 10px;
  color: #999;
  padding: 2px 6px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #555;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn,
.cancel-btn,
.delete-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.save-btn {
  background: #333;
  color: white;
  flex: 1;
}

.save-btn:hover {
  background: #000;
}

.cancel-btn {
  background: #f5f5f5;
  color: #333;
  flex: 1;
  border: 1px solid #ddd;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.delete-btn {
  background: #f44336;
  color: white;
}

.delete-btn:hover {
  background: #d32f2f;
}
</style>

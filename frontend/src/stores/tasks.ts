import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/tasks'
import type { Task, TaskCreate, TaskUpdate } from '@/types'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(userStoryId?: string) {
    loading.value = true
    error.value = null
    try {
      tasks.value = await api.listTasks(userStoryId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: TaskCreate): Promise<Task> {
    const task = await api.createTask(payload)
    tasks.value.push(task)
    return task
  }

  async function update(id: string, payload: TaskUpdate): Promise<Task> {
    const task = await api.updateTask(id, payload)
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) tasks.value[idx] = task
    return task
  }

  async function remove(id: string) {
    await api.deleteTask(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  return { tasks, loading, error, fetchAll, create, update, remove }
})

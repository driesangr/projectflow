import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/tasks'
import type { Task, TaskCreate, TaskUpdate } from '@/types'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const current = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getTask(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load task'
    } finally {
      loading.value = false
    }
  }

  async function fetchAll(userStoryId?: string, bugId?: string) {
    loading.value = true
    error.value = null
    try {
      tasks.value = await api.listTasks(userStoryId, bugId)
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
    if (current.value?.id === id) current.value = task
    return task
  }

  async function remove(id: string) {
    await api.deleteTask(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  async function reorder(items: { id: string; position: number }[]) {
    await api.reorderTasks(items)
  }

  return { tasks, current, loading, error, fetchOne, fetchAll, create, update, remove, reorder }
})

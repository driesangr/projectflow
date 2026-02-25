import apiClient from './client'
import type { Task, TaskCreate, TaskUpdate } from '@/types'

export async function listTasks(userStoryId?: string, bugId?: string): Promise<Task[]> {
  const params: Record<string, string> = {}
  if (userStoryId) params.user_story_id = userStoryId
  if (bugId) params.bug_id = bugId
  const { data } = await apiClient.get<Task[]>('/tasks/', { params })
  return data
}

export async function getTask(id: string): Promise<Task> {
  const { data } = await apiClient.get<Task>(`/tasks/${id}`)
  return data
}

export async function createTask(payload: TaskCreate): Promise<Task> {
  const { data } = await apiClient.post<Task>('/tasks/', payload)
  return data
}

export async function updateTask(id: string, payload: TaskUpdate): Promise<Task> {
  const { data } = await apiClient.put<Task>(`/tasks/${id}`, payload)
  return data
}

export async function deleteTask(id: string): Promise<void> {
  await apiClient.delete(`/tasks/${id}`)
}

export async function reorderTasks(items: { id: string; position: number }[]): Promise<void> {
  await apiClient.patch('/tasks/reorder', items)
}

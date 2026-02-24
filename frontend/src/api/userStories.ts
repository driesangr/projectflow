import apiClient from './client'
import type { UserStory, UserStoryCreate, UserStoryUpdate } from '@/types'

export async function listUserStories(deliverableId?: string, sprintId?: string, projectId?: string): Promise<UserStory[]> {
  const params: Record<string, string> = {}
  if (deliverableId) params.deliverable_id = deliverableId
  if (sprintId) params.sprint_id = sprintId
  if (projectId) params.project_id = projectId
  const { data } = await apiClient.get<UserStory[]>('/user-stories/', { params })
  return data
}

export async function getUserStory(id: string): Promise<UserStory> {
  const { data } = await apiClient.get<UserStory>(`/user-stories/${id}`)
  return data
}

export async function createUserStory(payload: UserStoryCreate): Promise<UserStory> {
  const { data } = await apiClient.post<UserStory>('/user-stories/', payload)
  return data
}

export async function updateUserStory(id: string, payload: UserStoryUpdate): Promise<UserStory> {
  const { data } = await apiClient.put<UserStory>(`/user-stories/${id}`, payload)
  return data
}

export async function deleteUserStory(id: string): Promise<void> {
  await apiClient.delete(`/user-stories/${id}`)
}

export async function reorderUserStories(items: { id: string; position: number }[]): Promise<void> {
  await apiClient.patch('/user-stories/reorder', items)
}

export async function setBulkStoryValues(
  items: { id: string; business_value?: number | null; sprint_value?: number | null }[],
): Promise<void> {
  await apiClient.patch('/user-stories/bulk-values', items)
}

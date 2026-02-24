import apiClient from './client'
import type { Topic, TopicCreate, TopicUpdate } from '@/types'

export async function listTopics(projectId?: string): Promise<Topic[]> {
  const params = projectId ? { project_id: projectId } : {}
  const { data } = await apiClient.get<Topic[]>('/topics/', { params })
  return data
}

export async function getTopic(id: string): Promise<Topic> {
  const { data } = await apiClient.get<Topic>(`/topics/${id}`)
  return data
}

export async function createTopic(payload: TopicCreate): Promise<Topic> {
  const { data } = await apiClient.post<Topic>('/topics/', payload)
  return data
}

export async function updateTopic(id: string, payload: TopicUpdate): Promise<Topic> {
  const { data } = await apiClient.put<Topic>(`/topics/${id}`, payload)
  return data
}

export async function deleteTopic(id: string): Promise<void> {
  await apiClient.delete(`/topics/${id}`)
}

export async function reorderTopics(items: { id: string; position: number }[]): Promise<void> {
  await apiClient.patch('/topics/reorder', items)
}

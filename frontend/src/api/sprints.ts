import apiClient from './client'
import type { Sprint, SprintCreate, SprintUpdate } from '@/types'

export async function listSprints(projectId?: string): Promise<Sprint[]> {
  const params = projectId ? { project_id: projectId } : {}
  const { data } = await apiClient.get<Sprint[]>('/sprints/', { params })
  return data
}

export async function getSprint(id: string): Promise<Sprint> {
  const { data } = await apiClient.get<Sprint>(`/sprints/${id}`)
  return data
}

export async function createSprint(payload: SprintCreate): Promise<Sprint> {
  const { data } = await apiClient.post<Sprint>('/sprints/', payload)
  return data
}

export async function updateSprint(id: string, payload: SprintUpdate): Promise<Sprint> {
  const { data } = await apiClient.put<Sprint>(`/sprints/${id}`, payload)
  return data
}

export async function deleteSprint(id: string): Promise<void> {
  await apiClient.delete(`/sprints/${id}`)
}

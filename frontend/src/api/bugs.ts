import apiClient from './client'
import type { Bug, BugCreate, BugUpdate } from '@/types'

export async function listBugs(deliverableId?: string, sprintId?: string, projectId?: string): Promise<Bug[]> {
  const params: Record<string, string> = {}
  if (deliverableId) params.deliverable_id = deliverableId
  if (sprintId) params.sprint_id = sprintId
  if (projectId) params.project_id = projectId
  const { data } = await apiClient.get<Bug[]>('/bugs/', { params })
  return data
}

export async function getBug(id: string): Promise<Bug> {
  const { data } = await apiClient.get<Bug>(`/bugs/${id}`)
  return data
}

export async function createBug(payload: BugCreate): Promise<Bug> {
  const { data } = await apiClient.post<Bug>('/bugs/', payload)
  return data
}

export async function updateBug(id: string, payload: BugUpdate): Promise<Bug> {
  const { data } = await apiClient.put<Bug>(`/bugs/${id}`, payload)
  return data
}

export async function deleteBug(id: string): Promise<void> {
  await apiClient.delete(`/bugs/${id}`)
}

export async function reorderBugs(items: { id: string; position: number }[]): Promise<void> {
  await apiClient.patch('/bugs/reorder', items)
}

export async function duplicateBug(
  id: string,
  payload: { task_ids: string[] },
): Promise<Bug> {
  const { data } = await apiClient.post<Bug>(`/bugs/${id}/duplicate`, payload)
  return data
}

export async function setBulkBugValues(
  items: { id: string; business_value?: number | null; sprint_value?: number | null }[],
): Promise<void> {
  await apiClient.patch('/bugs/bulk-values', items)
}

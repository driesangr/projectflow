import apiClient from './client'
import type { Deliverable, DeliverableCreate, DeliverableUpdate } from '@/types'

export async function listDeliverables(topicId?: string): Promise<Deliverable[]> {
  const params = topicId ? { topic_id: topicId } : {}
  const { data } = await apiClient.get<Deliverable[]>('/deliverables/', { params })
  return data
}

export async function getDeliverable(id: string): Promise<Deliverable> {
  const { data } = await apiClient.get<Deliverable>(`/deliverables/${id}`)
  return data
}

export async function createDeliverable(payload: DeliverableCreate): Promise<Deliverable> {
  const { data } = await apiClient.post<Deliverable>('/deliverables/', payload)
  return data
}

export async function updateDeliverable(id: string, payload: DeliverableUpdate): Promise<Deliverable> {
  const { data } = await apiClient.put<Deliverable>(`/deliverables/${id}`, payload)
  return data
}

export async function deleteDeliverable(id: string): Promise<void> {
  await apiClient.delete(`/deliverables/${id}`)
}

export async function reorderDeliverables(items: { id: string; position: number }[]): Promise<void> {
  await apiClient.patch('/deliverables/reorder', items)
}

export async function duplicateDeliverable(id: string): Promise<Deliverable> {
  const { data } = await apiClient.post<Deliverable>(`/deliverables/${id}/duplicate`)
  return data
}

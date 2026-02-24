import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/deliverables'
import type { Deliverable, DeliverableCreate, DeliverableUpdate } from '@/types'

export const useDeliverablesStore = defineStore('deliverables', () => {
  const deliverables = ref<Deliverable[]>([])
  const current = ref<Deliverable | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(topicId?: string) {
    loading.value = true
    error.value = null
    try {
      deliverables.value = await api.listDeliverables(topicId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load deliverables'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getDeliverable(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load deliverable'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: DeliverableCreate): Promise<Deliverable> {
    const deliverable = await api.createDeliverable(payload)
    deliverables.value.push(deliverable)
    return deliverable
  }

  async function update(id: string, payload: DeliverableUpdate): Promise<Deliverable> {
    const deliverable = await api.updateDeliverable(id, payload)
    const idx = deliverables.value.findIndex((d) => d.id === id)
    if (idx !== -1) deliverables.value[idx] = deliverable
    if (current.value?.id === id) current.value = deliverable
    return deliverable
  }

  async function remove(id: string) {
    await api.deleteDeliverable(id)
    deliverables.value = deliverables.value.filter((d) => d.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function reorder(items: { id: string; position: number }[]) {
    await api.reorderDeliverables(items)
  }

  async function duplicate(id: string): Promise<Deliverable> {
    const copy = await api.duplicateDeliverable(id)
    deliverables.value.push(copy)
    return copy
  }

  return { deliverables, current, loading, error, fetchAll, fetchOne, create, update, remove, reorder, duplicate }
})

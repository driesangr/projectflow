import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/sprints'
import type { Sprint, SprintCreate, SprintUpdate } from '@/types'

export const useSprintsStore = defineStore('sprints', () => {
  const sprints = ref<Sprint[]>([])
  const allSprints = ref<Sprint[]>([])
  const current = ref<Sprint | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAllGlobal() {
    try {
      allSprints.value = await api.listSprints()
    } catch {
      // silent – Sidebar zeigt einfach nichts
    }
  }

  async function fetchAll(projectId?: string) {
    loading.value = true
    error.value = null
    try {
      sprints.value = await api.listSprints(projectId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load sprints'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getSprint(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load sprint'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: SprintCreate): Promise<Sprint> {
    const sprint = await api.createSprint(payload)
    sprints.value.push(sprint)
    return sprint
  }

  async function update(id: string, payload: SprintUpdate): Promise<Sprint> {
    const sprint = await api.updateSprint(id, payload)
    const idx = sprints.value.findIndex((s) => s.id === id)
    if (idx !== -1) sprints.value[idx] = sprint
    if (current.value?.id === id) current.value = sprint
    return sprint
  }

  async function remove(id: string) {
    await api.deleteSprint(id)
    sprints.value = sprints.value.filter((s) => s.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { sprints, allSprints, current, loading, error, fetchAllGlobal, fetchAll, fetchOne, create, update, remove }
})

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/bugs'
import type { Bug, BugCreate, BugUpdate } from '@/types'

export const useBugsStore = defineStore('bugs', () => {
  const bugs = ref<Bug[]>([])
  const current = ref<Bug | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(deliverableId?: string, sprintId?: string, projectId?: string) {
    loading.value = true
    error.value = null
    try {
      bugs.value = await api.listBugs(deliverableId, sprintId, projectId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load bugs'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getBug(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load bug'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: BugCreate): Promise<Bug> {
    const bug = await api.createBug(payload)
    bugs.value.push(bug)
    return bug
  }

  async function update(id: string, payload: BugUpdate): Promise<Bug> {
    const bug = await api.updateBug(id, payload)
    const idx = bugs.value.findIndex((b) => b.id === id)
    if (idx !== -1) bugs.value[idx] = bug
    if (current.value?.id === id) current.value = bug
    return bug
  }

  async function remove(id: string) {
    await api.deleteBug(id)
    bugs.value = bugs.value.filter((b) => b.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function reorder(items: { id: string; position: number }[]) {
    await api.reorderBugs(items)
  }

  async function duplicate(id: string, taskIds: string[]): Promise<Bug> {
    const bug = await api.duplicateBug(id, { task_ids: taskIds })
    bugs.value.push(bug)
    return bug
  }

  async function setValues(
    items: { id: string; business_value?: number | null; sprint_value?: number | null }[],
  ) {
    await api.setBulkBugValues(items)
    for (const item of items) {
      const bug = bugs.value.find((b) => b.id === item.id)
      if (bug) {
        if (item.business_value !== undefined) bug.business_value = item.business_value ?? null
        if (item.sprint_value !== undefined) bug.sprint_value = item.sprint_value ?? null
      }
      if (current.value?.id === item.id) {
        if (item.business_value !== undefined) current.value.business_value = item.business_value ?? null
        if (item.sprint_value !== undefined) current.value.sprint_value = item.sprint_value ?? null
      }
    }
  }

  return { bugs, current, loading, error, fetchAll, fetchOne, create, update, remove, reorder, duplicate, setValues }
})

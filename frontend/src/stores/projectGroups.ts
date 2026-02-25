import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/projectGroups'
import type { ProjectGroup, ProjectGroupCreate, ProjectGroupUpdate } from '@/types'

export const useProjectGroupsStore = defineStore('projectGroups', () => {
  const projectGroups = ref<ProjectGroup[]>([])
  const current = ref<ProjectGroup | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      projectGroups.value = await api.listProjectGroups()
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load project groups'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getProjectGroup(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load project group'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ProjectGroupCreate): Promise<ProjectGroup> {
    const group = await api.createProjectGroup(payload)
    projectGroups.value.unshift(group)
    return group
  }

  async function update(id: string, payload: ProjectGroupUpdate): Promise<ProjectGroup> {
    const group = await api.updateProjectGroup(id, payload)
    const idx = projectGroups.value.findIndex((g) => g.id === id)
    if (idx !== -1) projectGroups.value[idx] = group
    if (current.value?.id === id) current.value = group
    return group
  }

  async function remove(id: string) {
    await api.deleteProjectGroup(id)
    projectGroups.value = projectGroups.value.filter((g) => g.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { projectGroups, current, loading, error, fetchAll, fetchOne, create, update, remove }
})

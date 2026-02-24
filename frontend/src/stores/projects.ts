import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/projects'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      projects.value = await api.listProjects()
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load projects'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getProject(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load project'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ProjectCreate): Promise<Project> {
    const project = await api.createProject(payload)
    projects.value.unshift(project)
    return project
  }

  async function update(id: string, payload: ProjectUpdate): Promise<Project> {
    const project = await api.updateProject(id, payload)
    const idx = projects.value.findIndex((p) => p.id === id)
    if (idx !== -1) projects.value[idx] = project
    if (current.value?.id === id) current.value = project
    return project
  }

  async function remove(id: string) {
    await api.deleteProject(id)
    projects.value = projects.value.filter((p) => p.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { projects, current, loading, error, fetchAll, fetchOne, create, update, remove }
})

import apiClient from './client'
import type { ProjectGroup, ProjectGroupCreate, ProjectGroupUpdate } from '@/types'

export async function listProjectGroups(): Promise<ProjectGroup[]> {
  const { data } = await apiClient.get<ProjectGroup[]>('/project-groups/')
  return data
}

export async function getProjectGroup(id: string): Promise<ProjectGroup> {
  const { data } = await apiClient.get<ProjectGroup>(`/project-groups/${id}`)
  return data
}

export async function createProjectGroup(payload: ProjectGroupCreate): Promise<ProjectGroup> {
  const { data } = await apiClient.post<ProjectGroup>('/project-groups/', payload)
  return data
}

export async function updateProjectGroup(id: string, payload: ProjectGroupUpdate): Promise<ProjectGroup> {
  const { data } = await apiClient.put<ProjectGroup>(`/project-groups/${id}`, payload)
  return data
}

export async function deleteProjectGroup(id: string): Promise<void> {
  await apiClient.delete(`/project-groups/${id}`)
}

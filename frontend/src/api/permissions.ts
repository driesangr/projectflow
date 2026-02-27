import apiClient from './client'
import type { RolePermission, RolePermissionUpdate, ProjectRole, ArtifactType } from '@/types'

export async function listPermissions(role?: ProjectRole): Promise<RolePermission[]> {
  const params = role ? { role } : {}
  const r = await apiClient.get('/admin/permissions/', { params })
  return r.data
}

export async function getPermission(role: ProjectRole, artifactType: ArtifactType): Promise<RolePermission> {
  const r = await apiClient.get(`/admin/permissions/${role}/${artifactType}`)
  return r.data
}

export async function upsertPermission(
  role: ProjectRole,
  artifactType: ArtifactType,
  payload: RolePermissionUpdate,
): Promise<RolePermission> {
  const r = await apiClient.put(`/admin/permissions/${role}/${artifactType}`, payload)
  return r.data
}

export async function deletePermission(role: ProjectRole, artifactType: ArtifactType): Promise<void> {
  await apiClient.delete(`/admin/permissions/${role}/${artifactType}`)
}

import apiClient from './client'
import type { UserResponse, UserCreate, UserUpdate, UserPublic, MembershipResponse, MembershipCreate, MembershipUpdate } from '@/types'

// ── Users ─────────────────────────────────────────────────────────────────────

export async function listUsers(): Promise<UserResponse[]> {
  const r = await apiClient.get('/users/')
  return r.data
}

export async function getUser(id: string): Promise<UserResponse> {
  const r = await apiClient.get(`/users/${id}`)
  return r.data
}

export async function createUser(payload: UserCreate): Promise<UserResponse> {
  const r = await apiClient.post('/users/', payload)
  return r.data
}

export async function updateUser(id: string, payload: UserUpdate): Promise<UserResponse> {
  const r = await apiClient.put(`/users/${id}`, payload)
  return r.data
}

export async function deleteUser(id: string): Promise<void> {
  await apiClient.delete(`/users/${id}`)
}

// ── Memberships ───────────────────────────────────────────────────────────────

export async function listPotentialMembers(projectId: string): Promise<UserPublic[]> {
  const r = await apiClient.get(`/projects/${projectId}/members/potential`)
  return r.data
}

export async function listMembers(projectId: string): Promise<MembershipResponse[]> {
  const r = await apiClient.get(`/projects/${projectId}/members/`)
  return r.data
}

export async function addMember(projectId: string, payload: MembershipCreate): Promise<MembershipResponse> {
  const r = await apiClient.post(`/projects/${projectId}/members/`, payload)
  return r.data
}

export async function updateMember(projectId: string, userId: string, payload: MembershipUpdate): Promise<MembershipResponse> {
  const r = await apiClient.put(`/projects/${projectId}/members/${userId}`, payload)
  return r.data
}

export async function removeMember(projectId: string, userId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/members/${userId}`)
}

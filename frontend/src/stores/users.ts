import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listUsers, createUser, updateUser, deleteUser } from '@/api/users'
import type { UserResponse, UserCreate, UserUpdate } from '@/types'

export const useUsersStore = defineStore('users', () => {
  const users = ref<UserResponse[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      users.value = await listUsers()
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Laden der User'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: UserCreate): Promise<UserResponse | null> {
    try {
      const user = await createUser(payload)
      users.value.push(user)
      return user
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Anlegen'
      return null
    }
  }

  async function update(id: string, payload: UserUpdate): Promise<UserResponse | null> {
    try {
      const updated = await updateUser(id, payload)
      const idx = users.value.findIndex(u => u.id === id)
      if (idx !== -1) users.value[idx] = updated
      return updated
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Speichern'
      return null
    }
  }

  async function remove(id: string): Promise<boolean> {
    try {
      await deleteUser(id)
      users.value = users.value.filter(u => u.id !== id)
      return true
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Löschen'
      return false
    }
  }

  return { users, loading, error, fetchAll, create, update, remove }
})

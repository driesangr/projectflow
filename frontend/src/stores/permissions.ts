import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { listPermissions, upsertPermission } from '@/api/permissions'
import type { RolePermission, RolePermissionUpdate, ProjectRole, ArtifactType } from '@/types'

// ── State ─────────────────────────────────────────────────────────────────────

export const usePermissionsStore = defineStore('permissions', () => {
  // All loaded permissions, keyed by "role:artifact_type"
  const permissions = ref<Map<string, RolePermission>>(new Map())
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ── Actions ──────────────────────────────────────────────────────────────────

  async function fetchByRole(role: ProjectRole): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const perms = await listPermissions(role)
      for (const p of perms) {
        permissions.value.set(_key(p.project_role, p.artifact_type), p)
      }
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Laden der Berechtigungen'
    } finally {
      loading.value = false
    }
  }

  async function updatePermission(
    role: ProjectRole,
    artifactType: ArtifactType,
    payload: RolePermissionUpdate,
  ): Promise<RolePermission | null> {
    try {
      const updated = await upsertPermission(role, artifactType, payload)
      permissions.value.set(_key(role, artifactType), updated)
      return updated
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Fehler beim Speichern'
      return null
    }
  }

  // ── Getters ──────────────────────────────────────────────────────────────────

  const permissionsByRole = computed(() => (role: ProjectRole): RolePermission[] => {
    return Array.from(permissions.value.values()).filter(p => p.project_role === role)
  })

  function permissionFor(role: ProjectRole, artifactType: ArtifactType): RolePermission | undefined {
    return permissions.value.get(_key(role, artifactType))
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────

  function _key(role: ProjectRole, artifactType: ArtifactType): string {
    return `${role}:${artifactType}`
  }

  return {
    permissions,
    loading,
    error,
    fetchByRole,
    updatePermission,
    permissionsByRole,
    permissionFor,
  }
})

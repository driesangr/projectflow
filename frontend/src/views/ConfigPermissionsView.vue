<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { usePermissionsStore } from '@/stores/permissions'
import PermissionsTreeNode from '@/components/permissions/PermissionsTreeNode.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import type { ProjectRole, ArtifactType, RolePermissionUpdate } from '@/types'

const store = usePermissionsStore()

const ROLES: { value: ProjectRole; label: string }[] = [
  { value: 'owner',   label: 'Owner' },
  { value: 'manager', label: 'Manager' },
  { value: 'member',  label: 'Member' },
  { value: 'viewer',  label: 'Viewer' },
]

const ARTIFACT_TYPES: ArtifactType[] = [
  'project_group',
  'project',
  'topic',
  'deliverable',
  'user_story',
  'task',
]

const selectedRole = ref<ProjectRole>('owner')

async function loadRole(role: ProjectRole) {
  await store.fetchByRole(role)
}

watch(selectedRole, (role) => loadRole(role))

onMounted(() => loadRole(selectedRole.value))

async function handleUpdate(role: ProjectRole, artifactType: ArtifactType, payload: RolePermissionUpdate) {
  await store.updatePermission(role, artifactType, payload)
}
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold mb-1">Granulare Berechtigungen</h1>
    <p class="text-sm text-gray-500 mb-6">
      Konfiguriere für jede Projektrolle, welche Aktionen auf welchem Artefakt-Typ erlaubt sind.
    </p>

    <!-- Rollen-Selector -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">Projektrolle</label>
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="r in ROLES"
          :key="r.value"
          class="btn btn-sm"
          :class="selectedRole === r.value ? 'btn-primary' : 'btn-outline'"
          @click="selectedRole = r.value"
        >
          {{ r.label }}
        </button>
      </div>
    </div>

    <ErrorBanner v-if="store.error" :message="store.error" class="mb-4" />

    <LoadingSpinner v-if="store.loading" />

    <!-- Berechtigungs-Baum -->
    <div v-else class="flex flex-col gap-3">
      <PermissionsTreeNode
        v-for="artifactType in ARTIFACT_TYPES"
        :key="artifactType"
        :role="selectedRole"
        :artifact-type="artifactType"
        :permission="store.permissionFor(selectedRole, artifactType)"
        @update="handleUpdate"
      />
    </div>
  </div>
</template>

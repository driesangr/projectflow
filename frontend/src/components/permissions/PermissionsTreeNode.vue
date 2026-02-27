<template>
  <div class="permissions-tree-node">
    <div class="node-header">
      <span class="artifact-label">{{ artifactLabel }}</span>
      <span v-if="!permission" class="badge badge-ghost badge-sm">nicht konfiguriert</span>
      <span v-else-if="!permission.is_explicit" class="badge badge-outline badge-sm">vererbt</span>
      <span v-else class="badge badge-primary badge-sm">explizit</span>
    </div>

    <div v-if="permission" class="permissions-grid">
      <label class="permission-checkbox">
        <input
          type="checkbox"
          :checked="permission.can_read"
          :disabled="saving"
          @change="onChange('can_read', ($event.target as HTMLInputElement).checked)"
        />
        <span>Lesen</span>
      </label>

      <label class="permission-checkbox">
        <input
          type="checkbox"
          :checked="permission.can_write"
          :disabled="saving"
          @change="onChange('can_write', ($event.target as HTMLInputElement).checked)"
        />
        <span>Schreiben</span>
      </label>

      <label class="permission-checkbox">
        <input
          type="checkbox"
          :checked="permission.can_create"
          :disabled="saving"
          @change="onChange('can_create', ($event.target as HTMLInputElement).checked)"
        />
        <span>Erstellen</span>
      </label>

      <label class="permission-checkbox">
        <input
          type="checkbox"
          :checked="permission.can_delete"
          :disabled="saving"
          @change="onChange('can_delete', ($event.target as HTMLInputElement).checked)"
        />
        <span>Löschen</span>
      </label>

      <label class="permission-checkbox inherit">
        <input
          type="checkbox"
          :checked="permission.inherit_to_children"
          :disabled="saving"
          @change="onChange('inherit_to_children', ($event.target as HTMLInputElement).checked)"
        />
        <span>Vererben</span>
      </label>
    </div>

    <div v-else class="no-permission">
      <button class="btn btn-xs btn-outline" :disabled="saving" @click="onCreateDefault">
        Standard anlegen
      </button>
    </div>

    <div v-if="saving" class="saving-indicator">
      <span class="loading loading-spinner loading-xs"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RolePermission, ProjectRole, ArtifactType, RolePermissionUpdate } from '@/types'

// ── Props ────────────────────────────────────────────────────────────────────

const props = defineProps<{
  role: ProjectRole
  artifactType: ArtifactType
  permission: RolePermission | undefined
}>()

// ── Emits ────────────────────────────────────────────────────────────────────

const emit = defineEmits<{
  (e: 'update', role: ProjectRole, artifactType: ArtifactType, payload: RolePermissionUpdate): void
}>()

// ── State ────────────────────────────────────────────────────────────────────

const saving = ref(false)

const ARTIFACT_LABELS: Record<ArtifactType, string> = {
  project_group: 'Projektgruppe',
  project:       'Projekt',
  topic:         'Topic',
  deliverable:   'Deliverable',
  user_story:    'User Story',
  task:          'Task',
}

const artifactLabel = ARTIFACT_LABELS[props.artifactType] ?? props.artifactType

// ── Event-Handler ─────────────────────────────────────────────────────────────

function onChange(field: keyof RolePermissionUpdate, value: boolean) {
  emit('update', props.role, props.artifactType, { [field]: value })
}

function onCreateDefault() {
  emit('update', props.role, props.artifactType, {
    can_read: true,
    can_write: false,
    can_create: false,
    can_delete: false,
    inherit_to_children: false,
  })
}

// Expose saving ref so parent can toggle it if needed
defineExpose({ saving })
</script>

<style scoped>
.permissions-tree-node {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: var(--base-200, #f2f2f2);
  position: relative;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
}

.artifact-label {
  flex: 1;
}

.permissions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.permission-checkbox {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  font-size: 0.8125rem;
}

.permission-checkbox.inherit {
  border-left: 2px solid var(--base-300, #ccc);
  padding-left: 0.5rem;
}

.no-permission {
  display: flex;
  align-items: center;
}

.saving-indicator {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
}
</style>

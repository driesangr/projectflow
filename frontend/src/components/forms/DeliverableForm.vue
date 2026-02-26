<script setup lang="ts">
import { reactive } from 'vue'
import type { Deliverable, DeliverableCreate } from '@/types'

const props = defineProps<{
  topicId?: string
  projectId?: string
  initial?: Partial<Deliverable>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: DeliverableCreate]
  cancel: []
}>()

const form = reactive({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
  epic_points: props.initial?.epic_points ?? null as number | null,
  business_value: props.initial?.business_value ?? null as number | null,
  status: props.initial?.status ?? 'todo' as Deliverable['status'],
  owner_name: props.initial?.owner_name ?? '',
})

function submit() {
  emit('submit', {
    title: form.title,
    description: form.description || null,
    epic_points: form.epic_points,
    business_value: form.business_value,
    status: form.status,
    owner_name: form.owner_name || null,
    topic_id: props.topicId ?? undefined,
    project_id: props.projectId ?? undefined,
  })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label">Title *</label>
      <input v-model="form.title" class="form-input" required placeholder="Deliverable title" />
    </div>
    <div>
      <label class="form-label">Description</label>
      <textarea v-model="form.description" class="form-textarea" placeholder="Optional description" />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Status</label>
        <select v-model="form.status" class="form-select">
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
          <option value="on_hold">On Hold</option>
        </select>
      </div>
      <div>
        <label class="form-label">Epic Points</label>
        <input v-model.number="form.epic_points" type="number" min="0" class="form-input" placeholder="e.g. 8" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Business Value</label>
        <input v-model.number="form.business_value" type="number" min="0" class="form-input" placeholder="0–100" />
      </div>
    </div>
    <div>
      <label class="form-label">Owner</label>
      <input v-model="form.owner_name" class="form-input" placeholder="Owner name" />
    </div>
    <div class="flex justify-end gap-2 pt-2">
      <button type="button" class="btn-secondary" :disabled="loading" @click="emit('cancel')">Cancel</button>
      <button type="submit" class="btn-primary" :disabled="loading || !form.title">
        {{ loading ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </form>
</template>

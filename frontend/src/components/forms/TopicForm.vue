<script setup lang="ts">
import { reactive } from 'vue'
import type { Topic, TopicCreate } from '@/types'

const props = defineProps<{
  projectId: string
  initial?: Partial<Topic>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: TopicCreate]
  cancel: []
}>()

const form = reactive({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
  business_value: props.initial?.business_value ?? null as number | null,
  priority: props.initial?.priority ?? 'medium' as 'high' | 'medium' | 'low',
  planned_start_date: props.initial?.planned_start_date ?? null as string | null,
  planned_end_date: props.initial?.planned_end_date ?? null as string | null,
  owner_name: props.initial?.owner_name ?? '',
})

function submit() {
  const payload: TopicCreate = {
    title: form.title,
    description: form.description || null,
    business_value: form.business_value,
    priority: form.priority,
    planned_start_date: form.planned_start_date || null,
    planned_end_date: form.planned_end_date || null,
    owner_name: form.owner_name || null,
    project_id: props.projectId,
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label">Title *</label>
      <input v-model="form.title" class="form-input" required placeholder="Topic title" />
    </div>
    <div>
      <label class="form-label">Description</label>
      <textarea v-model="form.description" class="form-textarea" placeholder="Optional description" />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Priority</label>
        <select v-model="form.priority" class="form-select">
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <div>
        <label class="form-label">Business Value</label>
        <input v-model.number="form.business_value" type="number" min="0" class="form-input" placeholder="0–100" />
      </div>
    </div>
    <div>
      <label class="form-label">Owner</label>
      <input v-model="form.owner_name" class="form-input" placeholder="Owner name" />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Planned Start</label>
        <input v-model="form.planned_start_date" type="date" class="form-input" />
      </div>
      <div>
        <label class="form-label">Planned End</label>
        <input v-model="form.planned_end_date" type="date" class="form-input" />
      </div>
    </div>
    <div class="flex justify-end gap-2 pt-2">
      <button type="button" class="btn-secondary" :disabled="loading" @click="emit('cancel')">Cancel</button>
      <button type="submit" class="btn-primary" :disabled="loading || !form.title">
        {{ loading ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </form>
</template>

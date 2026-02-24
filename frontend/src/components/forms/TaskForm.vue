<script setup lang="ts">
import { reactive } from 'vue'
import type { Task, TaskCreate } from '@/types'

const props = defineProps<{
  userStoryId: string
  initial?: Partial<Task>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: TaskCreate]
  cancel: []
}>()

const form = reactive({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
  status: props.initial?.status ?? 'todo' as Task['status'],
  effort_hours: props.initial?.effort_hours ?? null as number | null,
  owner_name: props.initial?.owner_name ?? '',
})

function submit() {
  emit('submit', {
    title: form.title,
    description: form.description || null,
    status: form.status,
    effort_hours: form.effort_hours,
    owner_name: form.owner_name || null,
    user_story_id: props.userStoryId,
  })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label">Title *</label>
      <input v-model="form.title" class="form-input" required placeholder="Task title" />
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
        </select>
      </div>
      <div>
        <label class="form-label">Effort (hours)</label>
        <input v-model.number="form.effort_hours" type="number" min="0" step="0.5" class="form-input" placeholder="e.g. 4" />
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

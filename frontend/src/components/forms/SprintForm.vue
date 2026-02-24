<script setup lang="ts">
import { reactive } from 'vue'
import type { Sprint, SprintCreate } from '@/types'

const props = defineProps<{
  projectId: string
  initial?: Partial<Sprint>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: SprintCreate]
  cancel: []
}>()

const form = reactive({
  name: props.initial?.name ?? '',
  goal: props.initial?.goal ?? '',
  start_date: props.initial?.start_date ?? null as string | null,
  end_date: props.initial?.end_date ?? null as string | null,
})

function submit() {
  emit('submit', {
    name: form.name,
    goal: form.goal || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    project_id: props.projectId,
  })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label">Name *</label>
      <input v-model="form.name" class="form-input" required placeholder="Sprint 1" />
    </div>
    <div>
      <label class="form-label">Goal</label>
      <textarea v-model="form.goal" class="form-textarea" placeholder="Sprint goal…" />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Start Date</label>
        <input v-model="form.start_date" type="date" class="form-input" />
      </div>
      <div>
        <label class="form-label">End Date</label>
        <input v-model="form.end_date" type="date" class="form-input" />
      </div>
    </div>
    <div class="flex justify-end gap-2 pt-2">
      <button type="button" class="btn-secondary" :disabled="loading" @click="emit('cancel')">Cancel</button>
      <button type="submit" class="btn-primary" :disabled="loading || !form.name">
        {{ loading ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </form>
</template>

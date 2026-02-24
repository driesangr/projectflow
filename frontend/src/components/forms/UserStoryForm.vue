<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import type { UserStory, UserStoryCreate, Sprint } from '@/types'
import { useSprintsStore } from '@/stores/sprints'

const props = defineProps<{
  deliverableId: string
  projectId: string
  initial?: Partial<UserStory>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: UserStoryCreate]
  cancel: []
}>()

const sprintsStore = useSprintsStore()

onMounted(() => sprintsStore.fetchAll(props.projectId))

const form = reactive({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
  acceptance_criteria: props.initial?.acceptance_criteria ?? '',
  story_points: props.initial?.story_points ?? null as number | null,
  business_value: props.initial?.business_value ?? null as number | null,
  sprint_value: props.initial?.sprint_value ?? null as number | null,
  status: props.initial?.status ?? 'todo' as UserStory['status'],
  owner_name: props.initial?.owner_name ?? '',
  sprint_id: props.initial?.sprint_id ?? null as string | null,
})

function submit() {
  emit('submit', {
    title: form.title,
    description: form.description || null,
    acceptance_criteria: form.acceptance_criteria || null,
    story_points: form.story_points,
    business_value: form.business_value,
    sprint_value: form.sprint_value,
    status: form.status,
    owner_name: form.owner_name || null,
    deliverable_id: props.deliverableId,
    sprint_id: form.sprint_id || null,
  })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label">Title *</label>
      <input v-model="form.title" class="form-input" required placeholder="As a user, I want to…" />
    </div>
    <div>
      <label class="form-label">Description</label>
      <textarea v-model="form.description" class="form-textarea" placeholder="Optional description" />
    </div>
    <div>
      <label class="form-label">Acceptance Criteria</label>
      <textarea v-model="form.acceptance_criteria" class="form-textarea" placeholder="Given… When… Then…" />
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
        <label class="form-label">Story Points</label>
        <input v-model.number="form.story_points" type="number" min="0" class="form-input" placeholder="e.g. 5" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label">Business Value</label>
        <input v-model.number="form.business_value" type="number" min="0" class="form-input" placeholder="0–100" />
      </div>
      <div>
        <label class="form-label">Sprint Value</label>
        <input v-model.number="form.sprint_value" type="number" min="0" class="form-input" placeholder="Priorität im Sprint" />
      </div>
    </div>
    <div>
      <label class="form-label">Sprint</label>
      <select v-model="form.sprint_id" class="form-select">
        <option :value="null">— No sprint —</option>
        <option v-for="sprint in sprintsStore.sprints" :key="sprint.id" :value="sprint.id">
          {{ sprint.name }}
        </option>
      </select>
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

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import type { Project, ProjectCreate } from '@/types'
import { useProjectGroupsStore } from '@/stores/projectGroups'

const props = defineProps<{
  initial?: Partial<Project>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: ProjectCreate]
  cancel: []
}>()

const groupsStore = useProjectGroupsStore()

const form = reactive<ProjectCreate>({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
  owner_name: props.initial?.owner_name ?? '',
  start_date: props.initial?.start_date ?? null,
  planned_end_date: props.initial?.planned_end_date ?? null,
  maturity_level: props.initial?.maturity_level ?? 'idea',
  status: props.initial?.status ?? 'active',
  tags: props.initial?.tags ?? null,
  project_group_id: props.initial?.project_group_id ?? null,
})

onMounted(() => groupsStore.fetchAll())

function submit() {
  const payload: ProjectCreate = {
    ...form,
    description: form.description || null,
    owner_name: form.owner_name || null,
    start_date: form.start_date || null,
    planned_end_date: form.planned_end_date || null,
    project_group_id: form.project_group_id || null,
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label" for="title">Title *</label>
      <input id="title" v-model="form.title" class="form-input" required placeholder="Project title" />
    </div>

    <div>
      <label class="form-label" for="description">Description</label>
      <textarea id="description" v-model="form.description" class="form-textarea" placeholder="Optional description" />
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label" for="status">Status</label>
        <select id="status" v-model="form.status" class="form-select">
          <option value="active">Active</option>
          <option value="on_hold">On Hold</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div>
        <label class="form-label" for="maturity">Maturity</label>
        <select id="maturity" v-model="form.maturity_level" class="form-select">
          <option value="idea">Idea</option>
          <option value="concept">Concept</option>
          <option value="in_planning">In Planning</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="on_hold">On Hold</option>
        </select>
      </div>
    </div>

    <div>
      <label class="form-label" for="group">Projektgruppe</label>
      <select id="group" v-model="form.project_group_id" class="form-select">
        <option :value="null">Keine Gruppe</option>
        <option v-for="g in groupsStore.projectGroups" :key="g.id" :value="g.id">{{ g.title }}</option>
      </select>
    </div>

    <div>
      <label class="form-label" for="owner">Owner</label>
      <input id="owner" v-model="form.owner_name" class="form-input" placeholder="Owner name" />
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="form-label" for="start">Start Date</label>
        <input id="start" v-model="form.start_date" type="date" class="form-input" />
      </div>
      <div>
        <label class="form-label" for="end">Planned End</label>
        <input id="end" v-model="form.planned_end_date" type="date" class="form-input" />
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

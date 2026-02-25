<script setup lang="ts">
import { reactive } from 'vue'
import type { ProjectGroup, ProjectGroupCreate } from '@/types'

const props = defineProps<{
  initial?: Partial<ProjectGroup>
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: ProjectGroupCreate]
  cancel: []
}>()

const form = reactive<ProjectGroupCreate>({
  title: props.initial?.title ?? '',
  description: props.initial?.description ?? '',
})

function submit() {
  const payload: ProjectGroupCreate = {
    ...form,
    description: form.description || null,
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="form-label" for="title">Titel *</label>
      <input id="title" v-model="form.title" class="form-input" required placeholder="Gruppenname" />
    </div>

    <div>
      <label class="form-label" for="description">Beschreibung</label>
      <textarea id="description" v-model="form.description" class="form-textarea" placeholder="Optionale Beschreibung" />
    </div>

    <div class="flex justify-end gap-2 pt-2">
      <button type="button" class="btn-secondary" :disabled="loading" @click="emit('cancel')">Abbrechen</button>
      <button type="submit" class="btn-primary" :disabled="loading || !form.title">
        {{ loading ? 'Speichern…' : 'Speichern' }}
      </button>
    </div>
  </form>
</template>

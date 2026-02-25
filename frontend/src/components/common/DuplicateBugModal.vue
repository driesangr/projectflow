<script setup lang="ts">
import { ref, watch } from 'vue'
import { listTasks } from '@/api/tasks'
import type { Task, Bug } from '@/types'
import { useBugsStore } from '@/stores/bugs'
import Modal from './Modal.vue'
import ErrorBanner from './ErrorBanner.vue'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps<{
  open: boolean
  bugId: string
  bugTitle: string
}>()

const emit = defineEmits<{
  close: []
  duplicated: [bug: Bug]
}>()

const bugsStore = useBugsStore()

const includeTasks = ref(false)
const tasks = ref<Task[]>([])
const selectedTaskIds = ref<Set<string>>(new Set())
const loadingTasks = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

watch(() => props.open, (open) => {
  if (!open) {
    includeTasks.value = false
    tasks.value = []
    selectedTaskIds.value = new Set()
    error.value = null
  }
})

watch(includeTasks, async (val) => {
  if (val && tasks.value.length === 0 && props.bugId) {
    loadingTasks.value = true
    try {
      tasks.value = await listTasks(undefined, props.bugId)
      selectedTaskIds.value = new Set(tasks.value.map((t) => t.id))
    } finally {
      loadingTasks.value = false
    }
  }
})

function toggleTask(id: string) {
  const next = new Set(selectedTaskIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedTaskIds.value = next
}

async function handleDuplicate() {
  saving.value = true
  error.value = null
  try {
    const taskIds = includeTasks.value ? [...selectedTaskIds.value] : []
    const newBug = await bugsStore.duplicate(props.bugId, taskIds)
    emit('duplicated', newBug)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Fehler beim Duplizieren'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Modal :open="open" title="Bug duplizieren" @close="emit('close')">
    <div class="space-y-4">
      <ErrorBanner v-if="error" :message="error" class="mb-1" />

      <p class="text-sm text-gray-600">
        Eine Kopie von <span class="font-medium">{{ bugTitle }}</span> wird erstellt.
        Der Titel wird automatisch um <span class="font-mono text-xs bg-gray-100 px-1 rounded">Kopie_N</span> ergänzt.
      </p>

      <label class="flex items-center gap-2 cursor-pointer select-none">
        <input
          v-model="includeTasks"
          type="checkbox"
          class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
        />
        <span class="text-sm font-medium text-gray-700">Tasks übernehmen</span>
      </label>

      <div v-if="includeTasks">
        <LoadingSpinner v-if="loadingTasks" />
        <p v-else-if="tasks.length === 0" class="text-sm text-gray-400">Keine Tasks vorhanden.</p>
        <ul v-else class="space-y-1 border rounded-md p-2 bg-gray-50 max-h-56 overflow-y-auto">
          <li v-for="task in tasks" :key="task.id">
            <label class="flex items-center gap-2 cursor-pointer select-none py-0.5">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                :checked="selectedTaskIds.has(task.id)"
                @change="toggleTask(task.id)"
              />
              <span class="text-sm text-gray-700">{{ task.title }}</span>
            </label>
          </li>
        </ul>
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="btn-secondary" :disabled="saving" @click="emit('close')">
          Abbrechen
        </button>
        <button type="button" class="btn-primary" :disabled="saving" @click="handleDuplicate">
          {{ saving ? 'Duplizieren…' : 'Duplizieren' }}
        </button>
      </div>
    </div>
  </Modal>
</template>

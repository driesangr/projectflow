<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listProjects } from '@/api/projects'
import { listTopics } from '@/api/topics'
import { moveDeliverable } from '@/api/deliverables'
import type { Project, Topic, Deliverable } from '@/types'
import Modal from '@/components/common/Modal.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { MagnifyingGlassIcon, CheckIcon, FolderIcon, TagIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{
  open: boolean
  deliverableId: string
  currentTopicId: string | null
  currentProjectId: string | null
}>()

const emit = defineEmits<{
  close: []
  moved: [deliverable: Deliverable]
}>()

const searchQuery = ref('')
const projects = ref<Project[]>([])
const topics = ref<Topic[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    ;[projects.value, topics.value] = await Promise.all([listProjects(), listTopics()])
  } finally {
    loading.value = false
  }
})

// Group topics by project_id
const topicsByProject = computed(() => {
  const map: Record<string, Topic[]> = {}
  for (const t of topics.value) {
    if (!map[t.project_id]) map[t.project_id] = []
    map[t.project_id].push(t)
  }
  return map
})

const q = computed(() => searchQuery.value.trim().toLowerCase())

// Filtered projects (shown as direct-parent option)
const filteredProjects = computed(() =>
  projects.value.filter((p) => !q.value || p.title.toLowerCase().includes(q.value)),
)

// Filtered topics with their project context
const filteredTopicGroups = computed(() => {
  return projects.value
    .map((p) => {
      const pts = (topicsByProject.value[p.id] ?? []).filter(
        (t) => !q.value || t.title.toLowerCase().includes(q.value) || p.title.toLowerCase().includes(q.value),
      )
      return { project: p, topics: pts }
    })
    .filter((g) => g.topics.length > 0)
})

function isCurrentParent(type: 'project' | 'topic', id: string) {
  if (type === 'project') return !props.currentTopicId && props.currentProjectId === id
  return props.currentTopicId === id
}

async function select(type: 'project' | 'topic', id: string) {
  if (isCurrentParent(type, id)) return
  saving.value = true
  error.value = null
  try {
    const payload =
      type === 'project' ? { project_id: id, topic_id: null } : { topic_id: id, project_id: null }
    const updated = await moveDeliverable(props.deliverableId, payload)
    emit('moved', updated)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Fehler beim Verschieben'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Modal :open="open" title="Parent ändern" @close="emit('close')">
    <!-- Search -->
    <div class="relative mb-4">
      <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <input
        v-model="searchQuery"
        class="form-input pl-9"
        placeholder="Projekt oder Topic suchen…"
        autofocus
      />
    </div>

    <div v-if="error" class="text-sm text-red-600 mb-3">{{ error }}</div>

    <LoadingSpinner v-if="loading" />

    <div v-else class="max-h-96 overflow-y-auto space-y-4">

      <!-- Direkt unter Projekt -->
      <div v-if="filteredProjects.length > 0">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
          Direkt unter Projekt
        </p>
        <ul class="space-y-0.5">
          <li v-for="project in filteredProjects" :key="project.id">
            <button
              class="flex items-center gap-2 w-full rounded-md px-3 py-2 text-sm text-left transition-colors"
              :class="isCurrentParent('project', project.id)
                ? 'bg-brand-50 text-brand-700 font-medium cursor-default'
                : 'hover:bg-gray-100 text-gray-800'"
              :disabled="saving"
              @click="select('project', project.id)"
            >
              <FolderIcon class="h-4 w-4 flex-shrink-0 text-blue-400" />
              <span class="flex-1 truncate">{{ project.title }}</span>
              <CheckIcon v-if="isCurrentParent('project', project.id)" class="h-4 w-4 text-brand-600 flex-shrink-0" />
            </button>
          </li>
        </ul>
      </div>

      <!-- Topics gruppiert nach Projekt -->
      <div v-for="group in filteredTopicGroups" :key="group.project.id">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
          Topics – {{ group.project.title }}
        </p>
        <ul class="space-y-0.5">
          <li v-for="topic in group.topics" :key="topic.id">
            <button
              class="flex items-center gap-2 w-full rounded-md px-3 py-2 text-sm text-left transition-colors"
              :class="isCurrentParent('topic', topic.id)
                ? 'bg-brand-50 text-brand-700 font-medium cursor-default'
                : 'hover:bg-gray-100 text-gray-800'"
              :disabled="saving"
              @click="select('topic', topic.id)"
            >
              <TagIcon class="h-4 w-4 flex-shrink-0 text-amber-400" />
              <span class="flex-1 truncate">{{ topic.title }}</span>
              <CheckIcon v-if="isCurrentParent('topic', topic.id)" class="h-4 w-4 text-brand-600 flex-shrink-0" />
            </button>
          </li>
        </ul>
      </div>

      <p v-if="filteredProjects.length === 0 && filteredTopicGroups.length === 0" class="text-sm text-gray-400 text-center py-4">
        Keine Ergebnisse für „{{ searchQuery }}"
      </p>

    </div>

    <div v-if="saving" class="flex items-center gap-2 mt-3 text-sm text-gray-500">
      <LoadingSpinner class="h-4 w-4" />
      Wird verschoben…
    </div>
  </Modal>
</template>

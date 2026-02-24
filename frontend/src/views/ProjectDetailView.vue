<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useTopicsStore } from '@/stores/topics'
import { useApi } from '@/composables/useApi'
import type { Topic, TopicCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import TopicForm from '@/components/forms/TopicForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, BoltIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const projectId = route.params.projectId as string

const projectsStore = useProjectsStore()
const topicsStore = useTopicsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<Topic | null>(null)
const deleteTarget = ref<Topic | null>(null)
const deleting = ref(false)

type SortKey = 'business_value' | 'title' | 'created_at'
type SortDir = 'asc' | 'desc'
const sortKey = ref<SortKey>('business_value')
const sortDir = ref<SortDir>('desc')

const sortedTopics = computed(() => {
  return [...topicsStore.topics].sort((a, b) => {
    let result = 0
    if (sortKey.value === 'business_value') {
      const aVal = a.business_value ?? -1
      const bVal = b.business_value ?? -1
      result = aVal - bVal
    } else if (sortKey.value === 'title') {
      result = a.title.localeCompare(b.title)
    } else {
      result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    }
    return sortDir.value === 'asc' ? result : -result
  })
})

const breadcrumbs = computed(() => [
  { label: 'Projects', to: '/projects' },
  { label: projectsStore.current?.title ?? '…' },
])

onMounted(async () => {
  await projectsStore.fetchOne(projectId)
  await topicsStore.fetchAll(projectId)
})

async function handleCreate(data: TopicCreate) {
  const result = await execute(() => topicsStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: TopicCreate) {
  if (!editTarget.value) return
  const result = await execute(() => topicsStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await topicsStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="projectsStore.loading" />

    <template v-else-if="projectsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ projectsStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="projectsStore.current.status" />
            <StatusBadge :status="projectsStore.current.maturity_level" />
            <span v-if="projectsStore.current.owner_name" class="text-sm text-gray-500">
              {{ projectsStore.current.owner_name }}
            </span>
          </div>
        </div>
        <RouterLink
          :to="`/projects/${projectId}/sprints`"
          class="btn-secondary"
        >
          <BoltIcon class="h-4 w-4" />
          Sprints
        </RouterLink>
      </div>

      <p v-if="projectsStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ projectsStore.current.description }}
      </p>

      <!-- Topics section -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">Topics</h2>
        <div class="flex items-center gap-2">
          <select v-model="sortKey" class="form-select py-1 text-xs">
            <option value="business_value">Business Value</option>
            <option value="title">Alphabetisch</option>
            <option value="created_at">Anlagedatum</option>
          </select>
          <button
            class="btn-icon"
            :title="sortDir === 'asc' ? 'Aufsteigend' : 'Absteigend'"
            @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
          >
            <ArrowUpIcon v-if="sortDir === 'asc'" class="h-3.5 w-3.5" />
            <ArrowDownIcon v-else class="h-3.5 w-3.5" />
          </button>
          <button class="btn-primary btn-sm" @click="showCreate = true">
            <PlusIcon class="h-3.5 w-3.5" />
            Add Topic
          </button>
        </div>
      </div>

      <ErrorBanner v-if="topicsStore.error" :message="topicsStore.error" class="mb-3" />
      <LoadingSpinner v-if="topicsStore.loading" />

      <EmptyState v-else-if="topicsStore.topics.length === 0" title="No topics yet" description="Topics group related deliverables.">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Topic
        </button>
      </EmptyState>

      <div v-else class="space-y-2">
        <div
          v-for="topic in sortedTopics"
          :key="topic.id"
          class="card group"
        >
          <div class="card-body">
            <div class="flex items-start gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <RouterLink
                    :to="`/topics/${topic.id}`"
                    class="font-medium text-gray-900 hover:text-brand-600 truncate"
                  >
                    {{ topic.title }}
                  </RouterLink>
                  <StatusBadge :status="topic.priority" />
                </div>
                <p v-if="topic.description" class="text-sm text-gray-500 line-clamp-1 mb-2">
                  {{ topic.description }}
                </p>
                <MaturityBar :percent="topic.maturity_percent" />
              </div>
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <button class="btn-icon" title="Edit" @click="editTarget = topic">
                  <PencilSquareIcon class="h-4 w-4" />
                </button>
                <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" title="Delete" @click="deleteTarget = topic">
                  <TrashIcon class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Create Modal -->
    <Modal :open="showCreate" title="New Topic" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TopicForm :project-id="projectId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <!-- Edit Modal -->
    <Modal :open="!!editTarget" title="Edit Topic" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TopicForm
        v-if="editTarget"
        :project-id="projectId"
        :initial="editTarget"
        :loading="saving"
        @submit="handleEdit"
        @cancel="editTarget = null"
      />
    </Modal>

    <!-- Delete Confirm -->
    <ConfirmDelete
      :open="!!deleteTarget"
      :item-name="deleteTarget?.title ?? ''"
      :loading="deleting"
      @close="deleteTarget = null"
      @confirm="handleDelete"
    />
  </div>
</template>

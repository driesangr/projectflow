<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useSprintsStore } from '@/stores/sprints'
import { useApi } from '@/composables/useApi'
import type { Sprint, SprintCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import SprintForm from '@/components/forms/SprintForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const projectId = route.params.projectId as string

const projectsStore = useProjectsStore()
const sprintsStore = useSprintsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<Sprint | null>(null)
const deleteTarget = ref<Sprint | null>(null)
const deleting = ref(false)

const breadcrumbs = computed(() => [
  { label: 'Projects', to: '/projects' },
  { label: projectsStore.current?.title ?? '…', to: `/projects/${projectId}` },
  { label: 'Sprints' },
])

onMounted(async () => {
  await projectsStore.fetchOne(projectId)
  await sprintsStore.fetchAll(projectId)
})

async function handleCreate(data: SprintCreate) {
  const result = await execute(() => sprintsStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: SprintCreate) {
  if (!editTarget.value) return
  const result = await execute(() => sprintsStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await sprintsStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString()
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <div class="page-header">
      <h1 class="page-title">Sprints</h1>
      <button class="btn-primary" @click="showCreate = true">
        <PlusIcon class="h-4 w-4" />
        New Sprint
      </button>
    </div>

    <ErrorBanner v-if="sprintsStore.error" :message="sprintsStore.error" class="mb-4" />
    <LoadingSpinner v-if="sprintsStore.loading" />

    <EmptyState v-else-if="sprintsStore.sprints.length === 0" title="No sprints yet">
      <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
        <PlusIcon class="h-4 w-4" />
        New Sprint
      </button>
    </EmptyState>

    <div v-else class="space-y-2">
      <div v-for="sprint in sprintsStore.sprints" :key="sprint.id" class="card group">
        <div class="card-body">
          <div class="flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3">
                <RouterLink
                  :to="`/projects/${projectId}/sprints/${sprint.id}`"
                  class="font-medium text-gray-900 hover:text-brand-600"
                >
                  {{ sprint.name }}
                </RouterLink>
                <span class="text-xs text-gray-500">
                  {{ formatDate(sprint.start_date) }} – {{ formatDate(sprint.end_date) }}
                </span>
              </div>
              <p v-if="sprint.goal" class="text-sm text-gray-500 mt-0.5 line-clamp-1">{{ sprint.goal }}</p>
            </div>
            <div class="flex items-center gap-1">
              <RouterLink
                :to="`/projects/${projectId}/sprints/${sprint.id}`"
                class="btn-icon"
                title="View sprint"
              >
                <ChevronRightIcon class="h-4 w-4" />
              </RouterLink>
              <button class="btn-icon opacity-0 group-hover:opacity-100 transition-opacity" @click="editTarget = sprint">
                <PencilSquareIcon class="h-4 w-4" />
              </button>
              <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity" @click="deleteTarget = sprint">
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Modal :open="showCreate" title="New Sprint" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <SprintForm :project-id="projectId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <Modal :open="!!editTarget" title="Edit Sprint" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <SprintForm
        v-if="editTarget"
        :project-id="projectId"
        :initial="editTarget"
        :loading="saving"
        @submit="handleEdit"
        @cancel="editTarget = null"
      />
    </Modal>

    <ConfirmDelete
      :open="!!deleteTarget"
      :item-name="deleteTarget?.name ?? ''"
      :loading="deleting"
      @close="deleteTarget = null"
      @confirm="handleDelete"
    />
  </div>
</template>

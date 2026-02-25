<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useApi } from '@/composables/useApi'
import type { TaskCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskForm from '@/components/forms/TaskForm.vue'
import { PencilSquareIcon, TrashIcon, ArrowLeftIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId as string

const tasksStore = useTasksStore()
const { loading: saving, error: saveError, execute } = useApi()

const showEdit = ref(false)
const showDelete = ref(false)
const deleting = ref(false)

const storyTitle = ref('')
const storyDeliverableId = ref('')

const breadcrumbs = computed(() => [
  { label: 'Projects', to: '/projects' },
  storyDeliverableId.value
    ? { label: 'Deliverable', to: `/deliverables/${storyDeliverableId.value}` }
    : { label: 'Deliverable' },
  storyTitle.value
    ? { label: storyTitle.value, to: `/user-stories/${tasksStore.current?.user_story_id}` }
    : { label: 'User Story' },
  { label: tasksStore.current?.title ?? '…' },
])

onMounted(async () => {
  await tasksStore.fetchOne(taskId)
  if (tasksStore.current) {
    const { getUserStory } = await import('@/api/userStories')
    const story = await getUserStory(tasksStore.current.user_story_id)
    storyTitle.value = story.title
    storyDeliverableId.value = story.deliverable_id
  }
})

async function handleEdit(data: TaskCreate) {
  const result = await execute(() => tasksStore.update(taskId, data))
  if (result) showEdit.value = false
}

async function handleDelete() {
  deleting.value = true
  try {
    await tasksStore.remove(taskId)
    router.push(`/user-stories/${tasksStore.current?.user_story_id ?? ''}`)
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="tasksStore.loading" />

    <template v-else-if="tasksStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ tasksStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="tasksStore.current.status" />
            <span v-if="tasksStore.current.effort_hours" class="text-xs text-gray-500">
              {{ tasksStore.current.effort_hours }}h
            </span>
            <span v-if="tasksStore.current.sprint_value != null" class="text-xs text-gray-500">
              SV {{ tasksStore.current.sprint_value }}
            </span>
            <span v-if="tasksStore.current.owner_name" class="text-xs text-gray-500">
              {{ tasksStore.current.owner_name }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="router.back()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
          <button class="btn-secondary btn-sm" @click="showEdit = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Task
          </button>
          <button class="btn-danger btn-sm" @click="showDelete = true">
            <TrashIcon class="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      <div v-if="tasksStore.current.description" class="card card-body mb-6">
        <p class="text-sm font-medium text-gray-700 mb-1">Description</p>
        <p class="text-sm text-gray-600 whitespace-pre-line">{{ tasksStore.current.description }}</p>
      </div>
    </template>

    <Modal :open="showEdit" title="Edit Task" @close="showEdit = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm
        v-if="tasksStore.current"
        :user-story-id="tasksStore.current.user_story_id"
        :initial="tasksStore.current"
        :loading="saving"
        @submit="handleEdit"
        @cancel="showEdit = false"
      />
    </Modal>

    <ConfirmDelete
      :open="showDelete"
      :item-name="tasksStore.current?.title ?? ''"
      :loading="deleting"
      @close="showDelete = false"
      @confirm="handleDelete"
    />
  </div>
</template>

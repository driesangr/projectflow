<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStoriesStore } from '@/stores/userStories'
import { useTasksStore } from '@/stores/tasks'
import { useApi } from '@/composables/useApi'
import type { Task, TaskCreate, UserStory, UserStoryCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskForm from '@/components/forms/TaskForm.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import DuplicateUserStoryModal from '@/components/common/DuplicateUserStoryModal.vue'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  CheckCircleIcon,
  ClockIcon,
  Bars3Icon,
  DocumentDuplicateIcon,
} from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const storyId = route.params.storyId as string

const storiesStore = useUserStoriesStore()
const tasksStore = useTasksStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditStory = ref(false)
const showDuplicate = ref(false)
const editTarget = ref<Task | null>(null)
const deleteTarget = ref<Task | null>(null)
const deleting = ref(false)

const projectId = ref<string>('')

const breadcrumbs = computed(() => {
  const story = storiesStore.current
  return [
    { label: 'Projects', to: '/projects' },
    story ? { label: 'Deliverable', to: `/deliverables/${story.deliverable_id}` } : { label: 'Deliverable' },
    { label: story?.title ?? '…' },
  ]
})

onMounted(async () => {
  await storiesStore.fetchOne(storyId)
  await tasksStore.fetchAll(storyId)

  if (storiesStore.current) {
    const { getDeliverable } = await import('@/api/deliverables')
    const deliverable = await getDeliverable(storiesStore.current.deliverable_id)
    const { getTopic } = await import('@/api/topics')
    const topic = await getTopic(deliverable.topic_id)
    projectId.value = topic.project_id
  }
})

function handleStoryDuplicated(story: UserStory) {
  showDuplicate.value = false
  router.push(`/user-stories/${story.id}`)
}

async function handleStoryEdit(data: UserStoryCreate) {
  const result = await execute(() => storiesStore.update(storyId, data))
  if (result) showEditStory.value = false
}

async function handleCreate(data: TaskCreate) {
  const result = await execute(() => tasksStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: TaskCreate) {
  if (!editTarget.value) return
  const result = await execute(() => tasksStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await tasksStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

async function quickStatusToggle(task: Task) {
  const nextStatus = task.status === 'todo'
    ? 'in_progress'
    : task.status === 'in_progress'
      ? 'done'
      : 'todo'
  await tasksStore.update(task.id, { status: nextStatus })
}

const tasksByStatus = computed(() => ({
  todo: [...tasksStore.tasks.filter((t) => t.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...tasksStore.tasks.filter((t) => t.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...tasksStore.tasks.filter((t) => t.status === 'done')].sort((a, b) => a.position - b.position),
}))

// Separate draggable refs for each Kanban column
const draggableTodo = ref<Task[]>([])
const draggableInProgress = ref<Task[]>([])
const draggableDone = ref<Task[]>([])
const isDragging = ref(false)

watch(tasksByStatus, (val) => {
  if (isDragging.value) return
  draggableTodo.value = [...val.todo]
  draggableInProgress.value = [...val.in_progress]
  draggableDone.value = [...val.done]
}, { immediate: true })

async function onTaskChange(status: Task['status'], column: Task[], evt: any) {
  if (evt.added) {
    isDragging.value = true
    try {
      await tasksStore.update(evt.added.element.id, { status })
      await tasksStore.reorder(column.map((t, i) => ({ id: t.id, position: i })))
    } finally {
      isDragging.value = false
    }
  } else if (evt.moved || evt.removed) {
    await tasksStore.reorder(column.map((t, i) => ({ id: t.id, position: i })))
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="storiesStore.loading" />

    <template v-else-if="storiesStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ storiesStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="storiesStore.current.status" />
            <span v-if="storiesStore.current.story_points" class="text-xs text-gray-500">
              {{ storiesStore.current.story_points }} story pts
            </span>
            <span v-if="storiesStore.current.business_value != null" class="text-xs text-gray-500">
              BV {{ storiesStore.current.business_value }}
            </span>
            <span v-if="storiesStore.current.sprint_value != null" class="text-xs text-gray-500">
              SV {{ storiesStore.current.sprint_value }}
            </span>
            <span v-if="storiesStore.current.owner_name" class="text-xs text-gray-500">
              {{ storiesStore.current.owner_name }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="showDuplicate = true">
            <DocumentDuplicateIcon class="h-4 w-4" />
            Duplicate
          </button>
          <button class="btn-secondary btn-sm" @click="showEditStory = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Story
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div v-if="storiesStore.current.description" class="card card-body">
          <p class="text-sm font-medium text-gray-700 mb-1">Description</p>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ storiesStore.current.description }}</p>
        </div>
        <div v-if="storiesStore.current.acceptance_criteria" class="card card-body">
          <p class="text-sm font-medium text-gray-700 mb-1">Acceptance Criteria</p>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ storiesStore.current.acceptance_criteria }}</p>
        </div>
      </div>

      <!-- Tasks -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">Tasks</h2>
        <button class="btn-primary btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Task
        </button>
      </div>

      <ErrorBanner v-if="tasksStore.error" :message="tasksStore.error" class="mb-3" />
      <LoadingSpinner v-if="tasksStore.loading" />

      <EmptyState v-else-if="tasksStore.tasks.length === 0" title="No tasks yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Task
        </button>
      </EmptyState>

      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- To Do column -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            To Do ({{ tasksByStatus.todo.length }})
          </h3>
          <draggable
            v-model="draggableTodo"
            class="space-y-2 min-h-[2rem]"
            item-key="id"
            handle=".drag-handle"
            animation="150"
            group="tasks"
            @change="(evt) => onTaskChange('todo', draggableTodo, evt)"
          >
            <template #item="{ element: task }">
              <div class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button
                      class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0"
                      title="Mark in-progress"
                      @click="quickStatusToggle(task)"
                    >
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-800 line-clamp-2">{{ task.title }}</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="task.effort_hours" class="text-xs text-gray-400">{{ task.effort_hours }}h</span>
                        <span v-if="task.owner_name" class="text-xs text-gray-400">{{ task.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="editTarget = task"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = task"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- In Progress column -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-blue-500 mb-2">
            In Progress ({{ tasksByStatus.in_progress.length }})
          </h3>
          <draggable
            v-model="draggableInProgress"
            class="space-y-2 min-h-[2rem]"
            item-key="id"
            handle=".drag-handle"
            animation="150"
            group="tasks"
            @change="(evt) => onTaskChange('in_progress', draggableInProgress, evt)"
          >
            <template #item="{ element: task }">
              <div class="card group border-blue-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button
                      class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0"
                      title="Mark done"
                      @click="quickStatusToggle(task)"
                    >
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-800 line-clamp-2">{{ task.title }}</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="task.effort_hours" class="text-xs text-gray-400">{{ task.effort_hours }}h</span>
                        <span v-if="task.owner_name" class="text-xs text-gray-400">{{ task.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="editTarget = task"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = task"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Done column -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">
            Done ({{ tasksByStatus.done.length }})
          </h3>
          <draggable
            v-model="draggableDone"
            class="space-y-2 min-h-[2rem]"
            item-key="id"
            handle=".drag-handle"
            animation="150"
            group="tasks"
            @change="(evt) => onTaskChange('done', draggableDone, evt)"
          >
            <template #item="{ element: task }">
              <div class="card group opacity-75">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button
                      class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0"
                      title="Mark to-do"
                      @click="quickStatusToggle(task)"
                    >
                      <CheckCircleIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-500 line-through line-clamp-2">{{ task.title }}</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="task.effort_hours" class="text-xs text-gray-400">{{ task.effort_hours }}h</span>
                      </div>
                    </div>
                    <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="editTarget = task"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = task"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>
      </div>
    </template>

    <Modal :open="showCreate" title="New Task" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm :user-story-id="storyId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <Modal :open="!!editTarget" title="Edit Task" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm
        v-if="editTarget"
        :user-story-id="storyId"
        :initial="editTarget"
        :loading="saving"
        @submit="handleEdit"
        @cancel="editTarget = null"
      />
    </Modal>

    <ConfirmDelete
      :open="!!deleteTarget"
      :item-name="deleteTarget?.title ?? ''"
      :loading="deleting"
      @close="deleteTarget = null"
      @confirm="handleDelete"
    />

    <DuplicateUserStoryModal
      v-if="storiesStore.current"
      :open="showDuplicate"
      :story-id="storyId"
      :story-title="storiesStore.current.title"
      @close="showDuplicate = false"
      @duplicated="handleStoryDuplicated"
    />

    <Modal :open="showEditStory" title="Edit User Story" @close="showEditStory = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <UserStoryForm
        v-if="storiesStore.current"
        :deliverable-id="storiesStore.current.deliverable_id"
        :project-id="projectId"
        :initial="storiesStore.current"
        :loading="saving"
        @submit="handleStoryEdit"
        @cancel="showEditStory = false"
      />
    </Modal>
  </div>
</template>

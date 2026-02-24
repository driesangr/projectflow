<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStoriesStore } from '@/stores/userStories'
import { useTasksStore } from '@/stores/tasks'
import { useApi } from '@/composables/useApi'
import type { Task, TaskCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskForm from '@/components/forms/TaskForm.vue'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const storyId = route.params.storyId as string

const storiesStore = useUserStoriesStore()
const tasksStore = useTasksStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<Task | null>(null)
const deleteTarget = ref<Task | null>(null)
const deleting = ref(false)

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
})

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
  todo: tasksStore.tasks.filter((t) => t.status === 'todo'),
  in_progress: tasksStore.tasks.filter((t) => t.status === 'in_progress'),
  done: tasksStore.tasks.filter((t) => t.status === 'done'),
}))
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
            <span v-if="storiesStore.current.owner_name" class="text-xs text-gray-500">
              {{ storiesStore.current.owner_name }}
            </span>
          </div>
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
          <div class="space-y-2">
            <div
              v-for="task in tasksByStatus.todo"
              :key="task.id"
              class="card group"
            >
              <div class="card-body py-3">
                <div class="flex items-start gap-2">
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
          </div>
        </div>

        <!-- In Progress column -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-blue-500 mb-2">
            In Progress ({{ tasksByStatus.in_progress.length }})
          </h3>
          <div class="space-y-2">
            <div
              v-for="task in tasksByStatus.in_progress"
              :key="task.id"
              class="card group border-blue-200"
            >
              <div class="card-body py-3">
                <div class="flex items-start gap-2">
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
          </div>
        </div>

        <!-- Done column -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">
            Done ({{ tasksByStatus.done.length }})
          </h3>
          <div class="space-y-2">
            <div
              v-for="task in tasksByStatus.done"
              :key="task.id"
              class="card group opacity-75"
            >
              <div class="card-body py-3">
                <div class="flex items-start gap-2">
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
          </div>
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
  </div>
</template>

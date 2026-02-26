<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBugsStore } from '@/stores/bugs'
import { useTasksStore } from '@/stores/tasks'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useTopicsStore } from '@/stores/topics'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useSprintsStore } from '@/stores/sprints'
import { useApi } from '@/composables/useApi'
import type { Task, TaskCreate, Bug, BugCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskForm from '@/components/forms/TaskForm.vue'
import BugForm from '@/components/forms/BugForm.vue'
import DuplicateBugModal from '@/components/common/DuplicateBugModal.vue'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  CheckCircleIcon,
  ClockIcon,
  Bars3Icon,
  DocumentDuplicateIcon,
  ArrowLeftIcon,
  BugAntIcon,
  ListBulletIcon,
} from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const bugId = route.params.bugId as string

function goBack() {
  const referrer = route.query.referrer as string | undefined
  if (referrer) router.push(referrer)
  else router.back()
}

const bugsStore = useBugsStore()
const tasksStore = useTasksStore()
const deliverablesStore = useDeliverablesStore()
const topicsStore = useTopicsStore()
const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const sprintsStore = useSprintsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditBug = ref(false)
const showDuplicate = ref(false)
const editTarget = ref<Task | null>(null)
const deleteTarget = ref<Task | null>(null)
const deleting = ref(false)

const projectId = ref<string>('')

function parseSprintReferrer(ref: string | undefined) {
  if (!ref) return null
  const m = ref.match(/^\/projects\/([^/]+)\/sprints\/([^/]+)$/)
  return m ? { projectId: m[1], sprintId: m[2] } : null
}

const sprintRef = computed(() => parseSprintReferrer(route.query.referrer as string | undefined))

const sprintBreadcrumbs = computed(() => {
  if (!sprintRef.value) return []
  const project = projectsStore.current
  const group = projectGroupsStore.current
  const sprint = sprintsStore.current
  const { projectId: pid, sprintId: sid } = sprintRef.value
  const items: { label: string; to?: string }[] = []
  if (project?.project_group_id && group) {
    items.push({ label: 'Projektgruppen', to: '/project-groups' })
    items.push({ label: group.title, to: `/project-groups/${group.id}` })
  }
  items.push({ label: project?.title ?? '…', to: `/projects/${pid}` })
  items.push({ label: 'Sprints', to: `/projects/${pid}/sprints` })
  items.push({ label: sprint?.name ?? '…', to: `/projects/${pid}/sprints/${sid}` })
  return items
})

function taskLink(taskId: string) {
  const ref = route.query.referrer as string | undefined
  return ref ? `/tasks/${taskId}?referrer=${encodeURIComponent(ref)}` : `/tasks/${taskId}`
}

const breadcrumbs = computed(() => {
  const bug = bugsStore.current
  const deliverable = deliverablesStore.current
  const topic = topicsStore.current
  const project = projectsStore.current
  const group = projectGroupsStore.current
  const items: { label: string; to?: string }[] = []
  if (project?.project_group_id && group) {
    items.push({ label: 'Projektgruppen', to: '/project-groups' })
    items.push({ label: group.title, to: `/project-groups/${group.id}` })
  }
  items.push(project ? { label: project.title, to: `/projects/${project.id}` } : { label: 'Project' })
  items.push(topic ? { label: topic.title, to: `/topics/${topic.id}` } : { label: 'Topic' })
  items.push(deliverable && bug ? { label: deliverable.title, to: `/deliverables/${bug.deliverable_id}` } : { label: 'Deliverable' })
  items.push({ label: bug?.title ?? '…' })
  return items
})

onMounted(async () => {
  await bugsStore.fetchOne(bugId)
  await tasksStore.fetchAll(undefined, bugId)

  if (bugsStore.current) {
    await deliverablesStore.fetchOne(bugsStore.current.deliverable_id)
    if (deliverablesStore.current) {
      await topicsStore.fetchOne(deliverablesStore.current.topic_id!)
      if (topicsStore.current) {
        projectId.value = topicsStore.current.project_id
        await projectsStore.fetchOne(topicsStore.current.project_id)
        if (projectsStore.current?.project_group_id) {
          await projectGroupsStore.fetchOne(projectsStore.current.project_group_id)
        } else {
          projectGroupsStore.current = null
        }
      }
    }
  }
  if (sprintRef.value) {
    await sprintsStore.fetchOne(sprintRef.value.sprintId)
  }
})

function handleBugDuplicated(bug: Bug) {
  showDuplicate.value = false
  router.push(`/bugs/${bug.id}`)
}

async function handleBugEdit(data: BugCreate) {
  const result = await execute(() => bugsStore.update(bugId, data))
  if (result) showEditBug.value = false
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

const draggableTodo = ref<Task[]>([])
const draggableInProgress = ref<Task[]>([])
const draggableDone = ref<Task[]>([])
const isDragging = ref(false)
const showAllTasks = ref(false)
const hiddenTasksCount = computed(() =>
  [draggableTodo, draggableInProgress, draggableDone]
    .reduce((s, c) => s + Math.max(0, c.value.length - 5), 0)
)

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
    <Breadcrumb v-if="sprintBreadcrumbs.length" :items="sprintBreadcrumbs" />

    <LoadingSpinner v-if="bugsStore.loading" />

    <template v-else-if="bugsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title flex items-center gap-2">
            <BugAntIcon class="h-6 w-6 text-red-500 flex-shrink-0" />
            {{ bugsStore.current.title }}
          </h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="bugsStore.current.status" />
            <span v-if="bugsStore.current.story_points" class="text-xs text-gray-500">
              {{ bugsStore.current.story_points }} story pts
            </span>
            <span v-if="bugsStore.current.business_value != null" class="text-xs text-gray-500">
              BV {{ bugsStore.current.business_value }}
            </span>
            <span v-if="bugsStore.current.sprint_value != null" class="text-xs text-gray-500">
              SV {{ bugsStore.current.sprint_value }}
            </span>
            <span v-if="bugsStore.current.owner_name" class="text-xs text-gray-500">
              {{ bugsStore.current.owner_name }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="goBack()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
          <button class="btn-secondary btn-sm" @click="showDuplicate = true">
            <DocumentDuplicateIcon class="h-4 w-4" />
            Duplicate
          </button>
          <button class="btn-secondary btn-sm" @click="showEditBug = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Bug
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div v-if="bugsStore.current.description" class="card card-body">
          <p class="text-sm font-medium text-gray-700 mb-1">Description</p>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ bugsStore.current.description }}</p>
        </div>
        <div v-if="bugsStore.current.acceptance_criteria" class="card card-body">
          <p class="text-sm font-medium text-gray-700 mb-1">Steps to Reproduce / Expected Behavior</p>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ bugsStore.current.acceptance_criteria }}</p>
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
            <template #item="{ element: task, index }">
              <div class="card group" v-show="showAllTasks || index < 5">
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
                      <div class="flex items-start gap-1">
                        <ListBulletIcon class="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="taskLink(task.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ task.title }}</RouterLink>
                      </div>
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
            <template #item="{ element: task, index }">
              <div class="card group border-blue-200" v-show="showAllTasks || index < 5">
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
                      <div class="flex items-start gap-1">
                        <ListBulletIcon class="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="taskLink(task.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ task.title }}</RouterLink>
                      </div>
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
            <template #item="{ element: task, index }">
              <div class="card group opacity-75" v-show="showAllTasks || index < 5">
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
                      <div class="flex items-start gap-1">
                        <ListBulletIcon class="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="taskLink(task.id)" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2">{{ task.title }}</RouterLink>
                      </div>
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
      <div v-if="hiddenTasksCount > 0 || showAllTasks" class="mt-3">
        <label class="flex items-center gap-2 text-sm text-gray-500 cursor-pointer select-none">
          <input v-model="showAllTasks" type="checkbox" class="w-4 h-4 appearance-auto" />
          Alle anzeigen
          <span v-if="!showAllTasks" class="text-gray-400">({{ hiddenTasksCount }} weitere ausgeblendet)</span>
        </label>
      </div>
    </template>

    <Modal :open="showCreate" title="New Task" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm :bug-id="bugId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <Modal :open="!!editTarget" title="Edit Task" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm
        v-if="editTarget"
        :bug-id="bugId"
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

    <DuplicateBugModal
      v-if="bugsStore.current"
      :open="showDuplicate"
      :bug-id="bugId"
      :bug-title="bugsStore.current.title"
      @close="showDuplicate = false"
      @duplicated="handleBugDuplicated"
    />

    <Modal :open="showEditBug" title="Edit Bug" @close="showEditBug = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <BugForm
        v-if="bugsStore.current"
        :deliverable-id="bugsStore.current.deliverable_id"
        :project-id="projectId"
        :initial="bugsStore.current"
        :loading="saving"
        @submit="handleBugEdit"
        @cancel="showEditBug = false"
      />
    </Modal>
  </div>
</template>

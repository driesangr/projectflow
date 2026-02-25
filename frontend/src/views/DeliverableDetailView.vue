<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useUserStoriesStore } from '@/stores/userStories'
import { useBugsStore } from '@/stores/bugs'
import { useTopicsStore } from '@/stores/topics'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useApi } from '@/composables/useApi'
import type { UserStory, UserStoryCreate, Bug, BugCreate, DeliverableCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import BugForm from '@/components/forms/BugForm.vue'
import DeliverableForm from '@/components/forms/DeliverableForm.vue'
import DuplicateUserStoryModal from '@/components/common/DuplicateUserStoryModal.vue'
import DuplicateBugModal from '@/components/common/DuplicateBugModal.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, DocumentDuplicateIcon, CheckCircleIcon, ClockIcon, Bars3Icon, ArrowLeftIcon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const deliverableId = route.params.deliverableId as string

const deliverablesStore = useDeliverablesStore()
const storiesStore = useUserStoriesStore()
const bugsStore = useBugsStore()
const topicsStore = useTopicsStore()
const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const { loading: saving, error: saveError, execute } = useApi()

// ── User Story state ──────────────────────────────────────────────────────────
const showCreate = ref(false)
const showEditDeliverable = ref(false)
const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const duplicateTarget = ref<UserStory | null>(null)
const deleting = ref(false)

// ── Bug state ─────────────────────────────────────────────────────────────────
const showCreateBug = ref(false)
const editBugTarget = ref<Bug | null>(null)
const deleteBugTarget = ref<Bug | null>(null)
const duplicateBugTarget = ref<Bug | null>(null)
const deletingBug = ref(false)

// ── Story Kanban ──────────────────────────────────────────────────────────────
const storiesByStatus = computed(() => ({
  todo: [...storiesStore.userStories.filter(s => s.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...storiesStore.userStories.filter(s => s.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...storiesStore.userStories.filter(s => s.status === 'done')].sort((a, b) => a.position - b.position),
  on_hold: [...storiesStore.userStories.filter(s => s.status === 'on_hold')].sort((a, b) => a.position - b.position),
}))

const draggableTodo = ref<UserStory[]>([])
const draggableInProgress = ref<UserStory[]>([])
const draggableDone = ref<UserStory[]>([])
const draggableOnHold = ref<UserStory[]>([])
const isDragging = ref(false)

watch(storiesByStatus, (val) => {
  if (isDragging.value) return
  draggableTodo.value = [...val.todo]
  draggableInProgress.value = [...val.in_progress]
  draggableDone.value = [...val.done]
  draggableOnHold.value = [...val.on_hold]
}, { immediate: true })

function calcDeliverableBV() {
  const allOrdered = [
    ...draggableTodo.value,
    ...draggableInProgress.value,
    ...draggableDone.value,
    ...draggableOnHold.value,
  ]
  const n = allOrdered.length
  if (n === 0) return Promise.resolve()
  return storiesStore.setValues(allOrdered.map((s, i) => ({ id: s.id, business_value: (n - i) * 10 })))
}

async function onStoryChange(status: UserStory['status'], column: UserStory[], evt: any) {
  if (evt.added) {
    isDragging.value = true
    try {
      await storiesStore.update(evt.added.element.id, { status })
      await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
    } finally {
      isDragging.value = false
    }
    await nextTick()
    await calcDeliverableBV()
  } else if (evt.moved) {
    await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
    await calcDeliverableBV()
  } else if (evt.removed) {
    await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
  }
}

async function quickStatusToggle(s: UserStory) {
  const next = s.status === 'todo' ? 'in_progress' : s.status === 'in_progress' ? 'done' : 'todo'
  await storiesStore.update(s.id, { status: next })
}

// ── Bug Kanban ────────────────────────────────────────────────────────────────
const bugsByStatus = computed(() => ({
  todo: [...bugsStore.bugs.filter(b => b.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...bugsStore.bugs.filter(b => b.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...bugsStore.bugs.filter(b => b.status === 'done')].sort((a, b) => a.position - b.position),
  on_hold: [...bugsStore.bugs.filter(b => b.status === 'on_hold')].sort((a, b) => a.position - b.position),
}))

const draggableBugTodo = ref<Bug[]>([])
const draggableBugInProgress = ref<Bug[]>([])
const draggableBugDone = ref<Bug[]>([])
const draggableBugOnHold = ref<Bug[]>([])
const isBugDragging = ref(false)

watch(bugsByStatus, (val) => {
  if (isBugDragging.value) return
  draggableBugTodo.value = [...val.todo]
  draggableBugInProgress.value = [...val.in_progress]
  draggableBugDone.value = [...val.done]
  draggableBugOnHold.value = [...val.on_hold]
}, { immediate: true })

function calcDeliverableBugBV() {
  const allOrdered = [
    ...draggableBugTodo.value,
    ...draggableBugInProgress.value,
    ...draggableBugDone.value,
    ...draggableBugOnHold.value,
  ]
  const n = allOrdered.length
  if (n === 0) return Promise.resolve()
  return bugsStore.setValues(allOrdered.map((b, i) => ({ id: b.id, business_value: (n - i) * 10 })))
}

async function onBugChange(status: Bug['status'], column: Bug[], evt: any) {
  if (evt.added) {
    isBugDragging.value = true
    try {
      await bugsStore.update(evt.added.element.id, { status })
      await bugsStore.reorder(column.map((b, i) => ({ id: b.id, position: i })))
    } finally {
      isBugDragging.value = false
    }
    await nextTick()
    await calcDeliverableBugBV()
  } else if (evt.moved) {
    await bugsStore.reorder(column.map((b, i) => ({ id: b.id, position: i })))
    await calcDeliverableBugBV()
  } else if (evt.removed) {
    await bugsStore.reorder(column.map((b, i) => ({ id: b.id, position: i })))
  }
}

async function quickBugStatusToggle(b: Bug) {
  const next = b.status === 'todo' ? 'in_progress' : b.status === 'in_progress' ? 'done' : 'todo'
  await bugsStore.update(b.id, { status: next })
}

// ── Breadcrumb ────────────────────────────────────────────────────────────────
const breadcrumbs = computed(() => {
  const d = deliverablesStore.current
  const topic = topicsStore.current
  const project = projectsStore.current
  const group = projectGroupsStore.current
  const items: { label: string; to?: string }[] = []
  if (project?.project_group_id && group) {
    items.push({ label: 'Projektgruppen', to: '/project-groups' })
    items.push({ label: group.title, to: `/project-groups/${group.id}` })
  }
  items.push(project ? { label: project.title, to: `/projects/${project.id}` } : { label: 'Project' })
  items.push(topic && d ? { label: topic.title, to: `/topics/${d.topic_id}` } : { label: 'Topic' })
  items.push({ label: d?.title ?? '…' })
  return items
})

const projectId = ref<string>('')

onMounted(async () => {
  await deliverablesStore.fetchOne(deliverableId)
  await Promise.all([
    storiesStore.fetchAll(deliverableId),
    bugsStore.fetchAll(deliverableId),
  ])

  if (deliverablesStore.current) {
    await topicsStore.fetchOne(deliverablesStore.current.topic_id)
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
})

// ── User Story CRUD ───────────────────────────────────────────────────────────
function handleStoryDuplicated(story: UserStory) {
  duplicateTarget.value = null
  router.push(`/user-stories/${story.id}`)
}

async function handleDeliverableEdit(data: DeliverableCreate) {
  const result = await execute(() => deliverablesStore.update(deliverableId, data))
  if (result) showEditDeliverable.value = false
}

async function handleDuplicate() {
  const copy = await execute(() => deliverablesStore.duplicate(deliverableId))
  if (copy) router.push(`/deliverables/${copy.id}`)
}

async function handleCreate(data: UserStoryCreate) {
  const result = await execute(() => storiesStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: UserStoryCreate) {
  if (!editTarget.value) return
  const result = await execute(() => storiesStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await storiesStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

// ── Bug CRUD ──────────────────────────────────────────────────────────────────
function handleBugDuplicated(bug: Bug) {
  duplicateBugTarget.value = null
  router.push(`/bugs/${bug.id}`)
}

async function handleCreateBug(data: BugCreate) {
  const result = await execute(() => bugsStore.create(data))
  if (result) showCreateBug.value = false
}

async function handleEditBug(data: BugCreate) {
  if (!editBugTarget.value) return
  const result = await execute(() => bugsStore.update(editBugTarget.value!.id, data))
  if (result) editBugTarget.value = null
}

async function handleDeleteBug() {
  if (!deleteBugTarget.value) return
  deletingBug.value = true
  try {
    await bugsStore.remove(deleteBugTarget.value.id)
    deleteBugTarget.value = null
  } finally {
    deletingBug.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="deliverablesStore.loading" />

    <template v-else-if="deliverablesStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ deliverablesStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="deliverablesStore.current.status" />
            <span v-if="deliverablesStore.current.epic_points" class="text-xs text-gray-500">
              {{ deliverablesStore.current.epic_points }} epic pts
            </span>
            <span v-if="deliverablesStore.current.business_value != null" class="text-xs text-gray-500">
              BV {{ deliverablesStore.current.business_value }}
            </span>
          </div>
          <div class="mt-2 w-64">
            <MaturityBar :percent="deliverablesStore.current.maturity_percent" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="router.back()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
          <button class="btn-secondary btn-sm" @click="handleDuplicate">
            <DocumentDuplicateIcon class="h-4 w-4" />
            Duplicate
          </button>
          <button class="btn-secondary btn-sm" @click="showEditDeliverable = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Deliverable
          </button>
        </div>
      </div>

      <p v-if="deliverablesStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ deliverablesStore.current.description }}
      </p>

      <!-- User Stories Kanban -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">User Stories</h2>
        <button class="btn-primary btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Story
        </button>
      </div>

      <ErrorBanner v-if="storiesStore.error" :message="storiesStore.error" class="mb-3" />
      <LoadingSpinner v-if="storiesStore.loading" />

      <EmptyState v-else-if="storiesStore.userStories.length === 0" title="No user stories yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Story
        </button>
      </EmptyState>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- To Do -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            To Do ({{ storiesByStatus.todo.length }})
          </h3>
          <draggable v-model="draggableTodo" group="stories" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onStoryChange('todo', draggableTodo, evt)">
            <template #item="{ element: story }">
              <div class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickStatusToggle(story)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/user-stories/${story.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                        <span v-if="story.owner_name" class="text-xs text-gray-400">{{ story.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateTarget = story"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editTarget = story"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = story"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- In Progress -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-blue-500 mb-2">
            In Progress ({{ storiesByStatus.in_progress.length }})
          </h3>
          <draggable v-model="draggableInProgress" group="stories" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onStoryChange('in_progress', draggableInProgress, evt)">
            <template #item="{ element: story }">
              <div class="card group border-blue-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0" title="Mark done" @click="quickStatusToggle(story)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/user-stories/${story.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                        <span v-if="story.owner_name" class="text-xs text-gray-400">{{ story.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateTarget = story"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editTarget = story"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = story"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Done -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">
            Done ({{ storiesByStatus.done.length }})
          </h3>
          <draggable v-model="draggableDone" group="stories" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onStoryChange('done', draggableDone, evt)">
            <template #item="{ element: story }">
              <div class="card group opacity-75">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0" title="Mark to-do" @click="quickStatusToggle(story)">
                      <CheckCircleIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/user-stories/${story.id}`" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateTarget = story"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editTarget = story"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = story"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- On Hold -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-yellow-600 mb-2">
            On Hold ({{ storiesByStatus.on_hold.length }})
          </h3>
          <draggable v-model="draggableOnHold" group="stories" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onStoryChange('on_hold', draggableOnHold, evt)">
            <template #item="{ element: story }">
              <div class="card group border-yellow-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/user-stories/${story.id}`" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                        <span v-if="story.owner_name" class="text-xs text-gray-400">{{ story.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateTarget = story"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editTarget = story"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteTarget = story"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

      </div>

      <!-- Bugs Kanban -->
      <div class="flex items-center justify-between mb-3 mt-8">
        <h2 class="section-title mb-0">Bugs</h2>
        <button class="btn-primary btn-sm" @click="showCreateBug = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Bug
        </button>
      </div>

      <ErrorBanner v-if="bugsStore.error" :message="bugsStore.error" class="mb-3" />
      <LoadingSpinner v-if="bugsStore.loading" />

      <EmptyState v-else-if="bugsStore.bugs.length === 0" title="No bugs yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreateBug = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Bug
        </button>
      </EmptyState>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- Bug To Do -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            To Do ({{ bugsByStatus.todo.length }})
          </h3>
          <draggable v-model="draggableBugTodo" group="bugs" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onBugChange('todo', draggableBugTodo, evt)">
            <template #item="{ element: bug }">
              <div class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickBugStatusToggle(bug)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/bugs/${bug.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ bug.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="bug.story_points" class="text-xs text-gray-400">{{ bug.story_points }} pts</span>
                        <span v-if="bug.owner_name" class="text-xs text-gray-400">{{ bug.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateBugTarget = bug"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editBugTarget = bug"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteBugTarget = bug"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Bug In Progress -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-blue-500 mb-2">
            In Progress ({{ bugsByStatus.in_progress.length }})
          </h3>
          <draggable v-model="draggableBugInProgress" group="bugs" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onBugChange('in_progress', draggableBugInProgress, evt)">
            <template #item="{ element: bug }">
              <div class="card group border-blue-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0" title="Mark done" @click="quickBugStatusToggle(bug)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/bugs/${bug.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ bug.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="bug.story_points" class="text-xs text-gray-400">{{ bug.story_points }} pts</span>
                        <span v-if="bug.owner_name" class="text-xs text-gray-400">{{ bug.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateBugTarget = bug"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editBugTarget = bug"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteBugTarget = bug"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Bug Done -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">
            Done ({{ bugsByStatus.done.length }})
          </h3>
          <draggable v-model="draggableBugDone" group="bugs" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onBugChange('done', draggableBugDone, evt)">
            <template #item="{ element: bug }">
              <div class="card group opacity-75">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0" title="Mark to-do" @click="quickBugStatusToggle(bug)">
                      <CheckCircleIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/bugs/${bug.id}`" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2 block">{{ bug.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="bug.story_points" class="text-xs text-gray-400">{{ bug.story_points }} pts</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateBugTarget = bug"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editBugTarget = bug"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteBugTarget = bug"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Bug On Hold -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-yellow-600 mb-2">
            On Hold ({{ bugsByStatus.on_hold.length }})
          </h3>
          <draggable v-model="draggableBugOnHold" group="bugs" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onBugChange('on_hold', draggableBugOnHold, evt)">
            <template #item="{ element: bug }">
              <div class="card group border-yellow-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/bugs/${bug.id}`" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2 block">{{ bug.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="bug.story_points" class="text-xs text-gray-400">{{ bug.story_points }} pts</span>
                        <span v-if="bug.owner_name" class="text-xs text-gray-400">{{ bug.owner_name }}</span>
                      </div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" @click="duplicateBugTarget = bug"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" @click="editBugTarget = bug"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" @click="deleteBugTarget = bug"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

      </div>
    </template>

    <!-- User Story modals -->
    <Modal :open="showCreate" title="New User Story" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <UserStoryForm
        :deliverable-id="deliverableId"
        :project-id="projectId"
        :loading="saving"
        @submit="handleCreate"
        @cancel="showCreate = false"
      />
    </Modal>

    <Modal :open="!!editTarget" title="Edit User Story" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <UserStoryForm
        v-if="editTarget"
        :deliverable-id="deliverableId"
        :project-id="projectId"
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
      :open="!!duplicateTarget"
      :story-id="duplicateTarget?.id ?? ''"
      :story-title="duplicateTarget?.title ?? ''"
      @close="duplicateTarget = null"
      @duplicated="handleStoryDuplicated"
    />

    <!-- Bug modals -->
    <Modal :open="showCreateBug" title="New Bug" @close="showCreateBug = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <BugForm
        :deliverable-id="deliverableId"
        :project-id="projectId"
        :loading="saving"
        @submit="handleCreateBug"
        @cancel="showCreateBug = false"
      />
    </Modal>

    <Modal :open="!!editBugTarget" title="Edit Bug" @close="editBugTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <BugForm
        v-if="editBugTarget"
        :deliverable-id="deliverableId"
        :project-id="projectId"
        :initial="editBugTarget"
        :loading="saving"
        @submit="handleEditBug"
        @cancel="editBugTarget = null"
      />
    </Modal>

    <ConfirmDelete
      :open="!!deleteBugTarget"
      :item-name="deleteBugTarget?.title ?? ''"
      :loading="deletingBug"
      @close="deleteBugTarget = null"
      @confirm="handleDeleteBug"
    />

    <DuplicateBugModal
      :open="!!duplicateBugTarget"
      :bug-id="duplicateBugTarget?.id ?? ''"
      :bug-title="duplicateBugTarget?.title ?? ''"
      @close="duplicateBugTarget = null"
      @duplicated="handleBugDuplicated"
    />

    <!-- Edit Deliverable Modal -->
    <Modal :open="showEditDeliverable" title="Edit Deliverable" @close="showEditDeliverable = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <DeliverableForm
        v-if="deliverablesStore.current"
        :topic-id="deliverablesStore.current.topic_id"
        :initial="deliverablesStore.current"
        :loading="saving"
        @submit="handleDeliverableEdit"
        @cancel="showEditDeliverable = false"
      />
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useSprintsStore } from '@/stores/sprints'
import { useUserStoriesStore } from '@/stores/userStories'
import { useBugsStore } from '@/stores/bugs'
import { useApi } from '@/composables/useApi'
import type { UserStory, UserStoryCreate, Bug, BugCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import BugForm from '@/components/forms/BugForm.vue'
import DuplicateUserStoryModal from '@/components/common/DuplicateUserStoryModal.vue'
import DuplicateBugModal from '@/components/common/DuplicateBugModal.vue'
import { ArrowLeftIcon, PencilSquareIcon, TrashIcon, DocumentDuplicateIcon, CheckCircleIcon, ClockIcon, Bars3Icon, CalendarDaysIcon, BookOpenIcon, BugAntIcon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.projectId as string)
const sprintId = computed(() => route.params.sprintId as string)

const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const sprintsStore = useSprintsStore()
const storiesStore = useUserStoriesStore()
const bugsStore = useBugsStore()
const { loading: saving, error: saveError, execute } = useApi()

// ── User Story state ──────────────────────────────────────────────────────────
const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const duplicateTarget = ref<UserStory | null>(null)
const deleting = ref(false)

// ── Bug state ─────────────────────────────────────────────────────────────────
const editBugTarget = ref<Bug | null>(null)
const deleteBugTarget = ref<Bug | null>(null)
const duplicateBugTarget = ref<Bug | null>(null)
const deletingBug = ref(false)

// ── Breadcrumb ────────────────────────────────────────────────────────────────
const breadcrumbs = computed(() => {
  const project = projectsStore.current
  const group = projectGroupsStore.current
  const items: { label: string; to?: string }[] = []
  if (project?.project_group_id && group) {
    items.push({ label: 'Projektgruppen', to: '/project-groups' })
    items.push({ label: group.title, to: `/project-groups/${group.id}` })
  }
  items.push({ label: project?.title ?? '…', to: `/projects/${projectId}` })
  items.push({ label: 'Sprints', to: `/projects/${projectId}/sprints` })
  items.push({ label: sprintsStore.current?.name ?? '…' })
  return items
})

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString()
}

// ── Story points summary ──────────────────────────────────────────────────────
const totalPoints = computed(() =>
  storiesStore.userStories.reduce((s, us) => s + (us.story_points ?? 0), 0)
  + bugsStore.bugs.reduce((s, b) => s + (b.story_points ?? 0), 0),
)
const donePoints = computed(() =>
  storiesStore.userStories
    .filter((us) => us.status === 'done')
    .reduce((s, us) => s + (us.story_points ?? 0), 0)
  + bugsStore.bugs
    .filter((b) => b.status === 'done')
    .reduce((s, b) => s + (b.story_points ?? 0), 0),
)

// ── Story Kanban ──────────────────────────────────────────────────────────────
const storiesByStatus = computed(() => ({
  todo: [...storiesStore.userStories.filter((s) => s.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...storiesStore.userStories.filter((s) => s.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...storiesStore.userStories.filter((s) => s.status === 'done')].sort((a, b) => a.position - b.position),
  on_hold: [...storiesStore.userStories.filter((s) => s.status === 'on_hold')].sort((a, b) => a.position - b.position),
}))

const draggableTodo = ref<UserStory[]>([])
const draggableInProgress = ref<UserStory[]>([])
const draggableDone = ref<UserStory[]>([])
const draggableOnHold = ref<UserStory[]>([])
const isDragging = ref(false)
const showAllStories = ref(false)
const hiddenStoriesCount = computed(() =>
  [storiesByStatus.value.todo, storiesByStatus.value.in_progress, storiesByStatus.value.done, storiesByStatus.value.on_hold]
    .reduce((s, col) => s + Math.max(0, col.length - 5), 0)
)

watch(storiesByStatus, (val) => {
  if (isDragging.value) return
  draggableTodo.value = [...val.todo]
  draggableInProgress.value = [...val.in_progress]
  draggableDone.value = [...val.done]
  draggableOnHold.value = [...val.on_hold]
}, { immediate: true })

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
  } else if (evt.moved) {
    await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
  } else if (evt.removed) {
    await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
  }
}

async function quickStatusToggle(s: UserStory) {
  const next = s.status === 'todo' ? 'in_progress' : s.status === 'in_progress' ? 'done' : 'todo'
  await storiesStore.update(s.id, { status: next })
}

function storyLink(sid: string) {
  return `/user-stories/${sid}?referrer=/projects/${projectId.value}/sprints/${sprintId.value}`
}

// ── Bug Kanban ────────────────────────────────────────────────────────────────
const bugsByStatus = computed(() => ({
  todo: [...bugsStore.bugs.filter((b) => b.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...bugsStore.bugs.filter((b) => b.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...bugsStore.bugs.filter((b) => b.status === 'done')].sort((a, b) => a.position - b.position),
  on_hold: [...bugsStore.bugs.filter((b) => b.status === 'on_hold')].sort((a, b) => a.position - b.position),
}))

const draggableBugTodo = ref<Bug[]>([])
const draggableBugInProgress = ref<Bug[]>([])
const draggableBugDone = ref<Bug[]>([])
const draggableBugOnHold = ref<Bug[]>([])
const isBugDragging = ref(false)
const showAllBugs = ref(false)
const hiddenBugsCount = computed(() =>
  [bugsByStatus.value.todo, bugsByStatus.value.in_progress, bugsByStatus.value.done, bugsByStatus.value.on_hold]
    .reduce((s, col) => s + Math.max(0, col.length - 5), 0)
)

watch(bugsByStatus, (val) => {
  if (isBugDragging.value) return
  draggableBugTodo.value = [...val.todo]
  draggableBugInProgress.value = [...val.in_progress]
  draggableBugDone.value = [...val.done]
  draggableBugOnHold.value = [...val.on_hold]
}, { immediate: true })

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
  } else if (evt.moved) {
    await bugsStore.reorder(column.map((b, i) => ({ id: b.id, position: i })))
  } else if (evt.removed) {
    await bugsStore.reorder(column.map((b, i) => ({ id: b.id, position: i })))
  }
}

async function quickBugStatusToggle(b: Bug) {
  const next = b.status === 'todo' ? 'in_progress' : b.status === 'in_progress' ? 'done' : 'todo'
  await bugsStore.update(b.id, { status: next })
}

function bugLink(bid: string) {
  return `/bugs/${bid}?referrer=/projects/${projectId.value}/sprints/${sprintId.value}`
}

// ── Story CRUD handlers ───────────────────────────────────────────────────────
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

function handleStoryDuplicated(story: UserStory) {
  duplicateTarget.value = null
  router.push(storyLink(story.id))
}

// ── Bug CRUD handlers ─────────────────────────────────────────────────────────
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

function handleBugDuplicated(bug: Bug) {
  duplicateBugTarget.value = null
  router.push(bugLink(bug.id))
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadData(pid: string, sid: string) {
  await Promise.all([
    projectsStore.fetchOne(pid),
    sprintsStore.fetchOne(sid),
    storiesStore.fetchAll(undefined, sid),
    bugsStore.fetchAll(undefined, sid),
  ])
  if (projectsStore.current?.project_group_id) {
    await projectGroupsStore.fetchOne(projectsStore.current.project_group_id)
  } else {
    projectGroupsStore.current = null
  }
}

onMounted(() => loadData(projectId.value, sprintId.value))

watch([projectId, sprintId], ([pid, sid]) => loadData(pid, sid))
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="sprintsStore.loading" />

    <template v-else-if="sprintsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title flex items-center gap-2">
            <CalendarDaysIcon class="h-6 w-6 text-blue-500 flex-shrink-0" />
            {{ sprintsStore.current.name }}
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            {{ formatDate(sprintsStore.current.start_date) }} – {{ formatDate(sprintsStore.current.end_date) }}
          </p>
          <p v-if="sprintsStore.current.goal" class="text-sm text-gray-600 mt-1">
            {{ sprintsStore.current.goal }}
          </p>
        </div>
        <div class="flex items-center gap-4">
          <div v-if="totalPoints > 0" class="text-right">
            <p class="text-2xl font-bold text-gray-900">{{ donePoints }}/{{ totalPoints }}</p>
            <p class="text-xs text-gray-500">story points done</p>
          </div>
          <button class="btn-secondary btn-sm" @click="router.back()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
        </div>
      </div>

      <!-- User Stories Kanban -->
      <ErrorBanner v-if="storiesStore.error" :message="storiesStore.error" class="mb-4" />
      <div v-show="!storiesStore.loading && storiesStore.userStories.length > 0 && (hiddenStoriesCount > 0 || showAllStories)" class="flex justify-end mb-2">
        <label class="flex items-center gap-2 text-sm text-gray-500 cursor-pointer select-none">
          <input v-model="showAllStories" type="checkbox" class="h-4 w-4" />
          Alle anzeigen
          <span v-if="!showAllStories" class="text-gray-400">({{ hiddenStoriesCount }} weitere ausgeblendet)</span>
        </label>
      </div>
      <LoadingSpinner v-if="storiesStore.loading" />

      <EmptyState
        v-else-if="storiesStore.userStories.length === 0"
        title="No stories in this sprint"
        description="Assign user stories to this sprint from the Deliverable detail view."
      />

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- To Do -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            To Do ({{ storiesByStatus.todo.length }})
          </h3>
          <draggable v-model="draggableTodo" group="stories" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onStoryChange('todo', draggableTodo, evt)">
            <template #item="{ element: story, index }">
              <div v-show="showAllStories || index < 5" class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickStatusToggle(story)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-start gap-1">
                        <BookOpenIcon class="h-3.5 w-3.5 text-violet-500 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ story.title }}</RouterLink>
                      </div>
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
            <template #item="{ element: story, index }">
              <div v-show="showAllStories || index < 5" class="card group border-blue-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0" title="Mark done" @click="quickStatusToggle(story)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-start gap-1">
                        <BookOpenIcon class="h-3.5 w-3.5 text-violet-500 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ story.title }}</RouterLink>
                      </div>
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
            <template #item="{ element: story, index }">
              <div v-show="showAllStories || index < 5" class="card group opacity-75">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0" title="Mark to-do" @click="quickStatusToggle(story)">
                      <CheckCircleIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-start gap-1">
                        <BookOpenIcon class="h-3.5 w-3.5 text-violet-500 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2">{{ story.title }}</RouterLink>
                      </div>
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
            <template #item="{ element: story, index }">
              <div v-show="showAllStories || index < 5" class="card group border-yellow-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-start gap-1">
                        <BookOpenIcon class="h-3.5 w-3.5 text-violet-500 flex-shrink-0 mt-0.5" />
                        <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2">{{ story.title }}</RouterLink>
                      </div>
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
      <div v-if="bugsStore.bugs.length > 0 || bugsStore.loading" class="mt-8">
        <h2 class="section-title mb-3">Bugs</h2>
        <ErrorBanner v-if="bugsStore.error" :message="bugsStore.error" class="mb-4" />
        <div v-show="!bugsStore.loading && (hiddenBugsCount > 0 || showAllBugs)" class="flex justify-end mb-2">
          <label class="flex items-center gap-2 text-sm text-gray-500 cursor-pointer select-none">
            <input v-model="showAllBugs" type="checkbox" class="h-4 w-4" />
            Alle anzeigen
            <span v-if="!showAllBugs" class="text-gray-400">({{ hiddenBugsCount }} weitere ausgeblendet)</span>
          </label>
        </div>
        <LoadingSpinner v-if="bugsStore.loading" />

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

          <!-- Bug To Do -->
          <div>
            <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
              To Do ({{ bugsByStatus.todo.length }})
            </h3>
            <draggable v-model="draggableBugTodo" group="bugs" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onBugChange('todo', draggableBugTodo, evt)">
              <template #item="{ element: bug, index }">
                <div v-show="showAllBugs || index < 5" class="card group">
                  <div class="card-body py-3">
                    <div class="flex items-start gap-2">
                      <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                      <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickBugStatusToggle(bug)">
                        <ClockIcon class="h-4 w-4" />
                      </button>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-start gap-1">
                          <BugAntIcon class="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                          <RouterLink :to="bugLink(bug.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ bug.title }}</RouterLink>
                        </div>
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
              <template #item="{ element: bug, index }">
                <div v-show="showAllBugs || index < 5" class="card group border-blue-200">
                  <div class="card-body py-3">
                    <div class="flex items-start gap-2">
                      <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                      <button class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0" title="Mark done" @click="quickBugStatusToggle(bug)">
                        <ClockIcon class="h-4 w-4" />
                      </button>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-start gap-1">
                          <BugAntIcon class="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                          <RouterLink :to="bugLink(bug.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2">{{ bug.title }}</RouterLink>
                        </div>
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
              <template #item="{ element: bug, index }">
                <div v-show="showAllBugs || index < 5" class="card group opacity-75">
                  <div class="card-body py-3">
                    <div class="flex items-start gap-2">
                      <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                      <button class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0" title="Mark to-do" @click="quickBugStatusToggle(bug)">
                        <CheckCircleIcon class="h-4 w-4" />
                      </button>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-start gap-1">
                          <BugAntIcon class="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                          <RouterLink :to="bugLink(bug.id)" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2">{{ bug.title }}</RouterLink>
                        </div>
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
              <template #item="{ element: bug, index }">
                <div v-show="showAllBugs || index < 5" class="card group border-yellow-200">
                  <div class="card-body py-3">
                    <div class="flex items-start gap-2">
                      <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                      <div class="flex-1 min-w-0">
                        <div class="flex items-start gap-1">
                          <BugAntIcon class="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                          <RouterLink :to="bugLink(bug.id)" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2">{{ bug.title }}</RouterLink>
                        </div>
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

      </div>
    </template>

    <!-- Story modals -->
    <Modal :open="!!editTarget" title="Edit User Story" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <UserStoryForm
        v-if="editTarget"
        :deliverable-id="editTarget.deliverable_id"
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
    <Modal :open="!!editBugTarget" title="Edit Bug" @close="editBugTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <BugForm
        v-if="editBugTarget"
        :deliverable-id="editBugTarget.deliverable_id"
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
  </div>
</template>

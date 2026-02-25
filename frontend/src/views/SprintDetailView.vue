<script setup lang="ts">
import { onMounted, computed, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useSprintsStore } from '@/stores/sprints'
import { useUserStoriesStore } from '@/stores/userStories'
import { useApi } from '@/composables/useApi'
import type { UserStory, UserStoryCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import DuplicateUserStoryModal from '@/components/common/DuplicateUserStoryModal.vue'
import { ArrowLeftIcon, PencilSquareIcon, TrashIcon, DocumentDuplicateIcon, CheckCircleIcon, ClockIcon, Bars3Icon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.projectId as string)
const sprintId = computed(() => route.params.sprintId as string)

const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const sprintsStore = useSprintsStore()
const storiesStore = useUserStoriesStore()
const { loading: saving, error: saveError, execute } = useApi()

const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const duplicateTarget = ref<UserStory | null>(null)
const deleting = ref(false)

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
  storiesStore.userStories.reduce((s, us) => s + (us.story_points ?? 0), 0),
)
const donePoints = computed(() =>
  storiesStore.userStories
    .filter((us) => us.status === 'done')
    .reduce((s, us) => s + (us.story_points ?? 0), 0),
)

// ── Kanban ────────────────────────────────────────────────────────────────────
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

function storyLink(storyId: string) {
  return `/user-stories/${storyId}?referrer=/projects/${projectId.value}/sprints/${sprintId.value}`
}

// ── CRUD handlers ─────────────────────────────────────────────────────────────
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

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadData(pid: string, sid: string) {
  await Promise.all([
    projectsStore.fetchOne(pid),
    sprintsStore.fetchOne(sid),
    storiesStore.fetchAll(undefined, sid),
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
          <h1 class="page-title">{{ sprintsStore.current.name }}</h1>
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

      <ErrorBanner v-if="storiesStore.error" :message="storiesStore.error" class="mb-4" />
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
            <template #item="{ element: story }">
              <div class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickStatusToggle(story)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
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
                      <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
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
                      <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
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
                      <RouterLink :to="storyLink(story.id)" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2 block">{{ story.title }}</RouterLink>
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
    </template>

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
  </div>
</template>

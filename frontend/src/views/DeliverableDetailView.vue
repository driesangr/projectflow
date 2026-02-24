<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useUserStoriesStore } from '@/stores/userStories'
import { useApi } from '@/composables/useApi'
import type { UserStory, UserStoryCreate, DeliverableCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import DeliverableForm from '@/components/forms/DeliverableForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, DocumentDuplicateIcon, CheckCircleIcon, ClockIcon, Bars3Icon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
const deliverableId = route.params.deliverableId as string

const deliverablesStore = useDeliverablesStore()
const storiesStore = useUserStoriesStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditDeliverable = ref(false)
const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const deleting = ref(false)

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

async function onStoryChange(status: UserStory['status'], column: UserStory[], evt: any) {
  if (evt.added) {
    isDragging.value = true
    try {
      await storiesStore.update(evt.added.element.id, { status })
      await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
    } finally {
      isDragging.value = false
    }
  } else if (evt.moved || evt.removed) {
    await storiesStore.reorder(column.map((s, i) => ({ id: s.id, position: i })))
  }
}

async function quickStatusToggle(s: UserStory) {
  const next = s.status === 'todo' ? 'in_progress' : s.status === 'in_progress' ? 'done' : 'todo'
  await storiesStore.update(s.id, { status: next })
}

const breadcrumbs = computed(() => {
  const d = deliverablesStore.current
  return [
    { label: 'Projects', to: '/projects' },
    d ? { label: 'Topic', to: `/topics/${d.topic_id}` } : { label: 'Topic' },
    { label: d?.title ?? '…' },
  ]
})

const projectId = ref<string>('')

onMounted(async () => {
  await deliverablesStore.fetchOne(deliverableId)
  await storiesStore.fetchAll(deliverableId)

  if (deliverablesStore.current) {
    const { getTopic } = await import('@/api/topics')
    const topic = await getTopic(deliverablesStore.current.topic_id)
    projectId.value = topic.project_id
  }
})

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

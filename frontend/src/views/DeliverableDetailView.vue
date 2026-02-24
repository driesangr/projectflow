<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
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
import { PlusIcon, PencilSquareIcon, TrashIcon, ArrowUpIcon, ArrowDownIcon, Bars3Icon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const deliverableId = route.params.deliverableId as string

const deliverablesStore = useDeliverablesStore()
const storiesStore = useUserStoriesStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditDeliverable = ref(false)
const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const deleting = ref(false)

type StorySortKey = 'position' | 'status' | 'title' | 'created_at'
type SortDir = 'asc' | 'desc'
const storySortKey = ref<StorySortKey>('position')
const storySortDir = ref<SortDir>('asc')

const STORY_STATUS_ORDER: Record<string, number> = {
  todo: 0, in_progress: 1, done: 2, on_hold: 3,
}

const sortedStories = computed(() => {
  return [...storiesStore.userStories].sort((a, b) => {
    let result = 0
    if (storySortKey.value === 'position') {
      result = a.position - b.position
    } else if (storySortKey.value === 'status') {
      result = (STORY_STATUS_ORDER[a.status] ?? 99) - (STORY_STATUS_ORDER[b.status] ?? 99)
    } else if (storySortKey.value === 'title') {
      result = a.title.localeCompare(b.title)
    } else {
      result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    }
    return storySortDir.value === 'asc' ? result : -result
  })
})

const draggableStories = ref<typeof storiesStore.userStories>([])
watch(sortedStories, (val) => { draggableStories.value = [...val] }, { immediate: true })

async function onStoryDragEnd() {
  if (storySortKey.value !== 'position') return
  await storiesStore.reorder(draggableStories.value.map((s, idx) => ({ id: s.id, position: idx })))
}

const breadcrumbs = computed(() => {
  const d = deliverablesStore.current
  return [
    { label: 'Projects', to: '/projects' },
    d ? { label: 'Topic', to: `/topics/${d.topic_id}` } : { label: 'Topic' },
    { label: d?.title ?? '…' },
  ]
})

// We need the project_id for the UserStoryForm sprint selector
// We'll store it after fetching the deliverable → topic → project chain is complex,
// so we pass the topic_id as projectId proxy; the form fetches sprints by project
// Actually we need project_id. Let's derive it by fetching the topic.
const projectId = ref<string>('')

onMounted(async () => {
  await deliverablesStore.fetchOne(deliverableId)
  await storiesStore.fetchAll(deliverableId)

  // Fetch topic to get project_id for sprint selector
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
        <button class="btn-secondary btn-sm" @click="showEditDeliverable = true">
          <PencilSquareIcon class="h-4 w-4" />
          Edit Deliverable
        </button>
      </div>

      <p v-if="deliverablesStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ deliverablesStore.current.description }}
      </p>

      <!-- User Stories -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">User Stories</h2>
        <div class="flex items-center gap-2">
          <select v-model="storySortKey" class="form-select py-1 text-xs">
            <option value="position">Manuell</option>
            <option value="status">Status</option>
            <option value="title">Alphabetisch</option>
            <option value="created_at">Anlagedatum</option>
          </select>
          <button
            class="btn-icon"
            :title="storySortDir === 'asc' ? 'Aufsteigend' : 'Absteigend'"
            @click="storySortDir = storySortDir === 'asc' ? 'desc' : 'asc'"
          >
            <ArrowUpIcon v-if="storySortDir === 'asc'" class="h-3.5 w-3.5" />
            <ArrowDownIcon v-else class="h-3.5 w-3.5" />
          </button>
          <button class="btn-primary btn-sm" @click="showCreate = true">
            <PlusIcon class="h-3.5 w-3.5" />
            Add Story
          </button>
        </div>
      </div>

      <ErrorBanner v-if="storiesStore.error" :message="storiesStore.error" class="mb-3" />
      <LoadingSpinner v-if="storiesStore.loading" />

      <EmptyState v-else-if="storiesStore.userStories.length === 0" title="No user stories yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Story
        </button>
      </EmptyState>

      <draggable
        v-else
        v-model="draggableStories"
        class="space-y-2"
        item-key="id"
        handle=".drag-handle"
        animation="150"
        :disabled="storySortKey !== 'position'"
        @end="onStoryDragEnd"
      >
        <template #item="{ element: story }">
          <div class="card group">
            <div class="card-body">
              <div class="flex items-start gap-3">
                <Bars3Icon
                  v-if="storySortKey === 'position'"
                  class="drag-handle h-5 w-5 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <RouterLink
                      :to="`/user-stories/${story.id}`"
                      class="font-medium text-gray-900 hover:text-brand-600 truncate"
                    >
                      {{ story.title }}
                    </RouterLink>
                    <StatusBadge :status="story.status" />
                    <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                  </div>
                  <p v-if="story.description" class="text-sm text-gray-500 line-clamp-1">
                    {{ story.description }}
                  </p>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button class="btn-icon" @click="editTarget = story"><PencilSquareIcon class="h-4 w-4" /></button>
                  <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" @click="deleteTarget = story"><TrashIcon class="h-4 w-4" /></button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </draggable>
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

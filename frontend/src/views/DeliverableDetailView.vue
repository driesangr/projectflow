<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useUserStoriesStore } from '@/stores/userStories'
import { useApi } from '@/composables/useApi'
import type { UserStory, UserStoryCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import UserStoryForm from '@/components/forms/UserStoryForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const deliverableId = route.params.deliverableId as string

const deliverablesStore = useDeliverablesStore()
const storiesStore = useUserStoriesStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<UserStory | null>(null)
const deleteTarget = ref<UserStory | null>(null)
const deleting = ref(false)

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
          </div>
          <div class="mt-2 w-64">
            <MaturityBar :percent="deliverablesStore.current.maturity_percent" />
          </div>
        </div>
      </div>

      <p v-if="deliverablesStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ deliverablesStore.current.description }}
      </p>

      <!-- User Stories -->
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

      <div v-else class="space-y-2">
        <div v-for="story in storiesStore.userStories" :key="story.id" class="card group">
          <div class="card-body">
            <div class="flex items-start gap-3">
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
  </div>
</template>

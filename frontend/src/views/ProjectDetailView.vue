<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useTopicsStore } from '@/stores/topics'
import { useUserStoriesStore } from '@/stores/userStories'
import { useApi } from '@/composables/useApi'
import type { Topic, TopicCreate, UserStory, ProjectCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import TopicForm from '@/components/forms/TopicForm.vue'
import ProjectForm from '@/components/forms/ProjectForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, BoltIcon, ArrowUpIcon, ArrowDownIcon, Bars3Icon, TagIcon, BookOpenIcon } from '@heroicons/vue/24/outline'
import { useSprintsStore } from '@/stores/sprints'
import draggable from 'vuedraggable'

const route = useRoute()
const projectId = route.params.projectId as string

const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const topicsStore = useTopicsStore()
const storiesStore = useUserStoriesStore()
const sprintsStore = useSprintsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditProject = ref(false)
const editTarget = ref<Topic | null>(null)
const deleteTarget = ref<Topic | null>(null)
const deleting = ref(false)

type StorySortKey = 'business_value' | 'title' | 'story_points'
type SortDirection = 'asc' | 'desc'
const storySortKey = ref<StorySortKey>('business_value')
const storySortDir = ref<SortDirection>('desc')

const sortedProjectStories = computed(() => {
  return [...storiesStore.userStories].sort((a, b) => {
    let result = 0
    if (storySortKey.value === 'business_value') {
      result = (a.business_value ?? -1) - (b.business_value ?? -1)
    } else if (storySortKey.value === 'story_points') {
      result = (a.story_points ?? -1) - (b.story_points ?? -1)
    } else {
      result = a.title.localeCompare(b.title)
    }
    return storySortDir.value === 'asc' ? result : -result
  })
})

function sprintName(sprintId: string | null): string {
  if (!sprintId) return ''
  return sprintsStore.sprints.find(s => s.id === sprintId)?.name ?? ''
}

type SortKey = 'position' | 'business_value' | 'title' | 'created_at'
type SortDir = 'asc' | 'desc'
const sortKey = ref<SortKey>('position')
const sortDir = ref<SortDir>('asc')

const sortedTopics = computed(() => {
  return [...topicsStore.topics].sort((a, b) => {
    let result = 0
    if (sortKey.value === 'position') {
      result = a.position - b.position
    } else if (sortKey.value === 'business_value') {
      const aVal = a.business_value ?? -1
      const bVal = b.business_value ?? -1
      result = aVal - bVal
    } else if (sortKey.value === 'title') {
      result = a.title.localeCompare(b.title)
    } else {
      result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    }
    return sortDir.value === 'asc' ? result : -result
  })
})

// Local list used by draggable (only active when sortKey === 'position')
const draggableTopics = ref<typeof topicsStore.topics>([])
// Local list for story BV drag (only active when storySortKey === 'business_value')
const draggableProjectStories = ref<typeof storiesStore.userStories>([])
watch(sortedTopics, (val) => { draggableTopics.value = [...val] }, { immediate: true })
watch(sortedProjectStories, (val) => { draggableProjectStories.value = [...val] }, { immediate: true })

async function onTopicDragEnd() {
  if (sortKey.value !== 'position') return
  await topicsStore.reorder(draggableTopics.value.map((t, idx) => ({ id: t.id, position: idx })))
}

async function onProjectStoryDragEnd() {
  const n = draggableProjectStories.value.length
  await storiesStore.setValues(
    draggableProjectStories.value.map((s, i) => ({ id: s.id, business_value: (n - i) * 10 })),
  )
}

const breadcrumbs = computed(() => {
  const items: { label: string; to?: string }[] = []
  if (projectsStore.current?.project_group_id && projectGroupsStore.current) {
    items.push({ label: 'Projektgruppen', to: '/project-groups' })
    items.push({ label: projectGroupsStore.current.title, to: `/project-groups/${projectGroupsStore.current.id}` })
  } else {
    items.push({ label: 'Projects', to: '/projects' })
  }
  items.push({ label: projectsStore.current?.title ?? '…' })
  return items
})

onMounted(async () => {
  await projectsStore.fetchOne(projectId)
  if (projectsStore.current?.project_group_id) {
    await projectGroupsStore.fetchOne(projectsStore.current.project_group_id)
  }
  await Promise.all([
    topicsStore.fetchAll(projectId),
    storiesStore.fetchAll(undefined, undefined, projectId),
    sprintsStore.fetchAll(projectId),
  ])
})

async function handleProjectEdit(data: ProjectCreate) {
  const result = await execute(() => projectsStore.update(projectId, data))
  if (result) {
    showEditProject.value = false
    if (result.project_group_id) {
      await projectGroupsStore.fetchOne(result.project_group_id)
    } else {
      projectGroupsStore.current = null
    }
  }
}

async function handleCreate(data: TopicCreate) {
  const result = await execute(() => topicsStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: TopicCreate) {
  if (!editTarget.value) return
  const result = await execute(() => topicsStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await topicsStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="projectsStore.loading" />

    <template v-else-if="projectsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ projectsStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="projectsStore.current.status" />
            <StatusBadge :status="projectsStore.current.maturity_level" />
            <span v-if="projectsStore.current.owner_name" class="text-sm text-gray-500">
              {{ projectsStore.current.owner_name }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary" @click="showEditProject = true">
            <PencilSquareIcon class="h-4 w-4" />
            Bearbeiten
          </button>
          <RouterLink
            :to="`/projects/${projectId}/sprints`"
            class="btn-secondary"
          >
            <BoltIcon class="h-4 w-4" />
            Sprints
          </RouterLink>
        </div>
      </div>

      <p v-if="projectsStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ projectsStore.current.description }}
      </p>

      <!-- Topics section -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">Topics</h2>
        <div class="flex items-center gap-2">
          <select v-model="sortKey" class="form-select py-1 text-xs">
            <option value="position">Manuell</option>
            <option value="business_value">Business Value</option>
            <option value="title">Alphabetisch</option>
            <option value="created_at">Anlagedatum</option>
          </select>
          <button
            class="btn-icon"
            :title="sortDir === 'asc' ? 'Aufsteigend' : 'Absteigend'"
            @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
          >
            <ArrowUpIcon v-if="sortDir === 'asc'" class="h-3.5 w-3.5" />
            <ArrowDownIcon v-else class="h-3.5 w-3.5" />
          </button>
          <button class="btn-primary btn-sm" @click="showCreate = true">
            <PlusIcon class="h-3.5 w-3.5" />
            Add Topic
          </button>
        </div>
      </div>

      <ErrorBanner v-if="topicsStore.error" :message="topicsStore.error" class="mb-3" />
      <LoadingSpinner v-if="topicsStore.loading" />

      <EmptyState v-else-if="topicsStore.topics.length === 0" title="No topics yet" description="Topics group related deliverables.">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Topic
        </button>
      </EmptyState>

      <draggable
        v-else
        v-model="draggableTopics"
        class="space-y-2"
        item-key="id"
        handle=".drag-handle"
        animation="150"
        :disabled="sortKey !== 'position'"
        @end="onTopicDragEnd"
      >
        <template #item="{ element: topic }">
          <div class="card group">
            <div class="card-body">
              <div class="flex items-start gap-3">
                <Bars3Icon
                  v-if="sortKey === 'position'"
                  class="drag-handle h-5 w-5 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <TagIcon class="h-4 w-4 text-amber-500 flex-shrink-0" />
                    <RouterLink
                      :to="`/topics/${topic.id}`"
                      class="font-medium text-gray-900 hover:text-brand-600 truncate"
                    >
                      {{ topic.title }}
                    </RouterLink>
                    <StatusBadge :status="topic.priority" />
                  </div>
                  <p v-if="topic.description" class="text-sm text-gray-500 line-clamp-1 mb-2">
                    {{ topic.description }}
                  </p>
                  <MaturityBar :percent="topic.maturity_percent" />
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button class="btn-icon" title="Edit" @click="editTarget = topic">
                    <PencilSquareIcon class="h-4 w-4" />
                  </button>
                  <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" title="Delete" @click="deleteTarget = topic">
                    <TrashIcon class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </draggable>
      <!-- User Stories section -->
      <div class="flex items-center justify-between mt-8 mb-3">
        <h2 class="section-title mb-0">User Stories</h2>
        <div class="flex items-center gap-2">
          <select v-model="storySortKey" class="form-select py-1 text-xs">
            <option value="business_value">Business Value</option>
            <option value="story_points">Story Points</option>
            <option value="title">Alphabetisch</option>
          </select>
          <button
            class="btn-icon"
            :title="storySortDir === 'asc' ? 'Aufsteigend' : 'Absteigend'"
            @click="storySortDir = storySortDir === 'asc' ? 'desc' : 'asc'"
          >
            <ArrowUpIcon v-if="storySortDir === 'asc'" class="h-3.5 w-3.5" />
            <ArrowDownIcon v-else class="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <LoadingSpinner v-if="storiesStore.loading" />
      <EmptyState v-else-if="storiesStore.userStories.length === 0" title="No user stories yet" description="Add user stories in the Deliverable detail view." />
      <draggable
        v-else
        v-model="draggableProjectStories"
        class="space-y-1"
        item-key="id"
        handle=".drag-handle"
        animation="150"
        :disabled="storySortKey !== 'business_value'"
        @end="onProjectStoryDragEnd"
      >
        <template #item="{ element: story }">
          <div class="card">
            <div class="card-body py-2">
              <div class="flex items-center gap-2 min-w-0">
                <Bars3Icon
                  v-if="storySortKey === 'business_value'"
                  class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <BookOpenIcon class="h-3.5 w-3.5 text-violet-500 flex-shrink-0" />
                    <RouterLink :to="`/user-stories/${story.id}`" class="font-medium text-gray-900 hover:text-brand-600 truncate">
                      {{ story.title }}
                    </RouterLink>
                    <StatusBadge :status="story.status" />
                  </div>
                </div>
                <div class="flex items-center gap-3 flex-shrink-0 text-xs text-gray-400">
                  <span v-if="story.business_value != null">BV {{ story.business_value }}</span>
                  <span v-if="story.story_points">{{ story.story_points }} pts</span>
                  <span v-if="story.sprint_id" class="text-brand-600">{{ sprintName(story.sprint_id) }}</span>
                  <span v-if="story.owner_name">{{ story.owner_name }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </draggable>
    </template>

    <!-- Edit Project Modal -->
    <Modal :open="showEditProject" title="Projekt bearbeiten" @close="showEditProject = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectForm
        v-if="projectsStore.current"
        :initial="projectsStore.current"
        :loading="saving"
        @submit="handleProjectEdit"
        @cancel="showEditProject = false"
      />
    </Modal>

    <!-- Create Modal -->
    <Modal :open="showCreate" title="New Topic" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TopicForm :project-id="projectId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <!-- Edit Modal -->
    <Modal :open="!!editTarget" title="Edit Topic" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TopicForm
        v-if="editTarget"
        :project-id="projectId"
        :initial="editTarget"
        :loading="saving"
        @submit="handleEdit"
        @cancel="editTarget = null"
      />
    </Modal>

    <!-- Delete Confirm -->
    <ConfirmDelete
      :open="!!deleteTarget"
      :item-name="deleteTarget?.title ?? ''"
      :loading="deleting"
      @close="deleteTarget = null"
      @confirm="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useSprintsStore } from '@/stores/sprints'
import { useUserStoriesStore } from '@/stores/userStories'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const projectId = route.params.projectId as string
const sprintId = route.params.sprintId as string

const projectsStore = useProjectsStore()
const sprintsStore = useSprintsStore()
const storiesStore = useUserStoriesStore()

const breadcrumbs = computed(() => [
  { label: 'Projects', to: '/projects' },
  { label: projectsStore.current?.title ?? '…', to: `/projects/${projectId}` },
  { label: 'Sprints', to: `/projects/${projectId}/sprints` },
  { label: sprintsStore.current?.name ?? '…' },
])

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString()
}

const totalPoints = computed(() =>
  storiesStore.userStories.reduce((s, us) => s + (us.story_points ?? 0), 0),
)
const donePoints = computed(() =>
  storiesStore.userStories
    .filter((us) => us.status === 'done')
    .reduce((s, us) => s + (us.story_points ?? 0), 0),
)

type StorySortKey = 'sprint_value' | 'title' | 'story_points'
type SortDir = 'asc' | 'desc'
const storySortKey = ref<StorySortKey>('sprint_value')
const storySortDir = ref<SortDir>('desc')

const sortedStories = computed(() => {
  return [...storiesStore.userStories].sort((a, b) => {
    let result = 0
    if (storySortKey.value === 'sprint_value') {
      result = (a.sprint_value ?? -1) - (b.sprint_value ?? -1)
    } else if (storySortKey.value === 'story_points') {
      result = (a.story_points ?? -1) - (b.story_points ?? -1)
    } else {
      result = a.title.localeCompare(b.title)
    }
    return storySortDir.value === 'asc' ? result : -result
  })
})

onMounted(async () => {
  await Promise.all([
    projectsStore.fetchOne(projectId),
    sprintsStore.fetchOne(sprintId),
    storiesStore.fetchAll(undefined, sprintId),
  ])
})
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
        <!-- Points summary -->
        <div v-if="totalPoints > 0" class="text-right">
          <p class="text-2xl font-bold text-gray-900">{{ donePoints }}/{{ totalPoints }}</p>
          <p class="text-xs text-gray-500">story points done</p>
        </div>
      </div>

      <ErrorBanner v-if="storiesStore.error" :message="storiesStore.error" class="mb-4" />
      <LoadingSpinner v-if="storiesStore.loading" />

      <EmptyState
        v-else-if="storiesStore.userStories.length === 0"
        title="No stories in this sprint"
        description="Assign user stories to this sprint from the Deliverable detail view."
      />

      <template v-else>
        <div class="flex items-center justify-end gap-2 mb-3">
          <select v-model="storySortKey" class="form-select py-1 text-xs">
            <option value="sprint_value">Sprint Value</option>
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

      <div class="space-y-2">
        <div v-for="story in sortedStories" :key="story.id" class="card">
          <div class="card-body">
            <div class="flex items-center gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <RouterLink
                    :to="`/user-stories/${story.id}`"
                    class="font-medium text-gray-900 hover:text-brand-600 truncate"
                  >
                    {{ story.title }}
                  </RouterLink>
                  <StatusBadge :status="story.status" />
                  <span v-if="story.story_points" class="text-xs text-gray-400">{{ story.story_points }} pts</span>
                  <span v-if="story.sprint_value != null" class="text-xs text-brand-600">SV {{ story.sprint_value }}</span>
                </div>
                <p v-if="story.description" class="text-sm text-gray-500 mt-0.5 line-clamp-1">
                  {{ story.description }}
                </p>
              </div>
              <span v-if="story.owner_name" class="text-xs text-gray-400 flex-shrink-0">{{ story.owner_name }}</span>
            </div>
          </div>
        </div>
      </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useUserStoriesStore } from '@/stores/userStories'
import { useBugsStore } from '@/stores/bugs'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useTopicsStore } from '@/stores/topics'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useSprintsStore } from '@/stores/sprints'
import { useApi } from '@/composables/useApi'
import type { TaskCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskForm from '@/components/forms/TaskForm.vue'
import { PencilSquareIcon, TrashIcon, ArrowLeftIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId as string

const tasksStore = useTasksStore()
const storiesStore = useUserStoriesStore()
const bugsStore = useBugsStore()
const deliverablesStore = useDeliverablesStore()
const topicsStore = useTopicsStore()
const projectsStore = useProjectsStore()
const projectGroupsStore = useProjectGroupsStore()
const sprintsStore = useSprintsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showEdit = ref(false)
const showDelete = ref(false)
const deleting = ref(false)

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

const breadcrumbs = computed(() => {
  const task = tasksStore.current
  const story = storiesStore.current
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
  if (task?.bug_id) {
    items.push(deliverable && bug ? { label: deliverable.title, to: `/deliverables/${bug.deliverable_id}` } : { label: 'Deliverable' })
    items.push(bug && task ? { label: bug.title, to: `/bugs/${task.bug_id}` } : { label: 'Bug' })
  } else {
    items.push(deliverable && story ? { label: deliverable.title, to: `/deliverables/${story.deliverable_id}` } : { label: 'Deliverable' })
    items.push(story && task ? { label: story.title, to: `/user-stories/${task.user_story_id}` } : { label: 'User Story' })
  }
  items.push({ label: task?.title ?? '…' })
  return items
})

async function loadParentChain(deliverableId: string) {
  await deliverablesStore.fetchOne(deliverableId)
  if (deliverablesStore.current) {
    await topicsStore.fetchOne(deliverablesStore.current.topic_id)
    if (topicsStore.current) {
      await projectsStore.fetchOne(topicsStore.current.project_id)
      if (projectsStore.current?.project_group_id) {
        await projectGroupsStore.fetchOne(projectsStore.current.project_group_id)
      } else {
        projectGroupsStore.current = null
      }
    }
  }
}

onMounted(async () => {
  await tasksStore.fetchOne(taskId)
  if (tasksStore.current) {
    if (tasksStore.current.bug_id) {
      await bugsStore.fetchOne(tasksStore.current.bug_id)
      if (bugsStore.current) {
        await loadParentChain(bugsStore.current.deliverable_id)
      }
    } else if (tasksStore.current.user_story_id) {
      await storiesStore.fetchOne(tasksStore.current.user_story_id)
      if (storiesStore.current) {
        await loadParentChain(storiesStore.current.deliverable_id)
      }
    }
  }
  if (sprintRef.value) {
    await sprintsStore.fetchOne(sprintRef.value.sprintId)
  }
})

async function handleEdit(data: TaskCreate) {
  const result = await execute(() => tasksStore.update(taskId, data))
  if (result) showEdit.value = false
}

async function handleDelete() {
  deleting.value = true
  const task = tasksStore.current
  try {
    await tasksStore.remove(taskId)
    if (task?.bug_id) {
      router.push(`/bugs/${task.bug_id}`)
    } else {
      router.push(`/user-stories/${task?.user_story_id ?? ''}`)
    }
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />
    <Breadcrumb v-if="sprintBreadcrumbs.length" :items="sprintBreadcrumbs" />

    <LoadingSpinner v-if="tasksStore.loading" />

    <template v-else-if="tasksStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ tasksStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="tasksStore.current.status" />
            <span v-if="tasksStore.current.effort_hours" class="text-xs text-gray-500">
              {{ tasksStore.current.effort_hours }}h
            </span>
            <span v-if="tasksStore.current.sprint_value != null" class="text-xs text-gray-500">
              SV {{ tasksStore.current.sprint_value }}
            </span>
            <span v-if="tasksStore.current.owner_name" class="text-xs text-gray-500">
              {{ tasksStore.current.owner_name }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="router.back()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
          <button class="btn-secondary btn-sm" @click="showEdit = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Task
          </button>
          <button class="btn-danger btn-sm" @click="showDelete = true">
            <TrashIcon class="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      <div v-if="tasksStore.current.description" class="card card-body mb-6">
        <p class="text-sm font-medium text-gray-700 mb-1">Description</p>
        <p class="text-sm text-gray-600 whitespace-pre-line">{{ tasksStore.current.description }}</p>
      </div>
    </template>

    <Modal :open="showEdit" title="Edit Task" @close="showEdit = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TaskForm
        v-if="tasksStore.current"
        :user-story-id="tasksStore.current.user_story_id"
        :bug-id="tasksStore.current.bug_id"
        :initial="tasksStore.current"
        :loading="saving"
        @submit="handleEdit"
        @cancel="showEdit = false"
      />
    </Modal>

    <ConfirmDelete
      :open="showDelete"
      :item-name="tasksStore.current?.title ?? ''"
      :loading="deleting"
      @close="showDelete = false"
      @confirm="handleDelete"
    />
  </div>
</template>

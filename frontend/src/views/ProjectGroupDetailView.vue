<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useProjectsStore } from '@/stores/projects'
import { useApi } from '@/composables/useApi'
import type { ProjectGroupCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ProjectGroupForm from '@/components/forms/ProjectGroupForm.vue'
import { PencilSquareIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const groupId = route.params.groupId as string

const groupsStore = useProjectGroupsStore()
const projectsStore = useProjectsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showEdit = ref(false)

const breadcrumbs = computed(() => [
  { label: 'Projektgruppen', to: '/project-groups' },
  { label: groupsStore.current?.title ?? '…' },
])

const groupProjects = computed(() =>
  projectsStore.projects.filter((p) => p.project_group_id === groupId)
)

onMounted(async () => {
  await Promise.all([
    groupsStore.fetchOne(groupId),
    projectsStore.fetchAll(),
  ])
})

async function handleEdit(data: ProjectGroupCreate) {
  const result = await execute(() => groupsStore.update(groupId, data))
  if (result) showEdit.value = false
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="groupsStore.loading" />

    <template v-else-if="groupsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ groupsStore.current.title }}</h1>
          <p v-if="groupsStore.current.description" class="text-sm text-gray-500 mt-1">
            {{ groupsStore.current.description }}
          </p>
        </div>
        <button class="btn-secondary" @click="showEdit = true">
          <PencilSquareIcon class="h-4 w-4" />
          Bearbeiten
        </button>
      </div>

      <h2 class="section-title mt-6 mb-3">Projekte</h2>

      <LoadingSpinner v-if="projectsStore.loading" />

      <EmptyState
        v-else-if="groupProjects.length === 0"
        title="Keine Projekte in dieser Gruppe"
        description="Weisen Sie Projekten diese Gruppe in den Projekteinstellungen zu."
      />

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="project in groupProjects" :key="project.id" class="card">
          <div class="card-body flex flex-col gap-2">
            <RouterLink
              :to="`/projects/${project.id}`"
              class="text-base font-semibold text-gray-900 hover:text-brand-600 line-clamp-2"
            >
              {{ project.title }}
            </RouterLink>
            <p v-if="project.description" class="text-sm text-gray-500 line-clamp-2">
              {{ project.description }}
            </p>
            <div class="flex items-center gap-2 flex-wrap mt-auto pt-2 border-t border-gray-100">
              <StatusBadge :status="project.status" />
              <StatusBadge :status="project.maturity_level" />
            </div>
            <RouterLink
              :to="`/projects/${project.id}`"
              class="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 mt-1"
            >
              Details <ChevronRightIcon class="h-3 w-3" />
            </RouterLink>
          </div>
        </div>
      </div>
    </template>

    <!-- Edit Modal -->
    <Modal :open="showEdit" title="Projektgruppe bearbeiten" @close="showEdit = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectGroupForm
        v-if="groupsStore.current"
        :initial="groupsStore.current"
        :loading="saving"
        @submit="handleEdit"
        @cancel="showEdit = false"
      />
    </Modal>
  </div>
</template>

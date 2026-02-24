<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProjectsStore } from '@/stores/projects'
import { useApi } from '@/composables/useApi'
import type { Project, ProjectCreate } from '@/types'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ProjectForm from '@/components/forms/ProjectForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

const store = useProjectsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<Project | null>(null)
const deleteTarget = ref<Project | null>(null)
const deleting = ref(false)

onMounted(() => store.fetchAll())

async function handleCreate(data: ProjectCreate) {
  const result = await execute(() => store.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: ProjectCreate) {
  if (!editTarget.value) return
  const result = await execute(() => store.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await store.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Projects</h1>
      <button class="btn-primary" @click="showCreate = true">
        <PlusIcon class="h-4 w-4" />
        New Project
      </button>
    </div>

    <ErrorBanner v-if="store.error" :message="store.error" class="mb-4" />
    <LoadingSpinner v-if="store.loading" />

    <div v-else-if="store.projects.length === 0">
      <EmptyState title="No projects yet" description="Create your first project to get started.">
        <button class="btn-primary mt-4" @click="showCreate = true">
          <PlusIcon class="h-4 w-4" />
          New Project
        </button>
      </EmptyState>
    </div>

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="project in store.projects" :key="project.id" class="card group">
        <div class="card-body flex flex-col gap-2">
          <div class="flex items-start justify-between gap-2">
            <RouterLink
              :to="`/projects/${project.id}`"
              class="text-base font-semibold text-gray-900 hover:text-brand-600 flex-1 line-clamp-2"
            >
              {{ project.title }}
            </RouterLink>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
              <button class="btn-icon" title="Edit" @click="editTarget = project">
                <PencilSquareIcon class="h-4 w-4" />
              </button>
              <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" title="Delete" @click="deleteTarget = project">
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          <p v-if="project.description" class="text-sm text-gray-500 line-clamp-2">
            {{ project.description }}
          </p>

          <div class="flex items-center gap-2 flex-wrap mt-auto pt-2 border-t border-gray-100">
            <StatusBadge :status="project.status" />
            <StatusBadge :status="project.maturity_level" />
            <span v-if="project.owner_name" class="text-xs text-gray-400">{{ project.owner_name }}</span>
          </div>

          <RouterLink
            :to="`/projects/${project.id}`"
            class="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 mt-1"
          >
            View details <ChevronRightIcon class="h-3 w-3" />
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Modal :open="showCreate" title="New Project" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectForm :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <!-- Edit Modal -->
    <Modal :open="!!editTarget" title="Edit Project" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectForm
        v-if="editTarget"
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

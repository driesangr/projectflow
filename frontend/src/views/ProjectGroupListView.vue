<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useApi } from '@/composables/useApi'
import type { ProjectGroup, ProjectGroupCreate } from '@/types'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import ProjectGroupForm from '@/components/forms/ProjectGroupForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

const store = useProjectGroupsStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<ProjectGroup | null>(null)
const deleteTarget = ref<ProjectGroup | null>(null)
const deleting = ref(false)

onMounted(() => store.fetchAll())

async function handleCreate(data: ProjectGroupCreate) {
  const result = await execute(() => store.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: ProjectGroupCreate) {
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
      <h1 class="page-title">Projektgruppen</h1>
      <button class="btn-primary" @click="showCreate = true">
        <PlusIcon class="h-4 w-4" />
        Neue Gruppe
      </button>
    </div>

    <ErrorBanner v-if="store.error" :message="store.error" class="mb-4" />
    <LoadingSpinner v-if="store.loading" />

    <div v-else-if="store.projectGroups.length === 0">
      <EmptyState title="Keine Projektgruppen" description="Erstellen Sie die erste Projektgruppe.">
        <button class="btn-primary mt-4" @click="showCreate = true">
          <PlusIcon class="h-4 w-4" />
          Neue Gruppe
        </button>
      </EmptyState>
    </div>

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="group in store.projectGroups" :key="group.id" class="card group">
        <div class="card-body flex flex-col gap-2">
          <div class="flex items-start justify-between gap-2">
            <RouterLink
              :to="`/project-groups/${group.id}`"
              class="text-base font-semibold text-gray-900 hover:text-brand-600 flex-1 line-clamp-2"
            >
              {{ group.title }}
            </RouterLink>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
              <button class="btn-icon" title="Bearbeiten" @click="editTarget = group">
                <PencilSquareIcon class="h-4 w-4" />
              </button>
              <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" title="Löschen" @click="deleteTarget = group">
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          <p v-if="group.description" class="text-sm text-gray-500 line-clamp-2">
            {{ group.description }}
          </p>

          <RouterLink
            :to="`/project-groups/${group.id}`"
            class="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 mt-1"
          >
            Details <ChevronRightIcon class="h-3 w-3" />
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Modal :open="showCreate" title="Neue Projektgruppe" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectGroupForm :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <!-- Edit Modal -->
    <Modal :open="!!editTarget" title="Projektgruppe bearbeiten" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <ProjectGroupForm
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

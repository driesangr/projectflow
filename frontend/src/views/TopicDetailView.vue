<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTopicsStore } from '@/stores/topics'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useApi } from '@/composables/useApi'
import type { Deliverable, DeliverableCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import DeliverableForm from '@/components/forms/DeliverableForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const topicId = route.params.topicId as string

const topicsStore = useTopicsStore()
const deliverablesStore = useDeliverablesStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const editTarget = ref<Deliverable | null>(null)
const deleteTarget = ref<Deliverable | null>(null)
const deleting = ref(false)

const breadcrumbs = computed(() => {
  const topic = topicsStore.current
  return [
    { label: 'Projects', to: '/projects' },
    topic ? { label: 'Project', to: `/projects/${topic.project_id}` } : { label: 'Project' },
    { label: topic?.title ?? '…' },
  ]
})

onMounted(async () => {
  await topicsStore.fetchOne(topicId)
  await deliverablesStore.fetchAll(topicId)
})

async function handleCreate(data: DeliverableCreate) {
  const result = await execute(() => deliverablesStore.create(data))
  if (result) showCreate.value = false
}

async function handleEdit(data: DeliverableCreate) {
  if (!editTarget.value) return
  const result = await execute(() => deliverablesStore.update(editTarget.value!.id, data))
  if (result) editTarget.value = null
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deliverablesStore.remove(deleteTarget.value.id)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <LoadingSpinner v-if="topicsStore.loading" />

    <template v-else-if="topicsStore.current">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ topicsStore.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <StatusBadge :status="topicsStore.current.priority" />
            <MaturityBar :percent="topicsStore.current.maturity_percent" />
          </div>
        </div>
      </div>

      <p v-if="topicsStore.current.description" class="text-sm text-gray-600 mb-6">
        {{ topicsStore.current.description }}
      </p>

      <!-- Deliverables section -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">Deliverables</h2>
        <button class="btn-primary btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Deliverable
        </button>
      </div>

      <ErrorBanner v-if="deliverablesStore.error" :message="deliverablesStore.error" class="mb-3" />
      <LoadingSpinner v-if="deliverablesStore.loading" />

      <EmptyState v-else-if="deliverablesStore.deliverables.length === 0" title="No deliverables yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Deliverable
        </button>
      </EmptyState>

      <div v-else class="space-y-2">
        <div v-for="d in deliverablesStore.deliverables" :key="d.id" class="card group">
          <div class="card-body">
            <div class="flex items-start gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <RouterLink
                    :to="`/deliverables/${d.id}`"
                    class="font-medium text-gray-900 hover:text-brand-600 truncate"
                  >
                    {{ d.title }}
                  </RouterLink>
                  <StatusBadge :status="d.status" />
                  <span v-if="d.epic_points" class="text-xs text-gray-400">{{ d.epic_points }} pts</span>
                </div>
                <p v-if="d.description" class="text-sm text-gray-500 line-clamp-1 mb-2">
                  {{ d.description }}
                </p>
                <MaturityBar :percent="d.maturity_percent" />
              </div>
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <button class="btn-icon" @click="editTarget = d"><PencilSquareIcon class="h-4 w-4" /></button>
                <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" @click="deleteTarget = d"><TrashIcon class="h-4 w-4" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <Modal :open="showCreate" title="New Deliverable" @close="showCreate = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <DeliverableForm :topic-id="topicId" :loading="saving" @submit="handleCreate" @cancel="showCreate = false" />
    </Modal>

    <Modal :open="!!editTarget" title="Edit Deliverable" @close="editTarget = null">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <DeliverableForm
        v-if="editTarget"
        :topic-id="topicId"
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

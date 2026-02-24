<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTopicsStore } from '@/stores/topics'
import { useDeliverablesStore } from '@/stores/deliverables'
import { useApi } from '@/composables/useApi'
import type { Deliverable, DeliverableCreate, TopicCreate } from '@/types'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MaturityBar from '@/components/common/MaturityBar.vue'
import DeliverableForm from '@/components/forms/DeliverableForm.vue'
import TopicForm from '@/components/forms/TopicForm.vue'
import { PlusIcon, PencilSquareIcon, TrashIcon, ArrowUpIcon, ArrowDownIcon, Bars3Icon, DocumentDuplicateIcon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const topicId = route.params.topicId as string

const topicsStore = useTopicsStore()
const deliverablesStore = useDeliverablesStore()
const { loading: saving, error: saveError, execute } = useApi()

const showCreate = ref(false)
const showEditTopic = ref(false)
const editTarget = ref<Deliverable | null>(null)
const deleteTarget = ref<Deliverable | null>(null)
const deleting = ref(false)
const businessValue = ref<number | null>(null)

type DeliverableSortKey = 'position' | 'status' | 'title' | 'created_at'
type SortDir = 'asc' | 'desc'
const deliverableSortKey = ref<DeliverableSortKey>('position')
const deliverableSortDir = ref<SortDir>('asc')

const DELIVERABLE_STATUS_ORDER: Record<string, number> = {
  todo: 0, in_progress: 1, done: 2, on_hold: 3,
}

const sortedDeliverables = computed(() => {
  return [...deliverablesStore.deliverables].sort((a, b) => {
    let result = 0
    if (deliverableSortKey.value === 'position') {
      result = a.position - b.position
    } else if (deliverableSortKey.value === 'status') {
      result = (DELIVERABLE_STATUS_ORDER[a.status] ?? 99) - (DELIVERABLE_STATUS_ORDER[b.status] ?? 99)
    } else if (deliverableSortKey.value === 'title') {
      result = a.title.localeCompare(b.title)
    } else {
      result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    }
    return deliverableSortDir.value === 'asc' ? result : -result
  })
})

const draggableDeliverables = ref<typeof deliverablesStore.deliverables>([])
watch(sortedDeliverables, (val) => { draggableDeliverables.value = [...val] }, { immediate: true })

async function onDeliverableDragEnd() {
  if (deliverableSortKey.value !== 'position') return
  await deliverablesStore.reorder(draggableDeliverables.value.map((d, idx) => ({ id: d.id, position: idx })))
}

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
  businessValue.value = topicsStore.current?.business_value ?? null
  await deliverablesStore.fetchAll(topicId)
})

async function saveBusinessValue() {
  await topicsStore.update(topicId, { business_value: businessValue.value })
}

async function handleTopicEdit(data: TopicCreate) {
  const result = await execute(() => topicsStore.update(topicId, data))
  if (result) {
    businessValue.value = topicsStore.current?.business_value ?? null
    showEditTopic.value = false
  }
}

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

async function handleDuplicate(id: string) {
  await execute(() => deliverablesStore.duplicate(id))
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
        <button class="btn-secondary btn-sm" @click="showEditTopic = true">
          <PencilSquareIcon class="h-4 w-4" />
          Edit Topic
        </button>
      </div>

      <p v-if="topicsStore.current.description" class="text-sm text-gray-600 mb-4">
        {{ topicsStore.current.description }}
      </p>

      <div class="mb-6">
        <label class="form-label">Business Value</label>
        <input
          v-model.number="businessValue"
          type="number"
          min="0"
          class="form-input w-36"
          placeholder="0–100"
          @blur="saveBusinessValue"
        />
      </div>

      <!-- Deliverables section -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="section-title mb-0">Deliverables</h2>
        <div class="flex items-center gap-2">
          <select v-model="deliverableSortKey" class="form-select py-1 text-xs">
            <option value="position">Manuell</option>
            <option value="status">Status</option>
            <option value="title">Alphabetisch</option>
            <option value="created_at">Anlagedatum</option>
          </select>
          <button
            class="btn-icon"
            :title="deliverableSortDir === 'asc' ? 'Aufsteigend' : 'Absteigend'"
            @click="deliverableSortDir = deliverableSortDir === 'asc' ? 'desc' : 'asc'"
          >
            <ArrowUpIcon v-if="deliverableSortDir === 'asc'" class="h-3.5 w-3.5" />
            <ArrowDownIcon v-else class="h-3.5 w-3.5" />
          </button>
          <button class="btn-primary btn-sm" @click="showCreate = true">
            <PlusIcon class="h-3.5 w-3.5" />
            Add Deliverable
          </button>
        </div>
      </div>

      <ErrorBanner v-if="deliverablesStore.error" :message="deliverablesStore.error" class="mb-3" />
      <LoadingSpinner v-if="deliverablesStore.loading" />

      <EmptyState v-else-if="deliverablesStore.deliverables.length === 0" title="No deliverables yet">
        <button class="btn-primary mt-3 btn-sm" @click="showCreate = true">
          <PlusIcon class="h-3.5 w-3.5" />
          Add Deliverable
        </button>
      </EmptyState>

      <draggable
        v-else
        v-model="draggableDeliverables"
        class="space-y-2"
        item-key="id"
        handle=".drag-handle"
        animation="150"
        :disabled="deliverableSortKey !== 'position'"
        @end="onDeliverableDragEnd"
      >
        <template #item="{ element: d }">
          <div class="card group">
            <div class="card-body">
              <div class="flex items-start gap-3">
                <Bars3Icon
                  v-if="deliverableSortKey === 'position'"
                  class="drag-handle h-5 w-5 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5"
                />
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
                  <button class="btn-icon" title="Edit" @click="editTarget = d"><PencilSquareIcon class="h-4 w-4" /></button>
                  <button class="btn-icon" title="Duplicate" @click="handleDuplicate(d.id)"><DocumentDuplicateIcon class="h-4 w-4" /></button>
                  <button class="btn-icon text-red-500 hover:text-red-700 hover:bg-red-50" title="Delete" @click="deleteTarget = d"><TrashIcon class="h-4 w-4" /></button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </draggable>
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

    <!-- Edit Topic Modal -->
    <Modal :open="showEditTopic" title="Edit Topic" @close="showEditTopic = false">
      <ErrorBanner v-if="saveError" :message="saveError" class="mb-3" />
      <TopicForm
        v-if="topicsStore.current"
        :project-id="topicsStore.current.project_id"
        :initial="topicsStore.current"
        :loading="saving"
        @submit="handleTopicEdit"
        @cancel="showEditTopic = false"
      />
    </Modal>
  </div>
</template>

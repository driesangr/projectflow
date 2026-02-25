<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
import { PlusIcon, PencilSquareIcon, TrashIcon, DocumentDuplicateIcon, CheckCircleIcon, ClockIcon, Bars3Icon, ArrowLeftIcon } from '@heroicons/vue/24/outline'
import draggable from 'vuedraggable'

const route = useRoute()
const router = useRouter()
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

const deliverablesByStatus = computed(() => ({
  todo: [...deliverablesStore.deliverables.filter(d => d.status === 'todo')].sort((a, b) => a.position - b.position),
  in_progress: [...deliverablesStore.deliverables.filter(d => d.status === 'in_progress')].sort((a, b) => a.position - b.position),
  done: [...deliverablesStore.deliverables.filter(d => d.status === 'done')].sort((a, b) => a.position - b.position),
  on_hold: [...deliverablesStore.deliverables.filter(d => d.status === 'on_hold')].sort((a, b) => a.position - b.position),
}))

const draggableTodo = ref<Deliverable[]>([])
const draggableInProgress = ref<Deliverable[]>([])
const draggableDone = ref<Deliverable[]>([])
const draggableOnHold = ref<Deliverable[]>([])
const isDragging = ref(false)

watch(deliverablesByStatus, (val) => {
  if (isDragging.value) return
  draggableTodo.value = [...val.todo]
  draggableInProgress.value = [...val.in_progress]
  draggableDone.value = [...val.done]
  draggableOnHold.value = [...val.on_hold]
}, { immediate: true })

async function onDeliverableChange(status: Deliverable['status'], column: Deliverable[], evt: any) {
  if (evt.added) {
    isDragging.value = true
    try {
      await deliverablesStore.update(evt.added.element.id, { status })
      await deliverablesStore.reorder(column.map((d, i) => ({ id: d.id, position: i })))
      await topicsStore.fetchOne(topicId)
    } finally {
      isDragging.value = false
    }
  } else if (evt.moved || evt.removed) {
    await deliverablesStore.reorder(column.map((d, i) => ({ id: d.id, position: i })))
  }
}

async function quickStatusToggle(d: Deliverable) {
  const next = d.status === 'todo' ? 'in_progress' : d.status === 'in_progress' ? 'done' : 'todo'
  await deliverablesStore.update(d.id, { status: next })
  await topicsStore.fetchOne(topicId)
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
        <div class="flex items-center gap-2">
          <button class="btn-secondary btn-sm" @click="router.back()">
            <ArrowLeftIcon class="h-4 w-4" />
            Zurück
          </button>
          <button class="btn-secondary btn-sm" @click="showEditTopic = true">
            <PencilSquareIcon class="h-4 w-4" />
            Edit Topic
          </button>
        </div>
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

      <!-- Deliverables Kanban -->
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

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- To Do -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            To Do ({{ deliverablesByStatus.todo.length }})
          </h3>
          <draggable v-model="draggableTodo" group="deliverables" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onDeliverableChange('todo', draggableTodo, evt)">
            <template #item="{ element: d }">
              <div class="card group">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-gray-300 hover:text-blue-500 transition-colors flex-shrink-0" title="Mark in-progress" @click="quickStatusToggle(d)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/deliverables/${d.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ d.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="d.epic_points" class="text-xs text-gray-400">{{ d.epic_points }} pts</span>
                        <span v-if="d.business_value != null" class="text-xs text-gray-400">BV {{ d.business_value }}</span>
                      </div>
                      <div class="mt-1.5"><MaturityBar :percent="d.maturity_percent" /></div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" title="Edit" @click="editTarget = d"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" title="Duplicate" @click="handleDuplicate(d.id)"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" title="Delete" @click="deleteTarget = d"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- In Progress -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-blue-500 mb-2">
            In Progress ({{ deliverablesByStatus.in_progress.length }})
          </h3>
          <draggable v-model="draggableInProgress" group="deliverables" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onDeliverableChange('in_progress', draggableInProgress, evt)">
            <template #item="{ element: d }">
              <div class="card group border-blue-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-blue-400 hover:text-green-500 transition-colors flex-shrink-0" title="Mark done" @click="quickStatusToggle(d)">
                      <ClockIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/deliverables/${d.id}`" class="text-sm font-medium text-gray-800 hover:text-brand-600 line-clamp-2 block">{{ d.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="d.epic_points" class="text-xs text-gray-400">{{ d.epic_points }} pts</span>
                        <span v-if="d.business_value != null" class="text-xs text-gray-400">BV {{ d.business_value }}</span>
                      </div>
                      <div class="mt-1.5"><MaturityBar :percent="d.maturity_percent" /></div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" title="Edit" @click="editTarget = d"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" title="Duplicate" @click="handleDuplicate(d.id)"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" title="Delete" @click="deleteTarget = d"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Done -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">
            Done ({{ deliverablesByStatus.done.length }})
          </h3>
          <draggable v-model="draggableDone" group="deliverables" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onDeliverableChange('done', draggableDone, evt)">
            <template #item="{ element: d }">
              <div class="card group opacity-75">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <button class="mt-0.5 text-green-500 hover:text-gray-400 transition-colors flex-shrink-0" title="Mark to-do" @click="quickStatusToggle(d)">
                      <CheckCircleIcon class="h-4 w-4" />
                    </button>
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/deliverables/${d.id}`" class="text-sm font-medium text-gray-500 line-through hover:text-brand-600 line-clamp-2 block">{{ d.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="d.epic_points" class="text-xs text-gray-400">{{ d.epic_points }} pts</span>
                        <span v-if="d.business_value != null" class="text-xs text-gray-400">BV {{ d.business_value }}</span>
                      </div>
                      <div class="mt-1.5"><MaturityBar :percent="d.maturity_percent" /></div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" title="Edit" @click="editTarget = d"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" title="Duplicate" @click="handleDuplicate(d.id)"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" title="Delete" @click="deleteTarget = d"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- On Hold -->
        <div>
          <h3 class="text-xs font-semibold uppercase tracking-wider text-yellow-600 mb-2">
            On Hold ({{ deliverablesByStatus.on_hold.length }})
          </h3>
          <draggable v-model="draggableOnHold" group="deliverables" class="space-y-2 min-h-[2rem]" item-key="id" handle=".drag-handle" animation="150" @change="(evt) => onDeliverableChange('on_hold', draggableOnHold, evt)">
            <template #item="{ element: d }">
              <div class="card group border-yellow-200">
                <div class="card-body py-3">
                  <div class="flex items-start gap-2">
                    <Bars3Icon class="drag-handle h-4 w-4 flex-shrink-0 text-gray-300 cursor-grab active:cursor-grabbing mt-0.5" />
                    <div class="flex-1 min-w-0">
                      <RouterLink :to="`/deliverables/${d.id}`" class="text-sm font-medium text-gray-700 hover:text-brand-600 line-clamp-2 block">{{ d.title }}</RouterLink>
                      <div class="flex items-center gap-2 mt-1">
                        <span v-if="d.epic_points" class="text-xs text-gray-400">{{ d.epic_points }} pts</span>
                        <span v-if="d.business_value != null" class="text-xs text-gray-400">BV {{ d.business_value }}</span>
                      </div>
                      <div class="mt-1.5"><MaturityBar :percent="d.maturity_percent" /></div>
                    </div>
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button class="btn-icon" title="Edit" @click="editTarget = d"><PencilSquareIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon" title="Duplicate" @click="handleDuplicate(d.id)"><DocumentDuplicateIcon class="h-3.5 w-3.5" /></button>
                      <button class="btn-icon text-red-500 hover:bg-red-50" title="Delete" @click="deleteTarget = d"><TrashIcon class="h-3.5 w-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
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

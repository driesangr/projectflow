<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import { useProjectGroupsStore } from '@/stores/projectGroups'
import { useSprintsStore } from '@/stores/sprints'
import { useApi } from '@/composables/useApi'
import type { Project, ProjectGroupCreate } from '@/types'
import Modal from '@/components/common/Modal.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import ProjectGroupForm from '@/components/forms/ProjectGroupForm.vue'
import draggable from 'vuedraggable'
import {
  FolderIcon,
  ArrowRightStartOnRectangleIcon,
  RocketLaunchIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  PlusIcon,
  CalendarDaysIcon,
  TagIcon,
  ArchiveBoxIcon,
  BookOpenIcon,
  BugAntIcon,
  ListBulletIcon,
  Cog6ToothIcon,
  LockClosedIcon,
  DocumentTextIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const auth = useAuthStore()
const projectsStore = useProjectsStore()
const groupsStore = useProjectGroupsStore()
const sprintsStore = useSprintsStore()
const { loading: savingGroup, error: groupError, execute: execGroup } = useApi()

// ── Sprints ───────────────────────────────────────────────────────────────────
const sprintsExpanded = ref(false)

function sprintProjectName(projectId: string) {
  return projectsStore.projects.find((p) => p.id === projectId)?.title ?? ''
}

const visibleSprints = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  const all = sprintsStore.allSprints

  const past = all
    .filter((s) => s.end_date && s.end_date < today)
    .sort((a, b) => (b.end_date ?? '').localeCompare(a.end_date ?? ''))
    .slice(0, 1)

  const current = all.filter(
    (s) => s.start_date && s.start_date <= today && (!s.end_date || s.end_date >= today),
  )

  const future = all
    .filter((s) => s.start_date && s.start_date > today)
    .sort((a, b) => (a.start_date ?? '').localeCompare(b.start_date ?? ''))
    .slice(0, 5)

  // Sprints without any dates: show them too (up to 3)
  const undated = all
    .filter((s) => !s.start_date && !s.end_date)
    .slice(0, 3)

  return [...past, ...current, ...future, ...undated]
})

// ── Gruppe aufklappen/zuklappen ───────────────────────────────────────────────
const expandedGroups = ref<string[]>([])
function isExpanded(id: string) { return expandedGroups.value.includes(id) }
function toggleGroup(id: string) {
  const idx = expandedGroups.value.indexOf(id)
  if (idx === -1) expandedGroups.value.push(id)
  else expandedGroups.value.splice(idx, 1)
}

// ── Draggable Listen ──────────────────────────────────────────────────────────
// Eine reaktive Map groupId → Project[]
const lists = reactive<Record<string, Project[]>>({})
const ungrouped = reactive<Project[]>([])
const isDragging = ref(false)

function syncLists() {
  for (const g of groupsStore.projectGroups) {
    const projects = projectsStore.projects.filter((p) => p.project_group_id === g.id)
    if (lists[g.id]) {
      lists[g.id].splice(0, lists[g.id].length, ...projects)
    } else {
      lists[g.id] = [...projects]
    }
  }
  const ug = projectsStore.projects.filter((p) => !p.project_group_id)
  ungrouped.splice(0, ungrouped.length, ...ug)
}

watch(
  [() => projectsStore.projects, () => groupsStore.projectGroups],
  () => { if (!isDragging.value) syncLists() },
  { deep: true },
)

async function onGroupChange(groupId: string | null, evt: any) {
  if (!evt.added) return
  isDragging.value = true
  try {
    await projectsStore.update(evt.added.element.id, { project_group_id: groupId })
  } finally {
    isDragging.value = false
    syncLists()
  }
}

// ── Gruppe anlegen ────────────────────────────────────────────────────────────
const showCreateGroup = ref(false)

async function handleCreateGroup(data: ProjectGroupCreate) {
  const result = await execGroup(() => groupsStore.create(data))
  if (result) {
    showCreateGroup.value = false
    lists[result.id] = []
    expandedGroups.value.push(result.id)
  }
}

// ── Mount ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([projectsStore.fetchAll(), groupsStore.fetchAll()])
  expandedGroups.value = groupsStore.projectGroups.map((g) => g.id)
  syncLists()
  // Sprint-Fetch läuft im Hintergrund – blockiert die Gruppenanzeige nicht
  sprintsStore.fetchAllGlobal()
})

async function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="flex flex-col w-56 min-h-screen bg-gray-900 text-gray-100 py-4">
    <!-- Logo -->
    <div class="px-4 mb-6">
      <div class="flex items-center gap-2">
        <RocketLaunchIcon class="h-6 w-6 text-brand-400" />
        <span class="text-lg font-bold tracking-tight">ProjectFlow</span>
      </div>
    </div>

    <!-- Nav -->
    <div class="flex-1 px-2 overflow-y-auto space-y-0.5">

      <!-- Sprints-Section -->
      <div class="mb-2">
        <button
          class="flex w-full items-center gap-2 px-3 pt-1 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors"
          @click="sprintsExpanded = !sprintsExpanded"
        >
          <CalendarDaysIcon class="h-3.5 w-3.5 flex-shrink-0" />
          <span class="flex-1 text-left">Sprints</span>
          <ChevronDownIcon v-if="sprintsExpanded" class="h-3 w-3" />
          <ChevronRightIcon v-else class="h-3 w-3" />
        </button>

        <template v-if="sprintsExpanded">
          <p v-if="visibleSprints.length === 0" class="px-3 py-1 text-xs text-gray-600">
            Keine Sprints
          </p>
          <RouterLink
            v-for="sprint in visibleSprints"
            :key="sprint.id"
            :to="`/projects/${sprint.project_id}/sprints/${sprint.id}`"
            class="flex items-center gap-2 rounded-md pl-7 pr-3 py-1.5 text-xs text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            active-class="bg-gray-800 text-white"
          >
            <span class="flex-1 truncate">{{ sprint.name }}</span>
            <span class="text-gray-600 text-xs truncate max-w-[5rem]">{{ sprintProjectName(sprint.project_id) }}</span>
          </RouterLink>
        </template>
      </div>

      <!-- Gruppen-Header mit + Button -->
      <div class="flex items-center justify-between px-3 pt-1 pb-1">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Gruppen</span>
        <button
          class="text-gray-500 hover:text-white transition-colors"
          title="Neue Gruppe anlegen"
          @click="showCreateGroup = true"
        >
          <PlusIcon class="h-4 w-4" />
        </button>
      </div>

      <!-- Projektgruppen -->
      <template v-for="group in groupsStore.projectGroups" :key="group.id">
        <!-- Gruppen-Header (klappbar) -->
        <button
          class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
          @click="toggleGroup(group.id)"
        >
          <FolderIcon class="h-4 w-4 flex-shrink-0" />
          <span class="flex-1 text-left truncate">{{ group.title }}</span>
          <ChevronDownIcon v-if="isExpanded(group.id)" class="h-3.5 w-3.5 flex-shrink-0 text-gray-500" />
          <ChevronRightIcon v-else class="h-3.5 w-3.5 flex-shrink-0 text-gray-500" />
        </button>

        <!-- Projekte der Gruppe (drag & drop) -->
        <draggable
          v-if="isExpanded(group.id)"
          v-model="lists[group.id]"
          :group="{ name: 'projects', pull: true, put: true }"
          item-key="id"
          class="min-h-[1.5rem]"
          ghost-class="opacity-40"
          @change="(evt) => onGroupChange(group.id, evt)"
        >
          <template #item="{ element: project }">
            <RouterLink
              :to="`/projects/${project.id}`"
              class="flex items-center gap-2 rounded-md pl-9 pr-3 py-1.5 text-xs font-medium text-gray-400 hover:bg-gray-800 hover:text-white transition-colors cursor-grab active:cursor-grabbing"
              active-class="bg-gray-800 text-white"
            >
              <span class="truncate">{{ project.title }}</span>
            </RouterLink>
          </template>
        </draggable>
      </template>

      <!-- Ohne Gruppe -->
      <div class="mt-2">
        <div class="px-3 py-1">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Projekte ohne Gruppe</span>
        </div>
        <draggable
          v-model="ungrouped"
          :group="{ name: 'projects', pull: true, put: true }"
          item-key="id"
          class="min-h-[1.5rem]"
          ghost-class="opacity-40"
          @change="(evt) => onGroupChange(null, evt)"
        >
          <template #item="{ element: project }">
            <RouterLink
              :to="`/projects/${project.id}`"
              class="flex items-center gap-2 rounded-md pl-9 pr-3 py-1.5 text-xs font-medium text-gray-400 hover:bg-gray-800 hover:text-white transition-colors cursor-grab active:cursor-grabbing"
              active-class="bg-gray-800 text-white"
            >
              <span class="truncate">{{ project.title }}</span>
            </RouterLink>
          </template>
        </draggable>
      </div>

    </div>

    <!-- Dokumentation -->
    <div class="px-2 border-t border-gray-800 pt-2 pb-1">
      <a
        href="/docs/enduser-guide.html"
        target="_blank"
        rel="noopener"
        class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
      >
        <DocumentTextIcon class="h-5 w-5" />
        Dokumentation
      </a>
    </div>

    <!-- Artefakt-Legende -->
    <div class="px-2 border-t border-gray-800 pt-3 pb-2">
      <p class="px-3 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">Legende</p>
      <div class="space-y-0.5">
        <div class="flex items-center gap-2 px-3 py-1">
          <CalendarDaysIcon class="h-3.5 w-3.5 text-blue-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">Sprint</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1">
          <TagIcon class="h-3.5 w-3.5 text-amber-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">Topic</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1">
          <ArchiveBoxIcon class="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">Deliverable</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1">
          <BookOpenIcon class="h-3.5 w-3.5 text-violet-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">User Story</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1">
          <BugAntIcon class="h-3.5 w-3.5 text-red-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">Bug</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1">
          <ListBulletIcon class="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
          <span class="text-xs text-gray-400">Task</span>
        </div>
      </div>
    </div>

    <!-- Konfiguration (nur Admin+) -->
    <div
      v-if="auth.user?.global_role === 'admin' || auth.user?.global_role === 'superuser'"
      class="px-2 border-t border-gray-800 pt-2"
    >
      <RouterLink
        to="/config/users"
        class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        active-class="bg-gray-800 text-white"
      >
        <Cog6ToothIcon class="h-5 w-5" />
        Benutzer
      </RouterLink>
      <RouterLink
        to="/config/permissions"
        class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        active-class="bg-gray-800 text-white"
      >
        <LockClosedIcon class="h-5 w-5" />
        Berechtigungen
      </RouterLink>
    </div>

    <!-- Logout -->
    <div class="px-2 border-t border-gray-800 pt-3 space-y-1">
      <button
        class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        @click="logout"
      >
        <ArrowRightStartOnRectangleIcon class="h-5 w-5" />
        Logout
      </button>
    </div>
  </nav>

  <!-- Neue Gruppe Modal -->
  <Modal :open="showCreateGroup" title="Neue Projektgruppe" @close="showCreateGroup = false">
    <ErrorBanner v-if="groupError" :message="groupError" class="mb-3" />
    <ProjectGroupForm :loading="savingGroup" @submit="handleCreateGroup" @cancel="showCreateGroup = false" />
  </Modal>
</template>

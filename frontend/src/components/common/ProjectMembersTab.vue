<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listMembers, addMember, updateMember, removeMember, listPotentialMembers } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import type { MembershipResponse, UserPublic, ProjectRole } from '@/types'
import { TrashIcon, PlusIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{ projectId: string }>()
const auth = useAuthStore()

const members = ref<MembershipResponse[]>([])
const allUsers = ref<UserPublic[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const showAdd = ref(false)
const addUserId = ref('')
const addRole = ref<ProjectRole>('member')
const adding = ref(false)

const roleLabel: Record<string, string> = { owner: 'Owner', manager: 'Manager', member: 'Member', viewer: 'Viewer' }
const roleColor: Record<string, string> = {
  owner:   'bg-amber-100 text-amber-700',
  manager: 'bg-indigo-100 text-indigo-700',
  member:  'bg-green-100 text-green-700',
  viewer:  'bg-gray-100 text-gray-500',
}

// Darf der aktuelle User Mitglieder verwalten?
const canManage = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    members.value = await listMembers(props.projectId)
    const myMembership = members.value.find(m => m.user.id === auth.user?.id)
    canManage.value = auth.user?.global_role === 'superuser'
      || myMembership?.role === 'owner'

    if (canManage.value) {
      allUsers.value = await listPotentialMembers(props.projectId)
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}

const nonMembers = () => {
  // listPotentialMembers already returns only non-members; filter locally for race condition safety
  const memberIds = new Set(members.value.map(m => m.user.id))
  return allUsers.value.filter(u => !memberIds.has(u.id))
}

async function changeRole(member: MembershipResponse, role: ProjectRole) {
  error.value = null
  try {
    const updated = await updateMember(props.projectId, member.user.id, { role })
    const idx = members.value.findIndex(m => m.id === member.id)
    if (idx !== -1) members.value[idx] = updated
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Fehler beim Speichern'
  }
}

async function remove(member: MembershipResponse) {
  if (!confirm(`${member.user.username} wirklich entfernen?`)) return
  error.value = null
  try {
    await removeMember(props.projectId, member.user.id)
    members.value = members.value.filter(m => m.id !== member.id)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Fehler beim Entfernen'
  }
}

async function add() {
  if (!addUserId.value) return
  adding.value = true
  error.value = null
  try {
    const membership = await addMember(props.projectId, { user_id: addUserId.value, role: addRole.value })
    members.value.push(membership)
    addUserId.value = ''
    addRole.value = 'member'
    showAdd.value = false
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Fehler beim Hinzufügen'
  } finally {
    adding.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-700">{{ members.length }} Mitglieder</h3>
      <button v-if="canManage" class="btn-secondary flex items-center gap-1 text-xs" @click="showAdd = !showAdd">
        <PlusIcon class="h-3.5 w-3.5" />
        Mitglied hinzufügen
      </button>
    </div>

    <ErrorBanner v-if="error" :message="error" />

    <!-- Hinzufügen-Formular -->
    <div v-if="showAdd && canManage" class="rounded-lg border border-indigo-100 bg-indigo-50 p-4 space-y-3">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Benutzer</label>
          <select v-model="addUserId" class="input w-full text-sm">
            <option value="">– Benutzer wählen –</option>
            <option v-for="u in nonMembers()" :key="u.id" :value="u.id">
              {{ u.full_name || u.username }} ({{ u.username }})
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Rolle</label>
          <select v-model="addRole" class="input w-full text-sm">
            <option value="viewer">Viewer</option>
            <option value="member">Member</option>
            <option value="manager">Manager</option>
            <option value="owner">Owner</option>
          </select>
        </div>
      </div>
      <div class="flex justify-end gap-2">
        <button class="btn-secondary text-xs" @click="showAdd = false">Abbrechen</button>
        <button class="btn-primary text-xs" :disabled="!addUserId || adding" @click="add">
          {{ adding ? 'Wird hinzugefügt…' : 'Hinzufügen' }}
        </button>
      </div>
    </div>

    <!-- Mitgliederliste -->
    <div v-if="loading" class="flex justify-center py-6">
      <LoadingSpinner />
    </div>

    <ul v-else class="divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white overflow-hidden">
      <li v-if="members.length === 0" class="px-4 py-6 text-center text-sm text-gray-400">
        Noch keine Mitglieder
      </li>
      <li v-for="m in members" :key="m.id" class="flex items-center gap-3 px-4 py-3">
        <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
          {{ (m.user.full_name || m.user.username).slice(0, 2).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">{{ m.user.full_name || m.user.username }}</p>
          <p class="text-xs text-gray-500 truncate">{{ m.user.email }}</p>
        </div>

        <!-- Rolle ändern (nur für Owner/Admin) -->
        <select
          v-if="canManage"
          :value="m.role"
          class="input text-xs py-1"
          @change="changeRole(m, ($event.target as HTMLSelectElement).value as ProjectRole)"
        >
          <option value="viewer">Viewer</option>
          <option value="member">Member</option>
          <option value="manager">Manager</option>
          <option value="owner">Owner</option>
        </select>
        <span v-else class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" :class="roleColor[m.role]">
          {{ roleLabel[m.role] }}
        </span>

        <button
          v-if="canManage && m.user.id !== auth.user?.id"
          class="btn-icon text-red-400 hover:text-red-600"
          title="Entfernen"
          @click="remove(m)"
        >
          <TrashIcon class="h-4 w-4" />
        </button>
      </li>
    </ul>
  </div>
</template>

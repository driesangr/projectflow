<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import Modal from '@/components/common/Modal.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDelete from '@/components/common/ConfirmDelete.vue'
import type { UserResponse, GlobalRole } from '@/types'
import {
  PlusIcon, PencilSquareIcon, TrashIcon,
  CheckCircleIcon, XCircleIcon, MagnifyingGlassIcon
} from '@heroicons/vue/24/outline'

const store = useUsersStore()
const auth = useAuthStore()
const isSuperuser = computed(() => auth.user?.global_role === 'superuser')

// ── Filter ────────────────────────────────────────────────────────────────────
const search = ref('')
const filterRole = ref<GlobalRole | ''>('')
const filterActive = ref<'all' | 'active' | 'inactive'>('active')

const filtered = computed(() => store.users.filter(u => {
  if (search.value && !u.username.toLowerCase().includes(search.value.toLowerCase())
      && !u.email.toLowerCase().includes(search.value.toLowerCase())
      && !(u.full_name?.toLowerCase().includes(search.value.toLowerCase()))) return false
  if (filterRole.value && u.global_role !== filterRole.value) return false
  if (filterActive.value === 'active' && !u.is_active) return false
  if (filterActive.value === 'inactive' && u.is_active) return false
  return true
}))

// ── User anlegen / bearbeiten ─────────────────────────────────────────────────
const showForm = ref(false)
const editUser = ref<UserResponse | null>(null)
const formSaving = ref(false)
const formError = ref<string | null>(null)

const form = ref({
  username: '', email: '', full_name: '', password: '', global_role: 'user' as GlobalRole, is_active: true,
})

function openCreate() {
  editUser.value = null
  form.value = { username: '', email: '', full_name: '', password: '', global_role: 'user', is_active: true }
  formError.value = null
  showForm.value = true
}

function openEdit(user: UserResponse) {
  editUser.value = user
  form.value = { username: user.username, email: user.email, full_name: user.full_name ?? '', password: '', global_role: user.global_role, is_active: user.is_active }
  formError.value = null
  showForm.value = true
}

async function saveForm() {
  formError.value = null
  formSaving.value = true
  try {
    if (editUser.value) {
      const payload: any = { email: form.value.email, full_name: form.value.full_name || null, global_role: form.value.global_role, is_active: form.value.is_active }
      if (form.value.password) payload.password = form.value.password
      const ok = await store.update(editUser.value.id, payload)
      if (!ok) { formError.value = store.error; return }
    } else {
      if (!form.value.password) { formError.value = 'Passwort ist erforderlich'; return }
      const ok = await store.create({ username: form.value.username, email: form.value.email, full_name: form.value.full_name || null, password: form.value.password, global_role: form.value.global_role })
      if (!ok) { formError.value = store.error; return }
    }
    showForm.value = false
  } finally {
    formSaving.value = false
  }
}

// ── Löschen ───────────────────────────────────────────────────────────────────
const deleteTarget = ref<UserResponse | null>(null)
const deleting = ref(false)

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  await store.remove(deleteTarget.value.id)
  deleting.value = false
  deleteTarget.value = null
}

const roleLabel: Record<string, string> = { superuser: 'Superuser', admin: 'Admin', user: 'User' }
const roleColor: Record<string, string> = {
  superuser: 'bg-purple-100 text-purple-700',
  admin: 'bg-blue-100 text-blue-700',
  user: 'bg-gray-100 text-gray-600',
}

onMounted(() => store.fetchAll())
</script>

<template>
  <div class="max-w-5xl mx-auto py-8 px-4 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Benutzerverwaltung</h1>
        <p class="text-sm text-gray-500 mt-1">{{ store.users.length }} Benutzer insgesamt</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="openCreate">
        <PlusIcon class="h-4 w-4" />
        Neuer Benutzer
      </button>
    </div>

    <ErrorBanner v-if="store.error" :message="store.error" />

    <!-- Filter -->
    <div class="flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-48">
        <MagnifyingGlassIcon class="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
        <input v-model="search" type="text" placeholder="Suche…" class="input pl-9 w-full" />
      </div>
      <select v-model="filterRole" class="input">
        <option value="">Alle Rollen</option>
        <option value="superuser">Superuser</option>
        <option value="admin">Admin</option>
        <option value="user">User</option>
      </select>
      <select v-model="filterActive" class="input">
        <option value="all">Alle</option>
        <option value="active">Aktiv</option>
        <option value="inactive">Inaktiv</option>
      </select>
    </div>

    <!-- Tabelle -->
    <div v-if="store.loading" class="flex justify-center py-12">
      <LoadingSpinner />
    </div>

    <div v-else class="rounded-xl border border-gray-200 overflow-hidden bg-white">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">Benutzer</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">E-Mail</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">Rolle</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
            <th class="px-4 py-3 text-right font-semibold text-gray-600">Aktionen</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="filtered.length === 0">
            <td colspan="5" class="px-4 py-8 text-center text-gray-400">Keine Benutzer gefunden</td>
          </tr>
          <tr v-for="user in filtered" :key="user.id" class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <div class="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {{ (user.full_name || user.username).slice(0, 2).toUpperCase() }}
                </div>
                <div>
                  <p class="font-medium text-gray-900">{{ user.username }}</p>
                  <p v-if="user.full_name" class="text-xs text-gray-500">{{ user.full_name }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ user.email }}</td>
            <td class="px-4 py-3">
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" :class="roleColor[user.global_role]">
                {{ roleLabel[user.global_role] }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span class="inline-flex items-center gap-1 text-xs" :class="user.is_active ? 'text-green-600' : 'text-gray-400'">
                <CheckCircleIcon v-if="user.is_active" class="h-3.5 w-3.5" />
                <XCircleIcon v-else class="h-3.5 w-3.5" />
                {{ user.is_active ? 'Aktiv' : 'Inaktiv' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <button class="btn-icon" title="Bearbeiten" @click="openEdit(user)">
                  <PencilSquareIcon class="h-4 w-4" />
                </button>
                <button
                  v-if="isSuperuser && user.id !== auth.user?.id"
                  class="btn-icon text-red-500 hover:text-red-700"
                  title="Löschen"
                  @click="deleteTarget = user"
                >
                  <TrashIcon class="h-4 w-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Formular Modal -->
  <Modal :open="showForm" :title="editUser ? 'Benutzer bearbeiten' : 'Neuer Benutzer'" @close="showForm = false">
    <div class="space-y-4">
      <ErrorBanner v-if="formError" :message="formError" />

      <div v-if="!editUser">
        <label class="block text-sm font-medium text-gray-700 mb-1">Benutzername *</label>
        <input v-model="form.username" type="text" class="input w-full" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
        <input v-model="form.full_name" type="text" class="input w-full" placeholder="Max Mustermann" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">E-Mail *</label>
        <input v-model="form.email" type="email" class="input w-full" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Passwort {{ editUser ? '(leer = unverändert)' : '*' }}
        </label>
        <input v-model="form.password" type="password" class="input w-full" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Globale Rolle</label>
        <select v-model="form.global_role" class="input w-full">
          <option value="user">User (Standard)</option>
          <option value="admin">Admin</option>
          <option v-if="isSuperuser" value="superuser">Superuser</option>
        </select>
      </div>
      <div v-if="editUser" class="flex items-center gap-2">
        <input id="is_active" v-model="form.is_active" type="checkbox" class="rounded" />
        <label for="is_active" class="text-sm text-gray-700">Konto aktiv</label>
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <button class="btn-secondary" @click="showForm = false">Abbrechen</button>
        <button class="btn-primary" :disabled="formSaving" @click="saveForm">
          {{ formSaving ? 'Speichert…' : 'Speichern' }}
        </button>
      </div>
    </div>
  </Modal>

  <!-- Löschen Bestätigung -->
  <ConfirmDelete
    :open="!!deleteTarget"
    :item-name="deleteTarget?.username ?? ''"
    :loading="deleting"
    @confirm="confirmDelete"
    @close="deleteTarget = null"
  />
</template>

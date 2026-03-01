<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { updateUser } from '@/api/users'
import { listMembers } from '@/api/users'
import { useProjectsStore } from '@/stores/projects'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import PasswordInput from '@/components/common/PasswordInput.vue'
import type { MembershipResponse } from '@/types'

const auth = useAuthStore()
const projectsStore = useProjectsStore()

const saving = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

const form = ref({
  full_name: auth.user?.full_name ?? '',
  email: auth.user?.email ?? '',
  password: '',
  password_confirm: '',
})

const roleLabel: Record<string, string> = {
  superuser: 'Superuser',
  admin: 'Administrator',
  user: 'Benutzer',
}

const projectRoleLabel: Record<string, string> = {
  owner: 'Owner',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

async function save() {
  if (!auth.user) return
  error.value = null
  success.value = false

  if (form.value.password && form.value.password !== form.value.password_confirm) {
    error.value = 'Die Passwörter stimmen nicht überein.'
    return
  }

  saving.value = true
  try {
    const payload: any = {
      full_name: form.value.full_name || null,
      email: form.value.email,
    }
    if (form.value.password) payload.password = form.value.password

    const updated = await updateUser(auth.user.id, payload)
    auth.user = updated as any
    form.value.password = ''
    form.value.password_confirm = ''
    success.value = true
    setTimeout(() => success.value = false, 3000)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Fehler beim Speichern'
  } finally {
    saving.value = false
  }
}

// Projektmitgliedschaften laden – wir rufen für jedes Projekt die Mitglieder ab
// und filtern nach dem eigenen User
const memberships = ref<{ project_title: string; role: string }[]>([])

onMounted(async () => {
  await projectsStore.fetchAll()
  const myId = auth.user?.id
  if (!myId) return

  const results: { project_title: string; role: string }[] = []
  for (const project of projectsStore.projects) {
    try {
      const members = await listMembers(project.id)
      const mine = members.find(m => m.user.id === myId)
      if (mine) {
        results.push({ project_title: project.title, role: mine.role })
      }
    } catch { /* ignore */ }
  }
  memberships.value = results
})
</script>

<template>
  <div class="max-w-2xl mx-auto py-8 px-4 space-y-8">
    <h1 class="text-2xl font-bold text-gray-900">Mein Profil</h1>

    <!-- Rolle Badge -->
    <div class="rounded-xl bg-white border border-gray-200 p-5 space-y-4">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide">Konto</h2>
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 rounded-full bg-indigo-600 text-white flex items-center justify-center text-lg font-bold">
          {{ (auth.user?.full_name || auth.user?.username || '?').slice(0, 2).toUpperCase() }}
        </div>
        <div>
          <p class="font-semibold text-gray-900">{{ auth.user?.username }}</p>
          <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
            :class="{
              'bg-purple-100 text-purple-700': auth.user?.global_role === 'superuser',
              'bg-blue-100 text-blue-700':     auth.user?.global_role === 'admin',
              'bg-gray-100 text-gray-600':     auth.user?.global_role === 'user',
            }"
          >
            {{ roleLabel[auth.user?.global_role ?? 'user'] }}
          </span>
        </div>
      </div>
    </div>

    <!-- Profildaten bearbeiten -->
    <div class="rounded-xl bg-white border border-gray-200 p-5 space-y-4">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide">Profildaten bearbeiten</h2>
      <ErrorBanner v-if="error" :message="error" />
      <div v-if="success" class="rounded-lg bg-green-50 border border-green-200 px-4 py-2 text-sm text-green-700">
        ✓ Erfolgreich gespeichert
      </div>

      <div class="space-y-3">
        <div>
          <label class="form-label">Name</label>
          <input v-model="form.full_name" type="text" class="form-input" placeholder="Max Mustermann" />
        </div>
        <div>
          <label class="form-label">E-Mail</label>
          <input v-model="form.email" type="email" class="form-input" />
        </div>
        <div class="border-t border-gray-100 pt-3">
          <p class="text-xs text-gray-500 mb-2">Passwort ändern (leer lassen = kein Wechsel)</p>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="form-label">Neues Passwort</label>
              <PasswordInput v-model="form.password" placeholder="••••••••" />
            </div>
            <div>
              <label class="form-label">Wiederholen</label>
              <PasswordInput v-model="form.password_confirm" placeholder="••••••••" />
            </div>
          </div>
          <p v-if="form.password_confirm && form.password !== form.password_confirm" class="form-error mt-2">
            Passwörter stimmen nicht überein
          </p>
        </div>
      </div>

      <div class="flex justify-end">
        <button class="btn-primary" :disabled="saving" @click="save">
          <span v-if="saving">Speichert…</span>
          <span v-else>Speichern</span>
        </button>
      </div>
    </div>

    <!-- Projektmitgliedschaften -->
    <div class="rounded-xl bg-white border border-gray-200 p-5 space-y-3">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide">Meine Projektmitgliedschaften</h2>
      <p v-if="memberships.length === 0" class="text-sm text-gray-400">Keine Mitgliedschaften gefunden.</p>
      <ul v-else class="divide-y divide-gray-100">
        <li v-for="m in memberships" :key="m.project_title" class="flex items-center justify-between py-2">
          <span class="text-sm text-gray-800">{{ m.project_title }}</span>
          <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700">
            {{ projectRoleLabel[m.role] ?? m.role }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

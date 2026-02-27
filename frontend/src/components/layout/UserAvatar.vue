<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { UserCircleIcon, Cog6ToothIcon, ArrowRightStartOnRectangleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const auth = useAuthStore()
const open = ref(false)

const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  if (u.full_name) return u.full_name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2)
  return u.username.slice(0, 2).toUpperCase()
})

const roleLabel: Record<string, string> = {
  superuser: 'Superuser',
  admin: 'Administrator',
  user: 'Benutzer',
}

function goProfile() {
  open.value = false
  router.push('/profile')
}

function logout() {
  open.value = false
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="relative">
    <!-- Avatar Button -->
    <button
      class="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400"
      :title="auth.user?.username"
      @click="open = !open"
    >
      {{ initials }}
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="open"
        class="absolute right-0 top-10 w-56 rounded-xl bg-white shadow-lg ring-1 ring-black/5 z-50"
        @click.stop
      >
        <!-- User Info -->
        <div class="px-4 py-3 border-b border-gray-100">
          <p class="text-sm font-semibold text-gray-900 truncate">
            {{ auth.user?.full_name || auth.user?.username }}
          </p>
          <p class="text-xs text-gray-500 truncate">{{ auth.user?.email }}</p>
          <span class="mt-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
            :class="{
              'bg-purple-100 text-purple-700': auth.user?.global_role === 'superuser',
              'bg-blue-100 text-blue-700':   auth.user?.global_role === 'admin',
              'bg-gray-100 text-gray-600':   auth.user?.global_role === 'user',
            }"
          >
            {{ roleLabel[auth.user?.global_role ?? 'user'] }}
          </span>
        </div>

        <!-- Actions -->
        <div class="py-1">
          <button
            class="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            @click="goProfile"
          >
            <UserCircleIcon class="h-4 w-4 text-gray-400" />
            Mein Profil
          </button>
          <button
            v-if="auth.user?.global_role === 'admin' || auth.user?.global_role === 'superuser'"
            class="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            @click="() => { open = false; router.push('/config/users') }"
          >
            <Cog6ToothIcon class="h-4 w-4 text-gray-400" />
            Konfiguration
          </button>
        </div>

        <div class="border-t border-gray-100 py-1">
          <button
            class="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            @click="logout"
          >
            <ArrowRightStartOnRectangleIcon class="h-4 w-4" />
            Abmelden
          </button>
        </div>
      </div>
    </Transition>

    <!-- Backdrop zum Schließen -->
    <div v-if="open" class="fixed inset-0 z-40" @click="open = false" />
  </div>
</template>

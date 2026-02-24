<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  FolderIcon,
  ArrowRightStartOnRectangleIcon,
  RocketLaunchIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const auth = useAuthStore()

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

    <!-- Nav links -->
    <div class="flex-1 space-y-1 px-2">
      <RouterLink
        to="/projects"
        class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        active-class="bg-gray-800 text-white"
      >
        <FolderIcon class="h-5 w-5" />
        Projects
      </RouterLink>
    </div>

    <!-- User + Logout -->
    <div class="mt-auto px-2 border-t border-gray-800 pt-3 space-y-1">
      <div v-if="auth.user" class="px-3 py-2 text-xs text-gray-400 truncate">
        {{ auth.user.username }}
      </div>
      <button
        class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        @click="logout"
      >
        <ArrowRightStartOnRectangleIcon class="h-5 w-5" />
        Logout
      </button>
    </div>
  </nav>
</template>

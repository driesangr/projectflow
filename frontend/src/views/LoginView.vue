<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { RocketLaunchIcon } from '@heroicons/vue/24/outline'
import PasswordInput from '@/components/common/PasswordInput.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

async function submit() {
  loading.value = true
  error.value = null
  try {
    await auth.login(username.value, password.value)
    router.push('/projects')
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="flex flex-col items-center mb-8">
        <div class="flex items-center gap-2 mb-2">
          <RocketLaunchIcon class="h-8 w-8 text-brand-600" />
          <span class="text-2xl font-bold text-gray-900">ProjectFlow</span>
        </div>
        <p class="text-sm text-gray-500">Sign in to your account</p>
      </div>

      <!-- Card -->
      <div class="card">
        <div class="card-body">
          <form class="space-y-4" @submit.prevent="submit">
            <div v-if="error" class="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {{ error }}
            </div>

            <div>
              <label class="form-label" for="username">Username</label>
              <input
                id="username"
                v-model="username"
                class="form-input"
                required
                autocomplete="username"
                placeholder="your-username"
              />
            </div>

            <div>
              <label class="form-label" for="password">Password</label>
              <PasswordInput
                id="password"
                v-model="password"
                placeholder="••••••••"
                :required="true"
              />
            </div>

            <button type="submit" class="btn-primary w-full justify-center" :disabled="loading">
              {{ loading ? 'Signing in…' : 'Sign in' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

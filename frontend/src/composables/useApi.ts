import { ref } from 'vue'

/**
 * Wraps an async API call with loading / error state.
 * Usage:
 *   const { execute, loading, error } = useApi()
 *   const data = await execute(() => api.createProject(payload))
 */
export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute<T>(fn: () => Promise<T>): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      return await fn()
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? e.message ?? 'An error occurred'
      return null
    } finally {
      loading.value = false
    }
  }

  return { loading, error, execute }
}

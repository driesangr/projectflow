<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'

const router = useRouter()

// Don't render anything until the initial navigation (incl. auth guard) is done.
// This prevents AppShell from briefly flashing before a redirect to /login.
const ready = ref(false)
router.isReady().then(() => { ready.value = true })
</script>

<template>
  <template v-if="$route.meta.public">
    <RouterView />
  </template>
  <AppShell v-else-if="ready">
    <RouterView />
  </AppShell>
</template>

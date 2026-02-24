<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <AppSidebar />
    <main class="flex-1 overflow-y-auto p-6">
      <slot />
    </main>
  </div>
</template>

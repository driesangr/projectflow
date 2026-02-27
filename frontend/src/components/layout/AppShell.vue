<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import UserAvatar from './UserAvatar.vue'
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <AppSidebar />
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top-Bar mit Avatar -->
      <header class="flex items-center justify-end h-12 px-5 bg-white border-b border-gray-200 flex-shrink-0">
        <UserAvatar />
      </header>
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

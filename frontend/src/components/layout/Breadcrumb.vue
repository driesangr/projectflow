<script setup lang="ts">
import { ChevronRightIcon } from '@heroicons/vue/20/solid'

export interface BreadcrumbItem {
  label: string
  to?: string
}

defineProps<{ items: BreadcrumbItem[] }>()
</script>

<template>
  <nav class="flex items-center gap-1 text-sm text-gray-500 mb-4" aria-label="Breadcrumb">
    <template v-for="(item, i) in items" :key="i">
      <ChevronRightIcon v-if="i > 0" class="h-4 w-4 text-gray-400 flex-shrink-0" />
      <RouterLink
        v-if="item.to"
        :to="item.to"
        class="hover:text-gray-700 truncate"
      >
        {{ item.label }}
      </RouterLink>
      <span v-else class="text-gray-800 font-medium truncate">{{ item.label }}</span>
    </template>
  </nav>
</template>

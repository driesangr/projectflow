<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const colorMap: Record<string, string> = {
  // generic
  todo:        'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  done:        'bg-green-100 text-green-700',
  on_hold:     'bg-yellow-100 text-yellow-700',
  // project status
  active:      'bg-emerald-100 text-emerald-700',
  completed:   'bg-green-100 text-green-700',
  cancelled:   'bg-red-100 text-red-700',
  // maturity
  idea:        'bg-purple-100 text-purple-700',
  concept:     'bg-indigo-100 text-indigo-700',
  in_planning: 'bg-sky-100 text-sky-700',
  // priority
  high:        'bg-red-100 text-red-700',
  medium:      'bg-amber-100 text-amber-700',
  low:         'bg-gray-100 text-gray-500',
}

const label = computed(() => props.status.replace(/_/g, ' '))
const color = computed(() => colorMap[props.status] ?? 'bg-gray-100 text-gray-600')
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize"
    :class="color"
  >
    {{ label }}
  </span>
</template>

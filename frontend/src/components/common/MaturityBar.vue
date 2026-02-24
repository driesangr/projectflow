<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ percent: number | null }>()

const pct = computed(() => Math.round(props.percent ?? 0))
const color = computed(() => {
  if (pct.value >= 80) return 'bg-green-500'
  if (pct.value >= 50) return 'bg-blue-500'
  if (pct.value >= 20) return 'bg-amber-400'
  return 'bg-gray-300'
})
</script>

<template>
  <div class="flex items-center gap-2">
    <div class="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="color"
        :style="{ width: `${pct}%` }"
      />
    </div>
    <span class="text-xs text-gray-500 tabular-nums w-8 text-right">{{ pct }}%</span>
  </div>
</template>

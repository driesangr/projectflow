<script setup lang="ts">
import { watch, onBeforeUnmount } from 'vue'
import Modal from './Modal.vue'

const props = defineProps<{
  open: boolean
  itemName: string
  loading?: boolean
}>()

const emit = defineEmits<{ close: []; confirm: [] }>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !props.loading) {
    e.preventDefault()
    emit('confirm')
  }
}

watch(() => props.open, (open) => {
  if (open) {
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('keydown', onKeydown)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Modal :open="open" title="Confirm Delete" @close="emit('close')">
    <p class="text-sm text-gray-600">
      Are you sure you want to delete
      <span class="font-semibold text-gray-900">{{ itemName }}</span>?
      This action cannot be undone.
    </p>
    <div class="mt-4 flex justify-end gap-2">
      <button class="btn-secondary" :disabled="loading" @click="emit('close')">Cancel</button>
      <button class="btn-danger" :disabled="loading" @click="emit('confirm')">
        {{ loading ? 'Deleting…' : 'Delete' }}
      </button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Modal from './Modal.vue'

defineProps<{
  open: boolean
  itemName: string
  loading?: boolean
}>()

const emit = defineEmits<{ close: []; confirm: [] }>()
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

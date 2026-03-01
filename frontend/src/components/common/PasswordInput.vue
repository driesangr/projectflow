<script setup lang="ts">
import { ref } from 'vue'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'

defineProps<{
  modelValue: string
  placeholder?: string
  id?: string
  required?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const show = ref(false)
</script>

<template>
  <div class="relative">
    <input
      :id="id"
      :type="show ? 'text' : 'password'"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      class="form-input w-full pr-10"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <button
      type="button"
      class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
      :title="show ? 'Passwort verbergen' : 'Passwort anzeigen'"
      @click="show = !show"
    >
      <EyeSlashIcon v-if="show" class="h-4 w-4" />
      <EyeIcon v-else class="h-4 w-4" />
    </button>
  </div>
</template>

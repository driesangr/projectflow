import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/userStories'
import type { UserStory, UserStoryCreate, UserStoryUpdate } from '@/types'

export const useUserStoriesStore = defineStore('userStories', () => {
  const userStories = ref<UserStory[]>([])
  const current = ref<UserStory | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(deliverableId?: string, sprintId?: string, projectId?: string) {
    loading.value = true
    error.value = null
    try {
      userStories.value = await api.listUserStories(deliverableId, sprintId, projectId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load user stories'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getUserStory(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load user story'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: UserStoryCreate): Promise<UserStory> {
    const story = await api.createUserStory(payload)
    userStories.value.push(story)
    return story
  }

  async function update(id: string, payload: UserStoryUpdate): Promise<UserStory> {
    const story = await api.updateUserStory(id, payload)
    const idx = userStories.value.findIndex((s) => s.id === id)
    if (idx !== -1) userStories.value[idx] = story
    if (current.value?.id === id) current.value = story
    return story
  }

  async function remove(id: string) {
    await api.deleteUserStory(id)
    userStories.value = userStories.value.filter((s) => s.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function reorder(items: { id: string; position: number }[]) {
    await api.reorderUserStories(items)
  }

  async function setValues(
    items: { id: string; business_value?: number | null; sprint_value?: number | null }[],
  ) {
    await api.setBulkStoryValues(items)
    for (const item of items) {
      const story = userStories.value.find((s) => s.id === item.id)
      if (story) {
        if (item.business_value !== undefined) story.business_value = item.business_value ?? null
        if (item.sprint_value !== undefined) story.sprint_value = item.sprint_value ?? null
      }
      if (current.value?.id === item.id) {
        if (item.business_value !== undefined) current.value.business_value = item.business_value ?? null
        if (item.sprint_value !== undefined) current.value.sprint_value = item.sprint_value ?? null
      }
    }
  }

  return { userStories, current, loading, error, fetchAll, fetchOne, create, update, remove, reorder, setValues }
})

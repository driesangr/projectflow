import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/topics'
import type { Topic, TopicCreate, TopicUpdate } from '@/types'

export const useTopicsStore = defineStore('topics', () => {
  const topics = ref<Topic[]>([])
  const current = ref<Topic | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(projectId?: string) {
    loading.value = true
    error.value = null
    try {
      topics.value = await api.listTopics(projectId)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load topics'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getTopic(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load topic'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: TopicCreate): Promise<Topic> {
    const topic = await api.createTopic(payload)
    topics.value.push(topic)
    return topic
  }

  async function update(id: string, payload: TopicUpdate): Promise<Topic> {
    const topic = await api.updateTopic(id, payload)
    const idx = topics.value.findIndex((t) => t.id === id)
    if (idx !== -1) topics.value[idx] = topic
    if (current.value?.id === id) current.value = topic
    return topic
  }

  async function remove(id: string) {
    await api.deleteTopic(id)
    topics.value = topics.value.filter((t) => t.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function reorder(items: { id: string; position: number }[]) {
    await api.reorderTopics(items)
  }

  return { topics, current, loading, error, fetchAll, fetchOne, create, update, remove, reorder }
})

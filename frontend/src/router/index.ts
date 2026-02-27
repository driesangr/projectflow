import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { GlobalRole } from '@/types'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      redirect: '/project-groups',
    },
    {
      path: '/project-groups',
      name: 'project-groups',
      component: () => import('@/views/ProjectGroupListView.vue'),
    },
    {
      path: '/project-groups/:groupId',
      name: 'project-group-detail',
      component: () => import('@/views/ProjectGroupDetailView.vue'),
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectListView.vue'),
    },
    {
      path: '/projects/:projectId',
      name: 'project-detail',
      component: () => import('@/views/ProjectDetailView.vue'),
    },
    {
      path: '/projects/:projectId/sprints',
      name: 'sprint-list',
      component: () => import('@/views/SprintListView.vue'),
    },
    {
      path: '/projects/:projectId/sprints/:sprintId',
      name: 'sprint-detail',
      component: () => import('@/views/SprintDetailView.vue'),
    },
    {
      path: '/topics/:topicId',
      name: 'topic-detail',
      component: () => import('@/views/TopicDetailView.vue'),
    },
    {
      path: '/deliverables/:deliverableId',
      name: 'deliverable-detail',
      component: () => import('@/views/DeliverableDetailView.vue'),
    },
    {
      path: '/user-stories/:storyId',
      name: 'user-story-detail',
      component: () => import('@/views/UserStoryDetailView.vue'),
    },
    {
      path: '/bugs/:bugId',
      name: 'bug-detail',
      component: () => import('@/views/BugDetailView.vue'),
    },
    {
      path: '/tasks/:taskId',
      name: 'task-detail',
      component: () => import('@/views/TaskDetailView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
    },
    {
      path: '/config',
      redirect: '/config/users',
    },
    {
      path: '/config/users',
      name: 'config-users',
      component: () => import('@/views/ConfigUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/config/permissions',
      name: 'config-permissions',
      component: () => import('@/views/ConfigPermissionsView.vue'),
      meta: { requiresAdmin: true },
    },
  ],
})

// Global auth guard
router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return { name: 'login' }
  }

  // Hydrate user on first navigation
  if (!auth.user) {
    await auth.fetchMe()
    // fetchMe() calls logout() internally on failure, clearing the token
    if (!auth.isAuthenticated) {
      return { name: 'login' }
    }
  }

  // Admin-Guard: /config/* nur für admin und superuser
  if (to.meta.requiresAdmin) {
    const role = auth.user?.global_role as GlobalRole | undefined
    if (role !== 'admin' && role !== 'superuser') {
      return { name: 'project-groups' }
    }
  }

  return true
})

export default router

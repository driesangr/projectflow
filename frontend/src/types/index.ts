// ── Enums ────────────────────────────────────────────────────────────────────

export type MaturityLevel =
  | 'idea'
  | 'concept'
  | 'in_planning'
  | 'in_progress'
  | 'completed'
  | 'on_hold'

export type ProjectStatus = 'active' | 'on_hold' | 'completed' | 'cancelled'

export type TopicPriority = 'high' | 'medium' | 'low'

export type DeliverableStatus = 'todo' | 'in_progress' | 'done' | 'on_hold'

export type UserStoryStatus = 'todo' | 'in_progress' | 'done' | 'on_hold'

export type BugStatus = 'todo' | 'in_progress' | 'done' | 'on_hold'

export type TaskStatus = 'todo' | 'in_progress' | 'done'

// ── Models ───────────────────────────────────────────────────────────────────

export interface ProjectGroup {
  id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export type GlobalRole = 'superuser' | 'admin' | 'user'
export type ProjectRole = 'owner' | 'manager' | 'member' | 'viewer'

export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  global_role: GlobalRole
  created_at: string
  updated_at: string
}

export type UserResponse = User

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string | null
  global_role?: GlobalRole
}

export interface UserUpdate {
  email?: string | null
  full_name?: string | null
  is_active?: boolean | null
  global_role?: GlobalRole | null
  password?: string | null
}

export interface UserPublic {
  id: string
  username: string
  full_name: string | null
  email: string
}

export interface MembershipResponse {
  id: string
  project_id: string
  role: ProjectRole
  created_at: string
  updated_at: string
  user: UserPublic
}

export interface MembershipCreate {
  user_id: string
  role: ProjectRole
}

export interface MembershipUpdate {
  role: ProjectRole
}

export interface Project {
  id: string
  title: string
  description: string | null
  start_date: string | null
  planned_end_date: string | null
  maturity_level: MaturityLevel
  status: ProjectStatus
  owner_name: string | null
  tags: string[] | null
  project_group_id: string | null
  created_at: string
  updated_at: string
  topics?: Topic[]
}

export interface Topic {
  id: string
  title: string
  description: string | null
  business_value: number | null
  priority: TopicPriority
  planned_start_date: string | null
  planned_end_date: string | null
  owner_name: string | null
  project_id: string
  maturity_percent: number | null
  position: number
  created_at: string
  updated_at: string
  deliverables?: Deliverable[]
}

export interface Deliverable {
  id: string
  title: string
  description: string | null
  epic_points: number | null
  business_value: number | null
  status: DeliverableStatus
  owner_name: string | null
  topic_id: string | null
  project_id: string | null
  maturity_percent: number | null
  position: number
  created_at: string
  updated_at: string
  user_stories?: UserStory[]
}

export interface UserStory {
  id: string
  title: string
  description: string | null
  acceptance_criteria: string | null
  story_points: number | null
  business_value: number | null
  sprint_value: number | null
  status: UserStoryStatus
  owner_name: string | null
  deliverable_id: string
  sprint_id: string | null
  position: number
  created_at: string
  updated_at: string
  tasks?: Task[]
}

export interface Bug {
  id: string
  title: string
  description: string | null
  acceptance_criteria: string | null
  story_points: number | null
  business_value: number | null
  sprint_value: number | null
  status: BugStatus
  owner_name: string | null
  deliverable_id: string
  sprint_id: string | null
  position: number
  created_at: string
  updated_at: string
  tasks?: Task[]
}

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  effort_hours: number | null
  sprint_value: number | null
  owner_name: string | null
  user_story_id: string | null
  bug_id: string | null
  position: number
  created_at: string
  updated_at: string
}

export interface Sprint {
  id: string
  name: string
  start_date: string | null
  end_date: string | null
  goal: string | null
  project_id: string
  created_at: string
  updated_at: string
}

// ── Permissions ──────────────────────────────────────────────────────────────

export type ArtifactType =
  | 'project_group'
  | 'project'
  | 'topic'
  | 'deliverable'
  | 'user_story'
  | 'task'

export interface RolePermission {
  id: string
  project_role: ProjectRole
  artifact_type: ArtifactType
  can_read: boolean
  can_write: boolean
  can_create: boolean
  can_delete: boolean
  inherit_to_children: boolean
  is_explicit: boolean
  created_at: string
  updated_at: string
}

export interface RolePermissionCreate {
  project_role: ProjectRole
  artifact_type: ArtifactType
  can_read?: boolean
  can_write?: boolean
  can_create?: boolean
  can_delete?: boolean
  inherit_to_children?: boolean
}

export interface RolePermissionUpdate {
  can_read?: boolean
  can_write?: boolean
  can_create?: boolean
  can_delete?: boolean
  inherit_to_children?: boolean
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ── Payload helpers ───────────────────────────────────────────────────────────

export interface ProjectGroupCreate {
  title: string
  description?: string | null
}

export type ProjectGroupUpdate = Partial<ProjectGroupCreate>

export interface ProjectCreate {
  title: string
  description?: string | null
  start_date?: string | null
  planned_end_date?: string | null
  maturity_level?: MaturityLevel
  status?: ProjectStatus
  owner_name?: string | null
  tags?: string[] | null
  project_group_id?: string | null
}

export type ProjectUpdate = Partial<ProjectCreate>

export interface TopicCreate {
  title: string
  description?: string | null
  business_value?: number | null
  priority?: TopicPriority
  planned_start_date?: string | null
  planned_end_date?: string | null
  owner_name?: string | null
  project_id: string
}

export type TopicUpdate = Partial<Omit<TopicCreate, 'project_id'>>

export interface DeliverableCreate {
  title: string
  description?: string | null
  epic_points?: number | null
  business_value?: number | null
  status?: DeliverableStatus
  owner_name?: string | null
  topic_id?: string | null
  project_id?: string | null
}

export type DeliverableUpdate = Partial<Omit<DeliverableCreate, 'topic_id' | 'project_id'>>

export interface UserStoryCreate {
  title: string
  description?: string | null
  acceptance_criteria?: string | null
  story_points?: number | null
  business_value?: number | null
  sprint_value?: number | null
  status?: UserStoryStatus
  owner_name?: string | null
  deliverable_id: string
  sprint_id?: string | null
}

export type UserStoryUpdate = Partial<Omit<UserStoryCreate, 'deliverable_id'>>

export interface BugCreate {
  title: string
  description?: string | null
  acceptance_criteria?: string | null
  story_points?: number | null
  business_value?: number | null
  sprint_value?: number | null
  status?: BugStatus
  owner_name?: string | null
  deliverable_id: string
  sprint_id?: string | null
}

export type BugUpdate = Partial<Omit<BugCreate, 'deliverable_id'>>

export interface TaskCreate {
  title: string
  description?: string | null
  status?: TaskStatus
  effort_hours?: number | null
  sprint_value?: number | null
  owner_name?: string | null
  user_story_id?: string | null
  bug_id?: string | null
}

export type TaskUpdate = Partial<Omit<TaskCreate, 'user_story_id' | 'bug_id'>>

export interface SprintCreate {
  name: string
  start_date?: string | null
  end_date?: string | null
  goal?: string | null
  project_id: string
}

export type SprintUpdate = Partial<Omit<SprintCreate, 'project_id'>>

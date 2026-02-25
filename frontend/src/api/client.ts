import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401 – use Vue Router to avoid a hard page reload
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      // Dynamic import avoids a circular-dependency with router → stores → api/client
      import('@/router').then(({ default: router }) => {
        if (router.currentRoute.value.name !== 'login') {
          router.push({ name: 'login' })
        }
      })
    }
    return Promise.reject(error)
  },
)

export default apiClient

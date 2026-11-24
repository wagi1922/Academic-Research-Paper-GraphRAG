import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Notification {
  id: number
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
}

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const loading = ref(false)
  const notifications = ref<Notification[]>([])
  let notificationId = 0

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(value: boolean): void {
    loading.value = value
  }

  function notify(type: Notification['type'], message: string): void {
    const id = ++notificationId
    notifications.value.push({ id, type, message })
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
  }

  function removeNotification(id: number): void {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return {
    sidebarCollapsed,
    loading,
    notifications,
    toggleSidebar,
    setLoading,
    notify,
    removeNotification,
  }
})

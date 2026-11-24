<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Menu, Moon, Bell, ChevronDown, User, LogOut, Search as SearchIcon, X } from 'lucide-vue-next'
import { useUIStore } from '@/stores/ui'

defineEmits<{
  'toggle-sidebar': []
}>()

const uiStore = useUIStore()
const route = useRoute()

const showProfileMenu = ref(false)
const showNotifications = ref(false)

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': 'Dashboard',
    '/query': 'Query Interface',
    '/graph': 'Knowledge Graph',
    '/papers': 'Papers',
    '/citations': 'Citations',
    '/entities': 'Entities',
    '/settings': 'Settings',
  }
  if (titles[route.path]) return titles[route.path]
  if (route.name === 'PaperDetail') return 'Paper Detail'
  return 'GraphRAG'
})

function toggleTheme(): void {
  const html = document.documentElement
  if (html.classList.contains('dark')) {
    html.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  } else {
    html.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  }
}

function closeMenus(): void {
  showProfileMenu.value = false
  showNotifications.value = false
}
</script>

<template>
  <header
    class="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border-primary bg-bg-secondary/80 px-6 backdrop-blur-sm"
  >
    <div class="flex items-center gap-4">
      <button
        @click="$emit('toggle-sidebar')"
        class="rounded-lg bg-bg-tertiary p-2 text-text-secondary transition-colors hover:bg-bg-hover lg:hidden"
        aria-label="Toggle menu"
      >
        <Menu class="h-5 w-5" />
      </button>

      <h1 class="text-lg font-semibold text-text-primary">{{ pageTitle }}</h1>
    </div>

    <div class="mx-8 hidden max-w-xl flex-1 md:flex">
      <div class="relative w-full">
        <SearchIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          placeholder="Search papers, entities, citations..."
          class="input pl-10 pr-4"
          aria-label="Global search"
        />
      </div>
    </div>

    <div class="flex items-center gap-2">
      <button
        @click="toggleTheme"
        class="rounded-lg bg-bg-tertiary p-2 text-text-secondary transition-colors hover:bg-bg-hover"
        aria-label="Toggle theme"
        title="Toggle theme"
      >
        <Moon class="h-5 w-5" />
      </button>

      <div class="relative">
        <button
          @click="showNotifications = !showNotifications; showProfileMenu = false"
          class="relative rounded-lg bg-bg-tertiary p-2 text-text-secondary transition-colors hover:bg-bg-hover"
          aria-label="Notifications"
        >
          <Bell class="h-5 w-5" />
          <span
            v-if="uiStore.notifications.length > 0"
            class="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-danger text-xs text-white"
          >
            {{ uiStore.notifications.length > 9 ? '9+' : uiStore.notifications.length }}
          </span>
        </button>

        <div
          v-if="showNotifications"
          class="absolute right-0 top-full z-50 mt-2 w-80 animate-in rounded-xl border border-border-primary bg-bg-secondary py-2 shadow-lg"
        >
          <div class="flex items-center justify-between border-b border-border-primary px-4 py-2">
            <h3 class="font-medium text-text-primary">Notifications</h3>
            <button @click="uiStore.notifications = []" class="text-sm text-text-muted hover:text-text-primary">
              Clear all
            </button>
          </div>
          <div v-if="uiStore.notifications.length === 0" class="px-4 py-8 text-center text-text-muted">
            No notifications
          </div>
          <div v-else class="max-h-96 overflow-y-auto">
            <div
              v-for="notification in uiStore.notifications"
              :key="notification.id"
              class="flex items-start gap-3 border-b border-border-primary/50 px-4 py-3 last:border-0 hover:bg-bg-tertiary"
            >
              <div class="min-w-0 flex-1">
                <p class="text-sm text-text-primary">{{ notification.message }}</p>
                <p class="mt-0.5 text-xs text-text-muted">Just now</p>
              </div>
              <button
                @click="uiStore.removeNotification(notification.id)"
                class="text-text-muted hover:text-text-primary"
                :aria-label="`Dismiss: ${notification.message}`"
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="relative">
        <button
          @click="showProfileMenu = !showProfileMenu; showNotifications = false"
          class="flex items-center gap-2 rounded-lg bg-bg-tertiary p-2 transition-colors hover:bg-bg-hover"
          aria-label="Profile menu"
        >
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-accent-primary">
            <User class="h-4 w-4 text-white" />
          </div>
          <span class="hidden text-sm font-medium text-text-primary sm:block">Researcher</span>
          <ChevronDown class="hidden h-4 w-4 text-text-muted sm:block" />
        </button>

        <div
          v-if="showProfileMenu"
          class="absolute right-0 top-full z-50 mt-2 w-48 animate-in rounded-xl border border-border-primary bg-bg-secondary py-2 shadow-lg"
        >
          <div class="border-b border-border-primary px-4 py-3">
            <p class="font-medium text-text-primary">Researcher</p>
            <p class="text-sm text-text-muted">GraphRAG Capstone</p>
          </div>
          <RouterLink
            to="/settings"
            class="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
            @click="closeMenus"
          >
            <LogOut class="h-4 w-4" />
            Settings
          </RouterLink>
        </div>
      </div>
    </div>
  </header>
</template>

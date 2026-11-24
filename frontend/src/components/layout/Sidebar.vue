<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Search,
  GitBranch,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Database,
  Lightbulb,
} from 'lucide-vue-next'

interface Props {
  collapsed: boolean
}

interface Emits {
  toggle: []
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
})

const emit = defineEmits<Emits>()

const router = useRouter()
const route = useRoute()

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { path: '/query', icon: Search, label: 'Query', exact: false },
  { path: '/graph', icon: GitBranch, label: 'Knowledge Graph', exact: false },
  { path: '/papers', icon: BookOpen, label: 'Papers', exact: false },
  { path: '/citations', icon: Lightbulb, label: 'Citations', exact: false },
  { path: '/entities', icon: Database, label: 'Entities', exact: false },
  { path: '/settings', icon: Settings, label: 'Settings', exact: false },
]

const isActive = (path: string, exact: boolean) => {
  if (exact) return route.path === path
  return route.path.startsWith(path) && path !== '/'
}
</script>

<template>
  <aside
    class="fixed left-0 top-0 h-screen bg-bg-secondary border-r border-border-primary transition-all duration-250 z-40 flex flex-col"
    :class="{ 'w-64': !collapsed, 'w-20': collapsed }"
    aria-label="Main navigation"
  >
    <!-- Logo / Brand -->
    <div class="flex items-center justify-between h-16 px-4 border-b border-border-primary">
      <div class="flex items-center gap-3" v-if="!collapsed">
        <div class="w-8 h-8 rounded-lg bg-accent-primary flex items-center justify-center">
          <GitBranch class="w-5 h-5 text-white" />
        </div>
        <span class="font-semibold text-lg text-text-primary">GraphRAG</span>
      </div>
      <div class="w-8 h-8 rounded-lg bg-accent-primary flex items-center justify-center mx-auto" v-else>
        <GitBranch class="w-5 h-5 text-white" />
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-1" aria-label="Navigation">
      <div v-if="!collapsed" class="px-3 py-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
        Main
      </div>
      <template v-for="item in navItems" :key="item.path">
        <router-link
          :to="item.path"
          class="sidebar-link"
          :class="{ 'sidebar-link-active': isActive(item.path, item.exact) }"
          @click="collapsed && emit('toggle')"
          :aria-current="isActive(item.path, item.exact) ? 'page' : undefined"
        >
          <component :is="item.icon" class="w-5 h-5 flex-shrink-0" :aria-hidden="true" />
          <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
        </router-link>
      </template>
    </nav>

    <!-- Collapse Toggle / Footer -->
    <div class="p-4 border-t border-border-primary">
      <button
        @click="emit('toggle')"
        class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-bg-tertiary hover:bg-bg-hover text-text-secondary transition-colors"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <ChevronLeft v-if="!collapsed" class="w-5 h-5" />
        <ChevronRight v-if="collapsed" class="w-5 h-5" />
        <span v-if="!collapsed" class="text-sm">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* Ensure smooth sidebar transitions */
aside {
  transition: width 0.25s ease-out;
}

/* Hide scrollbar but keep functionality */
nav::-webkit-scrollbar {
  display: none;
}
nav {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
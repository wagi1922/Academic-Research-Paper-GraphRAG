<script setup lang="ts">
import { RouterView } from 'vue-router'
import Sidebar from './components/layout/Sidebar.vue'
import Header from './components/layout/Header.vue'
import { useUIStore } from './stores/ui'

const uiStore = useUIStore()
</script>

<template>
  <div class="min-h-screen bg-bg-primary text-text-primary">
    <Sidebar :collapsed="uiStore.sidebarCollapsed" @toggle="uiStore.toggleSidebar" />

    <div
      class="flex min-h-screen flex-col transition-[margin] duration-200"
      :class="uiStore.sidebarCollapsed ? 'lg:ml-20' : 'lg:ml-64'"
    >
      <Header @toggle-sidebar="uiStore.toggleSidebar" />

      <main class="flex-1 overflow-auto p-6">
        <RouterView v-slot="{ Component }">
          <component :is="Component" class="animate-in block w-full" />
        </RouterView>
      </main>
    </div>
  </div>
</template>

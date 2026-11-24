<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { api } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import {
  Loader2,
  Search,
  Database,
  Lightbulb,
  Tag,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from 'lucide-vue-next'

const uiStore = useUIStore()

const entities = ref<Array<{ id: string; name: string; type: string; paper_count: number }>>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedType = ref('')
const sortBy = ref<'name' | 'count'>('count')
const sortDesc = ref(true)
const copiedEntity = ref<string | null>(null)

const entityTypes = computed(() => {
  const types = new Set(entities.value.map(e => e.type))
  return Array.from(types).sort()
})

const filteredEntities = computed(() => {
  let result = entities.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e => e.name.toLowerCase().includes(q))
  }
  if (selectedType.value) {
    result = result.filter(e => e.type === selectedType.value)
  }
  result.sort((a, b) => {
    const aVal = sortBy.value === 'name' ? a.name : a.paper_count
    const bVal = sortBy.value === 'name' ? b.name : b.paper_count
    return sortDesc.value ? (aVal > bVal ? -1 : 1) : (aVal > bVal ? 1 : -1)
  })
  return result
})

async function fetchEntities() {
  loading.value = true
  error.value = null
  try {
    const data = await api.getEntities({ limit: 1000 })
    entities.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load entities'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

function getTypeInfo(type: string) {
  const info: Record<string, { icon: any; color: string }> = {
    'Model': { icon: Database, color: 'accent-primary' },
    'Dataset': { icon: Database, color: 'accent-secondary' },
    'Metric': { icon: Lightbulb, color: 'accent-success' },
    'Method': { icon: Lightbulb, color: 'accent-warning' },
    'Concept': { icon: Lightbulb, color: 'accent-danger' },
    'Paper': { icon: Tag, color: 'text-text-muted' },
  }
  return info[type] || { icon: Lightbulb, color: 'text-text-muted' }
}

function copyEntity(name: string, id: string) {
  navigator.clipboard.writeText(name)
  copiedEntity.value = id
  setTimeout(() => copiedEntity.value = null, 2000)
  uiStore.notify('success', 'Entity name copied')
}

onMounted(() => {
  fetchEntities()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-text-primary">Entities</h1>
        <p class="text-text-secondary mt-1">{{ entities.length }} entities extracted from papers</p>
      </div>
      <button @click="fetchEntities" :disabled="loading" class="btn-secondary">
        <Loader2 :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <!-- Controls -->
    <div class="card">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search entities by name..."
            class="input pl-10"
            aria-label="Search entities"
          />
        </div>
        
        <select v-model="selectedType" class="input w-auto min-w-[180px]">
          <option value="">All Types</option>
          <option v-for="type in entityTypes" :key="type" :value="type">{{ type }}</option>
        </select>
        
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-muted">Sort:</label>
          <select v-model="sortBy" class="input w-auto">
            <option value="count">Paper Count</option>
            <option value="name">Name</option>
          </select>
          <button
            @click="sortDesc = !sortDesc"
            class="btn-ghost p-2"
            :title="sortDesc ? 'Descending' : 'Ascending'"
          >
            <ChevronDown v-if="sortDesc" class="w-4 h-4" />
            <ChevronUp v-if="!sortDesc" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Entities Table -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <Loader2 class="w-8 h-8 animate-spin text-accent-primary mx-auto mb-3" />
        <p class="text-text-secondary">Loading entities...</p>
      </div>
      
      <div v-else-if="filteredEntities.length === 0" class="p-8 text-center">
        <Lightbulb class="w-16 h-16 text-text-muted mx-auto mb-4" />
        <h3 class="text-lg font-medium text-text-primary mb-2">No entities found</h3>
        <p class="text-text-secondary">Try adjusting your search or filter</p>
      </div>
      
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border-primary text-left text-sm font-medium text-text-muted">
              <th class="p-4 w-12"></th>
              <th class="p-4 cursor-pointer hover:text-text-primary" @click="sortBy = 'name'; sortDesc = !sortDesc">
                Entity Name
                <span class="ml-1" v-if="sortBy === 'name'">{{ sortDesc ? '↓' : '↑' }}</span>
              </th>
              <th class="p-4 hidden md:table-cell">Type</th>
              <th class="p-4 cursor-pointer hover:text-text-primary" @click="sortBy = 'count'; sortDesc = !sortDesc">
                Papers
                <span class="ml-1" v-if="sortBy === 'count'">{{ sortDesc ? '↓' : '↑' }}</span>
              </th>
              <th class="p-4 w-12"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entity in filteredEntities"
              :key="entity.id"
              class="border-b border-border-primary/50 hover:bg-bg-tertiary transition-colors"
            >
              <td class="p-4">
                <component
                  :is="getTypeInfo(entity.type).icon"
                  :class="`w-5 h-5 ${getTypeInfo(entity.type).color}`"
                />
              </td>
              <td class="p-4">
                <p class="font-medium text-text-primary truncate max-w-md">{{ entity.name }}</p>
                <p class="text-xs text-text-muted font-mono">{{ entity.id }}</p>
              </td>
              <td class="p-4 hidden md:table-cell">
                <span class="badge badge-primary">{{ entity.type }}</span>
              </td>
              <td class="p-4">
                <span class="font-mono text-text-primary">{{ entity.paper_count }}</span>
              </td>
              <td class="p-4 text-center">
                <button
                  @click="copyEntity(entity.name, entity.id)"
                  class="btn-ghost p-1.5"
                  :title="copiedEntity === entity.id ? 'Copied!' : 'Copy name'"
                >
                  <Check v-if="copiedEntity === entity.id" class="w-4 h-4 text-accent-success" />
                  <Copy v-else class="w-4 h-4" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Type Distribution -->
    <div class="card">
      <h2 class="text-lg font-semibold text-text-primary mb-4">Entity Type Distribution</h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div
          v-for="type in entityTypes"
          :key="type"
          class="p-4 bg-bg-tertiary rounded-lg text-center hover:bg-bg-hover transition-colors"
        >
          <component
            :is="getTypeInfo(type).icon"
            :class="`w-8 h-8 mx-auto mb-2 ${getTypeInfo(type).color}`"
          />
          <p class="font-medium text-text-primary">{{ type }}</p>
          <p class="text-2xl font-bold text-text-primary mt-1">
            {{ entities.filter(e => e.type === type).length }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
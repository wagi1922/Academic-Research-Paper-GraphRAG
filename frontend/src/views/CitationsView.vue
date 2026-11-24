<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { api, type Paper } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import {
  Loader2,
  GitBranch,
  ArrowUpRight,
  ArrowDownLeft,
  FileText,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'

const uiStore = useUIStore()
const router = useRouter()

const papers = ref<Paper[]>([])
const citations = ref<Array<{ citing: Paper; cited: Paper; reference_title: string; reference_year: number | null }>>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const viewMode = ref<'outgoing' | 'incoming'>('outgoing')
const currentPage = ref(1)
const pageSize = 20

const filteredCitations = computed(() => {
  if (!searchQuery.value) return citations.value
  const q = searchQuery.value.toLowerCase()
  return citations.value.filter(c => 
    c.citing.title.toLowerCase().includes(q) ||
    c.cited.title.toLowerCase().includes(q) ||
    (c.reference_title?.toLowerCase().includes(q))
  )
})

const paginatedCitations = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredCitations.value.slice(start, start + pageSize)
})

const totalPages = computed(() => Math.ceil(filteredCitations.value.length / pageSize))

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const [papersData] = await Promise.all([
      api.getPapers({ limit: 100 }),
    ])
    papers.value = papersData.papers
    // Build citations from papers (since we don't have a global citations endpoint)
    // For now, we'll show a message
    citations.value = []
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load citations'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

function formatAuthors(authors: string[]) {
  return authors.slice(0, 3).join(', ') + (authors.length > 3 ? ' et al.' : '')
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

onMounted(() => {
  fetchData()
})

import { watch } from 'vue'
watch([searchQuery, viewMode], () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-text-primary">Citation Network</h1>
        <p class="text-text-secondary mt-1">Explore paper citations and references</p>
      </div>
      <button @click="fetchData" :disabled="loading" class="btn-secondary">
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
            placeholder="Search citations by paper title..."
            class="input pl-10"
            aria-label="Search citations"
          />
        </div>
        
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-muted">View:</label>
          <div class="flex bg-bg-tertiary rounded-lg p-1">
            <button
              @click="viewMode = 'outgoing'"
              :class="[
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                viewMode === 'outgoing' ? 'bg-bg-secondary text-text-primary shadow-sm' : 'text-text-muted hover:text-text-primary'
              ]"
            >
              <ArrowUpRight class="w-4 h-4 mr-1" />
              Outgoing
            </button>
            <button
              @click="viewMode = 'incoming'"
              :class="[
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                viewMode === 'incoming' ? 'bg-bg-secondary text-text-primary shadow-sm' : 'text-text-muted hover:text-text-primary'
              ]"
            >
              <ArrowDownLeft class="w-4 h-4 mr-1" />
              Incoming
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Citations List -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <Loader2 class="w-8 h-8 animate-spin text-accent-primary mx-auto mb-3" />
        <p class="text-text-secondary">Loading citation data...</p>
      </div>
      
      <div v-else-if="filteredCitations.length === 0" class="p-8 text-center">
        <GitBranch class="w-16 h-16 text-text-muted mx-auto mb-4" />
        <h3 class="text-lg font-medium text-text-primary mb-2">No citations found</h3>
        <p class="text-text-secondary">
          <span v-if="searchQuery.value">Try adjusting your search query</span>
          <span v-else>No citation data available. This feature requires a global citations endpoint.</span>
        </p>
      </div>
      
      <div v-else class="divide-y divide-border-primary/50">
        <div
          v-for="citation in paginatedCitations"
          :key="citation.citing.id + '-' + citation.cited.id"
          class="p-4 hover:bg-bg-tertiary transition-colors"
        >
          <div class="flex items-start gap-4">
            <!-- Citing Paper -->
            <div class="flex-1 min-w-0 p-3 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-2 mb-1">
                <span class="badge badge-primary">Citing</span>
                <FileText class="w-4 h-4 text-text-muted" />
              </div>
              <h4 class="font-medium text-text-primary truncate">{{ citation.citing.title }}</h4>
              <p class="text-sm text-text-muted mt-1">
                {{ citation.citing.year }} • {{ formatAuthors(citation.citing.authors) }}
              </p>
            </div>
            
            <!-- Arrow -->
            <div class="flex flex-col items-center justify-center text-accent-primary px-2">
              <GitBranch class="w-6 h-6" />
              <span class="text-xs text-text-muted mt-1">{{ viewMode === 'outgoing' ? 'cites' : 'cited by' }}</span>
            </div>
            
            <!-- Cited Paper -->
            <div class="flex-1 min-w-0 p-3 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-2 mb-1">
                <span class="badge badge-secondary">Cited</span>
                <FileText class="w-4 h-4 text-text-muted" />
              </div>
              <h4 class="font-medium text-text-primary truncate">{{ citation.cited.title }}</h4>
              <p v-if="citation.reference_title && citation.reference_title !== citation.cited.title" class="text-sm text-text-muted mt-1 italic">
                Ref: {{ citation.reference_title }}
              </p>
              <p class="text-sm text-text-muted mt-1">
                {{ citation.cited.year }} • {{ formatAuthors(citation.cited.authors) }}
                <span v-if="citation.reference_year"> (Ref: {{ citation.reference_year }})</span>
              </p>
            </div>
            
            <!-- Actions -->
            <div class="flex flex-col gap-1 flex-shrink-0">
              <router-link
                :to="`/papers/${citation.citing.id}`"
                class="btn-ghost text-xs px-2 py-1"
                @click.stop
              >
                View Citing
              </router-link>
              <router-link
                :to="`/papers/${citation.cited.id}`"
                class="btn-ghost text-xs px-2 py-1"
                @click.stop
              >
                View Cited
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="p-4 border-t border-border-primary flex items-center justify-between">
        <p class="text-sm text-text-muted">
          Page {{ currentPage }} of {{ totalPages }} ({{ filteredCitations.length }} citations)
        </p>
        <div class="flex items-center gap-2">
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="btn-ghost p-2"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="btn-ghost p-2"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
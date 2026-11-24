<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { api, type Paper } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import {
  Search,
  Loader2,
  FileText,
  Hash,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'

const uiStore = useUIStore()
const router = useRouter()

const papers = ref<Paper[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 20
const totalPages = ref(1)

const filteredPapers = computed(() => {
  if (!searchQuery.value) return papers.value
  const q = searchQuery.value.toLowerCase()
  return papers.value.filter(p => 
    p.title.toLowerCase().includes(q) ||
    (p.authors?.some(a => a.toLowerCase().includes(q)) ?? false) ||
    p.id.toLowerCase().includes(q)
  )
})

const paginatedPapers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredPapers.value.slice(start, start + pageSize)
})

async function fetchPapers() {
  loading.value = true
  error.value = null
  try {
    const data = await api.getPapers({ limit: 100 }) // Get all for client-side pagination
    papers.value = data.papers
    totalPages.value = Math.ceil(filteredPapers.value.length / pageSize)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load papers'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

function formatAuthors(authors?: string[]) {
  if (!authors || authors.length === 0) return 'Unknown authors'
  return authors.slice(0, 3).join(', ') + (authors.length > 3 ? ' et al.' : '')
}

onMounted(() => {
  fetchPapers()
})

// Watch search to reset pagination
import { watch } from 'vue'
watch(searchQuery, () => {
  currentPage.value = 1
  totalPages.value = Math.ceil(filteredPapers.value.length / pageSize)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-text-primary">Papers</h1>
        <p class="text-text-secondary mt-1">{{ papers.length }} papers in corpus</p>
      </div>
      <button @click="fetchPapers" :disabled="loading" class="btn-secondary">
        <Loader2 :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <!-- Search -->
    <div class="card">
      <div class="relative max-w-md">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search papers by title, author, ID..."
          class="input pl-10"
          aria-label="Search papers"
        />
      </div>
    </div>

    <!-- Papers Table -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <Loader2 class="w-8 h-8 animate-spin text-accent-primary mx-auto mb-3" />
        <p class="text-text-secondary">Loading papers...</p>
      </div>
      
      <div v-else-if="filteredPapers.length === 0" class="p-8 text-center">
        <FileText class="w-16 h-16 text-text-muted mx-auto mb-4" />
        <h3 class="text-lg font-medium text-text-primary mb-2">No papers found</h3>
        <p class="text-text-secondary">Try adjusting your search query</p>
      </div>
      
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border-primary text-left text-sm font-medium text-text-muted">
              <th class="p-4 w-12"></th>
              <th class="p-4">Title</th>
              <th class="p-4 hidden md:table-cell">Authors</th>
              <th class="p-4 hidden lg:table-cell">Year</th>
              <th class="p-4">Chunks</th>
              <th class="p-4 w-12"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="paper in paginatedPapers"
              :key="paper.id"
              class="border-b border-border-primary/50 hover:bg-bg-tertiary transition-colors cursor-pointer"
              @click="router.push(`/papers/${paper.id}`)"
            >
              <td class="p-4">
                <FileText class="w-5 h-5 text-accent-primary" />
              </td>
              <td class="p-4">
                <p class="font-medium text-text-primary truncate max-w-md">{{ paper.title }}</p>
                <p class="text-xs text-text-muted mt-1">{{ paper.id }}</p>
              </td>
              <td class="p-4 hidden md:table-cell text-text-secondary">
                {{ formatAuthors(paper.authors) }}
              </td>
              <td class="p-4 hidden lg:table-cell text-text-muted">{{ paper.year }}</td>
              <td class="p-4 text-text-muted">{{ paper.chunk_count }}</td>
              <td class="p-4 text-center">
                <Hash class="w-4 h-4 text-text-muted mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="p-4 border-t border-border-primary flex items-center justify-between">
        <p class="text-sm text-text-muted">
          Page {{ currentPage }} of {{ totalPages }} ({{ filteredPapers.length }} results)
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
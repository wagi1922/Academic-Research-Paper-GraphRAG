<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type HealthResponse, type Paper } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import {
  FileText,
  GitBranch,
  Database,
  Lightbulb,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-vue-next'

const uiStore = useUIStore()

const health = ref<HealthResponse | null>(null)
const recentPapers = ref<Paper[]>([])
const stats = ref({ papers: 0, chunks: 0, entities: 0, relations: 0, citations: 0 })
const loading = ref(true)
const error = ref<string | null>(null)

async function fetchData() {
  try {
    loading.value = true
    error.value = null
    
    const [healthRes, papersRes, statsRes] = await Promise.all([
      api.health(),
      api.getPapers({ limit: 5 }),
      api.getGraphStats(),
    ])
    
    health.value = healthRes
    recentPapers.value = papersRes.papers
    // Transform API response to match UI expectations
    // API returns: papers, authors, concepts, methods, datasets, chunks, citations, relations
    // UI expects: papers, chunks, entities (concepts+methods+datasets), citations, relations
    stats.value = {
      papers: statsRes.papers,
      chunks: statsRes.chunks,
      entities: (statsRes.concepts || 0) + (statsRes.methods || 0) + (statsRes.datasets || 0),
      relations: statsRes.relations,
      citations: statsRes.citations,
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load dashboard data'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})

const statCards = [
  { key: 'papers', label: 'Papers', icon: FileText, color: 'accent-primary' },
  { key: 'chunks', label: 'Chunks', icon: Database, color: 'accent-secondary' },
  { key: 'entities', label: 'Entities', icon: Lightbulb, color: 'accent-success' },
  { key: 'citations', label: 'Citations', icon: GitBranch, color: 'accent-warning' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-text-primary">Dashboard</h1>
        <p class="text-text-secondary mt-1">GraphRAG Research System Overview</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="px-3 py-1 rounded-full text-xs font-medium bg-accent-success/10 text-accent-success flex items-center gap-1">
          <CheckCircle class="w-3 h-3" />
          API Connected
        </span>
        <button @click="fetchData" :disabled="loading" class="btn-secondary">
          <Loader2 :class="{ 'animate-spin': loading }" class="w-4 h-4" />
          Refresh
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="card border-accent-danger/50 bg-accent-danger/5">
      <div class="flex items-center gap-3">
        <AlertCircle class="w-5 h-5 text-accent-danger flex-shrink-0" />
        <p class="text-text-primary">{{ error }}</p>
        <button @click="fetchData" class="ml-auto btn-secondary text-sm">Retry</button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in statCards"
        :key="stat.key"
        class="card-hover"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-text-muted text-sm font-medium">{{ stat.label }}</p>
            <p class="text-3xl font-bold text-text-primary mt-1" v-if="!loading">
              {{ stats[stat.key].toLocaleString() }}
            </p>
            <div v-else class="h-8 w-24 bg-bg-tertiary rounded animate-pulse mt-1" />
          </div>
          <div class="p-3 rounded-xl" :class="`bg-${stat.color}/10`">
            <component :is="stat.icon" :class="`w-6 h-6 text-${stat.color}`" />
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-border-primary flex items-center gap-2 text-sm text-text-muted">
          <Clock class="w-4 h-4" />
          <span>Updated just now</span>
        </div>
      </div>
    </div>

    <!-- Recent Papers & Quick Actions -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent Papers -->
      <div class="lg:col-span-2 card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-text-primary">Recent Papers</h2>
          <router-link to="/papers" class="text-sm text-accent-primary hover:underline">View all</router-link>
        </div>
        
        <div v-if="loading" class="space-y-4">
          <div v-for="i in 3" :key="i" class="flex items-center gap-4 animate-pulse">
            <div class="w-12 h-12 bg-bg-tertiary rounded-lg" />
            <div class="flex-1">
              <div class="h-4 w-3/4 bg-bg-tertiary rounded" />
              <div class="h-3 w-1/2 bg-bg-tertiary rounded mt-2" />
            </div>
          </div>
        </div>
        
        <div v-else-if="recentPapers.length === 0" class="text-center py-8 text-text-muted">
          <FileText class="w-12 h-12 mx-auto mb-3 text-text-muted/50" />
          <p>No papers found. Ingest some papers to get started.</p>
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="paper in recentPapers"
            :key="paper.id"
            class="flex items-center gap-4 p-3 rounded-lg hover:bg-bg-tertiary transition-colors cursor-pointer"
            @click="$router.push(`/papers/${paper.id}`)"
          >
            <div class="w-12 h-12 rounded-lg bg-accent-primary/10 flex items-center justify-center flex-shrink-0">
              <FileText class="w-6 h-6 text-accent-primary" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-medium text-text-primary truncate">{{ paper.title }}</h3>
              <p class="text-sm text-text-muted flex items-center gap-2">
                <span>{{ paper.year }}</span>
                <span>•</span>
                <span>{{ paper.chunk_count }} chunks</span>
              </p>
            </div>
            <TrendingUp class="w-5 h-5 text-text-muted" />
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card">
        <h2 class="text-lg font-semibold text-text-primary mb-4">Quick Actions</h2>
        <div class="space-y-3">
          <router-link to="/query" class="btn-secondary w-full justify-start gap-3 p-4 hover:bg-accent-primary/5 transition-colors">
            <GitBranch class="w-5 h-5 text-accent-primary" />
            <div class="text-left">
              <p class="font-medium text-text-primary">Query GraphRAG</p>
              <p class="text-sm text-text-muted">Ask questions, get grounded answers</p>
            </div>
          </router-link>
          
          <router-link to="/graph" class="btn-secondary w-full justify-start gap-3 p-4 hover:bg-accent-secondary/5 transition-colors">
            <Database class="w-5 h-5 text-accent-secondary" />
            <div class="text-left">
              <p class="font-medium text-text-primary">Explore Knowledge Graph</p>
              <p class="text-sm text-text-muted">Visualize entities and relationships</p>
            </div>
          </router-link>
          
          <router-link to="/papers" class="btn-secondary w-full justify-start gap-3 p-4 hover:bg-accent-success/5 transition-colors">
            <FileText class="w-5 h-5 text-accent-success" />
            <div class="text-left">
              <p class="font-medium text-text-primary">Browse Papers</p>
              <p class="text-sm text-text-muted">View all ingested papers</p>
            </div>
          </router-link>
          
          <router-link to="/citations" class="btn-secondary w-full justify-start gap-3 p-4 hover:bg-accent-warning/5 transition-colors">
            <Lightbulb class="w-5 h-5 text-accent-warning" />
            <div class="text-left">
              <p class="font-medium text-text-primary">Citation Network</p>
              <p class="text-sm text-text-muted">Explore paper citations</p>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <!-- System Status -->
    <div class="card">
      <h2 class="text-lg font-semibold text-text-primary mb-4">System Status</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div class="flex items-center gap-4 p-4 bg-bg-tertiary rounded-lg">
          <CheckCircle class="w-8 h-8 text-accent-success flex-shrink-0" />
          <div>
            <p class="font-medium text-text-primary">API Server</p>
            <p class="text-sm text-text-muted">Running on port 8000</p>
          </div>
        </div>
        <div class="flex items-center gap-4 p-4 bg-bg-tertiary rounded-lg">
          <CheckCircle class="w-8 h-8 text-accent-success flex-shrink-0" />
          <div>
            <p class="font-medium text-text-primary">Neo4j Database</p>
            <p class="text-sm text-text-muted" v-if="health">{{ health.neo4j }}</p>
            <p class="text-sm text-text-muted" v-else>Connected</p>
          </div>
        </div>
        <div class="flex items-center gap-4 p-4 bg-bg-tertiary rounded-lg">
          <CheckCircle class="w-8 h-8 text-accent-success flex-shrink-0" />
          <div>
            <p class="font-medium text-text-primary">Embedding Service</p>
            <p class="text-sm text-text-muted">guard-embedding.service (port 8788)</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { api, type GraphNode, type GraphEdge, type GraphVisualization } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import { useRoute } from 'vue-router'
import GraphVisualizationComp from '@/components/graph/GraphVisualization.vue'
import {
  Loader2,
  RotateCcw,
  Search,
  Database,
  Lightbulb,
  GitBranch,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Settings,
  RefreshCw,
  HelpCircle,
  FileText,
} from 'lucide-vue-next'

const uiStore = useUIStore()
const route = useRoute()

const stats = ref({ papers: 0, chunks: 0, entities: 0, relations: 0, citations: 0 })
const entities = ref<Array<{ id: string; name: string; type: string; paper_count: number }>>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedType = ref('')

// Graph visualization state
const graphData = ref<GraphVisualization | null>(null)
const graphLoading = ref(false)
const graphError = ref<string | null>(null)
const selectedPaperId = ref<string | null>(route.query.paper_id as string || null)
const selectedNodeId = ref<string | null>(null)
const layout = ref<'cose-bilkent' | 'fcose' | 'dagre' | 'circle' | 'grid' | 'concentric'>('cose-bilkent')
const stylePreset = ref<'default' | 'dark' | 'minimal'>('default')
const showControls = ref(true)
const showLegend = ref(true)
const showEntityPanel = ref(true)
const graphRef = ref<InstanceType<typeof GraphVisualizationComp> | null>(null)

// Transform API edges to component format
const graphEdges = computed(() => {
  if (!graphData.value?.edges) return []
  return graphData.value.edges.map((e, i) => ({
    id: `edge_${i}`,
    source: e.source,
    target: e.target,
    label: e.relation,
    type: e.relation.toLowerCase().replace('_', '-'),
    properties: {},
  }))
})

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
  return result.slice(0, 100)
})

const layouts = [
  { value: 'cose-bilkent', label: 'CoSE-Bilkent (Force-directed)', icon: GitBranch },
  { value: 'fcose', label: 'fCoSE (Fast CoSE)', icon: GitBranch },
  { value: 'dagre', label: 'Dagre (Hierarchical)', icon: Database },
  { value: 'circle', label: 'Circle', icon: Lightbulb },
  { value: 'grid', label: 'Grid', icon: Database },
  { value: 'concentric', label: 'Concentric', icon: Lightbulb },
] as const

async function fetchStats() {
  try {
    const statsData = await api.getGraphStats()
    stats.value = statsData
  } catch (err) {
    uiStore.notify('error', err instanceof Error ? err.message : 'Failed to load stats')
  }
}

async function fetchEntities() {
  try {
    const data = await api.listEntities({ limit: 500 })
    entities.value = data.entities
  } catch (err) {
    uiStore.notify('error', err instanceof Error ? err.message : 'Failed to load entities')
  }
}

async function fetchGraph() {
  if (!selectedPaperId.value && !selectedNodeId.value) {
    graphData.value = null
    return
  }

  graphLoading.value = true
  graphError.value = null

  try {
    const data = await api.getGraphVisualization({
      paperId: selectedPaperId.value || undefined,
      nodeId: selectedNodeId.value || undefined,
      depth: 2,
      maxNodes: 150
    })
    graphData.value = data
    graphError.value = null
  } catch (err) {
    graphError.value = err instanceof Error ? err.message : 'Failed to load graph'
    graphData.value = null
    uiStore.notify('error', graphError.value)
  } finally {
    graphLoading.value = false
  }
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    await Promise.all([fetchStats(), fetchEntities()])
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load graph data'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

function getTypeColor(type: string) {
  const colors: Record<string, string> = {
    'Paper': 'accent-primary',
    'Author': 'accent-secondary',
    'Concept': 'accent-danger',
    'Method': 'accent-warning',
    'Dataset': 'accent-success',
    'Model': 'accent-primary',
    'Metric': 'accent-success',
  }
  return colors[type] || 'text-text-muted'
}

function handlePaperSelect(paperId: string) {
  selectedPaperId.value = paperId
  selectedNodeId.value = null
  fetchGraph()
}

function handleNodeClick(node: GraphNode) {
  selectedNodeId.value = node.id
  if (node.type === 'paper') {
    selectedPaperId.value = node.id
  }
  fetchGraph()
}

function handleEdgeClick(edge: GraphEdge) {
  uiStore.notify('info', `${edge.source} ${edge.relation} ${edge.target}`)
}

function clearSelection() {
  selectedPaperId.value = null
  selectedNodeId.value = null
  graphData.value = null
  graphRef.value?.centerView()
}

function onGraphReady(cy: any) {
  uiStore.notify('success', `Graph loaded: ${cy.nodes().length} nodes, ${cy.edges().length} edges`)
}

function setLayout(newLayout: typeof layout.value) {
  layout.value = newLayout
  graphRef.value?.getCytoscapeInstance()?.layout({
    name: newLayout,
    animate: true,
    animationDuration: 1000,
  }).run()
}

function resetView() {
  graphRef.value?.fitView()
  graphRef.value?.centerView()
}

function toggleControls() {
  showControls.value = !showControls.value
}

function toggleLegend() {
  showLegend.value = !showLegend.value
}

function toggleEntityPanel() {
  showEntityPanel.value = !showEntityPanel.value
}

onMounted(() => {
  fetchData()
  // Watch for route query changes
  watch(() => route.query.paper_id, (newVal) => {
    if (newVal) {
      selectedPaperId.value = newVal as string
      fetchGraph()
    }
  }, { immediate: true })
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-text-primary">Knowledge Graph</h1>
        <p class="text-text-secondary mt-1">Explore entities and relationships</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="fetchData" :disabled="loading" class="btn-secondary">
          <Loader2 :class="{ 'animate-spin': loading }" class="w-4 h-4" />
          Refresh
        </button>
        <button @click="toggleEntityPanel" class="btn-ghost p-2" :aria-expanded="showEntityPanel" aria-label="Toggle entity panel">
          <ChevronDown :class="{ 'rotate-180': !showEntityPanel }" class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <div class="card-hover">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-accent-primary/10">
            <FileText class="w-5 h-5 text-accent-primary" />
          </div>
          <div>
            <p class="text-sm text-text-muted">Papers</p>
            <p class="text-2xl font-bold text-text-primary">{{ stats.papers }}</p>
          </div>
        </div>
      </div>
      <div class="card-hover">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-accent-secondary/10">
            <Database class="w-5 h-5 text-accent-secondary" />
          </div>
          <div>
            <p class="text-sm text-text-muted">Chunks</p>
            <p class="text-2xl font-bold text-text-primary">{{ stats.chunks }}</p>
          </div>
        </div>
      </div>
      <div class="card-hover">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-accent-success/10">
            <Lightbulb class="w-5 h-5 text-accent-success" />
          </div>
          <div>
            <p class="text-sm text-text-muted">Entities</p>
            <p class="text-2xl font-bold text-text-primary">{{ stats.entities }}</p>
          </div>
        </div>
      </div>
      <div class="card-hover">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-accent-warning/10">
            <GitBranch class="w-5 h-5 text-accent-warning" />
          </div>
          <div>
            <p class="text-sm text-text-muted">Relations</p>
            <p class="text-2xl font-bold text-text-primary">{{ stats.relations }}</p>
          </div>
        </div>
      </div>
      <div class="card-hover">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-accent-danger/10">
            <Database class="w-5 h-5 text-accent-danger" />
          </div>
          <div>
            <p class="text-sm text-text-muted">Citations</p>
            <p class="text-2xl font-bold text-text-primary">{{ stats.citations }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Entity Browser Panel -->
    <transition name="slide">
      <div v-show="showEntityPanel" class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-text-primary">Entities</h2>
          <button @click="toggleEntityPanel" class="btn-ghost p-2" aria-label="Collapse entity panel">
            <ChevronUp class="w-4 h-4" />
          </button>
        </div>

        <div class="flex flex-col sm:flex-row gap-4 mb-4">
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
        </div>

        <div v-if="loading" class="text-center py-8">
          <Loader2 class="w-8 h-8 animate-spin text-accent-primary mx-auto mb-3" />
          <p class="text-text-secondary">Loading entities...</p>
        </div>

        <div v-else-if="filteredEntities.length === 0" class="text-center py-8">
          <Lightbulb class="w-16 h-16 text-text-muted mx-auto mb-4" />
          <h3 class="text-lg font-medium text-text-primary mb-2">No entities found</h3>
          <p class="text-text-secondary">Try adjusting your search or filter</p>
        </div>

        <div v-else class="space-y-2 max-h-[400px] overflow-y-auto">
          <div
            v-for="entity in filteredEntities"
            :key="entity.id"
            class="flex items-center gap-4 p-3 rounded-lg hover:bg-bg-tertiary transition-colors cursor-pointer"
            @click="handlePaperSelect(entity.id)"
          >
            <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="`bg-${getTypeColor(entity.type)}/10`">
              <component :is="entity.type === 'Paper' ? 'FileText' : 'Lightbulb'" :class="`w-5 h-5 ${getTypeColor(entity.type)}`" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-text-primary truncate">{{ entity.name }}</p>
              <p class="text-sm text-text-muted">{{ entity.type }} • {{ entity.paper_count }} papers</p>
            </div>
            <span class="badge badge-primary">{{ entity.paper_count }}</span>
          </div>
        </div>

        <div v-if="entities.length > 100" class="mt-4 text-center text-sm text-text-muted">
          Showing 100 of {{ entities.length }} entities. Use search to filter.
        </div>
      </div>
    </transition>

    <!-- Graph Visualization -->
    <div class="card">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold text-text-primary">Graph Visualization</h2>
          <span v-if="graphData" class="badge badge-secondary">
            {{ graphData.nodes.length }} nodes, {{ graphEdges.length }} edges
          </span>
          <span v-if="selectedPaperId" class="badge badge-primary">
            Paper: {{ selectedPaperId.slice(0, 20) }}{{ selectedPaperId.length > 20 ? '...' : '' }}
          </span>
        </div>

        <!-- Controls -->
        <div v-if="showControls" class="flex flex-wrap items-center gap-2">
          <!-- Layout Selector -->
          <div class="relative">
            <select
              v-model="layout"
              @change="setLayout(layout)"
              class="input pr-8 appearance-none"
              aria-label="Layout algorithm"
            >
              <option v-for="l in layouts" :key="l.value" :value="l.value">{{ l.label }}</option>
            </select>
            <GitBranch class="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
          </div>

          <div class="flex items-center gap-1 bg-bg-tertiary rounded-lg p-1">
            <button
              v-for="l in layouts"
              :key="l.value"
              @click="setLayout(l.value)"
              :class="[
                'p-1.5 rounded transition-colors',
                layout === l.value ? 'bg-bg-secondary text-text-primary shadow-sm' : 'text-text-muted hover:text-text-primary'
              ]"
              :title="l.label"
              :aria-pressed="layout === l.value"
            >
              <component :is="l.icon" class="w-4 h-4" />
            </button>
          </div>

          <div class="flex items-center gap-1 bg-bg-tertiary rounded-lg p-1 ml-2">
            <button @click="resetView" class="btn-ghost p-1.5 rounded" title="Reset view" aria-label="Reset view">
              <RotateCcw class="w-4 h-4" />
            </button>
            <button @click="graphRef?.fitView" class="btn-ghost p-1.5 rounded" title="Fit to view" aria-label="Fit graph to view">
              <Maximize2 class="w-4 h-4" />
            </button>
          </div>

          <div class="flex items-center gap-1 bg-bg-tertiary rounded-lg p-1 ml-2">
            <button @click="toggleLegend" class="btn-ghost p-1.5 rounded" :class="showLegend ? 'bg-bg-secondary text-text-primary' : 'text-text-muted'" title="Toggle legend" aria-label="Toggle legend" :aria-pressed="showLegend">
              <HelpCircle class="w-4 h-4" />
            </button>
            <button @click="toggleControls" class="btn-ghost p-1.5 rounded" :class="showControls ? 'bg-bg-secondary text-text-primary' : 'text-text-muted'" title="Hide controls" aria-label="Hide controls" :aria-pressed="showControls">
              <Settings class="w-4 h-4" />
            </button>
          </div>

          <button v-if="graphData" @click="clearSelection" class="btn-ghost text-sm ml-2" :disabled="!selectedPaperId && !selectedNodeId">
            <RefreshCw class="w-4 h-4 mr-1" />
            Clear Selection
          </button>
        </div>
      </div>

      <!-- Graph Container -->
      <div class="relative" style="height: 600px;">
        <GraphVisualizationComp
          ref="graphRef"
          :nodes="graphData?.nodes || []"
          :edges="graphEdges"
          :layout="layout"
          :style-preset="stylePreset"
          :fit-on-init="true"
          :animate-on-init="true"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          @ready="onGraphReady"
        />

        <!-- Loading Overlay -->
        <div v-if="graphLoading" class="absolute inset-0 flex items-center justify-center bg-bg-primary/90 z-10">
          <div class="text-center">
            <Loader2 class="w-10 h-10 animate-spin text-accent-primary mx-auto mb-3" />
            <p class="text-text-secondary">Loading graph...</p>
          </div>
        </div>

        <!-- Error Overlay -->
        <div v-if="graphError" class="absolute inset-0 flex items-center justify-center bg-bg-primary/90 z-10 p-4">
          <div class="text-center text-accent-danger">
            <p class="font-medium mb-2">Failed to load graph</p>
            <p class="text-sm text-text-muted">{{ graphError }}</p>
            <button @click="fetchGraph" class="btn-secondary mt-3">Retry</button>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!graphLoading && !graphError && (!graphData || !graphData.nodes.length)" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center p-8">
            <GitBranch class="w-16 h-16 text-text-muted mx-auto mb-4" />
            <h3 class="text-lg font-medium text-text-primary mb-2">No graph data</h3>
            <p class="text-text-secondary mb-4">Select a paper from the entity list or enter a paper ID to visualize its knowledge graph</p>
            <p class="text-sm text-text-muted">Nodes: Papers, Authors, Concepts, Methods, Datasets</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, nextTick, h, defineComponent, type CSSProperties } from 'vue'
import * as cytoscapeModule from 'cytoscape'
import * as coseBilkentModule from 'cytoscape-cose-bilkent'
import * as fcoseModule from 'cytoscape-fcose'
import * as dagreModule from 'cytoscape-dagre'
import type { Core } from 'cytoscape'
type CyStylesheet = any
type CyLayoutOptions = any

const cytoscape = cytoscapeModule.default || cytoscapeModule
const coseBilkent = coseBilkentModule.default || coseBilkentModule
const fcose = fcoseModule.default || fcoseModule
const dagre = dagreModule.default || dagreModule

// Register extensions
cytoscape.use(coseBilkent)
cytoscape.use(fcose)
cytoscape.use(dagre)

interface Props {
  nodes: GraphNode[]
  edges: GraphEdge[]
  layout?: 'cose-bilkent' | 'fcose' | 'dagre' | 'circle' | 'grid' | 'concentric'
  stylePreset?: 'default' | 'dark' | 'minimal'
  fitOnInit?: boolean
  animateOnInit?: boolean
}

interface GraphNode {
  id: string
  label: string
  type: string
  properties: Record<string, unknown>
  classes: string
}

interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  type: string
  properties: Record<string, unknown>
}

interface Emits {
  (e: 'node-click', node: GraphNode): void
  (e: 'edge-click', edge: GraphEdge): void
  (e: 'ready', cy: Core): void
}

const props = withDefaults(defineProps<Props>(), {
  nodes: () => [],
  edges: () => [],
  layout: 'cose-bilkent',
  stylePreset: 'default',
  fitOnInit: true,
  animateOnInit: true,
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
const cyRef = ref<Core | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Default Cytoscape styles
const defaultStylesheet: CyStylesheet[] = [
  // Node styles by type
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'font-size': '11px',
      'font-family': 'Inter, system-ui, sans-serif',
      'font-weight': 500,
      'color': '#e5e7eb', // text-text-primary
      'text-outline-width': 2,
      'text-outline-color': '#111827', // bg-bg-primary
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '80px',
      'background-color': '#3b82f6', // accent-primary
      'border-width': 2,
      'border-color': '#111827',
      'width': 36,
      'height': 36,
      'overlay-padding': '6px',
      'z-index': 10,
    },
  },
  // Node type specific colors
  {
    selector: 'node[type="paper"]',
    style: {
      'background-color': '#3b82f6',
      'border-color': '#1d4ed8',
      'shape': 'rectangle',
      'width': 48,
      'height': 48,
    },
  },
  {
    selector: 'node[type="author"]',
    style: {
      'background-color': '#8b5cf6',
      'border-color': '#6d28d9',
      'shape': 'ellipse',
      'width': 40,
      'height': 40,
    },
  },
  {
    selector: 'node[type="concept"]',
    style: {
      'background-color': '#ef4444',
      'border-color': '#b91c1c',
      'shape': 'diamond',
      'width': 36,
      'height': 36,
    },
  },
  {
    selector: 'node[type="method"]',
    style: {
      'background-color': '#f59e0b',
      'border-color': '#b45309',
      'shape': 'hexagon',
      'width': 40,
      'height': 40,
    },
  },
  {
    selector: 'node[type="dataset"]',
    style: {
      'background-color': '#10b981',
      'border-color': '#047857',
      'shape': 'round-rectangle',
      'width': 40,
      'height': 40,
    },
  },
  // Edge styles
  {
    selector: 'edge',
    style: {
      'label': 'data(label)',
      'font-size': '9px',
      'font-family': 'Inter, system-ui, sans-serif',
      'color': '#9ca3af', // text-text-muted
      'text-outline-width': 2,
      'text-outline-color': '#111827',
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#6b7280',
      'line-color': '#6b7280',
      'width': 1.5,
      'overlay-padding': '3px',
      'z-index': 1,
    },
  },
  // Edge type specific
  {
    selector: 'edge[type="cites"]',
    style: {
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'width': 2,
    },
  },
  {
    selector: 'edge[type="wrote"]',
    style: {
      'line-color': '#8b5cf6',
      'target-arrow-color': '#8b5cf6',
    },
  },
  {
    selector: 'edge[type="addresses_topic"]',
    style: {
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
    },
  },
  {
    selector: 'edge[type="uses_method"]',
    style: {
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
    },
  },
  {
    selector: 'edge[type="uses_dataset"]',
    style: {
      'line-color': '#10b981',
      'target-arrow-color': '#10b981',
    },
  },
  // Interactive states
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#fbbf24', // accent-warning
      'z-index': 100,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'width': 3,
      'line-color': '#fbbf24',
      'target-arrow-color': '#fbbf24',
      'z-index': 50,
    },
  },
  {
    selector: '.faded',
    style: {
      'opacity': 0.2,
      'text-opacity': 0.1,
    },
  },
]

const darkStylesheet: CyStylesheet[] = defaultStylesheet.map(s => ({
  ...s,
  style: {
    ...s.style,
    'color': '#f9fafb',
    'text-outline-color': '#0f172a',
    'border-color': '#0f172a',
  },
}))

const minimalStylesheet: CyStylesheet[] = defaultStylesheet.map(s => ({
  ...s,
  style: {
    ...s.style,
    'font-size': '9px',
    'text-max-width': '60px',
    'overlay-padding': '3px',
  },
}))

function getStylesheet(): CyStylesheet[] {
  switch (props.stylePreset) {
    case 'dark': return darkStylesheet
    case 'minimal': return minimalStylesheet
    default: return defaultStylesheet
  }
}

function formatElements() {
  const nodes = props.nodes.map(n => ({
    data: {
      id: n.id,
      label: n.label,
      type: n.type,
      ...n.properties,
    },
    classes: n.classes || n.type,
  }))

  const edges = props.edges.map(e => ({
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      type: e.type.toLowerCase(),
      ...e.properties,
    },
    classes: e.type.toLowerCase(),
  }))

  return [...nodes, ...edges]
}

function initCytoscape() {
  if (!containerRef.value || cyRef.value) return

  loading.value = true
  error.value = null

  try {
    const cy = cytoscape({
      container: containerRef.value,
      elements: formatElements(),
      style: getStylesheet(),
      layout: getLayoutConfig(),
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.3,
      motionBlur: true,
    })

    cyRef.value = cy

    // Event handlers
    cy.on('tap', 'node', (evt) => {
      const node = evt.target.data()
      emit('node-click', node as GraphNode)
    })

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target.data()
      emit('edge-click', edge as GraphEdge)
    })

    // Fade unconnected on hover
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target
      const neighborhood = node.closedNeighborhood()
      cy.elements().addClass('faded')
      neighborhood.removeClass('faded')
    })

    cy.on('mouseout', 'node', () => {
      cy.elements().removeClass('faded')
    })

    // Fit view on init
    if (props.fitOnInit) {
      cy.one('layoutready', () => {
        if (props.animateOnInit) {
          cy.fit(cy.elements(), 50)
        } else {
          cy.fit(cy.elements(), 50)
        }
        loading.value = false
        emit('ready', cy)
      })
    } else {
      loading.value = false
      emit('ready', cy)
    }

    // Handle layout stop
    cy.on('layoutstop', () => {
      if (props.fitOnInit) {
        cy.fit(cy.elements(), 50)
      }
    })

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to initialize graph'
    loading.value = false
  }
}

function getLayoutConfig(): CyLayoutOptions {
  const baseConfig = {
    name: props.layout,
    animate: props.animateOnInit,
    animationDuration: 1000,
    animationEasing: 'ease-out',
    fit: false, // We handle fit manually
    padding: 50,
    randomize: true,
  } as CyLayoutOptions

  switch (props.layout) {
    case 'cose-bilkent':
      return {
        ...baseConfig,
        name: 'cose-bilkent',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
        tile: true,
      } as CyLayoutOptions

    case 'fcose':
      return {
        ...baseConfig,
        name: 'fcose',
        quality: 'proof',
        randomize: true,
        animate: true,
        animationDuration: 1000,
        idealEdgeLength: 100,
        nodeOverlap: 20,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 2000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      } as CyLayoutOptions

    case 'dagre':
      return {
        ...baseConfig,
        name: 'dagre',
        rankDir: 'TB',
        ranker: 'tight-tree',
        nodeSep: 50,
        edgeSep: 20,
        rankSep: 100,
      } as CyLayoutOptions

    case 'circle':
      return {
        ...baseConfig,
        name: 'circle',
        radius: 200,
        startAngle: 3 / 2 * Math.PI,
        counterclockwise: false,
      } as CyLayoutOptions

    case 'grid':
      return {
        ...baseConfig,
        name: 'grid',
        rows: Math.ceil(Math.sqrt(props.nodes.length)),
        cols: Math.ceil(Math.sqrt(props.nodes.length)),
      } as CyLayoutOptions

    case 'concentric':
      return {
        ...baseConfig,
        name: 'concentric',
        minNodeSpacing: 50,
        sweep: Math.PI,
        startAngle: 3 / 2 * Math.PI,
      } as CyLayoutOptions

    default:
      return baseConfig
  }
}

function updateElements() {
  if (!cyRef.value) return
  cyRef.value.elements().remove()
  cyRef.value.add(formatElements())
  cyRef.value.layout(getLayoutConfig()).run()
}

function updateStyle() {
  if (!cyRef.value) return
  cyRef.value.style(getStylesheet()).update()
}

// Watch for prop changes
watch(() => props.nodes, updateElements, { deep: true })
watch(() => props.edges, updateElements, { deep: true })
watch(() => props.stylePreset, updateStyle)
watch(() => props.layout, () => {
  if (cyRef.value) {
    cyRef.value.layout(getLayoutConfig()).run()
  }
})

// Public methods for external control
function fitView(padding = 50) {
  cyRef.value?.fit(cyRef.value.elements(), padding)
}

function centerView() {
  cyRef.value?.center()
}

function resetZoom() {
  cyRef.value?.zoom(1)
  cyRef.value?.pan({ x: 0, y: 0 })
}

function getCytoscapeInstance() {
  return cyRef.value
}

// Cleanup
onUnmounted(() => {
  cyRef.value?.destroy()
  cyRef.value = null
})

// Initialize on mount
onMounted(() => {
  nextTick(() => {
    initCytoscape()
  })
})

// Expose methods for parent component
defineExpose({
  fitView,
  centerView,
  resetZoom,
  getCytoscapeInstance,
})

// Legend Item Sub-component
const LegendItem = defineComponent({
  props: {
    color: { type: String, required: true },
    label: { type: String, required: true },
    shape: { type: String, default: 'circle' },
  },
  setup(props) {
    const shapeStyles: Record<string, CSSProperties> = {
      rectangle: { borderRadius: '4px' },
      circle: { borderRadius: '50%' },
      diamond: { clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' },
      hexagon: { clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' },
      'round-rectangle': { borderRadius: '12px' },
    }
    return () => h('div', { class: 'flex items-center gap-2' }, [
      h('div', {
        style: {
          width: '12px',
          height: '12px',
          backgroundColor: props.color,
          border: '1px solid #111827',
          ...shapeStyles[props.shape],
        },
      }),
      h('span', { class: 'text-text-secondary' }, props.label),
    ])
  },
})
</script>

<template>
  <div class="w-full h-full relative">
    <!-- Container -->
    <div
      ref="containerRef"
      class="w-full h-full bg-bg-primary"
      style="min-height: 400px;"
      aria-label="Knowledge graph visualization"
    />

    <!-- Loading Overlay -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-bg-primary/90 z-10">
      <div class="text-center">
        <div class="w-10 h-10 border-3 border-accent-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p class="text-text-secondary">Rendering graph...</p>
      </div>
    </div>

    <!-- Error Overlay -->
    <div v-if="error" class="absolute inset-0 flex items-center justify-center bg-bg-primary/90 z-10 p-4">
      <div class="text-center text-accent-danger">
        <p class="font-medium mb-2">Failed to render graph</p>
        <p class="text-sm text-text-muted">{{ error }}</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && (!props.nodes.length || !cyRef)" class="absolute inset-0 flex items-center justify-center">
      <div class="text-center p-8">
        <svg class="w-16 h-16 text-text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <p class="text-text-secondary">No graph data to display</p>
      </div>
    </div>

    <!-- Controls Overlay -->
    <div v-if="cyRef && !loading" class="absolute bottom-4 right-4 flex flex-col gap-2 z-20">
      <button
        @click="() => fitView()"
        class="btn-secondary p-2 shadow-lg"
        title="Fit to view"
        aria-label="Fit graph to view"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>
      <button
        @click="() => centerView()"
        class="btn-secondary p-2 shadow-lg"
        title="Center view"
        aria-label="Center graph view"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
      <button
        @click="() => resetZoom()"
        class="btn-secondary p-2 shadow-lg"
        title="Reset zoom"
        aria-label="Reset zoom level"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>
    </div>

    <!-- Legend Overlay -->
    <div v-if="cyRef && !loading" class="absolute top-4 left-4 z-20">
      <div class="bg-bg-secondary/95 backdrop-blur-sm border border-border-primary rounded-lg p-3 shadow-lg min-w-[160px]">
        <p class="text-xs font-semibold text-text-primary mb-2">Node Types</p>
        <div class="space-y-1.5 text-xs">
          <LegendItem color="#3b82f6" label="Paper" shape="rectangle" />
          <LegendItem color="#8b5cf6" label="Author" shape="circle" />
          <LegendItem color="#ef4444" label="Concept" shape="diamond" />
          <LegendItem color="#f59e0b" label="Method" shape="hexagon" />
          <LegendItem color="#10b981" label="Dataset" shape="round-rectangle" />
        </div>
      </div>
    </div>
  </div>
</template>
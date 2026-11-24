<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { api } from '@/services/api'
import {
  Loader2,
  Server,
  Database,
  Cpu,
  Save,
  Info,
  GitBranch,
} from 'lucide-vue-next'

const uiStore = useUIStore()

const apiBase = ref(import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1')
const healthStatus = ref<'checking' | 'healthy' | 'unhealthy' | 'unknown'>('unknown')
const healthDetails = ref<Record<string, string> | null>(null)
const checkingHealth = ref(false)

const tabs = ['Connection', 'About', 'Advanced'] as const
const activeTab = ref<(typeof tabs)[number]>('Connection')

const debugInfo = computed(() => ({
  apiBase: apiBase.value,
  userAgent: navigator.userAgent,
  viewport: `${window.innerWidth}x${window.innerHeight}`,
  timestamp: new Date().toISOString(),
  localStorage: Object.keys(localStorage).filter(k => k.startsWith('graphrag_')),
}))

async function checkHealth() {
  checkingHealth.value = true
  healthStatus.value = 'checking'
  try {
    const health = await api.health()
    healthStatus.value = health.status === 'healthy' ? 'healthy' : 'unhealthy'
    healthDetails.value = {
      neo4j: health.neo4j,
      version: health.version,
    }
    uiStore.notify(healthStatus.value === 'healthy' ? 'success' : 'error',
      `API ${healthStatus.value === 'healthy' ? 'connected' : 'unhealthy'}`)
  } catch (err) {
    healthStatus.value = 'unhealthy'
    healthDetails.value = null
    uiStore.notify('error', `Connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
  } finally {
    checkingHealth.value = false
  }
}

function saveSettings() {
  localStorage.setItem('graphrag_api_base', apiBase.value)
  uiStore.notify('success', 'Settings saved. Reload the page to apply changes.')
}

function resetSettings() {
  apiBase.value = 'http://localhost:8000/api/v1'
  localStorage.removeItem('graphrag_api_base')
  uiStore.notify('info', 'Settings reset to defaults')
}

onMounted(() => {
  const saved = localStorage.getItem('graphrag_api_base')
  if (saved) apiBase.value = saved
  checkHealth()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold text-text-primary">Settings</h1>
      <p class="text-text-secondary mt-1">Configure GraphRAG frontend settings</p>
    </div>

    <!-- Tabs -->
    <div class="card">
      <div class="border-b border-border-primary">
        <nav class="flex gap-1 p-1" aria-label="Settings sections">
          <button
            v-for="tab in tabs"
            :key="tab"
            @click="activeTab = tab"
            :class="[
              'flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors',
              activeTab === tab ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-primary'
            ]"
          >
            {{ tab }}
          </button>
        </nav>
      </div>

      <!-- Connection Tab -->
      <div v-if="activeTab === 'Connection'" class="p-6 space-y-6">
        <div>
          <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Server class="w-5 h-5 text-accent-primary" />
            API Connection
          </h2>
          
          <div class="space-y-4">
            <div>
              <label for="api-base" class="block text-sm font-medium text-text-secondary mb-1">
                API Base URL
              </label>
              <input
                id="api-base"
                v-model="apiBase"
                type="url"
                placeholder="http://localhost:8000/api/v1"
                class="input font-mono text-sm"
                :disabled="checkingHealth"
              />
              <p class="text-xs text-text-muted mt-1">Base URL for the GraphRAG API backend</p>
            </div>

            <div class="flex items-center gap-4">
              <button
                @click="checkHealth"
                :disabled="checkingHealth"
                class="btn-primary flex items-center gap-2"
              >
                <Loader2 v-if="checkingHealth" class="w-4 h-4 animate-spin" />
                <Server v-else class="w-4 h-4" />
                {{ checkingHealth ? 'Checking...' : 'Test Connection' }}
              </button>
              
              <div class="flex items-center gap-2">
                <div
                  class="w-3 h-3 rounded-full transition-colors"
                  :class="{
                    'bg-accent-success': healthStatus === 'healthy',
                    'bg-accent-danger': healthStatus === 'unhealthy',
                    'bg-accent-warning animate-pulse': healthStatus === 'checking',
                    'bg-border-primary': healthStatus === 'unknown',
                  }"
                />
                <span class="text-sm font-medium text-text-secondary capitalize">{{ healthStatus }}</span>
              </div>
            </div>

            <div v-if="healthDetails" class="p-4 bg-bg-tertiary rounded-lg space-y-2">
              <h3 class="text-sm font-medium text-text-primary">Health Details</h3>
              <dl class="space-y-1 text-sm">
                <div class="flex justify-between">
                  <dt class="text-text-muted">Neo4j Status</dt>
                  <dd class="font-medium" :class="healthDetails.neo4j === 'connected' ? 'text-accent-success' : 'text-accent-danger'">
                    {{ healthDetails.neo4j }}
                  </dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-text-muted">API Version</dt>
                  <dd class="font-medium text-text-primary">{{ healthDetails.version }}</dd>
                </div>
              </dl>
            </div>

            <div class="flex gap-3 pt-4 border-t border-border-primary">
              <button @click="saveSettings" class="btn-primary flex items-center gap-2">
                <Save class="w-4 h-4" />
                Save Settings
              </button>
              <button @click="resetSettings" class="btn-secondary">Reset to Defaults</button>
            </div>
          </div>
        </div>

        <!-- Service Status -->
        <div class="pt-6 border-t border-border-primary">
          <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Cpu class="w-5 h-5 text-accent-secondary" />
            Service Endpoints
          </h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="p-4 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-accent-primary/10">
                  <Server class="w-5 h-5 text-accent-primary" />
                </div>
                <div>
                  <p class="font-medium text-text-primary">GraphRAG API</p>
                  <p class="text-sm text-text-muted font-mono">{{ apiBase }}</p>
                </div>
              </div>
            </div>
            <div class="p-4 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-accent-secondary/10">
                  <Database class="w-5 h-5 text-accent-secondary" />
                </div>
                <div>
                  <p class="font-medium text-text-primary">Neo4j Database</p>
                  <p class="text-sm text-text-muted font-mono">bolt://localhost:7687</p>
                </div>
              </div>
            </div>
            <div class="p-4 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-accent-success/10">
                  <Cpu class="w-5 h-5 text-accent-success" />
                </div>
                <div>
                  <p class="font-medium text-text-primary">Embedding Service</p>
                  <p class="text-sm text-text-muted font-mono">http://localhost:8788</p>
                </div>
              </div>
            </div>
            <div class="p-4 bg-bg-tertiary rounded-lg">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-accent-warning/10">
                  <Database class="w-5 h-5 text-accent-warning" />
                </div>
                <div>
                  <p class="font-medium text-text-primary">Grobid</p>
                  <p class="text-sm text-text-muted font-mono">http://localhost:8070</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- About Tab -->
      <div v-if="activeTab === 'About'" class="p-6 space-y-6">
        <div class="text-center py-8">
          <div class="w-16 h-16 rounded-xl bg-accent-primary/10 flex items-center justify-center mx-auto mb-4">
            <GitBranch class="w-8 h-8 text-accent-primary" />
          </div>
          <h2 class="text-xl font-bold text-text-primary">GraphRAG Research System</h2>
          <p class="text-text-secondary mt-2">Capstone Project - Semester 7</p>
          <p class="text-text-muted mt-1">Universitas Islam Riau - Teknik Informatika</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="p-4 bg-bg-tertiary rounded-lg">
            <h3 class="font-medium text-text-primary mb-2 flex items-center gap-2">
              <Info class="w-4 h-4 text-accent-primary" />
              Features
            </h3>
            <ul class="space-y-1 text-sm text-text-secondary">
              <li>• Hybrid vector + graph retrieval</li>
              <li>• Grounded answer generation with citations</li>
              <li>• Knowledge graph exploration</li>
              <li>• Citation network analysis</li>
              <li>• Entity extraction & browsing</li>
            </ul>
          </div>
          
          <div class="p-4 bg-bg-tertiary rounded-lg">
            <h3 class="font-medium text-text-primary mb-2 flex items-center gap-2">
              <Info class="w-4 h-4 text-accent-primary" />
              Tech Stack
            </h3>
            <ul class="space-y-1 text-sm text-text-secondary">
              <li>• Backend: FastAPI + Neo4j + Grobid</li>
              <li>• Embeddings: all-MiniLM-L6-v2 (local)</li>
              <li>• LLM: OpenRouter (nemotron-3.5-lightning)</li>
              <li>• Frontend: Vue 3 + Vite + Tailwind</li>
              <li>• State: Pinia</li>
            </ul>
          </div>
        </div>

        <div class="p-4 bg-bg-tertiary rounded-lg">
          <h3 class="font-medium text-text-primary mb-2 flex items-center gap-2">
            <Info class="w-4 h-4 text-accent-primary" />
            Corpus Statistics
          </h3>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <p class="text-2xl font-bold text-accent-primary">59</p>
              <p class="text-sm text-text-muted">Papers</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-accent-secondary">7,224</p>
              <p class="text-sm text-text-muted">Chunks</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-accent-success">4</p>
              <p class="text-sm text-text-muted">Citation Edges</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-accent-warning">46</p>
              <p class="text-sm text-text-muted">QA Pairs</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Advanced Tab -->
      <div v-if="activeTab === 'Advanced'" class="p-6 space-y-6">
        <div>
          <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Info class="w-5 h-5 text-accent-warning" />
            Advanced Settings
          </h2>
          
          <div class="space-y-4">
            <div class="p-4 bg-bg-tertiary rounded-lg border border-border-primary">
              <h3 class="font-medium text-text-primary mb-2">Experimental Features</h3>
              <p class="text-sm text-text-muted mb-4">These features are experimental and may be unstable.</p>
              <div class="space-y-3">
                <label class="flex items-center justify-between cursor-pointer">
                  <div>
                    <p class="font-medium text-text-primary">Graph Visualization (Cytoscape.js)</p>
                    <p class="text-sm text-text-muted">Interactive force-directed graph</p>
                  </div>
                  <input type="checkbox" class="rounded border-border-primary text-accent-primary focus:ring-accent-primary" disabled />
                </label>
                <label class="flex items-center justify-between cursor-pointer">
                  <div>
                    <p class="font-medium text-text-primary">Real-time Query Streaming</p>
                    <p class="text-sm text-text-muted">Stream answers token by token</p>
                  </div>
                  <input type="checkbox" class="rounded border-border-primary text-accent-primary focus:ring-accent-primary" disabled />
                </label>
                <label class="flex items-center justify-between cursor-pointer">
                  <div>
                    <p class="font-medium text-text-primary">Export Results (PDF/JSON)</p>
                    <p class="text-sm text-text-muted">Download query results</p>
                  </div>
                  <input type="checkbox" class="rounded border-border-primary text-accent-primary focus:ring-accent-primary" disabled />
                </label>
              </div>
            </div>

            <div class="p-4 bg-bg-tertiary rounded-lg border border-border-primary">
              <h3 class="font-medium text-text-primary mb-2">Debug Information</h3>
              <div class="code-block text-xs">
                <pre>{{ debugInfo }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
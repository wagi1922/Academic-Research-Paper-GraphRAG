<script setup lang="ts">
import { ref, computed, type ComputedRef } from 'vue'
import { api, type QueryRequest, type QueryResponse, type Source } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import {
  Send,
  Loader2,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  GitBranch,
  Lightbulb,
  Database,
  AlertCircle,
  Info,
} from 'lucide-vue-next'

const uiStore = useUIStore()

const query = ref('')
const isLoading = ref(false)
const response = ref<QueryResponse | null>(null)
const error = ref<string | null>(null)
const showAdvanced = ref(false)
const copiedSource = ref<string | null>(null)

const topK = ref(10)
const depth = ref(2)
const includeGraph = ref(true)
const retrievalOnly = ref(false)

const hasResponse = computed(() => response.value !== null)
const responseData = computed(() => {
  if (!response.value) throw new Error('Response is null')
  return response.value
}) as ComputedRef<QueryResponse>

async function submitQuery() {
  if (!query.value.trim() || isLoading.value) return
  
  isLoading.value = true
  error.value = null
  response.value = null
  
  try {
    const request: QueryRequest = {
      query: query.value.trim(),
      top_k: topK.value,
      depth: depth.value,
      include_graph: includeGraph.value,
      retrieval_only: retrievalOnly.value,
    }
    
    const result = await api.query(request)
    response.value = result
    uiStore.notify('success', 'Query completed successfully')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Query failed'
    uiStore.notify('error', error.value)
  } finally {
    isLoading.value = false
  }
}

function copyToClipboard(text: string, sourceId: string) {
  navigator.clipboard.writeText(text)
  copiedSource.value = sourceId
  setTimeout(() => copiedSource.value = null, 2000)
  uiStore.notify('success', 'Copied to clipboard')
}

function formatScore(score: number) {
  return (score * 100).toFixed(1) + '%'
}

function getScoreColor(score: number) {
  if (score >= 0.7) return 'text-accent-success'
  if (score >= 0.4) return 'text-accent-warning'
  return 'text-accent-danger'
}

function formatAnswer(answer: string) {
  // Convert markdown-like citations [1] to styled spans
  return answer.replace(/\[(\d+)\]/g, '<span class="badge badge-primary ml-1">[$1]</span>')
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold text-text-primary">Query GraphRAG</h1>
      <p class="text-text-secondary mt-1">Ask questions and get grounded answers with citations</p>
    </div>

    <!-- Query Input -->
    <div class="card">
      <div class="space-y-4">
        <div class="relative">
          <textarea
            v-model="query"
            @keydown.ctrl.enter="submitQuery"
            @keydown.meta.enter="submitQuery"
            placeholder="Enter your question... (Ctrl+Enter to submit)"
            class="input min-h-[120px] resize-y font-mono text-sm"
            rows="5"
            :disabled="isLoading"
            aria-label="Query input"
          />
          <div class="absolute bottom-3 right-3 text-text-muted text-xs">
            Ctrl+Enter to submit
          </div>
        </div>

        <!-- Advanced Options -->
        <button
          @click="showAdvanced = !showAdvanced"
          class="btn-ghost text-sm flex items-center gap-2"
        >
          <span>Advanced Options</span>
          <ChevronDown v-if="!showAdvanced" class="w-4 h-4" />
          <ChevronUp v-if="showAdvanced" class="w-4 h-4" />
        </button>

        <div v-if="showAdvanced" class="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2 border-t border-border-primary">
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Top K</label>
            <input type="number" v-model.number="topK" min="1" max="50" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">Graph Depth</label>
            <input type="number" v-model.number="depth" min="1" max="5" class="input" />
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="includeGraph" class="rounded border-border-primary text-accent-primary focus:ring-accent-primary" />
              <span class="text-sm text-text-secondary">Include Graph Traversal</span>
            </label>
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="retrievalOnly" class="rounded border-border-primary text-accent-primary focus:ring-accent-primary" />
              <span class="text-sm text-text-secondary">Retrieval Only</span>
            </label>
          </div>
        </div>

        <button
          @click="submitQuery"
          :disabled="isLoading || !query.trim()"
          class="btn-primary w-full sm:w-auto px-6 py-3 text-base flex items-center gap-2"
        >
          <Loader2 v-if="isLoading" class="w-5 h-5 animate-spin" />
          <Send v-else class="w-5 h-5" />
          <span>{{ isLoading ? 'Querying...' : 'Submit Query' }}</span>
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="card border-accent-danger/50 bg-accent-danger/5">
      <div class="flex items-center gap-3">
        <AlertCircle class="w-5 h-5 text-accent-danger flex-shrink-0" />
        <p class="text-text-primary">{{ error }}</p>
      </div>
    </div>

    <!-- Response -->
    <div v-if="hasResponse" class="space-y-6 animate-in">
      <!-- Answer -->
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-text-primary flex items-center gap-2">
                  <Lightbulb class="w-5 h-5 text-accent-warning" />
                  Answer
                </h2>
                <div class="flex items-center gap-2 text-sm text-text-muted">
                  <span class="badge badge-primary">
                    {{ responseData.retrieval_metadata?.grounding_score?.toFixed(2) ?? '0.00' }} Grounding
                  </span>
                  <span class="badge badge-secondary">
                    {{ responseData.retrieval_metadata?.latency_ms ?? 0 }}ms
                  </span>
                </div>
              </div>
       
              <div class="prose prose-invert max-w-none text-text-primary">
                <div v-html="formatAnswer(responseData.answer)" />
              </div>
        
              <!-- Metadata -->
              <div class="mt-4 pt-4 border-t border-border-primary grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <p class="text-text-muted">Vector Results</p>
                  <p class="font-medium text-text-primary">{{ responseData.retrieval_metadata?.vector_results ?? 0 }}</p>
                </div>
                <div>
                  <p class="text-text-muted">Chunk Results</p>
                  <p class="font-medium text-text-primary">{{ responseData.retrieval_metadata?.chunk_results ?? 0 }}</p>
                </div>
                <div>
                  <p class="text-text-muted">Graph Paths</p>
                  <p class="font-medium text-text-primary">{{ responseData.retrieval_metadata?.graph_paths ?? 0 }}</p>
                </div>
                <div>
                  <p class="text-text-muted">Valid Citations</p>
                  <p class="font-medium text-text-primary">{{ responseData.retrieval_metadata?.valid_citations ?? 0 }}/{{ responseData.retrieval_metadata?.total_citations ?? 0 }}</p>
                </div>
              </div>
            </div>

      <!-- Sources -->
      <div v-if="responseData.sources.length > 0" class="card">
        <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <FileText class="w-5 h-5 text-accent-primary" />
          Sources ({{ responseData.sources.length }})
        </h2>
        <div class="space-y-3">
          <div
            v-for="source in responseData.sources"
            :key="source.paper_id"
            class="border border-border-primary rounded-lg p-4 hover:border-border-hover transition-colors"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-text-primary">{{ source.title }}</h3>
                <p class="text-sm text-text-muted flex items-center gap-2 mt-1">
                  <span>{{ source.year }}</span>
                  <span>•</span>
                  <span>{{ (source.authors ?? []).slice(0, 3).join(', ') }}{{ (source.authors ?? []).length > 3 ? ' et al.' : '' }}</span>
                  <span>•</span>
                  <span :class="getScoreColor(source.relevance_score ?? 0)">
                    Relevance: {{ formatScore(source.relevance_score ?? 0) }}
                  </span>
                </p>
                <p v-if="source.citation_text" class="mt-2 text-sm text-text-secondary italic">
                  "{{ source.citation_text }}"
                </p>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <router-link
                  :to="`/papers/${source.paper_id}`"
                  class="btn-ghost text-sm px-3 py-1"
                >
                  View Paper
                </router-link>
                <button
                  @click="copyToClipboard(source.citation_text || source.title, source.paper_id)"
                  class="btn-ghost p-2"
                  :title="copiedSource === source.paper_id ? 'Copied!' : 'Copy citation'"
                >
                  <Check v-if="copiedSource === source.paper_id" class="w-4 h-4 text-accent-success" />
                  <Copy v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Graph Paths -->
      <div v-if="responseData.graph_path.length > 0" class="card">
        <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <GitBranch class="w-5 h-5 text-accent-secondary" />
          Graph Paths ({{ responseData.graph_path.length }})
        </h2>
        <div class="space-y-2">
          <div
            v-for="(path, index) in responseData.graph_path"
            :key="index"
            class="bg-bg-tertiary rounded-lg p-4 font-mono text-sm"
          >
            <div class="flex items-center gap-2 flex-wrap text-text-secondary">
              <span class="text-text-primary">{{ path.source }}</span>
              <span class="text-accent-secondary px-2">→ {{ path.relation }} →</span>
              <span class="text-text-primary">{{ path.target }}</span>
              <span class="text-text-muted ml-2 text-xs">
                ({{ path.source_type }} → {{ path.target_type }})
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Extracted Entities -->
      <div v-if="Object.keys(responseData.extracted_entities).length > 0" class="card">
        <h2 class="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <Database class="w-5 h-5 text-accent-success" />
          Extracted Entities
        </h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="(entities, type) in responseData.extracted_entities"
            :key="type"
            class="badge badge-primary"
          >
            {{ type }}: {{ (entities as string[]).join(', ') }}
          </span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isLoading" class="card text-center py-12">
      <Info class="w-16 h-16 text-text-muted mx-auto mb-4" />
      <h3 class="text-lg font-medium text-text-primary mb-2">Ready to Query</h3>
      <p class="text-text-secondary">Enter a question above to search the knowledge graph and get grounded answers with citations.</p>
    </div>
  </div>
</template>
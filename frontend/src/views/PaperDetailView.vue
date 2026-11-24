<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { api, type Paper, type CitationEdge } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import { useRoute, useRouter } from 'vue-router'
import {
  Loader2,
  ArrowLeft,
  ArrowUpRight,
  ArrowDownLeft,
  FileText,
  Calendar,
  Hash,
  ExternalLink,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-vue-next'

const uiStore = useUIStore()
const route = useRoute()
const router = useRouter()

const paper = ref<Paper | null>(null)
const chunks = ref<Array<{ id: string; text: string; chunk_index: number; token_count: number }>>([])
const citations = ref<{ outgoing: CitationEdge[]; incoming: CitationEdge[] }>({ outgoing: [], incoming: [] })
const loading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'overview' | 'chunks' | 'citations'>('overview')
const showAbstract = ref(false)
const copiedChunk = ref<string | null>(null)

const props = defineProps<{ id: string }>()
const paperId = computed(() => props.id)

async function fetchPaper() {
  loading.value = true
  error.value = null
  try {
    const [paperData, chunksData, citationsData] = await Promise.all([
      api.getPaper(paperId.value),
      api.getPaperChunks(paperId.value),
      api.getCitations(paperId.value),
    ])
    paper.value = paperData
    chunks.value = chunksData.chunks
    citations.value = {
      outgoing: citationsData.outgoing,
      incoming: citationsData.incoming,
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load paper'
    uiStore.notify('error', error.value)
  } finally {
    loading.value = false
  }
}

function copyChunk(text: string, chunkId: string) {
  navigator.clipboard.writeText(text)
  copiedChunk.value = chunkId
  setTimeout(() => copiedChunk.value = null, 2000)
  uiStore.notify('success', 'Chunk copied to clipboard')
}

function formatAuthors(authors: string[]) {
  return authors.join(', ')
}

onMounted(() => {
  fetchPaper()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <button @click="router.push('/papers')" class="btn-ghost p-2">
        <ArrowLeft class="w-5 h-5" />
      </button>
      <div class="flex-1 min-w-0">
        <span class="badge badge-primary mb-2">Paper Detail</span>
        <h1 v-if="paper" class="text-2xl font-bold text-text-primary truncate">{{ paper.title }}</h1>
        <h1 v-else class="text-2xl font-bold text-text-primary animate-pulse">Loading...</h1>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="card border-accent-danger/50 bg-accent-danger/5">
      <div class="flex items-center gap-3">
        <Loader2 class="w-5 h-5 text-accent-danger" />
        <p class="text-text-primary">{{ error }}</p>
        <button @click="fetchPaper" class="ml-auto btn-secondary text-sm">Retry</button>
      </div>
    </div>

    <!-- Paper Content -->
    <div v-if="paper" class="space-y-6">
      <!-- Metadata Card -->
      <div class="card">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <p class="text-sm font-medium text-text-muted">Paper ID</p>
            <p class="font-mono text-sm text-text-primary break-all">{{ paper.id }}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-text-muted">Year</p>
            <p class="font-medium text-text-primary">{{ paper.year }}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-text-muted">Chunks</p>
            <p class="font-medium text-text-primary">{{ paper.chunk_count }}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-text-muted">DOI</p>
            <p v-if="paper.doi" class="font-mono text-sm text-text-primary">
              <a :href="`https://doi.org/${paper.doi}`" target="_blank" rel="noopener" class="flex items-center gap-1 hover:text-accent-primary">
                {{ paper.doi }}
                <ExternalLink class="w-3 h-3" />
              </a>
            </p>
            <p v-else class="text-text-muted">—</p>
          </div>
        </div>

        <div class="mt-6 pt-6 border-t border-border-primary">
          <p class="text-sm font-medium text-text-muted mb-2">Authors</p>
          <p class="text-text-primary">{{ formatAuthors(paper.authors) }}</p>
        </div>

        <div class="mt-6 pt-6 border-t border-border-primary">
          <div class="flex items-center justify-between mb-2">
            <p class="text-sm font-medium text-text-muted">Abstract</p>
            <button @click="showAbstract = !showAbstract" class="btn-ghost text-sm">
              {{ showAbstract ? 'Show less' : 'Show more' }}
              <ChevronUp v-if="showAbstract" class="w-4 h-4" />
              <ChevronDown v-if="!showAbstract" class="w-4 h-4" />
            </button>
          </div>
          <div class="prose prose-invert max-w-none text-text-secondary" :class="{ 'line-clamp-3': !showAbstract }">
            {{ paper.abstract || 'No abstract available.' }}
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="card overflow-hidden">
        <div class="border-b border-border-primary">
          <nav class="flex gap-1 p-1" aria-label="Paper sections">
            <button
              @click="activeTab = 'overview'"
              :class="[
                'flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors',
                activeTab === 'overview' ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-primary'
              ]"
            >
              Overview
            </button>
            <button
              @click="activeTab = 'chunks'"
              :class="[
                'flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors',
                activeTab === 'chunks' ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-primary'
              ]"
            >
              Chunks ({{ chunks.length }})
            </button>
            <button
              @click="activeTab = 'citations'"
              :class="[
                'flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors',
                activeTab === 'citations' ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-primary'
              ]"
            >
              Citations ({{ citations.length }})
            </button>
          </nav>
        </div>

        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 class="font-medium text-text-primary mb-3">Quick Actions</h3>
              <div class="space-y-2">
                <router-link to="/query" class="btn-secondary w-full justify-start gap-3">
                  <FileText class="w-5 h-5" />
                  Query about this paper
                </router-link>
                <router-link :to="`/graph`" class="btn-secondary w-full justify-start gap-3">
                  <Hash class="w-5 h-5" />
                  Explore in Knowledge Graph
                </router-link>
              </div>
            </div>
            <div>
              <h3 class="font-medium text-text-primary mb-3">Statistics</h3>
              <dl class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <dt class="text-text-muted">Total Chunks</dt>
                  <dd class="font-medium text-text-primary">{{ paper.chunk_count }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-text-muted">Citations (outgoing)</dt>
                  <dd class="font-medium text-text-primary">{{ citations.length }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-text-muted">Authors</dt>
                  <dd class="font-medium text-text-primary">{{ paper.authors.length }}</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        <!-- Chunks Tab -->
        <div v-if="activeTab === 'chunks'" class="p-6">
          <div v-if="loading" class="text-center py-8">
            <Loader2 class="w-8 h-8 animate-spin text-accent-primary mx-auto mb-3" />
            <p class="text-text-secondary">Loading chunks...</p>
          </div>
          
          <div v-else-if="chunks.length === 0" class="text-center py-8">
            <FileText class="w-16 h-16 text-text-muted mx-auto mb-4" />
            <p class="text-text-secondary">No chunks available</p>
          </div>
          
          <div v-else class="space-y-3 max-h-[600px] overflow-y-auto">
            <div
              v-for="chunk in chunks"
              :key="chunk.id"
              class="border border-border-primary rounded-lg p-4 hover:border-border-hover transition-colors"
            >
              <div class="flex items-start justify-between gap-4 mb-2">
                <div class="flex items-center gap-2 text-sm text-text-muted">
                  <span class="font-mono">#{{ chunk.chunk_index }}</span>
                  <span>•</span>
                  <span>{{ chunk.token_count }} tokens</span>
                </div>
                <button
                  @click="copyChunk(chunk.text, chunk.id)"
                  class="btn-ghost p-1.5"
                  :title="copiedChunk === chunk.id ? 'Copied!' : 'Copy chunk'"
                >
                  <Check v-if="copiedChunk === chunk.id" class="w-4 h-4 text-accent-success" />
                  <Copy v-else class="w-4 h-4" />
                </button>
              </div>
              <pre class="code-block text-text-secondary whitespace-pre-wrap">{{ chunk.text }}</pre>
            </div>
          </div>
        </div>

        <!-- Citations Tab -->
                <div v-if="activeTab === 'citations'" class="p-6">
                  <div v-if="citations.outgoing.length === 0 && citations.incoming.length === 0" class="text-center py-8">
                    <Hash class="w-16 h-16 text-text-muted mx-auto mb-4" />
                    <h3 class="text-lg font-medium text-text-primary mb-2">No citations found</h3>
                    <p class="text-text-secondary">This paper doesn't cite or isn't cited by other papers in the corpus.</p>
                  </div>

                  <div v-else class="space-y-6">
                    <!-- Outgoing Citations (papers this paper cites) -->
                    <div v-if="citations.outgoing.length > 0">
                      <h4 class="font-medium text-text-primary mb-3 flex items-center gap-2">
                        <ArrowUpRight class="w-4 h-4 text-accent-primary" />
                        Cites ({{ citations.outgoing.length }})
                      </h4>
                      <div class="space-y-3">
                        <div
                          v-for="citation in citations.outgoing"
                          :key="citation.paper_id"
                          class="border border-border-primary rounded-lg p-4 hover:border-border-hover transition-colors"
                        >
                          <div class="flex items-start gap-4">
                            <div class="w-10 h-10 rounded-lg bg-accent-primary/10 flex items-center justify-center flex-shrink-0">
                              <FileText class="w-5 h-5 text-accent-primary" />
                            </div>
                            <div class="flex-1 min-w-0">
                              <h4 class="font-medium text-text-primary">{{ citation.title }}</h4>
                              <p class="text-sm text-text-muted mt-1">
                                {{ citation.year }} • {{ citation.venue || 'Unknown venue' }}
                              </p>
                            </div>
                            <router-link
                              :to="`/papers/${citation.paper_id}`"
                              class="btn-ghost text-sm flex-shrink-0"
                            >
                              View Paper
                            </router-link>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Incoming Citations (papers that cite this paper) -->
                    <div v-if="citations.incoming.length > 0">
                      <h4 class="font-medium text-text-primary mb-3 flex items-center gap-2">
                        <ArrowDownLeft class="w-4 h-4 text-accent-secondary" />
                        Cited by ({{ citations.incoming.length }})
                      </h4>
                      <div class="space-y-3">
                        <div
                          v-for="citation in citations.incoming"
                          :key="citation.paper_id"
                          class="border border-border-primary rounded-lg p-4 hover:border-border-hover transition-colors"
                        >
                          <div class="flex items-start gap-4">
                            <div class="w-10 h-10 rounded-lg bg-accent-secondary/10 flex items-center justify-center flex-shrink-0">
                              <FileText class="w-5 h-5 text-accent-secondary" />
                            </div>
                            <div class="flex-1 min-w-0">
                              <h4 class="font-medium text-text-primary">{{ citation.title }}</h4>
                              <p class="text-sm text-text-muted mt-1">
                                {{ citation.year }} • {{ citation.venue || 'Unknown venue' }}
                              </p>
                            </div>
                            <router-link
                              :to="`/papers/${citation.paper_id}`"
                              class="btn-ghost text-sm flex-shrink-0"
                            >
                              View Paper
                            </router-link>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
      </div>
    </div>
  </div>
</template>
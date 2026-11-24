const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

// ---------------- Types ----------------

export interface QueryRequest {
  query: string
  top_k?: number
  depth?: number
  include_graph?: boolean
  retrieval_only?: boolean
}

export interface SourceCitation {
  paper_id: string
  title: string
  year: number | null
  authors?: string[]
  relevance_score?: number | null
  citation_text?: string | null
}

export interface GraphPathElement {
  source: string
  relation: string
  target: string
  source_type: string
  target_type: string
}

export interface RetrievalMetadata {
  vector_results: number
  chunk_results: number
  graph_paths: number
  seed_papers: string[]
  grounding_score: number
  valid_citations: number
  total_citations: number
  latency_ms: number
}

export interface QueryResponse {
  answer: string
  sources: SourceCitation[]
  graph_path: GraphPathElement[]
  extracted_entities: Record<string, unknown>
  metadata: Record<string, unknown>
  retrieval_metadata?: RetrievalMetadata
}

export interface Paper {
  id: string
  title: string
  abstract: string | null
  year: number | null
  doi: string | null
  venue: string | null
  keywords: string[]
  authors?: string[]
  chunk_count?: number
  citation_count?: number
  citing_count?: number
}

export type Source = SourceCitation

export interface PaperDetail extends Paper {
  authors?: string[]
  concepts?: string[]
  methods?: string[]
  datasets?: string[]
}

export interface ChunkItem {
  id: string
  paper_id: string
  text: string
  chunk_index: number
  token_count?: number
}

export interface ChunksResponse {
  chunks: ChunkItem[]
  total: number
  limit: number
  offset: number
}

export interface CitationEdge {
  paper_id: string
  title: string
  year: number | null
  venue: string | null
  doi: string | null
  context?: string
}

export interface CitationsResponse {
  outgoing: CitationEdge[]
  incoming: CitationEdge[]
}

export interface EntityItem {
  id: string
  name: string
  type: string
  paper_count: number
  extra?: string
}

export interface EntitiesResponse {
  entities: EntityItem[]
  total: number
  limit: number
  offset: number
}

export interface GraphStats {
  papers: number
  authors: number
  concepts: number
  methods: number
  datasets: number
  chunks: number
  citations: number
  relations: number
}

export interface GraphNode {
  id: string
  label: string
  type: string
  paper_count?: number
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
}

export interface GraphVisualization {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface PapersResponse {
  papers: Paper[]
  total: number
  limit: number
  offset: number
}

export interface SuggestionsResponse {
  suggestions: string[]
}

export interface HealthStatus {
  status: string
  neo4j: string
  version: string
}

// ---------------- Fetch Helper ----------------

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// ---------------- API Methods ----------------

export const api = {
  // Health
  health: () => fetchApi<HealthStatus>('/graph/health'),

  // Query
  query: (request: QueryRequest) =>
    fetchApi<QueryResponse>('/query/', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  querySuggestions: (partial = '', limit = 6) =>
    fetchApi<SuggestionsResponse>(`/query/suggestions?partial=${encodeURIComponent(partial)}&limit=${limit}`),

  // Papers (catalog endpoints)
  getPapers: (params?: { q?: string; year?: number; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.q) searchParams.set('q', params.q)
    if (params?.year) searchParams.set('year', params.year.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    const qs = searchParams.toString()
    return fetchApi<PapersResponse>(`/papers${qs ? `?${qs}` : ''}`)
  },

  // Alias for compatibility
  listPapers: (params?: { q?: string; year?: number; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.q) searchParams.set('q', params.q)
    if (params?.year) searchParams.set('year', params.year.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    const qs = searchParams.toString()
    return fetchApi<PapersResponse>(`/papers${qs ? `?${qs}` : ''}`)
  },

  getPaper: (id: string) =>
    fetchApi<PaperDetail>(`/papers/${encodeURIComponent(id)}`),

  getPaperChunks: (id: string, limit = 100, offset = 0) =>
    fetchApi<ChunksResponse>(`/papers/${encodeURIComponent(id)}/chunks?limit=${limit}&offset=${offset}`),

  getCitations: (paperId: string, direction = 'both') =>
    fetchApi<CitationsResponse>(`/papers/${encodeURIComponent(paperId)}/citations?direction=${direction}`),

  // Graph stats
  getGraphStats: () => fetchApi<GraphStats>('/graph/stats'),

  // Graph visualization
  getGraphVisualization: (paperId: string, depth = 2, maxNodes = 150) =>
    fetchApi<GraphVisualization>(
      `/graph/visualize?paper_id=${encodeURIComponent(paperId)}&depth=${depth}&max_nodes=${maxNodes}`
    ),

  // Entities
  listEntities: (params?: { q?: string; type?: string; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.q) searchParams.set('q', params.q)
    if (params?.type) searchParams.set('type', params.type)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const qs = searchParams.toString()
    return fetchApi<EntitiesResponse>(`/entities${qs ? `?${qs}` : ''}`)
  },
}


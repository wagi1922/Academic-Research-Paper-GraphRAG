// Type declarations for cytoscape extensions
declare module 'cytoscape-cose-bilkent' {
  import cytoscape from 'cytoscape'
  const coseBilkent: (cytoscape: typeof cytoscape) => void
  export default coseBilkent
}

declare module 'cytoscape-fcose' {
  import cytoscape from 'cytoscape'
  const fcose: (cytoscape: typeof cytoscape) => void
  export default fcose
}
<template>
  <div class="chat-graph">
    <div class="graph-controls">
      <button @click="resetZoom" class="control-button">
        <span>⟲</span>
      </button>
      <button @click="fitGraph" class="control-button">
        <span>⊡</span>
      </button>
      <button @click="refreshGraph" class="control-button">
        <span>↻</span>
      </button>
    </div>

    <div ref="graphContainer" class="graph-container"></div>

    <!-- Info panel -->
    <div v-if="selectedNode" class="info-panel">
      <div class="info-header">
        <h4>{{ selectedNode.data.label }}</h4>
        <button @click="selectedNode = null" class="close-button">×</button>
      </div>
      <div class="info-content">
        <p><strong>ID:</strong> {{ selectedNode.data.id }}</p>
        <p><strong>Тип:</strong> {{ getNodeTypeLabel(selectedNode.data.type) }}</p>
        <p v-if="selectedNode.data.messageCount">
          <strong>Сообщений:</strong> {{ selectedNode.data.messageCount }}
        </p>
        <p v-if="selectedNode.data.createdAt">
          <strong>Создан:</strong> {{ formatDate(selectedNode.data.createdAt) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import cytoscape, { type Core } from 'cytoscape'

interface ChatNode {
  id: string
  label: string
  type: 'chat' | 'user' | 'topic'
  messageCount?: number
  createdAt?: string
}

interface ChatEdge {
  source: string
  target: string
  type: 'replied' | 'mentioned' | 'related'
}

const graphContainer = ref<HTMLElement | null>(null)
const selectedNode = ref<{ data: ChatNode } | null>(null)
let cy: Core | null = null

// Mock data
const mockNodes: ChatNode[] = [
  { id: '1', label: 'Общий чат', type: 'chat', messageCount: 150, createdAt: '2025-01-01' },
  { id: '2', label: 'Проект А', type: 'chat', messageCount: 89, createdAt: '2025-01-05' },
  { id: '3', label: 'Вопросы', type: 'chat', messageCount: 45, createdAt: '2025-01-10' },
  { id: '4', label: 'Разработка', type: 'topic', messageCount: 120 },
  { id: '5', label: 'Дизайн', type: 'topic', messageCount: 67 },
  { id: '6', label: 'Тестирование', type: 'topic', messageCount: 34 },
  { id: '7', label: 'Пользователь 1', type: 'user' },
  { id: '8', label: 'Пользователь 2', type: 'user' },
  { id: '9', label: 'Архитектура', type: 'topic', messageCount: 52 },
  { id: '10', label: 'UI/UX', type: 'topic', messageCount: 38 },
]

const mockEdges: ChatEdge[] = [
  { source: '1', target: '2', type: 'related' },
  { source: '1', target: '4', type: 'mentioned' },
  { source: '2', target: '4', type: 'mentioned' },
  { source: '2', target: '5', type: 'mentioned' },
  { source: '3', target: '6', type: 'mentioned' },
  { source: '4', target: '5', type: 'related' },
  { source: '4', target: '9', type: 'related' },
  { source: '5', target: '10', type: 'related' },
  { source: '7', target: '1', type: 'replied' },
  { source: '7', target: '2', type: 'replied' },
  { source: '8', target: '1', type: 'replied' },
  { source: '8', target: '3', type: 'replied' },
  { source: '9', target: '2', type: 'mentioned' },
  { source: '10', target: '5', type: 'mentioned' },
]

onMounted(() => {
  initGraph()
})

onBeforeUnmount(() => {
  if (cy) {
    cy.destroy()
  }
})

function initGraph() {
  if (!graphContainer.value) return

  const elements = {
    nodes: mockNodes.map((node) => ({
      data: { ...node, id: node.id },
    })),
    edges: mockEdges.map((edge, idx) => ({
      data: { ...edge, id: `edge-${idx}` },
    })),
  }

  cy = cytoscape({
    container: graphContainer.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#6366f1',
          label: 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '11px',
          color: '#e0e0e0',
          'text-outline-color': '#1a1a2e',
          'text-outline-width': 1,
          width: 60,
          height: 60,
          'border-width': 2,
          'border-color': '#8b8bf1',
          'border-opacity': 0.5,
        },
      },
      {
        selector: 'node[type="chat"]',
        style: {
          'background-color': '#8b5cf6',
          'border-color': '#a78bfa',
          width: 70,
          height: 70,
          'font-size': '12px',
        },
      },
      {
        selector: 'node[type="topic"]',
        style: {
          'background-color': '#3b82f6',
          'border-color': '#60a5fa',
          width: 55,
          height: 55,
        },
      },
      {
        selector: 'node[type="user"]',
        style: {
          'background-color': '#f59e0b',
          'border-color': '#fbbf24',
          shape: 'hexagon',
          width: 50,
          height: 50,
        },
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 3,
          'border-color': '#fbbf24',
          'border-opacity': 1,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#444466',
          'target-arrow-color': '#444466',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          opacity: 0.6,
        },
      },
      {
        selector: 'edge[type="replied"]',
        style: {
          'line-color': '#8b5cf6',
          'target-arrow-color': '#8b5cf6',
          width: 2,
          opacity: 0.7,
        },
      },
      {
        selector: 'edge[type="mentioned"]',
        style: {
          'line-color': '#3b82f6',
          'target-arrow-color': '#3b82f6',
          'line-style': 'dashed',
          opacity: 0.5,
        },
      },
      {
        selector: 'edge[type="related"]',
        style: {
          'line-color': '#6366f1',
          'target-arrow-color': '#6366f1',
          width: 1.5,
          opacity: 0.6,
        },
      },
    ],
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 1000,
      animationEasing: 'ease-out',
      nodeRepulsion: 12000,
      idealEdgeLength: 120,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 60,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0,
      randomize: false,
    },
    minZoom: 0.3,
    maxZoom: 2.5,
    wheelSensitivity: 0.2,
  })

  // Handle node click
  cy.on('tap', 'node', (event) => {
    const node = event.target
    selectedNode.value = {
      data: node.data() as ChatNode,
    }
  })

  // Handle background click
  cy.on('tap', (event) => {
    if (event.target === cy) {
      selectedNode.value = null
    }
  })

  // Handle node hover
  cy.on('mouseover', 'node', (event) => {
    const node = event.target
    document.body.style.cursor = 'pointer'

    // Highlight connected edges
    const connectedEdges = node.connectedEdges()
    connectedEdges.style('opacity', 1)
    connectedEdges.style('width', 3)
  })

  cy.on('mouseout', 'node', () => {
    document.body.style.cursor = 'default'

    // Reset edges
    cy?.edges().style('opacity', 0.6)
    cy?.edges('[type="replied"]').style('width', 2)
    cy?.edges('[type="mentioned"]').style('width', 1.5)
    cy?.edges('[type="related"]').style('width', 1.5)
  })
}

async function refreshGraph() {
  if (!cy) return

  try {
    // TODO: Fetch data from backend
    // const response = await apiService.getChatGraph()
    // const data = await response.data

    // Re-layout with animation
    cy.layout({
      name: 'cose',
      animate: true,
      animationDuration: 1000,
      nodeRepulsion: 12000,
      idealEdgeLength: 120,
    }).run()
  } catch (error) {
    console.error('Error refreshing graph:', error)
  }
}

function resetZoom() {
  if (cy) {
    cy.zoom(1)
    cy.center()
  }
}

function fitGraph() {
  if (cy) {
    cy.fit(undefined, 50)
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU')
}

function getNodeTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    chat: 'Чат',
    topic: 'Тема',
    user: 'Пользователь',
  }
  return labels[type] || type
}
</script>

<style scoped>
.chat-graph {
  position: relative;
  width: 100%;
  height: 600px;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.3);
}

.graph-controls {
  position: absolute;
  top: 15px;
  right: 15px;
  z-index: 10;
  display: flex;
  gap: 8px;
}

.control-button {
  width: 36px;
  height: 36px;
  padding: 0;
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  color: #a0a0a0;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-button:hover {
  background: rgba(50, 50, 80, 0.9);
  border-color: rgba(255, 255, 255, 0.2);
  color: #e0e0e0;
  transform: translateY(-1px);
}

.control-button span {
  line-height: 1;
}

.graph-container {
  width: 100%;
  height: 100%;
}

.info-panel {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(30, 30, 50, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 15px;
  min-width: 250px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
  z-index: 10;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.info-header h4 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1rem;
  font-weight: 500;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  line-height: 1;
}

.close-button:hover {
  color: #e0e0e0;
}

.info-content p {
  margin: 8px 0;
  font-size: 13px;
  color: #b0b0b0;
}

.info-content strong {
  color: #e0e0e0;
}
</style>

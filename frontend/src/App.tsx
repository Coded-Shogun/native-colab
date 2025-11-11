import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Header */}
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight">
              Welcome to <span className="text-primary">Native Colab</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Unified Collaboration Platform
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
            <FeatureCard
              icon="💬"
              title="Team Chat"
              description="Real-time messaging with channels and direct messages"
            />
            <FeatureCard
              icon="📋"
              title="Projects"
              description="Kanban boards, tasks, and workflow management"
            />
            <FeatureCard
              icon="📄"
              title="Documents"
              description="Collaborative editing with version control"
            />
            <FeatureCard
              icon="✍️"
              title="Signatures"
              description="Digital document signing workflows"
            />
            <FeatureCard
              icon="⏱️"
              title="Time Tracking"
              description="Track time, generate timesheets and reports"
            />
            <FeatureCard
              icon="🎨"
              title="Whiteboard"
              description="Collaborative drawing and brainstorming"
            />
          </div>

          {/* Status */}
          <div className="mt-12 p-6 border border-border rounded-lg bg-card">
            <p className="text-sm text-muted-foreground mb-2">
              Application Status
            </p>
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-lg font-medium">System Ready</span>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Backend API: <code className="text-primary">http://localhost:8000</code>
            </p>
            <p className="text-sm text-muted-foreground">
              API Docs: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">http://localhost:8000/docs</a>
            </p>
          </div>

          {/* Counter Demo */}
          <div className="mt-8 p-6 border border-border rounded-lg bg-card">
            <h3 className="text-lg font-semibold mb-4">Interactive Demo</h3>
            <button
              onClick={() => setCount((count) => count + 1)}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
            >
              Count is {count}
            </button>
          </div>

          {/* Footer */}
          <div className="mt-12 text-sm text-muted-foreground">
            <p>Built with React + Vite + TypeScript + Tailwind CSS + shadcn/ui</p>
            <p className="mt-2">Backend: FastAPI + PostgreSQL + Redis + Socket.io</p>
          </div>
        </div>
      </div>
    </div>
  )
}

interface FeatureCardProps {
  icon: string
  title: string
  description: string
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="p-6 border border-border rounded-lg bg-card hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

export default App

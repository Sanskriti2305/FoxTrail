import { useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft,
  ArrowUpRight,
  Check,
  ChevronRight,
  Circle,
  CircleDot,
  Database,
  FileText,
  GitBranch,
  Loader2,
  Search,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import CaseList from './CaseList'
import CaseDetail from './CaseDetail'

export type Action = {
  action: string
  route?: string
  reason?: string
}

export type CaseRow = {
  case_id: string
  customer_id: string
  verdict: string
  status: string
  pattern: string
  exposure_usd: number
  fraud_probability: number
  sar: boolean
  written_to_graph: boolean
  trigger_type: string
  summary: string
  final_actions?: Action[]
  initial_actions?: Action[]
  opened_at: string
  flagged_txn_id: string
  what_changed?: string
  next_best_actions?: {
  initial?: {
    action: string
    reason?: string
    route?: string
  }[]
  final?: {
    action: string
    reason?: string
    route?: string
  }[]
  what_changed?: string
}
}

export type Overview = {
  metrics: {
    total_cases: number
    fraud_cases: number
    legitimate_cases: number
    uncertain_cases: number
    fraud_exposure_usd: number
    reported_exposure_usd: number
    sar_cases: number
    graph_written: number
  }
  cases: CaseRow[]
}

export type Page = 'overview' | 'cases' | 'detail' | 'evidence' | 'memory'

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

async function loadOverview(): Promise<Overview> {
  const base =
    (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || ''

  const candidates = [
    base ? `${base}/api/overview` : '/api/overview',
    '/demo-overview.json',
  ]

  let lastError: unknown

  for (const url of candidates) {
    try {
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`)
      }

      const result = (await response.json()) as Overview

      if (result?.cases && result?.metrics) {
        const normalizedCases = result.cases.map((item) => ({
          ...item,

          // Preserve existing fields if they already exist.
          // Otherwise read them from next_best_actions.
          initial_actions:
            item.initial_actions ??
            item.next_best_actions?.initial ??
            [],

          final_actions:
            item.final_actions ??
            item.next_best_actions?.final ??
            [],

          what_changed:
            item.what_changed ??
            item.next_best_actions?.what_changed ??
            undefined,
        }))

        return {
          ...result,
          cases: normalizedCases,
        }
      }
    } catch (error) {
      lastError = error
    }
  }

  throw lastError ?? new Error('Unable to load investigation data.')
}

function formatLabel(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function Header({
  page,
  setPage,
}: {
  page: Page
  setPage: (page: Page) => void
}) {
  return (
    <header className="topbar">
      <button className="brand" onClick={() => setPage('overview')} aria-label="Foxtrail home">
        <img src="/assets/fox-logo.png" alt="Foxtrail fox emblem" className="brand-logo" />
        <span>FOXTRAIL</span>
      </button>

      <nav aria-label="Primary navigation">
        <button className={page === 'overview' ? 'active' : ''} onClick={() => setPage('overview')}>
          Overview
        </button>
        <button
          className={page === 'cases' || page === 'detail' ? 'active' : ''}
          onClick={() => setPage('cases')}
        >
          Investigations
        </button>
        <button className={page === 'evidence' ? 'active' : ''} onClick={() => setPage('evidence')}>
          Evidence
        </button>
        <button className={page === 'memory' ? 'active' : ''} onClick={() => setPage('memory')}>
          Memory
        </button>
      </nav>

      <div className="system">
        <span className="live-dot" />
        <span>Agent online</span>
        <span className="divider" />
        <span>TG Savanna</span>
      </div>
    </header>
  )
}

function Footer() {
  return (
    <footer className="site-footer">
      <span>FOXTRAIL / AGENTIC FRAUD INVESTIGATION</span>
      <span className="footer-stack">
        <Database size={13} />
        TigerGraph Savanna · GraphRAG · LangGraph
      </span>
    </footer>
  )
}

function Stat({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      <span className="stat-detail">{detail}</span>
    </div>
  )
}

function OverviewPage({
  data,
  query,
  setQuery,
  setPage,
}: {
  data: Overview
  query: string
  setQuery: (value: string) => void
  setPage: (page: Page) => void
}) {
  const metrics = data.metrics
  const total = Math.max(metrics.total_cases, 1)

  const recent = useMemo(() => {
    const q = query.trim().toLowerCase()
    return data.cases
      .filter((item) => {
        if (!q) return true
        return [
          item.case_id,
          item.customer_id,
          item.flagged_txn_id,
          item.pattern,
          item.trigger_type,
          item.status,
        ]
          .join(' ')
          .toLowerCase()
          .includes(q)
      })
      .slice(0, 6)
  }, [data.cases, query])

  return (
    <div className="app-shell">
      <Header page="overview" setPage={setPage} />

      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <CircleDot size={12} />
              FRAUD INVESTIGATION CONSOLE
            </div>

            <h1>
              Find the signal.
              <br />
              <em>Follow the evidence.</em>
            </h1>

            <p className="hero-sub">
              An agentic investigation workspace for turning uncertain transaction alerts into
              defensible decisions.
            </p>

            <div className="hero-actions">
              <button className="primary" onClick={() => setPage('cases')}>
                View investigations
                <ArrowUpRight size={16} />
              </button>
              <span className="benchmark">20 benchmark cases · graph-backed investigation</span>
            </div>
          </div>

          <div className="hero-art">
            <img src="/assets/money-glitch.png" alt="Abstract money signal artwork" />
            <div className="art-caption">SIGNAL / EVIDENCE / ACTION</div>
          </div>
        </section>

        <section className="stats-grid">
          <Stat label="Investigated" value={String(metrics.total_cases)} detail="cases processed" />
          <Stat
            label="Confirmed fraud"
            value={String(metrics.fraud_cases).padStart(2, '0')}
            detail={`${Math.round((metrics.fraud_cases / total) * 100)}% of investigations`}
          />
          <Stat
            label="Cleared"
            value={String(metrics.legitimate_cases).padStart(2, '0')}
            detail="closed as legitimate"
          />
          <Stat
            label="Fraud exposure"
            value={money.format(metrics.fraud_exposure_usd)}
            detail="identified exposure"
          />
          <Stat
            label="SAR"
            value={String(metrics.sar_cases).padStart(2, '0')}
            detail="reports requiring filing"
          />
        </section>

        <section className="signal-row">
          <div>
            <span className="section-kicker">01 / INVESTIGATION STATUS</span>
            <h2>
              Twenty cases.
              <br />
              <i>One evidence trail.</i>
            </h2>
          </div>

          <div className="status-card">
            <div className="status-top">
              <span>CASE MEMORY</span>
              <strong>
                {metrics.graph_written}/{metrics.total_cases} written to graph
              </strong>
            </div>
            <div className="progress">
              <div style={{ width: `${(metrics.graph_written / total) * 100}%` }} />
            </div>
            <p>Closed investigations are retained as memory for subsequent analysis.</p>
          </div>

          <div className="status-card">
            <div className="status-top">
              <span>DECISION MIX</span>
              <strong>
                {metrics.fraud_cases} fraud · {metrics.legitimate_cases} cleared
              </strong>
            </div>
            <div className="mix">
              <span style={{ width: `${(metrics.fraud_cases / total) * 100}%` }} />
              <span style={{ width: `${(metrics.legitimate_cases / total) * 100}%` }} />
            </div>
            <p>Risk is assessed from evidence, not from the trigger score alone.</p>
          </div>
        </section>

        <section className="cases-section">
          <div className="section-head">
            <div>
              <span className="section-kicker">02 / ACTIVE RECORD</span>
              <h2>Investigations</h2>
            </div>

            <label className="search">
              <Search size={15} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search cases"
              />
            </label>
          </div>

          <div className="case-table">
            <div className="table-head">
              <span>CASE</span>
              <span>TRIGGER</span>
              <span>PATTERN</span>
              <span>PROBABILITY</span>
              <span>EXPOSURE</span>
              <span>STATUS</span>
              <span />
            </div>

            {recent.map((item) => {
              const probability = Math.round(item.fraud_probability * 100)
              return (
                <button
                  className="case-row"
                  key={item.case_id}
                  onClick={() => {
                    setPage('detail')
                  }}
                  title="Open investigations to inspect this case"
                >
                  <div>
                    <strong>{item.case_id}</strong>
                    <small>
                      {item.flagged_txn_id} · {item.customer_id}
                    </small>
                  </div>

                  <span className="trigger">{formatLabel(item.trigger_type)}</span>
                  <span className="pattern">
                    {item.pattern === 'none' ? '—' : formatLabel(item.pattern)}
                  </span>

                  <div className="prob">
                    <span>{probability}%</span>
                    <div>
                      <i style={{ width: `${probability}%` }} />
                    </div>
                  </div>

                  <span>{money.format(item.exposure_usd)}</span>

                  <span className={`badge ${item.verdict}`}>
                    {item.verdict === 'fraud' ? 'FRAUD' : 'CLEARED'}
                  </span>

                  <ChevronRight size={17} />
                </button>
              )
            })}
          </div>

          <button className="view-all" onClick={() => setPage('cases')}>
            View all investigations
            <ArrowUpRight size={15} />
          </button>
        </section>

        <section className="method">
          <div className="method-title">
            <span className="section-kicker">03 / AGENTIC FLOW</span>
            <h2>
              From alert
              <br />
              <i>to action.</i>
            </h2>
          </div>

          <div className="flow">
            {['Trigger', 'Investigate', 'Gather evidence', 'Assess', 'Decide', 'Explain', 'Memory'].map(
              (step, index) => (
                <div className="flow-step" key={step}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <strong>{step}</strong>
                  {index < 6 && <ChevronRight size={14} />}
                </div>
              ),
            )}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}


function EvidencePage({ data, setPage }: { data: Overview; setPage: (page: Page) => void }) {
  const fraudCases = data.cases.filter((item) => item.verdict.toLowerCase() === 'fraud')
  const graphCases = data.cases.filter((item) => item.written_to_graph)

  return (
    <div className="app-shell">
      <Header page="evidence" setPage={setPage} />
      <main>
        <section className="workspace-page">
          <button className="back-button" onClick={() => setPage('overview')}>
            <ArrowLeft size={15} /> Overview
          </button>
          <div className="section-kicker">03 / EVIDENCE REGISTER</div>
          <div className="workspace-heading">
            <div>
              <h1>Evidence<br /><i>that connects.</i></h1>
              <p>Trace the graph-backed evidence collected across the investigation set.</p>
            </div>
            <div className="workspace-number">
              <span>GRAPH-LINKED CASES</span>
              <strong>{String(graphCases.length).padStart(2, '0')}</strong>
            </div>
          </div>

          <div className="evidence-overview-grid">
            <div className="evidence-stat-card">
              <span>CASES WITH GRAPH MEMORY</span>
              <strong>{graphCases.length}</strong>
              <p>Investigations written back into the graph for future retrieval.</p>
            </div>
            <div className="evidence-stat-card">
              <span>FRAUD CASES</span>
              <strong>{fraudCases.length}</strong>
              <p>Cases whose evidence chain ended in a fraud assessment.</p>
            </div>
            <div className="evidence-stat-card">
              <span>IDENTIFIED EXPOSURE</span>
              <strong>{money.format(data.metrics.fraud_exposure_usd)}</strong>
              <p>Combined exposure associated with identified fraud.</p>
            </div>
          </div>

          <div className="evidence-register">
            <div className="register-head"><span>CASE</span><span>TRANSACTION</span><span>PATTERN</span><span>EVIDENCE STATE</span><span /></div>
            {data.cases.map((item) => (
              <button key={item.case_id} className="evidence-register-row" onClick={() => setPage('cases')}>
                <div><strong>{item.case_id}</strong><small>{item.customer_id}</small></div>
                <span>{item.flagged_txn_id}</span>
                <span>{formatLabel(item.pattern)}</span>
                <span className="evidence-state"><span className="state-dot" />{item.written_to_graph ? 'GRAPH WRITTEN' : 'PENDING'}</span>
                <ChevronRight size={16} />
              </button>
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

function MemoryPage({ data, setPage }: { data: Overview; setPage: (page: Page) => void }) {
  const memories = data.cases.filter((item) => item.written_to_graph)

  return (
    <div className="app-shell">
      <Header page="memory" setPage={setPage} />
      <main>
        <section className="workspace-page">
          <button className="back-button" onClick={() => setPage('overview')}>
            <ArrowLeft size={15} /> Overview
          </button>
          <div className="section-kicker">04 / INVESTIGATION MEMORY</div>
          <div className="workspace-heading">
            <div>
              <h1>What the agent<br /><i>remembers.</i></h1>
              <p>Completed investigations become reusable context for subsequent fraud analysis.</p>
            </div>
            <div className="workspace-number">
              <span>MEMORIES STORED</span>
              <strong>{String(memories.length).padStart(2, '0')}</strong>
            </div>
          </div>

          <div className="memory-intro">
            <div className="memory-icon"><Database size={22} /></div>
            <div>
              <span>LONG-TERM INVESTIGATION MEMORY</span>
              <h2>Every closed case can become evidence for the next one.</h2>
              <p>The memory layer retains case outcomes, patterns and graph relationships so the agent can retrieve prior investigations instead of starting from zero.</p>
            </div>
          </div>

          <div className="memory-list">
            {memories.map((item, index) => (
              <div className="memory-row" key={item.case_id}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <div><strong>{item.case_id}</strong><p>{item.summary}</p></div>
                <div><span>PATTERN</span><strong>{formatLabel(item.pattern)}</strong></div>
                <div><span>OUTCOME</span><strong>{item.verdict.toUpperCase()}</strong></div>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  const [data, setData] = useState<Overview | null>(null)
  const [page, setPage] = useState<Page>('overview')
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    loadOverview()
      .then(setData)
      .catch((reason) => {
        console.error(reason)
        setError('Unable to load investigation data.')
      })
  }, [])

  if (!data && !error) {
    return (
      <div className="boot">
        <img src="/assets/fox-logo.png" alt="Foxtrail" className="boot-logo" />
        <span>Preparing investigation console</span>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="boot">
        <img src="/assets/fox-logo.png" alt="Foxtrail" className="boot-logo" />
        <span>{error}</span>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  if (page === 'evidence') {
    return <EvidencePage data={data} setPage={setPage} />
  }

  if (page === 'memory') {
    return <MemoryPage data={data} setPage={setPage} />
  }

  if (page === 'detail' && selectedCaseId) {
    const selected = data.cases.find((item) => item.case_id === selectedCaseId)

    if (selected) {
      return (
        <div className="app-shell">
          <Header page="detail" setPage={setPage} />
          <main>
            <CaseDetail caseItem={selected} onBack={() => setPage('cases')} />
          </main>
          <Footer />
        </div>
      )
    }
  }

  if (page === 'cases') {
    return (
      <div className="app-shell">
        <Header page="cases" setPage={setPage} />
        <main>
          <CaseList
            cases={data.cases}
            onBack={() => setPage('overview')}
            onOpenCase={(caseId) => {
              setSelectedCaseId(caseId)
              setPage('detail')
            }}
          />
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <OverviewPage
      data={data}
      query={query}
      setQuery={setQuery}
      setPage={(next) => {
        if (next === 'detail') return
        setPage(next)
      }}
    />
  )
}

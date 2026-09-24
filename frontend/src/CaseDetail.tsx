import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  Check,
  Database,
  FileText,
  GitBranch,
  Loader2,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import type { CaseRow } from './App'

type Props = {
  caseItem: CaseRow
  onBack: () => void
}

const stages = [
  ['Trigger detected', 'Initial transaction alert received.'],
  ['Transaction investigated', 'Transaction and customer context examined.'],
  ['Graph evidence gathered', 'Related cards, devices and historical cases examined.'],
  ['Cross-case analysis', 'Previous investigations compared for similar patterns.'],
  ['Decision reached', 'Evidence consolidated into a final action.'],
  ['Explanation generated', 'Decision rationale prepared for review.'],
  ['Memory updated', 'Investigation outcome written back to the graph.'],
] as const

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

function label(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function CaseDetail({ caseItem, onBack }: Props) {
  const [activeStage, setActiveStage] = useState(0)
  const [activeTab, setActiveTab] = useState<'investigation' | 'evidence' | 'decision' | 'report'>(
    'investigation',
  )

  useEffect(() => {
    setActiveStage(0)

    const timer = window.setInterval(() => {
      setActiveStage((current) => {
        if (current >= stages.length - 1) {
          window.clearInterval(timer)
          return current
        }
        return current + 1
      })
    }, 950)

    return () => window.clearInterval(timer)
  }, [caseItem.case_id])

  const probability = Math.round(caseItem.fraud_probability * 100)
  const isFraud = caseItem.verdict.toLowerCase() === 'fraud'
  const complete = activeStage === stages.length - 1
  const actions = caseItem.final_actions ?? []

  const initialActions = caseItem.initial_actions ?? []
  const finalActions = caseItem.final_actions ?? []

  const whatChanged =
    caseItem.what_changed ||
    'The final recommendation reflects the evidence gathered during the investigation.'

  return (
    <div className="case-detail-page">
      <div className="case-detail-top">
        <button className="detail-back" onClick={onBack}>
          <ArrowLeft size={16} />
          Investigations
        </button>
        <div className="detail-kicker">CASE / {caseItem.case_id}</div>
      </div>

      <section className="case-hero">
        <div className="case-hero-main">
          <div className="detail-eyebrow">
            <span className={`signal-dot ${isFraud ? 'danger' : ''}`} />
            AGENTIC INVESTIGATION
          </div>

          <h1>{caseItem.case_id}</h1>

          <p className="case-hero-summary">
            {caseItem.summary || 'Investigation initiated from a transaction risk signal.'}
          </p>
        </div>

        <div className="case-verdict-panel">
          <span>FINAL ASSESSMENT</span>
          <strong className={isFraud ? 'verdict-fraud' : 'verdict-clear'}>
            {isFraud ? 'FRAUD' : 'CLEARED'}
          </strong>

          <div className="verdict-probability">
            <span>{probability}% confidence</span>
            <div>
              <i style={{ width: `${probability}%` }} />
            </div>
          </div>
        </div>
      </section>

      <section className="case-facts">
        <div>
          <span>TRANSACTION</span>
          <strong>{caseItem.flagged_txn_id}</strong>
        </div>
        <div>
          <span>CUSTOMER</span>
          <strong>{caseItem.customer_id}</strong>
        </div>
        <div>
          <span>EXPOSURE</span>
          <strong>{money.format(caseItem.exposure_usd)}</strong>
        </div>
        <div>
          <span>TRIGGER</span>
          <strong>{label(caseItem.trigger_type)}</strong>
        </div>
        <div>
          <span>PATTERN</span>
          <strong>{label(caseItem.pattern)}</strong>
        </div>
        <div>
          <span>SAR</span>
          <strong>{caseItem.sar ? 'REQUIRED' : 'NOT REQUIRED'}</strong>
        </div>
      </section>

      <section className="live-investigation">
        <div className="live-heading">
          <div>
            <span className="section-kicker">LIVE AGENT TRACE</span>
            <h2>
              Following the evidence.
            </h2>
          </div>

          <div className="agent-running">
            {complete ? (
              <>
                <Check size={14} />
                INVESTIGATION COMPLETE
              </>
            ) : (
              <>
                <span className="pulse-dot" />
                AGENT WORKING
              </>
            )}
          </div>
        </div>

        <div className="investigation-layout">
          <div className="agent-timeline">
            {stages.map(([stage, description], index) => {
              const completed = index < activeStage || (index === activeStage && complete)
              const current = index === activeStage && !complete

              return (
                <div
                  key={stage}
                  className={`agent-stage ${completed ? 'completed' : ''} ${
                    current ? 'current' : ''
                  }`}
                >
                  <div className="stage-marker">
                    {completed ? (
                      <Check size={13} />
                    ) : current ? (
                      <Loader2 size={14} className="spin" />
                    ) : (
                      <span className="stage-empty" />
                    )}
                  </div>

                  <div className="stage-content">
                    <div className="stage-top">
                      <strong>{stage}</strong>
                      <span>{String(index + 1).padStart(2, '0')}</span>
                    </div>
                    <p>{current || completed ? description : 'Awaiting agent execution.'}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="agent-output">
            <div className="output-header">
              <div>
                <span>AGENT OUTPUT</span>
                <strong>{stages[activeStage][0]}</strong>
              </div>
              <GitBranch size={18} />
            </div>

            <div className="output-body">
              {activeStage === 0 && (
                <Trace icon={<ShieldAlert size={20} />} title="Risk signal received">
                  The transaction entered the investigation queue from a{' '}
                  {label(caseItem.trigger_type).toLowerCase()} trigger.
                </Trace>
              )}

              {activeStage === 1 && (
                <Trace icon={<Database size={20} />} title="Inspecting transaction context">
                  Resolving transaction {caseItem.flagged_txn_id} for customer {caseItem.customer_id}.
                </Trace>
              )}

              {activeStage === 2 && (
                <Trace icon={<GitBranch size={20} />} title="Traversing investigation graph">
                  Searching connected cards, devices, transactions and prior investigations.
                </Trace>
              )}

              {activeStage === 3 && (
                <Trace icon={<Sparkles size={20} />} title="Comparing historical cases">
                  Looking for previously closed investigations with overlapping evidence patterns.
                </Trace>
              )}

              {activeStage === 4 && (
                <Trace icon={<ShieldAlert size={20} />} title="Consolidating evidence">
                  Current assessment: {probability}% fraud probability with{' '}
                  {money.format(caseItem.exposure_usd)} exposure.
                </Trace>
              )}

              {activeStage === 5 && (
                <Trace icon={<FileText size={20} />} title="Building decision rationale">
                  Translating the evidence chain into an auditable explanation.
                </Trace>
              )}

              {activeStage === 6 && (
                <Trace icon={<Database size={20} />} title="Investigation committed">
                  Case outcome is ready to be retained as investigation memory.
                </Trace>
              )}
            </div>

            <div className="output-footer">
              <span>
                NODE {activeStage + 1} / {stages.length}
              </span>
              <span>TIGERGRAPH · LANGGRAPH</span>
            </div>
          </div>
        </div>
      </section>

      <section className="case-information">
        <div className="detail-tabs">
          {(['investigation', 'evidence', 'decision', 'report'] as const).map((tab) => (
            <button
              key={tab}
              className={activeTab === tab ? 'active' : ''}
              onClick={() => setActiveTab(tab)}
            >
              {tab[0].toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="detail-panel">
          {activeTab === 'investigation' && (
            <div className="information-grid">
              <InfoBlock
                title="FLAGGED TRANSACTION"
                value={caseItem.flagged_txn_id}
                text={`Customer ${caseItem.customer_id} was associated with the transaction that triggered this investigation.`}
              />
              <InfoBlock
                title="TRIGGER"
                value={label(caseItem.trigger_type)}
                text="Initial risk signal that caused the case to enter investigation."
              />
              <InfoBlock
                title="IDENTIFIED PATTERN"
                value={label(caseItem.pattern)}
                text="Pattern identified during the investigation process."
              />
              <InfoBlock
                title="EXPOSURE"
                value={money.format(caseItem.exposure_usd)}
                text="Financial exposure associated with this case."
              />
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="evidence-view">
              <div className="evidence-intro">
                <span className="section-kicker">EVIDENCE GRAPH</span>
                <h3>
                  The decision follows
                  <br />
                  <i>the connected evidence.</i>
                </h3>
                <p>
                  The graph-backed evidence layer is where related cards, transactions, devices and
                  historical cases can be surfaced from TigerGraph.
                </p>
              </div>

              <div className="evidence-nodes">
                <EvidenceNode label="CASE" value={caseItem.case_id} primary />
                <div className="evidence-line" />
                <EvidenceNode label="TRANSACTION" value={caseItem.flagged_txn_id} />
                <div className="evidence-line" />
                <EvidenceNode label="CUSTOMER" value={caseItem.customer_id} />
              </div>
            </div>
          )}

          {activeTab === 'decision' && (
            <div className="decision-view">

              <div className="decision-intro">
                <span className="section-kicker">DECISION TRACE</span>

                <h3>
                  The recommendation
                  <br />
                  <i>evolved with evidence.</i>
                </h3>

                <p>
                  The agent records its recommendation before evidence is gathered,
                  then shows how that recommendation changes after investigation.
                </p>
              </div>

              <div className="decision-columns">

                {/* =====================================================
                    BEFORE EVIDENCE — INITIAL RECOMMENDATION
                    ===================================================== */}
                <div className="decision-stage initial-stage">

                  <div className="decision-stage-header">
                    <span>01</span>

                    <div>
                      <small>BEFORE EVIDENCE</small>
                      <h4>Initial recommendation</h4>
                    </div>
                  </div>

                  <div className="action-list">
                    {initialActions.length > 0 ? (
                      initialActions.map((action, index) => (
                        <div
                          className="decision-action"
                          key={`initial-${action.action}-${index}`}
                        >
                          <div className="action-top">
                            <strong>{label(action.action)}</strong>

                            {action.route && (
                              <span className={`route route-${action.route}`}>
                                {action.route}
                              </span>
                            )}
                          </div>

                          <p>
                            {action.reason ||
                              'Recorded by the investigation agent.'}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="decision-empty">
                        No initial recommendation recorded.
                      </div>
                    )}
                  </div>

                </div>


                {/* =====================================================
                    AFTER EVIDENCE — FINAL RECOMMENDATION
                    ===================================================== */}
                <div className="decision-stage final-stage">

                  <div className="decision-stage-header">
                    <span>02</span>

                    <div>
                      <small>AFTER EVIDENCE</small>
                      <h4>Final recommendation</h4>
                    </div>
                  </div>

                  <div className="action-list">
                    {finalActions.length > 0 ? (
                      finalActions.map((action, index) => (
                        <div
                          className="decision-action"
                          key={`final-${action.action}-${index}`}
                        >
                          <div className="action-top">
                            <strong>{label(action.action)}</strong>

                            {action.route && (
                              <span className={`route route-${action.route}`}>
                                {action.route}
                              </span>
                            )}
                          </div>

                          <p>
                            {action.reason ||
                              'Recorded by the investigation agent.'}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="decision-empty">
                        No final recommendation recorded.
                      </div>
                    )}
                  </div>

                </div>

              </div>


              {/* =====================================================
                  WHAT CHANGED — ONE SINGLE BLOCK
                  ===================================================== */}
              <div className="decision-change">

                <div className="change-marker">
                  <span>Δ</span>
                </div>

                <div>
                  <small>WHAT CHANGED</small>

                  <p>{whatChanged}</p>
                </div>

              </div>
            </div>
          )}

          {activeTab === 'report' && (
            <div className="report-view">
              <div className="report-paper">
                <div className="report-top">
                  <span>FOXTRAIL / CASE REPORT</span>
                  <span>{caseItem.case_id}</span>
                </div>

                <h3>Investigation Summary</h3>

                <p>{caseItem.summary || 'No investigation summary is available yet.'}</p>

                <div className="report-fields">
                  <div>
                    <span>CASE</span>
                    <strong>{caseItem.case_id}</strong>
                  </div>
                  <div>
                    <span>TRANSACTION</span>
                    <strong>{caseItem.flagged_txn_id}</strong>
                  </div>
                  <div>
                    <span>DECISION</span>
                    <strong>{isFraud ? 'FRAUD' : 'CLEARED'}</strong>
                  </div>
                  <div>
                    <span>SAR</span>
                    <strong>{caseItem.sar ? 'REQUIRED' : 'NOT REQUIRED'}</strong>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

function Trace({
  icon,
  title,
  children,
}: {
  icon: ReactNode
  title: string
  children: ReactNode
}) {
  return (
    <div className="trace-message">
      <div className="trace-icon">{icon}</div>
      <div>
        <strong>{title}</strong>
        <p>{children}</p>
      </div>
    </div>
  )
}

function InfoBlock({
  title,
  value,
  text,
}: {
  title: string
  value: string
  text: string
}) {
  return (
    <div>
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{text}</p>
    </div>
  )
}

function EvidenceNode({
  label: nodeLabel,
  value,
  primary = false,
}: {
  label: string
  value: string
  primary?: boolean
}) {
  return (
    <div className={`evidence-node ${primary ? 'primary' : ''}`}>
      <span>{nodeLabel}</span>
      <strong>{value}</strong>
    </div>
  )
}

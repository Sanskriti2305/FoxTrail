import { useMemo, useState } from 'react'
import { ArrowLeft, ArrowUpDown, ChevronRight, Search, SlidersHorizontal } from 'lucide-react'
import type { CaseRow } from './App'

type Props = {
  cases: CaseRow[]
  onBack: () => void
  onOpenCase?: (caseId: string) => void
}

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

function label(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function CaseList({ cases, onBack, onOpenCase }: Props) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('ALL')
  const [sort, setSort] = useState('risk')

  const filteredCases = useMemo(() => {
    let result = [...cases]

    if (filter !== 'ALL') {
      result = result.filter((item) => item.verdict.toUpperCase() === filter)
    }

    const q = search.trim().toLowerCase()
    if (q) {
      result = result.filter((item) =>
        [
          item.case_id,
          item.customer_id,
          item.flagged_txn_id,
          item.pattern,
          item.trigger_type,
          item.status,
        ]
          .join(' ')
          .toLowerCase()
          .includes(q),
      )
    }

    result.sort((a, b) => {
      if (sort === 'risk') return b.fraud_probability - a.fraud_probability
      if (sort === 'exposure') return b.exposure_usd - a.exposure_usd
      return a.case_id.localeCompare(b.case_id)
    })

    return result
  }, [cases, search, filter, sort])

  const fraudCount = cases.filter((item) => item.verdict.toLowerCase() === 'fraud').length
  const legitimateCount = cases.filter((item) => item.verdict.toLowerCase() === 'legitimate').length
  const reviewCount = cases.filter(
    (item) => item.status !== 'closed' && item.status !== 'completed',
  ).length

  return (
    <div className="investigations-page">
      <div className="investigations-heading">
        <div>
          <button className="back-button" onClick={onBack}>
            <ArrowLeft size={15} />
            Overview
          </button>

          <div className="section-kicker">02 / INVESTIGATION REGISTER</div>

          <h1>
            Every case.
            <br />
            <i>Every signal.</i>
          </h1>

          <p>A complete record of the investigations processed by the agent.</p>
        </div>

        <div className="case-count">
          <span>CASES IN SCOPE</span>
          <strong>{String(cases.length).padStart(2, '0')}</strong>
        </div>
      </div>

      <div className="investigation-summary">
        <div>
          <span>ALL CASES</span>
          <strong>{cases.length}</strong>
        </div>
        <div>
          <span>FRAUD</span>
          <strong>{fraudCount}</strong>
        </div>
        <div>
          <span>CLEARED</span>
          <strong>{legitimateCount}</strong>
        </div>
        <div>
          <span>REQUIRES REVIEW</span>
          <strong>{reviewCount}</strong>
        </div>
      </div>

      <div className="case-controls">
        <label className="case-search">
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search case, customer, transaction..."
          />
        </label>

        <div className="filter-group">
          <button className={filter === 'ALL' ? 'selected' : ''} onClick={() => setFilter('ALL')}>
            All
          </button>
          <button
            className={filter === 'FRAUD' ? 'selected' : ''}
            onClick={() => setFilter('FRAUD')}
          >
            Fraud
          </button>
          <button
            className={filter === 'LEGITIMATE' ? 'selected' : ''}
            onClick={() => setFilter('LEGITIMATE')}
          >
            Cleared
          </button>
        </div>

        <div className="sort-control">
          <SlidersHorizontal size={14} />
          <select value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="risk">Highest risk</option>
            <option value="exposure">Highest exposure</option>
            <option value="case">Case ID</option>
          </select>
        </div>
      </div>

      <div className="investigation-table">
        <div className="investigation-table-head">
          <span>CASE</span>
          <span>TRIGGER</span>
          <span>PATTERN</span>
          <span>RISK</span>
          <span>EXPOSURE</span>
          <span>STATUS</span>
          <span />
        </div>

        {filteredCases.map((item) => {
          const probability = Math.round(item.fraud_probability * 100)

          return (
            <button
              className="investigation-row"
              key={item.case_id}
              onClick={() => onOpenCase?.(item.case_id)}
            >
              <div className="case-identity">
                <strong>{item.case_id}</strong>
                <small>{item.flagged_txn_id}</small>
                <small>{item.customer_id}</small>
              </div>

              <div className="case-trigger">
                <span>{label(item.trigger_type)}</span>
              </div>

              <div className="case-pattern">
                {item.pattern && item.pattern !== 'none' ? label(item.pattern) : 'No dominant pattern'}
              </div>

              <div className="case-risk">
                <div className="risk-number">{probability}%</div>
                <div className="risk-track">
                  <div style={{ width: `${probability}%` }} />
                </div>
              </div>

              <div className="case-exposure">{money.format(item.exposure_usd)}</div>

              <div>
                <span className={`case-verdict ${item.verdict === 'fraud' ? 'fraud' : 'cleared'}`}>
                  {item.verdict === 'fraud' ? 'FRAUD' : 'CLEARED'}
                </span>
                {item.sar && <small className="sar-label">SAR</small>}
              </div>

              <ChevronRight size={17} className="row-arrow" />
            </button>
          )
        })}
      </div>

      <div className="result-footer">
        <span>
          Showing {filteredCases.length} of {cases.length} investigations
        </span>
        <span>
          <ArrowUpDown size={12} />
          Sorted by {sort === 'risk' ? 'risk' : sort === 'exposure' ? 'exposure' : 'case ID'}
        </span>
      </div>
    </div>
  )
}

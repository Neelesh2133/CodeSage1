import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import client from '../api/client'
import HeroWave from '../components/ui/dynamic-wave-canvas-background'

const SEVERITY_COLOR = {
  critical: '#ef4444', // Red-500
  high: '#f97316',     // Orange-500
  medium: '#f59e0b',   // Amber-500
  low: '#3b82f6',      // Blue-500
  info: '#10b981',     // Emerald-500
}

const SEVERITY_BG = {
  critical: 'rgba(239, 68, 68, 0.15)',
  high: 'rgba(249, 115, 22, 0.15)',
  medium: 'rgba(245, 158, 11, 0.15)',
  low: 'rgba(59, 130, 246, 0.15)',
  info: 'rgba(16, 185, 129, 0.15)',
}

const SEVERITY_BORDER = {
  critical: 'rgba(239, 68, 68, 0.4)',
  high: 'rgba(249, 115, 22, 0.4)',
  medium: 'rgba(245, 158, 11, 0.4)',
  low: 'rgba(59, 130, 246, 0.4)',
  info: 'rgba(16, 185, 129, 0.4)',
}

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info']

function severityCounts(findings = []) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
  findings.forEach((f) => {
    const sev = f.severity?.toLowerCase()
    if (counts[sev] !== undefined) counts[sev]++
  })
  return counts
}

function calculateSecurityScore(findings = []) {
  let score = 100
  findings.forEach((f) => {
    const sev = f.severity?.toLowerCase()
    if (sev === 'critical') score -= 20
    else if (sev === 'high') score -= 14
    else if (sev === 'medium') score -= 8
    else if (sev === 'low') score -= 3
  })
  return Math.max(10, score)
}

function topSeverity(findings = []) {
  for (const s of SEVERITY_ORDER) {
    if (findings.some((f) => f.severity?.toLowerCase() === s)) return s
  }
  return null
}

function Spinner() {
  return (
    <span className="inline-block w-4 h-4 border-2 border-zinc-650 border-t-white rounded-full animate-spin-slow" />
  )
}

function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(onClose, 3500)
    return () => clearTimeout(t)
  }, [toast, onClose])

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 15, scale: 0.95 }}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border border-zinc-700 bg-zinc-900/90 backdrop-blur-md shadow-xl text-sm"
          style={{
            boxShadow: '0 8px 30px rgba(0,0,0,0.5)'
          }}
        >
          <span className={`w-2.5 h-2.5 rounded-full ${toast.type === 'error' ? 'bg-red-500 animate-pulse' : 'bg-emerald-550'}`} />
          <span className="text-zinc-100 font-mono text-xs">{toast.message}</span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function ScoreWidget({ score }) {
  const strokeDashoffset = 251.2 - (251.2 * score) / 100
  let strokeColor = '#ffffff' // High-contrast White
  if (score < 55) {
    strokeColor = '#ef4444' // Red
  } else if (score < 80) {
    strokeColor = '#f97316' // Orange
  } else if (score < 100) {
    strokeColor = '#10b981' // Green
  }

  return (
    <div className="flex items-center gap-4 bg-zinc-900/90 border border-zinc-700/80 rounded-xl p-4 shadow-md backdrop-blur-sm">
      <div className="relative w-16 h-16 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" stroke="#444452" strokeWidth="6" fill="transparent" />
          <motion.circle
            cx="50"
            cy="50"
            r="40"
            stroke={strokeColor}
            strokeWidth="6"
            fill="transparent"
            strokeDasharray="251.2"
            initial={{ strokeDashoffset: 251.2 }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute text-xs font-mono font-bold text-white">{score}%</span>
      </div>
      <div>
        <p className="text-[10px] text-zinc-400 uppercase tracking-widest font-mono font-semibold">Integrity Score</p>
        <h4 className="text-sm font-bold text-zinc-150 mt-0.5 font-mono">
          {score === 100 ? 'Secure' : score > 80 ? 'Low Risk' : score > 50 ? 'Warning' : 'Vulnerable'}
        </h4>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [reviews, setReviews] = useState([])
  const [selected, setSelected] = useState(null)
  const [mode, setMode] = useState('code')
  const [code, setCode] = useState('')
  const [prUrl, setPrUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoading, setHistoryLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [expandedFindings, setExpandedFindings] = useState({})
  
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')

  const navigate = useNavigate()

  async function loadReviews() {
    try {
      const res = await client.get('/reviews/')
      setReviews(res.data)
      if (res.data.length > 0 && !selected) {
        setSelected(res.data[0])
      }
    } catch {
      /* ignore */
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadReviews()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function logout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  async function submitReview(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const isPR = mode === 'pr'
      const endpoint = isPR ? '/reviews/pr' : '/reviews/'
      const payload = isPR ? { pr_url: prUrl } : { code }
      const res = await client.post(endpoint, payload)
      setCode('')
      setPrUrl('')
      await loadReviews()
      setSelected(res.data)
      const n = res.data.findings?.length ?? 0
      setToast({
        type: 'success',
        message: n === 0 ? 'Auditing complete — codebase verified clean.' : `Auditing complete — ${n} threat flags.`
      })
    } catch (err) {
      const msg = err.response?.data?.detail || 'Audit request failed.'
      setError(msg)
      setToast({ type: 'error', message: 'Audit failed.' })
    } finally {
      setLoading(false)
    }
  }

  const toggleFindingExpand = (index) => {
    setExpandedFindings((prev) => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const copyToClipboard = (text, label = 'Content') => {
    navigator.clipboard.writeText(text)
    setToast({ type: 'success', message: `${label} copied to clipboard!` })
  }

  const filteredFindings = (selected?.findings ?? []).filter((f) => {
    const matchesSearch =
      f.message?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.file_path?.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesSeverity = severityFilter === 'all' || f.severity?.toLowerCase() === severityFilter.toLowerCase()
    return matchesSearch && matchesSeverity
  })

  const currentScore = selected ? calculateSecurityScore(selected.findings ?? []) : 100
  const counts = selected ? severityCounts(selected.findings ?? []) : { critical: 0, high: 0, medium: 0, low: 0, info: 0 }

  return (
    <div className="min-h-screen text-zinc-150 flex flex-col font-sans bg-zinc-950 relative overflow-hidden">
      {/* Dynamic Wave Canvas Background */}
      <HeroWave />
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Header Bar */}
      <header className="border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-30 shadow-md relative">
        <div className="flex items-center gap-3">
          <div className="w-6.5 h-6.5 rounded bg-white text-zinc-950 flex items-center justify-center font-bold text-xs shadow-md">
            S
          </div>
          <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2 font-mono">
            CodeSage <span className="text-[9px] text-zinc-300 font-normal px-2 py-0.5 bg-zinc-900 border border-zinc-700 rounded-md">v2.4</span>
          </h1>
        </div>

        <div className="flex items-center gap-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={logout}
            className="text-xs text-zinc-300 hover:text-white font-mono transition-colors flex items-center gap-1.5 border border-zinc-700 px-3 py-1.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-800"
          >
            Sign out
          </motion.button>
        </div>
      </header>

      {/* Main Workspace Frame */}
      <div className="grid md:grid-cols-[360px_1fr] flex-1 min-h-[calc(100vh-65px)] relative z-10">
        {/* Sidebar panel */}
        <aside className="border-r border-zinc-800 bg-zinc-950/90 backdrop-blur-md p-5 overflow-y-auto flex flex-col gap-6 relative">
          <div>
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 font-mono">Scan Dispatcher</h3>
            
            {/* Simplified Multi-Source tabs */}
            <div className="grid grid-cols-2 gap-2 mb-3.5">
              <motion.button
                type="button"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => setMode('code')}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  mode === 'code'
                    ? 'border-white bg-zinc-900/90 text-white shadow-sm font-bold'
                    : 'border-zinc-800 bg-zinc-950/80 text-zinc-500 hover:bg-zinc-900/50'
                }`}
              >
                <span className="text-xs font-mono">CODE</span>
                <span className="text-[9px] mt-0.5 opacity-80">Paste raw text</span>
              </motion.button>
              <motion.button
                type="button"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => setMode('pr')}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  mode === 'pr'
                    ? 'border-white bg-zinc-900/90 text-white shadow-sm font-bold'
                    : 'border-zinc-800 bg-zinc-950/80 text-zinc-500 hover:bg-zinc-900/50'
                }`}
              >
                <span className="text-xs font-mono">PR URL</span>
                <span className="text-[9px] mt-0.5 opacity-80">GitHub PR</span>
              </motion.button>
            </div>

            {/* Target inputs */}
            <form onSubmit={submitReview} className="bg-zinc-900/60 border border-zinc-700/80 rounded-xl p-4 backdrop-blur-sm">
              {mode === 'code' ? (
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                  rows={6}
                  placeholder="Paste source code (Python, Go, JS, etc.) to scan..."
                  className="w-full bg-zinc-950/90 border border-zinc-700 rounded-lg p-3 text-xs font-mono focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-white placeholder:text-zinc-500 editor-textarea transition-all"
                />
              ) : (
                <div className="space-y-1">
                  <input
                    value={prUrl}
                    onChange={(e) => setPrUrl(e.target.value)}
                    required
                    placeholder="https://github.com/owner/repo/pull/123"
                    className="w-full bg-zinc-950/90 border border-zinc-700 rounded-lg p-2.5 text-xs focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-white placeholder:text-zinc-500 font-mono transition-all"
                  />
                </div>
              )}

              {error && (
                <p className="text-xs text-red-400 mt-2 font-mono bg-red-950/20 border border-red-900/50 p-2.5 rounded-lg">
                  {error}
                </p>
              )}
              
              <motion.button
                type="submit"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                disabled={loading || (mode === 'code' && !code) || (mode === 'pr' && !prUrl)}
                className="w-full mt-4.5 bg-white text-zinc-950 py-2.5 rounded-lg text-xs font-bold hover:bg-zinc-200 active:scale-[0.99] transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center justify-center gap-2 font-mono"
              >
                {loading ? (
                  <>
                    <Spinner /> SCANNING WORKSPACE...
                  </>
                ) : (
                  'RUN AUDIT TARGET'
                )}
              </motion.button>
            </form>
          </div>

          {/* Audit History List */}
          <div className="flex-grow flex flex-col min-h-0">
            <div className="flex justify-between items-center mb-3">
              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono">Run Registry</p>
              <span className="text-[10px] text-zinc-400 font-mono bg-zinc-900 px-2.5 py-0.5 rounded border border-zinc-800">{reviews.length} logs</span>
            </div>

            <div className="space-y-2 overflow-y-auto flex-grow pr-1">
              {historyLoading && (
                <div className="h-12 bg-zinc-900/60 border border-zinc-800 rounded-xl animate-pulse" />
              )}

              {!historyLoading && reviews.length === 0 && (
                <div className="text-center py-8 bg-zinc-900/20 border border-zinc-800 rounded-xl border-dashed">
                  <p className="text-xs text-zinc-500 font-mono">No security logs recorded.</p>
                </div>
              )}

              {reviews.map((r) => {
                const top = topSeverity(r.findings)
                const isSelected = selected?.id === r.id
                return (
                  <motion.button
                    key={r.id}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => setSelected(r)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                      isSelected
                        ? 'border-white bg-zinc-900 text-white font-medium shadow-sm'
                        : 'border-zinc-800/80 bg-zinc-950/80 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-mono flex items-center gap-2 text-zinc-200">
                        {top && <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: SEVERITY_COLOR[top] }} />}
                        Run #{r.id}
                      </span>
                      <span className="text-xs text-zinc-400 font-mono">
                        {r.findings?.length ?? 0} flags
                      </span>
                    </div>
                  </motion.button>
                )
              })}
            </div>
          </div>
        </aside>

        {/* Main Content Area - Full screen stretching grid to prevent empty right side */}
        <main className="p-6 flex flex-col min-h-0 overflow-y-auto bg-zinc-950/50 backdrop-blur-sm relative">
          {!selected ? (
            <div className="flex-grow flex flex-col items-center justify-center text-center p-8 max-w-sm mx-auto">
              <p className="text-xs text-zinc-400 font-mono leading-5">
                Select a historical audit log or paste code into the dispatcher to evaluate codebase vulnerabilities.
              </p>
            </div>
          ) : (
            <div className="w-full flex-1 flex flex-col lg:flex-row gap-6 items-start">
              
              {/* Left Column: Report Details & Vulnerabilities */}
              <div className="w-full lg:w-[65%] space-y-6">
                
                {/* Header Title Section */}
                <div className="border-b border-zinc-800 pb-5">
                  <div className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest font-bold">Workspace Evaluation Report</div>
                  <h2 className="text-xl font-bold text-white mt-1 font-mono">Audit #{selected.id}</h2>
                </div>

                {/* Findings list with search/filter */}
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row gap-3 justify-between items-start sm:items-center">
                    <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-widest font-mono">Audit Flags</h3>
                    
                    <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search anomalies..."
                        className="bg-zinc-900/90 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-white w-full sm:w-44 font-mono transition-colors"
                      />
                      
                      <select
                        value={severityFilter}
                        onChange={(e) => setSeverityFilter(e.target.value)}
                        className="bg-zinc-900/90 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-white font-mono transition-colors"
                      >
                        <option value="all">All severities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                        <option value="info">Info</option>
                      </select>
                    </div>
                  </div>

                  {/* Findings cards with entrance animations */}
                  <div className="space-y-3">
                    {filteredFindings.length === 0 ? (
                      <div className="border border-zinc-800 bg-zinc-900/20 p-8 text-center rounded-xl">
                        <p className="text-xs text-zinc-400 font-mono">No findings matches the applied filter query.</p>
                      </div>
                    ) : (
                      <AnimatePresence mode="popLayout">
                        {filteredFindings.map((f, i) => {
                          const isExpanded = !!expandedFindings[i]
                          const severity = f.severity?.toLowerCase()
                          return (
                            <motion.div
                              key={i}
                              layout="position"
                              initial={{ opacity: 0, y: 12, scale: 0.99 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              exit={{ opacity: 0, y: -10, scale: 0.99 }}
                              transition={{ duration: 0.25 }}
                              className="bg-zinc-900/95 border border-zinc-700/80 rounded-xl p-4.5 shadow-sm transition-all"
                              style={{
                                borderLeftWidth: '4px',
                                borderLeftColor: SEVERITY_COLOR[severity]
                              }}
                            >
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                  <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono mb-2">
                                    <span
                                      className="uppercase px-2.5 py-0.5 rounded font-bold border"
                                      style={{
                                        color: SEVERITY_COLOR[severity],
                                        borderColor: SEVERITY_BORDER[severity],
                                        backgroundColor: SEVERITY_BG[severity]
                                      }}
                                    >
                                      {f.severity}
                                    </span>
                                    <span className="text-zinc-200 px-2 py-0.5 bg-zinc-950 border border-zinc-800 rounded">
                                      {f.category}
                                    </span>
                                    {f.file_path && (
                                      <span className="text-zinc-300 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">
                                        {f.file_path}
                                        {f.line_number ? `:${f.line_number}` : ''}
                                      </span>
                                    )}
                                  </div>

                                  <p className="text-xs font-bold text-white leading-5">{f.message}</p>
                                </div>

                                <button
                                  onClick={() => toggleFindingExpand(i)}
                                  className="text-zinc-500 hover:text-white p-1 rounded transition-colors"
                                >
                                  <svg
                                    className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                  >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                  </svg>
                                </button>
                              </div>

                              {/* Accordion animation for Suggestion block */}
                              <AnimatePresence initial={false}>
                                {isExpanded && f.suggestion && (
                                  <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.25, ease: 'easeInOut' }}
                                    className="overflow-hidden"
                                  >
                                    <div className="mt-4 pt-3.5 border-t border-zinc-800 space-y-2">
                                      <div className="flex items-center justify-between">
                                        <span className="text-[10px] text-zinc-400 uppercase tracking-widest font-mono font-bold">Suggested Remediation Code</span>
                                        <motion.button
                                          whileHover={{ scale: 1.02 }}
                                          whileTap={{ scale: 0.98 }}
                                          onClick={() => copyToClipboard(f.suggestion, 'Remediation code')}
                                          className="text-[10px] text-zinc-300 hover:text-white font-mono flex items-center gap-1.5 bg-zinc-950 border border-zinc-700 px-2.5 py-1 rounded"
                                        >
                                          Copy Fix
                                        </motion.button>
                                      </div>

                                      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4.5 font-mono text-[10px] leading-5 text-zinc-300 relative overflow-hidden">
                                        <div className="text-zinc-500"># Remediation diff recommendations:</div>
                                        <div className="text-red-400 bg-red-950/20 border-l border-red-650 pl-2.5 my-1 select-none">- Legacy vulnerable declaration</div>
                                        <div className="text-emerald-400 bg-emerald-950/20 border-l border-emerald-650 pl-2.5 my-1">
                                          + {f.suggestion}
                                        </div>
                                      </div>
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </motion.div>
                          )
                        })}
                      </AnimatePresence>
                    )}
                  </div>
                </div>

              </div>

              {/* Right Column: Score Widget, Breakdown Card, and Warnings (35% Width) */}
              <div className="w-full lg:w-[35%] lg:sticky lg:top-[85px] space-y-6">
                
                {/* Integrity Score */}
                <ScoreWidget score={currentScore} />

                {/* Threat Distribution Panel */}
                <div className="bg-zinc-900/90 border border-zinc-700/80 rounded-xl p-4.5 shadow-md backdrop-blur-sm">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-xs font-bold text-zinc-300 font-mono">Anomaly Breakdown</span>
                    <span className="text-xs text-zinc-300 font-mono">{selected.findings?.length ?? 0} flags</span>
                  </div>

                  {selected.findings?.length > 0 ? (
                    <div>
                      <div className="flex h-2.5 w-full rounded bg-zinc-800 overflow-hidden mb-4 border border-zinc-700">
                        {SEVERITY_ORDER.map((s) => {
                          const count = counts[s]
                          if (count === 0) return null
                          return (
                            <div
                              key={s}
                              style={{
                                width: `${(count / selected.findings.length) * 100}%`,
                                backgroundColor: SEVERITY_COLOR[s]
                              }}
                            />
                          )
                        })}
                      </div>

                      <div className="flex flex-col gap-2.5 text-xs font-mono">
                        {SEVERITY_ORDER.map((s) => {
                          const count = counts[s]
                          if (count === 0) return null
                          return (
                            <div key={s} className="flex justify-between items-center bg-zinc-950/50 p-2 rounded border border-zinc-800/80">
                              <span className="flex items-center gap-2">
                                <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: SEVERITY_COLOR[s] }} />
                                <span className="capitalize text-zinc-200 font-bold">{s}</span>
                              </span>
                              <span className="text-zinc-400">{count} occurrences</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-zinc-400 font-mono italic">No security vulnerabilities detected. Codebase verified.</div>
                  )}
                </div>

                {/* Warnings alert */}
                {selected.warnings?.length > 0 && (
                  <div className="bg-zinc-900/90 border border-zinc-700/80 border-l-4 border-l-red-500 text-zinc-200 p-4 rounded-r-xl space-y-1.5 shadow-sm backdrop-blur-sm">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider font-mono text-red-400">Execution Warnings</h5>
                    <div className="text-xs space-y-1 font-mono text-zinc-300">
                      {selected.warnings.map((w, i) => (
                        <p key={i}>· {w}</p>
                      ))}
                    </div>
                  </div>
                )}

              </div>

            </div>
          )}
        </main>
      </div>
    </div>
  )
}
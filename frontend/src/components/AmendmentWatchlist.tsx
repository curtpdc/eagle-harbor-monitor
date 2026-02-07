'use client'

import { useState, useEffect, useCallback } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

interface MatterHistory {
  id: number
  action_date: string | null
  action_text: string | null
  action_body: string | null
  result: string | null
  vote_info: string | null
  is_milestone: boolean
  discovered_date: string | null
}

interface MatterAttachment {
  id: number
  name: string | null
  hyperlink: string | null
  file_type: string | null
  ai_summary: string | null
  analyzed: boolean
  discovered_date: string | null
}

interface MatterVote {
  id: number
  vote_date: string | null
  body_name: string | null
  result: string | null
  tally: string | null
  roll_call: Array<{ person: string; vote: string }> | null
  discovered_date: string | null
}

interface WatchedMatter {
  id: number
  matter_id: number
  matter_file: string | null
  matter_type: string | null
  title: string
  body_name: string | null
  current_status: string | null
  last_action_date: string | null
  legistar_url: string | null
  watch_reason: string | null
  is_active: boolean
  priority: string
  approval_path: string | null
  qualified_definition: string | null
  power_provisions: string | null
  infrastructure_triggers: string | null
  compatibility_standards: string | null
  created_date: string | null
  updated_date: string | null
}

interface WatchedMatterDetail extends WatchedMatter {
  histories: MatterHistory[]
  attachments: MatterAttachment[]
  votes: MatterVote[]
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${colors[priority] || colors.medium}`}>
      {priority.toUpperCase()}
    </span>
  )
}

function StatusPill({ status }: { status: string | null }) {
  if (!status) return null
  return (
    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full whitespace-nowrap">
      {status}
    </span>
  )
}

export default function AmendmentWatchlist() {
  const [matters, setMatters] = useState<WatchedMatter[]>([])
  const [selectedMatter, setSelectedMatter] = useState<WatchedMatterDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<'timeline' | 'documents' | 'votes' | 'analysis'>('timeline')

  const fetchWatchlist = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/watchlist`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMatters(data)
      setError(null)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Unknown error'
      setError(`Failed to load watchlist: ${message}`)
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchDetail = useCallback(async (matterId: number) => {
    try {
      setDetailLoading(true)
      const res = await fetch(`${API_BASE}/watchlist/${matterId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: WatchedMatterDetail = await res.json()
      setSelectedMatter(data)
      setActiveSection('timeline')
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Unknown error'
      setError(`Failed to load detail: ${message}`)
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const triggerAnalysis = async (matterId: number) => {
    try {
      const res = await fetch(`${API_BASE}/watchlist/${matterId}/analyze`, { method: 'POST' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      alert(`Analysis complete: ${data.analyzed} attachment(s) processed`)
      fetchDetail(matterId)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Unknown error'
      alert(`Analysis failed: ${message}`)
    }
  }

  useEffect(() => {
    fetchWatchlist()
  }, [fetchWatchlist])

  // ── Empty State ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading watchlist...</span>
      </div>
    )
  }

  if (error && matters.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">📋</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">Amendment Watchlist</h3>
        <p className="text-gray-500 mb-4">
          {error.includes('Failed') ? 'The watchlist feature is initializing. Check back soon.' : error}
        </p>
        <button onClick={fetchWatchlist} className="text-blue-600 hover:underline text-sm">
          Try Again
        </button>
      </div>
    )
  }

  if (matters.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">📋</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">No Watched Amendments Yet</h3>
        <p className="text-gray-500 max-w-md mx-auto">
          The system auto-detects data-center-related zoning text amendments and legislation from PG County Legistar.
          When matching matters are found, they&apos;ll appear here with full lifecycle tracking.
        </p>
      </div>
    )
  }

  // ── Detail View ──────────────────────────────────────────────────────────
  if (selectedMatter) {
    const m = selectedMatter
    return (
      <div>
        {/* Back button */}
        <button
          onClick={() => setSelectedMatter(null)}
          className="flex items-center text-blue-600 hover:text-blue-800 mb-6 font-medium"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Watchlist
        </button>

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{m.title}</h2>
              <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                {m.matter_file && <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{m.matter_file}</span>}
                {m.matter_type && <span>{m.matter_type}</span>}
                {m.body_name && <span>• {m.body_name}</span>}
              </div>
            </div>
            <PriorityBadge priority={m.priority} />
          </div>
          <div className="flex items-center gap-3 mt-3">
            <StatusPill status={m.current_status} />
            {m.legistar_url && (
              <a href={m.legistar_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">
                View on Legistar ↗
              </a>
            )}
            <span className="text-xs text-gray-400">Last updated: {formatDate(m.updated_date)}</span>
          </div>
        </div>

        {/* Section Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          {(['timeline', 'documents', 'votes', 'analysis'] as const).map((sec) => (
            <button
              key={sec}
              onClick={() => setActiveSection(sec)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition ${
                activeSection === sec
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {sec === 'timeline' && `Timeline (${m.histories.length})`}
              {sec === 'documents' && `Documents (${m.attachments.length})`}
              {sec === 'votes' && `Votes (${m.votes.length})`}
              {sec === 'analysis' && 'AI Analysis'}
            </button>
          ))}
        </div>

        {/* Timeline Section */}
        {activeSection === 'timeline' && (
          <div className="space-y-4">
            {m.histories.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No status history recorded yet.</p>
            ) : (
              m.histories.map((h) => (
                <div
                  key={h.id}
                  className={`flex items-start gap-4 p-4 rounded-lg ${
                    h.is_milestone ? 'bg-amber-50 border border-amber-200' : 'bg-gray-50'
                  }`}
                >
                  <div className={`w-3 h-3 rounded-full mt-1.5 flex-shrink-0 ${
                    h.is_milestone ? 'bg-amber-500' : 'bg-gray-300'
                  }`} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{h.action_text || 'Action'}</span>
                      {h.is_milestone && (
                        <span className="text-xs bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">MILESTONE</span>
                      )}
                      {h.result && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          h.result.toLowerCase().includes('pass') ? 'bg-green-100 text-green-800'
                          : h.result.toLowerCase().includes('fail') ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                        }`}>
                          {h.result}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {h.action_body && <span>{h.action_body} • </span>}
                      {formatDate(h.action_date)}
                      {h.vote_info && <span> • Vote: {h.vote_info}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Documents Section */}
        {activeSection === 'documents' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-medium text-gray-600">Attachments & Draft Text</h4>
              <button
                onClick={() => triggerAnalysis(m.matter_id)}
                className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition"
              >
                Analyze Unanalyzed
              </button>
            </div>
            {m.attachments.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No attachments found yet.</p>
            ) : (
              <div className="space-y-3">
                {m.attachments.map((a) => (
                  <div key={a.id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{a.file_type === 'pdf' ? '📄' : '📎'}</span>
                        <div>
                          <div className="font-medium text-gray-900 text-sm">{a.name || 'Untitled'}</div>
                          <div className="text-xs text-gray-400">{formatDate(a.discovered_date)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {a.analyzed && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">Analyzed</span>
                        )}
                        {a.hyperlink && (
                          <a href={a.hyperlink} target="_blank" rel="noopener noreferrer"
                             className="text-xs text-blue-600 hover:underline">
                            Download ↗
                          </a>
                        )}
                      </div>
                    </div>
                    {a.ai_summary && (
                      <div className="mt-3 p-3 bg-white rounded border border-gray-200 text-sm text-gray-700">
                        <span className="text-xs font-semibold text-blue-600 block mb-1">AI Summary</span>
                        {a.ai_summary}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Votes Section */}
        {activeSection === 'votes' && (
          <div className="space-y-3">
            {m.votes.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No votes recorded yet.</p>
            ) : (
              m.votes.map((v) => (
                <div key={v.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">
                        {v.body_name || 'Vote'} — {formatDate(v.vote_date)}
                      </div>
                      {v.tally && <div className="text-sm text-gray-600 mt-1">Tally: {v.tally}</div>}
                    </div>
                    {v.result && (
                      <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
                        v.result.toLowerCase().includes('pass') ? 'bg-green-100 text-green-800'
                        : v.result.toLowerCase().includes('fail') ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                      }`}>
                        {v.result}
                      </span>
                    )}
                  </div>
                  {v.roll_call && v.roll_call.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {v.roll_call.map((rc, i) => (
                        <span key={i} className={`text-xs px-2 py-1 rounded ${
                          rc.vote.toLowerCase() === 'aye' ? 'bg-green-50 text-green-700'
                          : rc.vote.toLowerCase() === 'nay' ? 'bg-red-50 text-red-700'
                          : 'bg-gray-100 text-gray-600'
                        }`}>
                          {rc.person}: {rc.vote}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* AI Analysis Section */}
        {activeSection === 'analysis' && (
          <div className="space-y-6">
            {!m.approval_path && !m.qualified_definition && !m.power_provisions ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">🔍</div>
                <p className="text-gray-600 mb-4">
                  AI analysis hasn&apos;t been run on this matter&apos;s attachments yet.
                </p>
                <button
                  onClick={() => triggerAnalysis(m.matter_id)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition font-medium"
                >
                  Run AI Analysis
                </button>
              </div>
            ) : (
              <>
                {m.approval_path && (
                  <AnalysisCard
                    icon="🏛️"
                    title="Approval Path"
                    value={m.approval_path}
                    highlight={m.approval_path === 'by_right'}
                  />
                )}
                {m.qualified_definition && (
                  <AnalysisCard icon="📏" title="&quot;Qualified Data Center&quot; Definition" value={m.qualified_definition} />
                )}
                {m.power_provisions && (
                  <AnalysisCard icon="⚡" title="Power Provisions" value={m.power_provisions} />
                )}
                {m.infrastructure_triggers && (
                  <AnalysisCard icon="🏗️" title="Infrastructure Triggers" value={m.infrastructure_triggers} />
                )}
                {m.compatibility_standards && (
                  <AnalysisCard icon="🛡️" title="Compatibility Standards" value={m.compatibility_standards} />
                )}
              </>
            )}
          </div>
        )}
      </div>
    )
  }

  // ── List View ────────────────────────────────────────────────────────────
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Amendment Watchlist</h2>
          <p className="text-sm text-gray-500">
            Tracking {matters.length} active piece{matters.length !== 1 ? 's' : ''} of legislation
          </p>
        </div>
        <button
          onClick={fetchWatchlist}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        {matters.map((m) => (
          <button
            key={m.id}
            onClick={() => fetchDetail(m.matter_id)}
            className="w-full text-left p-5 bg-white border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition group"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {m.matter_file && (
                    <span className="text-xs font-mono bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                      {m.matter_file}
                    </span>
                  )}
                  <PriorityBadge priority={m.priority} />
                </div>
                <h3 className="font-semibold text-gray-900 group-hover:text-blue-700 transition">
                  {m.title}
                </h3>
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  {m.matter_type && <span>{m.matter_type}</span>}
                  {m.body_name && <span>• {m.body_name}</span>}
                  <span>• Updated {formatDate(m.updated_date)}</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2 ml-4">
                <StatusPill status={m.current_status} />
                <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
            {m.watch_reason && (
              <div className="mt-2 text-xs text-gray-400 italic">{m.watch_reason}</div>
            )}
          </button>
        ))}
      </div>

      {detailLoading && (
        <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 shadow-xl flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="text-gray-700">Loading matter details...</span>
          </div>
        </div>
      )}
    </div>
  )
}

function AnalysisCard({
  icon,
  title,
  value,
  highlight = false,
}: {
  icon: string
  title: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className={`p-4 rounded-lg border ${highlight ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <h4 className="font-semibold text-gray-900 text-sm">{title}</h4>
        {highlight && <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full">⚠️ By Right</span>}
      </div>
      <p className="text-sm text-gray-700 whitespace-pre-wrap">{value}</p>
    </div>
  )
}

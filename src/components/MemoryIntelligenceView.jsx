import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  GitCommit,
  TrendingUp,
  ShieldCheck,
  Search,
  BookOpen,
  Calendar,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import {
  getDecisionMemory,
  getContradictions,
  getPersonalEvolution,
  getMemoryIntegrityStats,
} from '../services/aiJournalService';

export const MemoryIntelligenceView = ({ entries, onSelectEntry }) => {
  const [activeTab, setActiveTab] = useState('decisions'); // 'decisions' | 'contradictions' | 'evolution' | 'integrity'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data states
  const [decisionData, setDecisionData] = useState(null);
  const [contradictionData, setContradictionData] = useState(null);
  const [evolutionData, setEvolutionData] = useState(null);
  const [integrityStats, setIntegrityStats] = useState(null);

  // Evolution custom query
  const [evolutionQuery, setEvolutionQuery] = useState('');

  const loadTabData = async (tab) => {
    setLoading(true);
    setError(null);
    try {
      if (tab === 'decisions') {
        const res = await getDecisionMemory();
        setDecisionData(res);
      } else if (tab === 'contradictions') {
        const res = await getContradictions();
        setContradictionData(res);
      } else if (tab === 'evolution') {
        const res = await getPersonalEvolution(evolutionQuery);
        setEvolutionData(res);
      } else if (tab === 'integrity') {
        const res = await getMemoryIntegrityStats();
        setIntegrityStats(res);
      }
    } catch (err) {
      setError(err.message || 'Failed to analyze memory intelligence');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab]);

  const handleRunEvolution = (e) => {
    e?.preventDefault();
    loadTabData('evolution');
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      {/* Header */}
      <div className="mb-6 flex flex-col justify-between gap-4 border-b border-[#27272A] pb-6 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950/50 border border-cyan-800/60 text-cyan-400">
              <BrainCircuit className="h-4 w-4" />
            </div>
            <h1 className="font-serif text-2xl font-bold tracking-tight text-[#EDEDED]">
              Aegis Memory Intelligence
            </h1>
          </div>
          <p className="mt-1 text-xs text-[#A1A1AA]">
            Evidence-grounded cognitive analysis: Decisions, Evolving Stances, and Trajectories backed strictly by authorized journal records.
          </p>
        </div>

        {/* Refresh Button */}
        <button
          id="refresh-memory-intel-btn"
          onClick={() => loadTabData(activeTab)}
          disabled={loading}
          className="inline-flex items-center gap-2 self-start rounded-xl border border-[#27272A] bg-[#1E1E22] px-3.5 py-2 text-xs font-semibold text-[#EDEDED] transition hover:bg-[#27272A] disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="mb-6 flex flex-wrap gap-2 border-b border-[#27272A] pb-3">
        <button
          id="tab-decisions-btn"
          onClick={() => setActiveTab('decisions')}
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
            activeTab === 'decisions'
              ? 'bg-cyan-950/50 text-cyan-300 border border-cyan-800/60'
              : 'text-[#A1A1AA] hover:bg-[#1E1E22] hover:text-[#EDEDED]'
          }`}
        >
          <GitCommit className="h-3.5 w-3.5" />
          <span>Decision Memory</span>
          {decisionData?.totalDecisions !== undefined && (
            <span className="ml-1 rounded-full bg-cyan-900/60 px-1.5 py-0.2 text-[10px] text-cyan-200">
              {decisionData.totalDecisions}
            </span>
          )}
        </button>

        <button
          id="tab-contradictions-btn"
          onClick={() => setActiveTab('contradictions')}
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
            activeTab === 'contradictions'
              ? 'bg-amber-950/50 text-amber-300 border border-amber-800/60'
              : 'text-[#A1A1AA] hover:bg-[#1E1E22] hover:text-[#EDEDED]'
          }`}
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Contradiction Detection</span>
          {contradictionData?.totalDetected !== undefined && (
            <span className="ml-1 rounded-full bg-amber-900/60 px-1.5 py-0.2 text-[10px] text-amber-200">
              {contradictionData.totalDetected}
            </span>
          )}
        </button>

        <button
          id="tab-evolution-btn"
          onClick={() => setActiveTab('evolution')}
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
            activeTab === 'evolution'
              ? 'bg-indigo-950/50 text-indigo-300 border border-indigo-800/60'
              : 'text-[#A1A1AA] hover:bg-[#1E1E22] hover:text-[#EDEDED]'
          }`}
        >
          <TrendingUp className="h-3.5 w-3.5" />
          <span>Personal Evolution</span>
        </button>

        <button
          id="tab-integrity-btn"
          onClick={() => setActiveTab('integrity')}
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
            activeTab === 'integrity'
              ? 'bg-emerald-950/50 text-emerald-300 border border-emerald-800/60'
              : 'text-[#A1A1AA] hover:bg-[#1E1E22] hover:text-[#EDEDED]'
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>Memory Integrity</span>
        </button>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-[#27272A] bg-[#161618] py-16 text-center">
          <div className="relative mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-950/40 border border-cyan-800/40">
            <RefreshCw className="h-6 w-6 animate-spin text-cyan-400" />
          </div>
          <h3 className="text-sm font-semibold text-[#EDEDED]">Extracting Evidence-Backed Insights...</h3>
          <p className="mt-1 text-xs text-[#71717A] max-w-sm">
            Evaluating candidate journal records with cryptographic token authentication and candidate verification.
          </p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="mb-6 rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-xs text-red-300">
          <div className="flex items-center gap-2 font-semibold">
            <ShieldAlert className="h-4 w-4 text-red-400" />
            <span>Analysis Notice</span>
          </div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* TAB 1: DECISION MEMORY */}
      {!loading && !error && activeTab === 'decisions' && (
        <div>
          {decisionData?.summary && (
            <div className="mb-6 rounded-2xl border border-cyan-900/40 bg-cyan-950/10 p-5">
              <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400">
                <Sparkles className="h-4 w-4" />
                <span>Decision Synthesis</span>
              </div>
              <p className="mt-2 text-sm text-[#D4D4D8] leading-relaxed">
                {decisionData.summary}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-4 text-[11px] text-[#71717A] border-t border-[#27272A] pt-3">
                <span>Verified Evidence Citations: <strong className="text-cyan-300">{decisionData.verifiedEvidenceCount}</strong></span>
                <span>Zero-Evidence Enforced: <strong className="text-emerald-400">Active</strong></span>
              </div>
            </div>
          )}

          {decisionData?.decisions?.length === 0 ? (
            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-12 text-center">
              <GitCommit className="mx-auto h-8 w-8 text-[#52525B]" />
              <h3 className="mt-3 text-sm font-semibold text-[#EDEDED]">No Explicit Decisions Detected</h3>
              <p className="mt-1 text-xs text-[#71717A] max-w-md mx-auto">
                Write entries describing choices you have made (e.g. project directions, personal commitments, technology choices) to track your decision landscape.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {decisionData?.decisions?.map((dec, idx) => (
                <div
                  key={dec.decisionId || idx}
                  className="rounded-2xl border border-[#27272A] bg-[#161618] p-5 transition hover:border-[#3F3F46]"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-[#27272A] px-2 py-0.5 text-[10px] font-mono text-[#A1A1AA]">
                        {dec.date || 'Historical'}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                          dec.status === 'active'
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                            : dec.status === 'completed'
                            ? 'bg-blue-950/60 text-blue-400 border border-blue-800/40'
                            : 'bg-zinc-800 text-zinc-300'
                        }`}
                      >
                        {dec.status}
                      </span>
                      <span className="rounded bg-cyan-950/50 text-cyan-300 px-1.5 py-0.5 text-[10px] border border-cyan-800/40">
                        {dec.confidence} confidence
                      </span>
                    </div>

                    {dec.entryTitle && (
                      <span className="flex items-center gap-1 text-[11px] text-[#A1A1AA]">
                        <BookOpen className="h-3 w-3 text-cyan-400" />
                        <span>Source: {dec.entryTitle}</span>
                      </span>
                    )}
                  </div>

                  <h3 className="mt-3 text-base font-semibold text-[#EDEDED]">
                    {dec.decision}
                  </h3>

                  {dec.reasoning && (
                    <p className="mt-2 text-xs text-[#A1A1AA] leading-relaxed">
                      <strong className="text-[#D4D4D8]">Rationale:</strong> {dec.reasoning}
                    </p>
                  )}

                  {dec.evidenceQuote && (
                    <div className="mt-3 rounded-xl border border-[#27272A] bg-[#121214] p-3 text-xs italic text-[#71717A]">
                      "{dec.evidenceQuote}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CONTRADICTION DETECTION */}
      {!loading && !error && activeTab === 'contradictions' && (
        <div>
          <div className="mb-4 rounded-xl border border-amber-900/40 bg-amber-950/10 p-3.5 text-xs text-amber-300/90">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
              <span>Neutral Perspective Analysis</span>
            </div>
            <p className="mt-1 text-[11px] text-amber-200/70">
              {contradictionData?.disclaimer || 'Identifies shifting priorities or evolving perspectives across journal entries. Not psychological diagnosis.'}
            </p>
          </div>

          {contradictionData?.contradictions?.length === 0 ? (
            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-12 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400" />
              <h3 className="mt-3 text-sm font-semibold text-[#EDEDED]">Consistent Perspectives Detected</h3>
              <p className="mt-1 text-xs text-[#71717A] max-w-md mx-auto">
                No significant conflicting commitments or contradictory stances found across your analyzed journal entries.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {contradictionData?.contradictions?.map((contra, idx) => (
                <div
                  key={contra.contradictionId || idx}
                  className="rounded-2xl border border-[#27272A] bg-[#161618] p-5"
                >
                  <div className="flex items-center justify-between border-b border-[#27272A] pb-3">
                    <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                      {contra.topic}
                    </span>
                    <span className="text-[10px] text-[#71717A]">
                      Dual-Entry Evidence Verified
                    </span>
                  </div>

                  {/* Earlier vs Later Comparison Grid */}
                  <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                    {/* Earlier stance */}
                    <div className="rounded-xl border border-[#27272A] bg-[#121214] p-3.5">
                      <div className="flex items-center justify-between text-[11px] text-[#71717A] mb-1.5">
                        <span className="font-semibold text-[#A1A1AA]">Earlier Position</span>
                        <span>{contra.earlierDate}</span>
                      </div>
                      <p className="text-xs text-[#D4D4D8] italic">
                        "{contra.earlierStatement}"
                      </p>
                    </div>

                    {/* Later stance */}
                    <div className="rounded-xl border border-amber-900/30 bg-amber-950/10 p-3.5">
                      <div className="flex items-center justify-between text-[11px] text-amber-400 mb-1.5">
                        <span className="font-semibold">Later Position</span>
                        <span>{contra.laterDate}</span>
                      </div>
                      <p className="text-xs text-[#D4D4D8] italic">
                        "{contra.laterStatement}"
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 text-xs text-[#A1A1AA] leading-relaxed">
                    <strong className="text-[#EDEDED]">Analysis:</strong> {contra.neutralAnalysis}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PERSONAL EVOLUTION */}
      {!loading && !error && activeTab === 'evolution' && (
        <div>
          {/* Custom Exploration Input */}
          <form onSubmit={handleRunEvolution} className="mb-6 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#71717A]" />
              <input
                id="evolution-query-input"
                type="text"
                value={evolutionQuery}
                onChange={(e) => setEvolutionQuery(e.target.value)}
                placeholder="Ask about your personal trajectory (e.g. 'How has my approach to work changed?')..."
                className="w-full rounded-xl border border-[#27272A] bg-[#161618] py-2.5 pl-9 pr-4 text-xs text-[#EDEDED] placeholder-[#71717A] focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <button
              id="submit-evolution-query-btn"
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 active:scale-98"
            >
              <span>Explore</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </form>

          {evolutionData && (
            <div>
              {/* Narrative Box */}
              <div className="mb-6 rounded-2xl border border-indigo-900/40 bg-indigo-950/10 p-5">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
                  <TrendingUp className="h-4 w-4" />
                  <span>Longitudinal Trajectory</span>
                </div>
                <h3 className="mt-1 text-sm font-semibold text-[#EDEDED]">
                  {evolutionData.trajectorySummary}
                </h3>
                <p className="mt-2 text-xs text-[#D4D4D8] leading-relaxed">
                  {evolutionData.synthesis}
                </p>
              </div>

              {/* Theme Breakdown */}
              <div className="grid gap-4">
                {evolutionData.evolutionItems?.map((item, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-[#27272A] bg-[#161618] p-5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#27272A] pb-3">
                      <h4 className="text-sm font-semibold text-[#EDEDED]">{item.theme}</h4>
                      <span className="rounded bg-indigo-950/60 text-indigo-300 px-2 py-0.5 text-[10px] border border-indigo-800/40">
                        {item.trend}
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <div className="rounded-xl border border-[#27272A] bg-[#121214] p-3">
                        <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Earlier Phase</span>
                        <p className="mt-1 text-xs text-[#A1A1AA]">{item.earlierPhase}</p>
                      </div>
                      <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/10 p-3">
                        <span className="text-[10px] uppercase tracking-wider text-indigo-400 font-semibold">Current Phase</span>
                        <p className="mt-1 text-xs text-[#D4D4D8]">{item.laterPhase}</p>
                      </div>
                    </div>

                    {/* Supporting Evidence Citations */}
                    {item.supportingEvidence?.length > 0 && (
                      <div className="mt-4 border-t border-[#27272A] pt-3">
                        <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Verified Citations</span>
                        <div className="mt-2 space-y-2">
                          {item.supportingEvidence.map((ev, evIdx) => (
                            <div key={evIdx} className="rounded-lg bg-[#121214] p-2.5 text-xs text-[#71717A]">
                              <span className="font-medium text-[#A1A1AA]">{ev.entryTitle}:</span> "{ev.quote}"
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: MEMORY INTEGRITY */}
      {!loading && !error && activeTab === 'integrity' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-5">
              <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Evidence Verification</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-400 font-mono">
                  {integrityStats?.verifiedEvidencePercentage ?? 100}%
                </span>
                <span className="text-[10px] text-emerald-500">Verified</span>
              </div>
              <p className="mt-1 text-[11px] text-[#71717A]">Against authorized tenant entries</p>
            </div>

            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-5">
              <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Authorized Verified</span>
              <div className="mt-2 text-2xl font-bold text-[#EDEDED] font-mono">
                {integrityStats?.authorizedEvidenceVerified ?? 0}
              </div>
              <p className="mt-1 text-[11px] text-[#71717A]">Citations cryptographic matches</p>
            </div>

            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-5">
              <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Unauthorized Blocked</span>
              <div className="mt-2 text-2xl font-bold text-amber-400 font-mono">
                {integrityStats?.unauthorizedEvidenceRejected ?? 0}
              </div>
              <p className="mt-1 text-[11px] text-[#71717A]">Hallucinated/cross-tenant rejected</p>
            </div>

            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-5">
              <span className="text-[10px] uppercase tracking-wider text-[#71717A] font-semibold">Zero-Evidence Filter</span>
              <div className="mt-2 text-2xl font-bold text-cyan-400 font-mono">
                {integrityStats?.zeroEvidenceEnforcement || 'ACTIVE'}
              </div>
              <p className="mt-1 text-[11px] text-[#71717A]">Ungrounded claims discarded</p>
            </div>
          </div>

          <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-6">
            <h3 className="text-sm font-semibold text-[#EDEDED] flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Zero-Trust Memory Verification Architecture</span>
            </h3>
            <p className="mt-2 text-xs text-[#A1A1AA] leading-relaxed">
              In Aegis Journal, Gemini is treated as an <strong>untrusted cognitive processor</strong> for authorization. The LLM cannot grant access to documents, hallucinate valid candidate citations, or bypass multi-tenant scoping. Every decision, contradiction, and evolution theme is strictly verified against Firestore document IDs authorized for the authenticated user session.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

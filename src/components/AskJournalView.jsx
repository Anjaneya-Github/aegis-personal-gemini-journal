import React, { useState } from 'react';
import { 
  Sparkles, 
  Search, 
  ShieldCheck, 
  Quote, 
  ExternalLink, 
  AlertCircle, 
  CheckCircle2, 
} from 'lucide-react';
import { askMyJournal } from '../services/aiJournalService';
import { MOODS } from '../constants/moods';

const SUGGESTED_QUESTIONS = [
  'What moments brought me the deepest sense of gratitude recently?',
  'What recurring challenges have I reflected on, and how did I respond?',
  'When have I felt most energized and inspired?',
  'What habits or routines have supported my peace of mind?',
];

export const AskJournalView = ({
  entries,
  onSelectEntryById,
  onNewEntry,
}) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState('');

  const handleSearch = async (targetQuery) => {
    const q = (targetQuery || query).trim();
    if (!q) return;

    setIsLoading(true);
    setError(null);
    setLastQuery(q);

    try {
      const res = await askMyJournal(q);
      setResult(res);
    } catch (err) {
      setError(err?.message || 'Failed to search your journal. Please try again.');
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header Banner */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-serif text-2xl font-bold tracking-tight text-[#EDEDED] sm:text-3xl">
                Ask My Journal
              </h2>
              <p className="text-xs text-[#A1A1AA]">
                Bounded retrieval & verified evidence-backed answers from your private thoughts
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 rounded-full bg-[#1E1E22] px-3 py-1 text-[11px] font-medium text-emerald-400 border border-emerald-900/40">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Candidate Guardrails Active</span>
          </div>
        </div>

        {/* Input Bar */}
        <div className="mt-6 flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#71717A]" />
            <input
              id="ask-journal-input"
              type="text"
              placeholder="Ask anything about your past entries, thoughts, or reflections..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              maxLength={400}
              className="w-full rounded-xl border border-[#27272A] bg-[#0F0F10] py-3 pl-10 pr-4 text-sm text-[#EDEDED] placeholder:text-[#71717A] focus:border-amber-400 focus:outline-none"
            />
          </div>
          <button
            id="ask-journal-submit-btn"
            onClick={() => handleSearch()}
            disabled={isLoading || !query.trim()}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#EDEDED] px-5 py-3 text-sm font-semibold text-[#0F0F10] transition hover:bg-white active:scale-98 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#0F0F10] border-t-transparent" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 text-[#0F0F10]" />
                <span>Ask Journal</span>
              </>
            )}
          </button>
        </div>

        {/* Suggested Queries */}
        <div className="mt-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#71717A]">
            Try asking:
          </span>
          <div className="mt-2 flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => {
                  setQuery(q);
                  handleSearch(q);
                }}
                disabled={isLoading}
                className="rounded-lg border border-[#27272A] bg-[#1E1E22] px-2.5 py-1.5 text-xs text-[#A1A1AA] transition hover:border-[#3F3F46] hover:text-[#EDEDED]"
              >
                "{q}"
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div
          id="ask-error-alert"
          className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-xs text-rose-300"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Main Answer Card */}
          <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-[#27272A] pb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#71717A]">
                Query: "{lastQuery}"
              </span>
              <div className="flex items-center gap-1 text-[11px] text-[#A1A1AA]">
                {result.sufficientContext ? (
                  <span className="inline-flex items-center gap-1 rounded bg-emerald-950/60 px-2 py-0.5 text-emerald-400 border border-emerald-800/60">
                    <CheckCircle2 className="h-3 w-3" />
                    {result.sources?.length || 0} Verified {(result.sources?.length || 0) === 1 ? 'Citation' : 'Citations'}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded bg-amber-950/60 px-2 py-0.5 text-amber-400 border border-amber-800/60">
                    <AlertCircle className="h-3 w-3" />
                    Insufficient Context Discard Rule Enforced
                  </span>
                )}
              </div>
            </div>

            {/* Answer Content */}
            <div className="mt-4 font-sans text-base leading-relaxed text-[#EDEDED]">
              {result.answer}
            </div>

            {/* Bounded retrieval footer stats */}
            {typeof result.totalCandidatesAnalyzed === 'number' && (
              <div className="mt-4 flex flex-wrap items-center gap-3 text-[11px] text-[#71717A]">
                <span>Analyzed {result.totalCandidatesAnalyzed} authorized journal entries</span>
                {result.rejectedSourceCount ? (
                  <>
                    <span>•</span>
                    <span className="text-amber-400/80">
                      Rejected {result.rejectedSourceCount} unauthorized or invalid citations
                    </span>
                  </>
                ) : null}
              </div>
            )}
          </div>

          {/* Validated Evidence Cards */}
          {result.sources && result.sources.length > 0 && (
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#A1A1AA]">
                <Quote className="h-3.5 w-3.5 text-amber-400" />
                <span>Substantiating Evidence & Journal Sources</span>
              </h3>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {result.sources.map((source, idx) => {
                  const mood = MOODS[source.mood] || MOODS.neutral;
                  return (
                    <div
                      key={`${source.entryId}-${idx}`}
                      className="group flex flex-col justify-between rounded-xl border border-[#27272A] bg-[#1E1E22] p-4 transition-all hover:border-[#3F3F46]"
                    >
                      <div>
                        {/* Source Entry Title and Meta */}
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${mood.bgClass} border ${mood.borderClass}`}
                          >
                            <span>{mood.emoji}</span>
                            <span>{mood.label}</span>
                          </span>
                          <span className="text-[11px] text-[#71717A]">{source.date}</span>
                        </div>

                        <h4 className="mt-2 font-serif text-base font-semibold text-[#EDEDED] group-hover:text-white">
                          {source.title}
                        </h4>

                        {/* Quoted Evidence */}
                        <blockquote className="mt-2 rounded-lg bg-[#161618] p-2.5 text-xs italic leading-relaxed text-[#A1A1AA] border-l-2 border-amber-400">
                          "{source.evidenceQuote}"
                        </blockquote>

                        {/* Relevance Note */}
                        <p className="mt-2 text-[11px] text-[#71717A]">
                          <strong>Relevance:</strong> {source.relevanceReason}
                        </p>
                      </div>

                      {/* Jump to Entry Button */}
                      <button
                        onClick={() => onSelectEntryById(source.entryId)}
                        className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-amber-400 hover:text-amber-300"
                      >
                        <span>Open Entry</span>
                        <ExternalLink className="h-3 w-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Insufficient context guide */}
          {!result.sufficientContext && (
            <div className="rounded-xl border border-[#27272A] bg-[#161618] p-5 text-center">
              <p className="text-xs text-[#A1A1AA]">
                Want to build richer reflections? Write more entries about your experiences, goals, and daily thoughts.
              </p>
              <button
                onClick={onNewEntry}
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-[#1E1E22] px-3 py-1.5 text-xs font-medium text-[#EDEDED] border border-[#27272A] hover:bg-[#26262B]"
              >
                <span>Write a new entry</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

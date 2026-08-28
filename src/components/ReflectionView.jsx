import React, { useState, useEffect } from 'react';
import { 
  Compass, 
  Sparkles, 
  RefreshCw, 
  TrendingUp, 
  Lightbulb, 
  ExternalLink, 
  BookOpen, 
  AlertCircle,
  PenTool
} from 'lucide-react';
import { getMyReflection } from '../services/aiJournalService';

export const ReflectionView = ({
  entries,
  onSelectEntryById,
  onWriteWithPrompt,
  onNewEntry,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [reflection, setReflection] = useState(null);
  const [error, setError] = useState(null);

  const fetchReflection = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getMyReflection();
      setReflection(res);
    } catch (err) {
      setError(err?.message || 'Failed to synthesize reflections. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (entries.length > 0) {
      fetchReflection();
    }
  }, [entries.length]);

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header Banner */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Compass className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-serif text-2xl font-bold tracking-tight text-[#EDEDED] sm:text-3xl">
                My Reflection
              </h2>
              <p className="text-xs text-[#A1A1AA]">
                Synthesizing patterns, emotional growth, and recurring themes across your entries
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="refresh-reflection-btn"
              onClick={fetchReflection}
              disabled={isLoading || entries.length === 0}
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#27272A] bg-[#1E1E22] px-3.5 py-2 text-xs font-medium text-[#EDEDED] transition hover:bg-[#26262B] active:scale-98 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Synthesizing...' : 'Regenerate'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-xs text-rose-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Empty State / Not enough entries */}
      {entries.length === 0 && (
        <div className="rounded-2xl border border-dashed border-[#27272A] bg-[#161618]/50 py-16 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#1E1E22] text-[#A1A1AA]">
            <BookOpen className="h-6 w-6" />
          </div>
          <h3 className="mt-4 font-serif text-xl font-semibold text-[#EDEDED]">
            No Journal Entries Yet
          </h3>
          <p className="mx-auto mt-2 max-w-sm text-xs leading-relaxed text-[#A1A1AA]">
            Write a few journal entries to unlock evidence-backed reflections, theme analysis, and personal growth insights.
          </p>
          <button
            onClick={onNewEntry}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#EDEDED] px-4 py-2.5 text-xs font-semibold text-[#0F0F10] transition hover:bg-white"
          >
            <PenTool className="h-3.5 w-3.5" />
            <span>Write Your First Entry</span>
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          <div className="animate-pulse rounded-2xl border border-[#27272A] bg-[#161618] p-6">
            <div className="h-4 w-1/3 rounded bg-[#27272A]" />
            <div className="mt-4 h-5 w-full rounded bg-[#27272A]" />
            <div className="mt-2 h-5 w-4/5 rounded bg-[#27272A]" />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse rounded-xl border border-[#27272A] bg-[#161618] p-5">
                <div className="h-4 w-1/2 rounded bg-[#27272A]" />
                <div className="mt-3 h-3 w-full rounded bg-[#27272A]" />
                <div className="mt-2 h-3 w-3/4 rounded bg-[#27272A]" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Reflection Content */}
      {!isLoading && reflection && (
        <div className="space-y-6">
          {/* Overarching Narrative */}
          {reflection.overallNarrative && (
            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-6 sm:p-8">
              <div className="flex items-center gap-2 border-b border-[#27272A] pb-3 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                <Sparkles className="h-4 w-4" />
                <span>Executive Synthesis</span>
              </div>
              <p className="mt-4 font-sans text-sm leading-relaxed text-[#EDEDED] sm:text-base">
                {reflection.overallNarrative}
              </p>

              {reflection.sentimentArc && (
                <div className="mt-6 rounded-xl border border-[#27272A] bg-[#1E1E22] p-4 text-xs">
                  <div className="flex items-center gap-2 text-[#A1A1AA] font-semibold">
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Emotional & Sentiment Trajectory:</span>
                  </div>
                  <p className="mt-1.5 leading-relaxed text-[#EDEDED]">
                    {reflection.sentimentArc}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Growth Themes & Evidence */}
          {reflection.growthThemes && reflection.growthThemes.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#A1A1AA]">
                  Identified Themes & Evidence Citations
                </h3>
                <span className="text-[11px] text-[#71717A]">
                  Analyzed {reflection.totalEntriesAnalyzed || entries.length} entries
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {reflection.growthThemes.map((themeItem, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between rounded-xl border border-[#27272A] bg-[#161618] p-5"
                  >
                    <div>
                      <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-950/80 text-[10px] text-indigo-400 border border-indigo-800/60">
                          {idx + 1}
                        </span>
                        <span>{themeItem.theme}</span>
                      </div>

                      <p className="mt-2 text-xs leading-relaxed text-[#A1A1AA]">
                        {themeItem.insight}
                      </p>

                      {/* Evidence Citations */}
                      {themeItem.evidence && themeItem.evidence.length > 0 && (
                        <div className="mt-3 space-y-2 border-t border-[#27272A] pt-3">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#71717A]">
                            Direct Evidence:
                          </span>
                          {themeItem.evidence.map((ev, eIdx) => (
                            <div
                              key={eIdx}
                              className="rounded-lg bg-[#1E1E22] p-2.5 text-xs text-[#EDEDED] border-l-2 border-indigo-400"
                            >
                              <p className="italic leading-relaxed text-[#EDEDED]">"{ev.quote}"</p>
                              <div className="mt-1 flex items-center justify-between">
                                <span className="text-[10px] text-[#71717A] truncate max-w-[180px]">
                                  From: {ev.entryTitle}
                                </span>
                                <button
                                  onClick={() => onSelectEntryById(ev.entryId)}
                                  className="inline-flex items-center gap-1 text-[10px] font-semibold text-indigo-400 hover:text-indigo-300"
                                >
                                  <span>View</span>
                                  <ExternalLink className="h-2.5 w-2.5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Next Prompt */}
          {reflection.suggestedPrompt && (
            <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-[#161618] to-[#161618] p-6">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                <Lightbulb className="h-4 w-4" />
                <span>Mindful Reflection Prompt</span>
              </div>
              <p className="mt-2 font-serif text-lg font-semibold text-[#EDEDED]">
                "{reflection.suggestedPrompt}"
              </p>
              <div className="mt-4">
                <button
                  id="write-from-prompt-btn"
                  onClick={() => onWriteWithPrompt(reflection.suggestedPrompt || '')}
                  className="inline-flex items-center gap-2 rounded-xl bg-amber-400 px-4 py-2 text-xs font-semibold text-stone-950 transition hover:bg-amber-300"
                >
                  <PenTool className="h-3.5 w-3.5" />
                  <span>Write Entry from this Prompt</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React, { useState, useMemo } from 'react';
import { Search, Plus, Edit2, Trash2, BookOpen, Sparkles, Compass, MessageSquare } from 'lucide-react';
import { MOODS } from '../constants/moods';
import { JournalStats } from './JournalStats';

export const JournalList = ({
  entries,
  isLoading,
  onSelectEntry,
  onEditEntry,
  onDeleteEntry,
  onNewEntry,
  onNavigateToAsk,
  onNavigateToReflect,
  onNavigateToCompanion,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMood, setSelectedMood] = useState('all');
  const [selectedTag, setSelectedTag] = useState(null);

  // Extract all unique tags
  const allTags = useMemo(() => {
    const tagSet = new Set();
    entries.forEach((e) => {
      (e.tags || []).forEach((t) => tagSet.add(t));
    });
    return Array.from(tagSet).sort();
  }, [entries]);

  // Filtered and sorted entries
  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const matchesSearch =
        !searchQuery ||
        entry.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.content.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesMood = selectedMood === 'all' || entry.mood === selectedMood;
      const matchesTag = !selectedTag || (entry.tags && entry.tags.includes(selectedTag));

      return matchesSearch && matchesMood && matchesTag;
    });
  }, [entries, searchQuery, selectedMood, selectedTag]);

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Stats summary */}
      <JournalStats entries={entries} />

      {/* Quick AI Exploration Toolbar */}
      {entries.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {onNavigateToAsk && (
            <button
              onClick={onNavigateToAsk}
              className="flex items-center gap-3 rounded-2xl border border-[#27272A] bg-[#161618] p-3.5 text-left transition hover:border-amber-500/40 hover:bg-[#1E1E22]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#EDEDED]">Ask My Journal</div>
                <div className="text-[11px] text-[#71717A]">Evidence-backed Q&A</div>
              </div>
            </button>
          )}

          {onNavigateToReflect && (
            <button
              onClick={onNavigateToReflect}
              className="flex items-center gap-3 rounded-2xl border border-[#27272A] bg-[#161618] p-3.5 text-left transition hover:border-indigo-500/40 hover:bg-[#1E1E22]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400">
                <Compass className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#EDEDED]">My Reflections</div>
                <div className="text-[11px] text-[#71717A]">Themes & growth trajectory</div>
              </div>
            </button>
          )}

          {onNavigateToCompanion && (
            <button
              onClick={onNavigateToCompanion}
              className="flex items-center gap-3 rounded-2xl border border-[#27272A] bg-[#161618] p-3.5 text-left transition hover:border-purple-500/40 hover:bg-[#1E1E22]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
                <MessageSquare className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#EDEDED]">Journal Companion</div>
                <div className="text-[11px] text-[#71717A]">Mindful dialogue & auto-draft</div>
              </div>
            </button>
          )}
        </div>
      )}

      {/* Control Bar: Search & Filter */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#27272A] bg-[#161618] p-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Search Field */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#71717A]" />
          <input
            id="journal-search-input"
            type="text"
            placeholder="Search entries by title or thoughts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-[#27272A] bg-[#0F0F10] py-2 pl-9 pr-4 text-xs text-[#EDEDED] placeholder:text-[#71717A] focus:border-[#EDEDED] focus:outline-none"
          />
        </div>

        {/* Mood Filter Pill Dropdown */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            id="mood-filter-select"
            value={selectedMood}
            onChange={(e) => setSelectedMood(e.target.value)}
            className="rounded-xl border border-[#27272A] bg-[#0F0F10] px-3 py-2 text-xs font-medium text-[#A1A1AA] focus:border-[#EDEDED] focus:outline-none"
          >
            <option value="all">All Sentiments</option>
            {Object.keys(MOODS).map((m) => (
              <option key={m} value={m}>
                {MOODS[m].emoji} {MOODS[m].label}
              </option>
            ))}
          </select>

          {allTags.length > 0 && (
            <select
              id="tag-filter-select"
              value={selectedTag || ''}
              onChange={(e) => setSelectedTag(e.target.value ? e.target.value : null)}
              className="rounded-xl border border-[#27272A] bg-[#0F0F10] px-3 py-2 text-xs font-medium text-[#A1A1AA] focus:border-[#EDEDED] focus:outline-none"
            >
              <option value="">All Tags ({allTags.length})</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>
                  #{tag}
                </option>
              ))}
            </select>
          )}

          {(searchQuery || selectedMood !== 'all' || selectedTag) && (
            <button
              id="reset-filters-btn"
              onClick={() => {
                setSearchQuery('');
                setSelectedMood('all');
                setSelectedTag(null);
              }}
              className="rounded-xl px-2.5 py-2 text-xs font-medium text-[#71717A] hover:text-[#EDEDED]"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4 py-8">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-2xl border border-[#27272A] bg-[#161618] p-6"
            >
              <div className="h-4 w-1/4 rounded bg-[#27272A]" />
              <div className="mt-4 h-6 w-3/4 rounded bg-[#27272A]" />
              <div className="mt-2 h-4 w-full rounded bg-[#27272A]" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && entries.length === 0 && (
        <div className="rounded-2xl border border-dashed border-[#27272A] bg-[#161618]/50 py-16 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1E1E22] text-[#A1A1AA]">
            <BookOpen className="h-7 w-7" />
          </div>
          <h3 className="mt-4 font-serif text-xl font-semibold text-[#EDEDED]">
            Your journal is waiting
          </h3>
          <p className="mx-auto mt-2 max-w-sm text-xs leading-relaxed text-[#A1A1AA]">
            Capture your reflections, thoughts, and moments. Everything is privately isolated and secured under your account.
          </p>
          <button
            id="empty-state-new-entry-btn"
            onClick={onNewEntry}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#EDEDED] px-4 py-2.5 text-xs font-semibold text-[#0F0F10] transition hover:bg-white active:scale-98"
          >
            <Plus className="h-4 w-4" />
            <span>Write First Entry</span>
          </button>
        </div>
      )}

      {/* Filter with No Results */}
      {!isLoading && entries.length > 0 && filteredEntries.length === 0 && (
        <div className="rounded-2xl border border-[#27272A] bg-[#161618] py-12 text-center">
          <p className="text-xs text-[#A1A1AA]">
            No journal entries match your active search filters.
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedMood('all');
              setSelectedTag(null);
            }}
            className="mt-3 text-xs font-semibold text-[#EDEDED] underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Entry Cards List */}
      {!isLoading && filteredEntries.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#71717A]">
              {filteredEntries.length} {filteredEntries.length === 1 ? 'Entry' : 'Entries'}
            </span>
          </div>

          {filteredEntries.map((entry) => {
            const mood = MOODS[entry.mood] || MOODS.neutral;
            const date = new Date(entry.createdAt);
            const dateString = date.toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });
            const timeString = date.toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={entry.id}
                id={`journal-card-${entry.id}`}
                onClick={() => onSelectEntry(entry)}
                className="group relative cursor-pointer rounded-2xl border border-[#27272A] bg-[#161618] p-5 transition-all hover:border-[#3F3F46] hover:bg-[#1A1A1D]"
              >
                {/* Top Meta Line */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${mood.bgClass} border ${mood.borderClass}`}
                    >
                      <span>{mood.emoji}</span>
                      <span>{mood.label}</span>
                    </span>
                    <span className="text-xs text-[#71717A]">•</span>
                    <span className="text-xs text-[#71717A]">
                      {dateString} at {timeString}
                    </span>
                  </div>

                  {/* Actions on card hover */}
                  <div
                    className="flex items-center gap-1 opacity-90 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      id={`edit-card-btn-${entry.id}`}
                      onClick={() => onEditEntry(entry)}
                      title="Edit Entry"
                      className="rounded-lg p-1.5 text-[#71717A] hover:bg-[#27272A] hover:text-[#EDEDED]"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      id={`delete-card-btn-${entry.id}`}
                      onClick={() => onDeleteEntry(entry)}
                      title="Delete Entry"
                      className="rounded-lg p-1.5 text-[#71717A] hover:bg-rose-950/40 hover:text-rose-400"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Entry Title */}
                <h3 className="mt-3 font-serif text-xl font-bold text-[#EDEDED] transition group-hover:text-white">
                  {entry.title}
                </h3>

                {/* Snippet Preview */}
                <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-[#A1A1AA]">
                  {entry.content}
                </p>

                {/* Bottom Footer (Tags & Word Count) */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[#27272A] pt-3">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {(entry.tags || []).map((t) => (
                      <span
                        key={t}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTag(t);
                        }}
                        className="rounded-md bg-[#1E1E22] px-2 py-0.5 text-[11px] font-medium text-[#A1A1AA] hover:bg-[#27272A] hover:text-[#EDEDED]"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>

                  <span className="text-[11px] text-[#71717A]">
                    {entry.wordCount} words
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

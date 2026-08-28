import React from 'react';
import { BookOpen, Flame, PenTool, Sparkles } from 'lucide-react';
import { MOODS } from '../constants/moods';

export const JournalStats = ({ entries }) => {
  const totalEntries = entries.length;
  const totalWords = entries.reduce((acc, curr) => acc + (curr.wordCount || 0), 0);

  // Entries written within the last 7 days
  const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const entriesThisWeek = entries.filter((e) => e.createdAt >= oneWeekAgo).length;

  // Most frequent mood
  const moodCounts = {};
  entries.forEach((e) => {
    moodCounts[e.mood] = (moodCounts[e.mood] || 0) + 1;
  });

  let topMoodKey = 'serene';
  let topMoodCount = 0;
  Object.entries(moodCounts).forEach(([mood, count]) => {
    if (count > topMoodCount) {
      topMoodCount = count;
      topMoodKey = mood;
    }
  });

  const topMood = MOODS[topMoodKey] || MOODS.serene;

  if (totalEntries === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {/* Metric 1: Total Entries */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4">
        <div className="flex items-center gap-2 text-[#71717A]">
          <BookOpen className="h-4 w-4" />
          <span className="text-xs font-medium">Total Entries</span>
        </div>
        <div className="mt-2 font-serif text-2xl font-bold text-[#EDEDED]">
          {totalEntries}
        </div>
      </div>

      {/* Metric 2: Total Words */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4">
        <div className="flex items-center gap-2 text-[#71717A]">
          <PenTool className="h-4 w-4" />
          <span className="text-xs font-medium">Words Written</span>
        </div>
        <div className="mt-2 font-serif text-2xl font-bold text-[#EDEDED]">
          {totalWords.toLocaleString()}
        </div>
      </div>

      {/* Metric 3: Recent Activity */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4">
        <div className="flex items-center gap-2 text-[#71717A]">
          <Flame className="h-4 w-4 text-amber-400" />
          <span className="text-xs font-medium">This Week</span>
        </div>
        <div className="mt-2 font-serif text-2xl font-bold text-[#EDEDED]">
          {entriesThisWeek} {entriesThisWeek === 1 ? 'entry' : 'entries'}
        </div>
      </div>

      {/* Metric 4: Primary Mood */}
      <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4">
        <div className="flex items-center gap-2 text-[#71717A]">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-medium">Dominant Sentiment</span>
        </div>
        <div className="mt-2 flex items-center gap-1.5 font-sans text-sm font-semibold text-[#EDEDED]">
          <span className="text-base">{topMood.emoji}</span>
          <span className="truncate">{topMood.label}</span>
        </div>
      </div>
    </div>
  );
};

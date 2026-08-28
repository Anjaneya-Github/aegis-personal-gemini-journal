import React from 'react';
import { ArrowLeft, Edit3, Trash2, Calendar, Clock, Tag } from 'lucide-react';
import { MOODS } from '../constants/moods';

export const JournalDetail = ({
  entry,
  onBack,
  onEdit,
  onDeleteRequest,
}) => {
  const moodInfo = MOODS[entry.mood] || MOODS.neutral;
  const createdDate = new Date(entry.createdAt);
  const formattedDate = createdDate.toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
  const formattedTime = createdDate.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
      {/* Navigation & Controls */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-[#27272A] pb-4">
        <button
          id="detail-back-btn"
          onClick={onBack}
          className="inline-flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-[#A1A1AA] transition hover:bg-[#1E1E22] hover:text-[#EDEDED] focus:outline-none"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Journal</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            id="detail-edit-btn"
            onClick={() => onEdit(entry)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#27272A] bg-[#1E1E22] px-3 py-1.5 text-xs font-medium text-[#EDEDED] shadow-2xs transition hover:bg-[#26262B] hover:border-[#3F3F46]"
          >
            <Edit3 className="h-3.5 w-3.5" />
            <span>Edit</span>
          </button>
          <button
            id="detail-delete-btn"
            onClick={() => onDeleteRequest(entry)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-rose-900/60 bg-[#1E1E22] px-3 py-1.5 text-xs font-medium text-rose-400 shadow-2xs transition hover:bg-rose-950/40"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Main Journal Article Content */}
      <article className="rounded-2xl border border-[#27272A] bg-[#161618] p-6 shadow-sm sm:p-8">
        {/* Mood & Meta Header */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${moodInfo.bgClass} border ${moodInfo.borderClass}`}
          >
            <span>{moodInfo.emoji}</span>
            <span>{moodInfo.label}</span>
          </span>

          <div className="flex items-center gap-1.5 text-xs text-[#71717A]">
            <Calendar className="h-3.5 w-3.5" />
            <span>{formattedDate}</span>
            <span>•</span>
            <Clock className="h-3.5 w-3.5" />
            <span>{formattedTime}</span>
          </div>

          <span className="text-xs text-[#71717A]">
            {entry.wordCount} words
          </span>
        </div>

        {/* Title */}
        <h1 className="mb-6 font-serif text-3xl font-bold tracking-tight text-[#EDEDED] sm:text-4xl">
          {entry.title}
        </h1>

        {/* Content */}
        <div className="font-sans text-base leading-relaxed text-[#EDEDED] whitespace-pre-wrap">
          {entry.content}
        </div>

        {/* Tags */}
        {entry.tags && entry.tags.length > 0 && (
          <div className="mt-8 border-t border-[#27272A] pt-4">
            <div className="flex flex-wrap items-center gap-1.5">
              <Tag className="h-3.5 w-3.5 text-[#71717A]" />
              {entry.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-md bg-[#1E1E22] px-2 py-0.5 text-xs text-[#A1A1AA] border border-[#27272A]"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </article>
    </div>
  );
};

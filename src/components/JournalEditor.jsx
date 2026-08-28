import React, { useState } from 'react';
import { ArrowLeft, Save, Tag, X } from 'lucide-react';
import { MOODS } from '../constants/moods';
import { calculateWordCount } from '../services/journalService';

export const JournalEditor = ({
  initialEntry,
  initialDraft,
  onSave,
  onCancel,
  isSaving,
}) => {
  const [title, setTitle] = useState(initialEntry?.title || initialDraft?.title || '');
  const [content, setContent] = useState(initialEntry?.content || initialDraft?.content || '');
  const [mood, setMood] = useState(
    initialEntry?.mood || initialDraft?.mood || 'serene'
  );
  const [tags, setTags] = useState(
    initialEntry?.tags || initialDraft?.tags || []
  );
  const [tagInput, setTagInput] = useState('');
  const [error, setError] = useState(null);

  const wordCount = calculateWordCount(content);
  const readingTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));

  const handleAddTag = (e) => {
    if ('key' in e && e.key !== 'Enter' && e.key !== ',') return;
    e.preventDefault();
    const cleanTag = tagInput.trim().toLowerCase().replace(/^[#,]+/, '');
    if (cleanTag && !tags.includes(cleanTag)) {
      setTags([...tags, cleanTag]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() && !content.trim()) {
      setError('Please add a title or write some thoughts before saving.');
      return;
    }

    try {
      setError(null);
      await onSave({
        title: title.trim() || 'Untitled Journal Entry',
        content: content.trim(),
        mood,
        tags,
      });
    } catch (err) {
      setError(err?.message || 'Failed to save journal entry. Please try again.');
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
      {/* Top Header / Actions */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-[#27272A] pb-4">
        <button
          id="editor-back-btn"
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-[#A1A1AA] transition hover:bg-[#1E1E22] hover:text-[#EDEDED] focus:outline-none"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Journal</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[#71717A]">
            {wordCount} {wordCount === 1 ? 'word' : 'words'} • ~{readingTimeMinutes} min read
          </span>
          <button
            id="editor-save-btn"
            onClick={handleSubmit}
            disabled={isSaving}
            className="inline-flex items-center gap-1.5 rounded-xl bg-[#EDEDED] px-4 py-2 text-xs font-semibold text-[#0F0F10] shadow-sm transition hover:bg-white active:scale-98 disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-stone-800 border-t-transparent" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="h-3.5 w-3.5" />
                <span>{initialEntry ? 'Update Entry' : 'Save Entry'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div
          id="editor-error-alert"
          className="mb-6 rounded-xl border border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300"
        >
          {error}
        </div>
      )}

      {/* Main Form Canvas */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Mood Selector */}
        <div>
          <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-[#71717A]">
            Current Sentiment & Mood
          </label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-6">
            {Object.keys(MOODS).map((key) => {
              const item = MOODS[key];
              const isSelected = mood === key;
              return (
                <button
                  type="button"
                  key={key}
                  id={`mood-btn-${key}`}
                  onClick={() => setMood(key)}
                  className={`flex flex-col items-center justify-center gap-1 rounded-xl border p-2.5 text-center transition-all ${
                    isSelected
                      ? 'border-[#EDEDED] bg-[#1E1E22] ring-1 ring-[#EDEDED]'
                      : 'border-[#27272A] bg-[#161618] hover:border-[#3F3F46] hover:bg-[#1A1A1D]'
                  }`}
                >
                  <span className="text-xl">{item.emoji}</span>
                  <span className="text-[11px] font-medium text-[#EDEDED]">
                    {item.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Title Input */}
        <div>
          <input
            id="journal-title-input"
            type="text"
            placeholder="Give your entry a reflective title..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border-b border-[#27272A] bg-transparent py-2 font-serif text-2xl font-semibold text-[#EDEDED] placeholder:text-[#71717A] focus:border-[#EDEDED] focus:outline-none sm:text-3xl"
          />
        </div>

        {/* Content Textarea */}
        <div>
          <textarea
            id="journal-content-input"
            rows={14}
            placeholder="Write your thoughts freely. What is happening in your life? What feelings or ideas want to be expressed today?"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full resize-y rounded-2xl border border-[#27272A] bg-[#161618] p-5 font-sans text-sm leading-relaxed text-[#EDEDED] placeholder:text-[#71717A] focus:border-[#EDEDED] focus:outline-none"
          />
        </div>

        {/* Tags Section */}
        <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4">
          <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-[#71717A]">
            Tags & Themes
          </label>
          <div className="flex flex-wrap items-center gap-2">
            {tags.map((t) => (
              <span
                key={t}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#1E1E22] px-2.5 py-1 text-xs text-[#EDEDED] border border-[#27272A]"
              >
                <span>#{t}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(t)}
                  className="text-[#71717A] hover:text-rose-400"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}

            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Add a tag..."
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                className="rounded-lg border border-[#27272A] bg-[#0F0F10] px-2.5 py-1 text-xs text-[#EDEDED] placeholder:text-[#71717A] focus:border-[#EDEDED] focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="rounded-lg bg-[#1E1E22] px-2.5 py-1 text-xs font-medium text-[#EDEDED] border border-[#27272A] hover:bg-[#27272A]"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

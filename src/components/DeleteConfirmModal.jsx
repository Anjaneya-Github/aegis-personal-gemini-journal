import React from 'react';
import { AlertTriangle, Trash2 } from 'lucide-react';

export const DeleteConfirmModal = ({
  entry,
  isOpen,
  isDeleting,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen || !entry) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <div className="w-full max-w-md rounded-2xl border border-[#27272A] bg-[#161618] p-6 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-950/60 text-rose-400 border border-rose-800/60">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-[#EDEDED]">
              Delete Journal Entry?
            </h3>
            <p className="text-xs text-[#71717A]">
              This action cannot be undone.
            </p>
          </div>
        </div>

        <div className="my-4 rounded-xl bg-[#0F0F10] p-3 text-xs text-[#A1A1AA] border border-[#27272A]">
          <span className="font-semibold text-[#EDEDED]">"{entry.title}"</span>
        </div>

        <div className="flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onCancel}
            disabled={isDeleting}
            className="rounded-xl px-3.5 py-2 text-xs font-medium text-[#A1A1AA] hover:bg-[#1E1E22] hover:text-[#EDEDED]"
          >
            Cancel
          </button>
          <button
            type="button"
            id="confirm-delete-btn"
            onClick={onConfirm}
            disabled={isDeleting}
            className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-rose-500 disabled:opacity-50"
          >
            {isDeleting ? (
              <>
                <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Deleting...</span>
              </>
            ) : (
              <>
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Entry</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

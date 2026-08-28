import React from 'react';
import { ShieldCheck, CheckCircle2, X } from 'lucide-react';

export const SecurityNotice = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const rules = [
    {
      id: 1,
      title: 'Firebase Authentication with Google Sign-In',
      desc: 'Users authenticate directly with cryptographically signed Google identity tokens.',
      status: 'Active',
    },
    {
      id: 2,
      title: 'Private Firestore Partitioning',
      desc: 'All entries are strictly isolated under /users/{uid}/ guarded by Firestore security rules.',
      status: 'Enforced',
    },
    {
      id: 3,
      title: 'Zero Client-Supplied UID Trust',
      desc: 'The server verifies Firebase ID tokens with Firebase Admin. Client-provided UIDs are never trusted.',
      status: 'Enforced',
    },
    {
      id: 4,
      title: 'Bounded Retrieval & Candidate Guardrails',
      desc: 'Gemini queries are bounded strictly to authorized candidate entries. Gemini is never an authorization authority.',
      status: 'Enforced',
    },
    {
      id: 5,
      title: 'Source ID Validation & Zero-Evidence Discard',
      desc: 'All model-returned source IDs are verified against the backend candidate set. Answers with zero verified evidence are rejected.',
      status: 'Enforced',
    },
    {
      id: 6,
      title: 'Zero Secret & Content Logging',
      desc: 'Gemini API keys remain server-side. Journal entries, tokens, and authorization headers are never logged.',
      status: 'Enforced',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <div className="w-full max-w-2xl rounded-2xl border border-[#27272A] bg-[#161618] p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#27272A] pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-[#EDEDED]">
                Security & Privacy Architecture
              </h2>
              <p className="text-xs text-[#71717A]">
                Specification Verification & Zero-Trust Guarantees
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-[#71717A] hover:bg-[#1E1E22] hover:text-[#EDEDED]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="my-4 max-h-[60vh] space-y-3 overflow-y-auto pr-1">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-start gap-3 rounded-xl border border-[#27272A] bg-[#0F0F10] p-3 text-xs"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <div className="flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-[#EDEDED]">
                    {rule.title}
                  </span>
                  <span className="rounded bg-emerald-950/80 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-800/60">
                    {rule.status}
                  </span>
                </div>
                <p className="mt-0.5 leading-relaxed text-[#A1A1AA]">
                  {rule.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end pt-3 border-t border-[#27272A]">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-[#EDEDED] px-4 py-2 text-xs font-semibold text-[#0F0F10] hover:bg-white"
          >
            Close Overview
          </button>
        </div>
      </div>
    </div>
  );
};

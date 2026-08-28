import React, { useState } from 'react';
import { BookOpen, ShieldCheck, Lock, Sparkles } from 'lucide-react';
import { signInWithGoogle } from '../lib/firebase';

export const AuthScreen = ({ onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await signInWithGoogle();
      if (onSuccess) onSuccess();
    } catch (err) {
      if (err?.code !== 'auth/popup-closed-by-user') {
        setErrorMessage('Unable to complete Google Sign-In. Please check popup permissions and retry.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-65px)] items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="relative rounded-2xl border border-[#27272A] bg-[#161618] p-8 shadow-2xl">
          {/* Header Icon */}
          <div className="mb-6 flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#EDEDED] text-[#0F0F10] shadow-md">
              <BookOpen className="h-7 w-7" />
            </div>
          </div>

          <div className="text-center">
            <h1 className="font-serif text-2xl font-bold tracking-tight text-[#EDEDED] sm:text-3xl">
              Personal Gemini Journal
            </h1>
            <p className="mt-2 text-xs leading-relaxed text-[#A1A1AA]">
              Your private sanctuary for thoughtful reflection, daily journaling, and evidence-backed AI synthesis.
            </p>
          </div>

          {/* Privacy & Architecture Guarantees */}
          <div className="my-6 space-y-2.5 rounded-xl border border-[#27272A] bg-[#0F0F10] p-4 text-xs">
            <div className="flex items-start gap-2.5 text-[#EDEDED]">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <span>
                <strong className="text-white">Private Firestore Scoping:</strong> Data strictly isolated under{' '}
                <code className="rounded bg-[#1E1E22] px-1 py-0.5 text-[11px] text-emerald-300">
                  /users/{'{uid}'}/
                </code>
              </span>
            </div>
            <div className="flex items-start gap-2.5 text-[#EDEDED]">
              <Lock className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
              <span>
                <strong className="text-white">Zero Client Trust:</strong> Authentication verified cryptographically on the server.
              </span>
            </div>
            <div className="flex items-start gap-2.5 text-[#EDEDED]">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
              <span>
                <strong className="text-white">Evidence Guardrails:</strong> AI queries strictly validated against authorized candidate sets.
              </span>
            </div>
          </div>

          {/* Error notice */}
          {errorMessage && (
            <div
              id="auth-error-banner"
              className="mb-5 rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300"
            >
              {errorMessage}
            </div>
          )}

          {/* Action Button */}
          <div className="mt-6">
            <button
              id="google-signin-btn"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-[#27272A] bg-[#1E1E22] px-4 py-3 text-sm font-semibold text-[#EDEDED] transition hover:bg-[#26262B] hover:border-[#3F3F46] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-stone-400 border-t-transparent" />
                  <span>Signing in with Google...</span>
                </div>
              ) : (
                <>
                  <svg className="h-4 w-4" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <span>Continue with Google</span>
                </>
              )}
            </button>
          </div>

          {/* Footer note */}
          <div className="mt-6 text-center text-[11px] text-[#71717A]">
            Sign in securely using your Google account to access your personal journal.
          </div>
        </div>
      </div>
    </div>
  );
};

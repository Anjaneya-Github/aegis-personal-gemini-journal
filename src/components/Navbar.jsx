import React from 'react';
import { 
  BookOpen, 
  Sparkles, 
  Compass, 
  MessageSquare, 
  Plus, 
  Lock, 
  LogOut, 
} from 'lucide-react';

export const Navbar = ({
  user,
  activeView,
  onChangeView,
  onNewEntry,
  onSignOut,
  onOpenSecurityModal,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-[#27272A] bg-[#161618]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <button
            id="brand-logo-btn"
            onClick={() => onChangeView('list')}
            className="flex items-center gap-2.5 text-left transition-opacity hover:opacity-85 focus:outline-none"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#EDEDED] text-[#0F0F10] shadow-sm">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <span className="font-serif text-lg font-bold tracking-tight text-[#EDEDED]">
                Gemini Journal
              </span>
              <span className="ml-2 hidden rounded bg-[#27272A] px-1.5 py-0.5 text-[10px] font-medium tracking-wide uppercase text-[#A1A1AA] sm:inline">
                Private
              </span>
            </div>
          </button>
        </div>

        {/* View Tabs */}
        {user && (
          <nav className="hidden items-center gap-1 md:flex">
            <button
              id="nav-tab-entries"
              onClick={() => onChangeView('list')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                activeView === 'list' || activeView === 'detail' || activeView === 'editor'
                  ? 'bg-[#1E1E22] text-[#EDEDED] border border-[#27272A]'
                  : 'text-[#A1A1AA] hover:bg-[#1E1E22]/60 hover:text-[#EDEDED]'
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Entries</span>
            </button>

            <button
              id="nav-tab-ask"
              onClick={() => onChangeView('ask')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                activeView === 'ask'
                  ? 'bg-amber-950/40 text-amber-300 border border-amber-800/60'
                  : 'text-[#A1A1AA] hover:bg-[#1E1E22]/60 hover:text-amber-300'
              }`}
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
              <span>Ask Journal</span>
            </button>

            <button
              id="nav-tab-reflect"
              onClick={() => onChangeView('reflect')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                activeView === 'reflect'
                  ? 'bg-indigo-950/40 text-indigo-300 border border-indigo-800/60'
                  : 'text-[#A1A1AA] hover:bg-[#1E1E22]/60 hover:text-indigo-300'
              }`}
            >
              <Compass className="h-3.5 w-3.5 text-indigo-400" />
              <span>Reflections</span>
            </button>

            <button
              id="nav-tab-companion"
              onClick={() => onChangeView('companion')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                activeView === 'companion'
                  ? 'bg-purple-950/40 text-purple-300 border border-purple-800/60'
                  : 'text-[#A1A1AA] hover:bg-[#1E1E22]/60 hover:text-purple-300'
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5 text-purple-400" />
              <span>Companion</span>
            </button>
          </nav>
        )}

        {/* Actions & User */}
        <div className="flex items-center gap-2">
          {user && (
            <>
              {activeView !== 'editor' && (
                <button
                  id="navbar-new-entry-btn"
                  onClick={onNewEntry}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-[#EDEDED] px-3 py-2 text-xs font-semibold text-[#0F0F10] transition hover:bg-white active:scale-98"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Write Entry</span>
                </button>
              )}

              <button
                id="navbar-security-audit-btn"
                onClick={onOpenSecurityModal}
                title="View Security & Privacy Architecture"
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#27272A] bg-[#1E1E22] px-2.5 py-2 text-xs font-medium text-[#A1A1AA] transition hover:border-[#3F3F46] hover:text-[#EDEDED]"
              >
                <Lock className="h-3.5 w-3.5 text-emerald-400" />
                <span className="hidden lg:inline">Private & Scoped</span>
              </button>

              {/* User Profile Pill */}
              <div className="flex items-center gap-2 pl-2 border-l border-[#27272A]">
                {user.photoURL ? (
                  <img
                    id="user-avatar-img"
                    src={user.photoURL}
                    alt={user.displayName || 'User'}
                    className="h-8 w-8 rounded-full border border-[#27272A] object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div
                    id="user-avatar-fallback"
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1E1E22] font-medium text-[#EDEDED] text-xs border border-[#27272A]"
                  >
                    {(user.displayName || user.email || 'U')[0].toUpperCase()}
                  </div>
                )}

                <div className="hidden flex-col text-left xl:flex">
                  <span className="max-w-[120px] truncate text-xs font-semibold text-[#EDEDED]">
                    {user.displayName || 'Journalist'}
                  </span>
                  <span className="max-w-[120px] truncate text-[10px] text-[#71717A]">
                    {user.email}
                  </span>
                </div>

                <button
                  id="navbar-signout-btn"
                  onClick={onSignOut}
                  title="Sign out securely"
                  className="rounded-lg p-2 text-[#71717A] transition hover:bg-[#1E1E22] hover:text-[#EDEDED] focus:outline-none"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Mobile Sub-Navigation Bar */}
      {user && (
        <div className="flex items-center justify-around border-t border-[#27272A] bg-[#161618] px-2 py-2 md:hidden">
          <button
            onClick={() => onChangeView('list')}
            className={`flex flex-col items-center gap-0.5 text-[11px] ${
              activeView === 'list' || activeView === 'detail' || activeView === 'editor'
                ? 'text-[#EDEDED] font-semibold'
                : 'text-[#71717A]'
            }`}
          >
            <BookOpen className="h-4 w-4" />
            <span>Entries</span>
          </button>
          <button
            onClick={() => onChangeView('ask')}
            className={`flex flex-col items-center gap-0.5 text-[11px] ${
              activeView === 'ask' ? 'text-amber-300 font-semibold' : 'text-[#71717A]'
            }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>Ask</span>
          </button>
          <button
            onClick={() => onChangeView('reflect')}
            className={`flex flex-col items-center gap-0.5 text-[11px] ${
              activeView === 'reflect' ? 'text-indigo-300 font-semibold' : 'text-[#71717A]'
            }`}
          >
            <Compass className="h-4 w-4" />
            <span>Reflect</span>
          </button>
          <button
            onClick={() => onChangeView('companion')}
            className={`flex flex-col items-center gap-0.5 text-[11px] ${
              activeView === 'companion' ? 'text-purple-300 font-semibold' : 'text-[#71717A]'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Companion</span>
          </button>
        </div>
      )}
    </header>
  );
};

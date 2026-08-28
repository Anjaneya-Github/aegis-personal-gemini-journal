import React, { useState, useEffect } from 'react';
import { auth, onAuthStateChanged, signOutUser } from './lib/firebase';
import { 
  subscribeToUserEntries, 
  createJournalEntry, 
  updateJournalEntry, 
  deleteJournalEntry 
} from './services/journalService';
import { Navbar } from './components/Navbar';
import { AuthScreen } from './components/AuthScreen';
import { JournalList } from './components/JournalList';
import { JournalEditor } from './components/JournalEditor';
import { JournalDetail } from './components/JournalDetail';
import { AskJournalView } from './components/AskJournalView';
import { ReflectionView } from './components/ReflectionView';
import { CompanionChatView } from './components/CompanionChatView';
import { MemoryIntelligenceView } from './components/MemoryIntelligenceView';
import { SecuritySOCView } from './components/SecuritySOCView';
import { DeleteConfirmModal } from './components/DeleteConfirmModal';
import { SecurityNotice } from './components/SecurityNotice';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [entries, setEntries] = useState([]);
  const [isEntriesLoading, setIsEntriesLoading] = useState(true);

  // View Navigation
  const [activeView, setActiveView] = useState('list');
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [editingEntry, setEditingEntry] = useState(null);
  const [initialDraft, setInitialDraft] = useState(null);

  // Modals & Action States
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState(null);
  const [isSecurityModalOpen, setIsSecurityModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  // Listen to Firebase Auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setCurrentUser({
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        });
      } else {
        setCurrentUser(null);
        setEntries([]);
        setActiveView('list');
      }
      setIsAuthLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Subscribe to real-time user entries under /users/{uid}/entries
  useEffect(() => {
    if (!currentUser?.uid) {
      setEntries([]);
      setIsEntriesLoading(false);
      return;
    }

    setIsEntriesLoading(true);
    const unsubscribe = subscribeToUserEntries(
      currentUser.uid,
      (updatedEntries) => {
        setEntries(updatedEntries);
        setIsEntriesLoading(false);
      },
      () => {
        setIsEntriesLoading(false);
      }
    );

    return () => unsubscribe();
  }, [currentUser?.uid]);

  // Handlers
  const handleSignOut = async () => {
    try {
      await signOutUser();
      showToast('Signed out securely');
    } catch {
      showToast('Failed to sign out');
    }
  };

  const handleStartNewEntry = () => {
    setEditingEntry(null);
    setSelectedEntry(null);
    setInitialDraft(null);
    setActiveView('editor');
  };

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
    setSelectedEntry(null);
    setInitialDraft(null);
    setActiveView('editor');
  };

  const handleSelectEntry = (entry) => {
    setSelectedEntry(entry);
    setActiveView('detail');
  };

  const handleSelectEntryById = (entryId) => {
    const found = entries.find((e) => e.id === entryId);
    if (found) {
      setSelectedEntry(found);
      setActiveView('detail');
    } else {
      showToast('Entry not found in current list');
    }
  };

  const handleWriteWithPrompt = (promptText) => {
    setEditingEntry(null);
    setSelectedEntry(null);
    setInitialDraft({
      title: `Reflection: ${promptText.slice(0, 45)}...`,
      content: `Prompt: ${promptText}\n\n`,
      mood: 'reflective',
      tags: ['reflection', 'prompt'],
    });
    setActiveView('editor');
  };

  const handleDraftCreatedFromCompanion = (draft) => {
    setEditingEntry(null);
    setSelectedEntry(null);
    setInitialDraft(draft);
    setActiveView('editor');
    showToast('Conversation converted into a journal draft');
  };

  const handleSaveEntry = async (draft) => {
    if (!currentUser?.uid) return;
    setIsSaving(true);
    try {
      if (editingEntry) {
        await updateJournalEntry(currentUser.uid, editingEntry.id, draft);
        showToast('Journal entry updated');
      } else {
        await createJournalEntry(currentUser.uid, draft);
        showToast('Journal entry saved');
      }
      setActiveView('list');
      setEditingEntry(null);
      setInitialDraft(null);
    } catch (err) {
      throw err;
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!currentUser?.uid || !entryToDelete) return;
    setIsDeleting(true);
    try {
      await deleteJournalEntry(currentUser.uid, entryToDelete.id);
      showToast('Journal entry deleted');
      setEntryToDelete(null);
      if (activeView === 'detail') {
        setActiveView('list');
      }
    } catch {
      showToast('Failed to delete entry');
    } finally {
      setIsDeleting(false);
    }
  };

  // Auth Loading State
  if (isAuthLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0F0F10]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#EDEDED] border-t-transparent" />
          <span className="font-serif text-xs text-[#A1A1AA]">
            Opening your personal journal...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F0F10] font-sans text-[#EDEDED] antialiased">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 rounded-xl border border-[#27272A] bg-[#161618] px-4 py-2.5 text-xs font-medium text-[#EDEDED] shadow-2xl">
          {toastMessage}
        </div>
      )}

      {/* Security Architecture Modal */}
      <SecurityNotice
        isOpen={isSecurityModalOpen}
        onClose={() => setIsSecurityModalOpen(false)}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={Boolean(entryToDelete)}
        entry={entryToDelete}
        isDeleting={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setEntryToDelete(null)}
      />

      {/* Main App Canvas */}
      {!currentUser ? (
        <AuthScreen />
      ) : (
        <>
          <Navbar
            user={currentUser}
            activeView={activeView}
            onChangeView={(view) => {
              setActiveView(view);
              setSelectedEntry(null);
              setEditingEntry(null);
              setInitialDraft(null);
            }}
            onNewEntry={handleStartNewEntry}
            onSignOut={handleSignOut}
            onOpenSecurityModal={() => setIsSecurityModalOpen(true)}
          />

          <main className="pb-16">
            {activeView === 'list' && (
              <JournalList
                entries={entries}
                isLoading={isEntriesLoading}
                onSelectEntry={handleSelectEntry}
                onEditEntry={handleEditEntry}
                onDeleteEntry={(entry) => setEntryToDelete(entry)}
                onNewEntry={handleStartNewEntry}
                onNavigateToAsk={() => setActiveView('ask')}
                onNavigateToReflect={() => setActiveView('reflect')}
                onNavigateToCompanion={() => setActiveView('companion')}
              />
            )}

            {activeView === 'ask' && (
              <AskJournalView
                entries={entries}
                onSelectEntryById={handleSelectEntryById}
                onNewEntry={handleStartNewEntry}
              />
            )}

            {activeView === 'reflect' && (
              <ReflectionView
                entries={entries}
                onSelectEntryById={handleSelectEntryById}
                onWriteWithPrompt={handleWriteWithPrompt}
                onNewEntry={handleStartNewEntry}
              />
            )}

            {activeView === 'companion' && (
              <CompanionChatView
                onDraftCreated={handleDraftCreatedFromCompanion}
              />
            )}

            {activeView === 'memory' && (
              <MemoryIntelligenceView
                entries={entries}
                onSelectEntry={handleSelectEntry}
              />
            )}

            {activeView === 'soc' && (
              <SecuritySOCView
                user={currentUser}
              />
            )}

            {activeView === 'editor' && (
              <JournalEditor
                initialEntry={editingEntry}
                initialDraft={initialDraft}
                onSave={handleSaveEntry}
                onCancel={() => {
                  setActiveView('list');
                  setEditingEntry(null);
                  setInitialDraft(null);
                }}
                isSaving={isSaving}
              />
            )}

            {activeView === 'detail' && selectedEntry && (
              <JournalDetail
                entry={selectedEntry}
                onBack={() => {
                  setActiveView('list');
                  setSelectedEntry(null);
                }}
                onEdit={handleEditEntry}
                onDeleteRequest={(entry) => setEntryToDelete(entry)}
              />
            )}
          </main>
        </>
      )}
    </div>
  );
}

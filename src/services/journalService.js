import {
  collection,
  doc,
  setDoc,
  updateDoc,
  deleteDoc,
  getDoc,
  query,
  orderBy,
  onSnapshot,
} from 'firebase/firestore';
import { db } from '../lib/firebase';

/**
 * Service for managing user journal entries in Firestore under /users/{uid}/entries
 * Note: Data is strictly private to the authenticated user.
 */

export function calculateWordCount(text) {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function subscribeToUserEntries(uid, onUpdate, onError) {
  if (!uid) {
    onUpdate([]);
    return () => {};
  }

  const entriesRef = collection(db, 'users', uid, 'entries');
  const q = query(entriesRef, orderBy('createdAt', 'desc'));

  return onSnapshot(
    q,
    (snapshot) => {
      const entries = snapshot.docs.map((docSnap) => {
        const data = docSnap.data();
        return {
          id: docSnap.id,
          userId: uid,
          title: data.title || 'Untitled Entry',
          content: data.content || '',
          mood: data.mood || 'neutral',
          tags: Array.isArray(data.tags) ? data.tags : [],
          wordCount: typeof data.wordCount === 'number' ? data.wordCount : calculateWordCount(data.content || ''),
          createdAt: data.createdAt || Date.now(),
          updatedAt: data.updatedAt || Date.now(),
          summary: data.summary,
          reflectionPrompt: data.reflectionPrompt,
        };
      });
      onUpdate(entries);
    },
    (err) => {
      if (onError) {
        onError(err);
      }
    }
  );
}

export async function createJournalEntry(uid, draft) {
  if (!uid) throw new Error('Authentication required to create journal entry');

  const entriesRef = collection(db, 'users', uid, 'entries');
  const newDocRef = doc(entriesRef);
  const now = Date.now();

  const entryData = {
    userId: uid,
    title: draft.title.trim() || 'Untitled Entry',
    content: draft.content.trim(),
    mood: draft.mood,
    tags: draft.tags.map((t) => t.trim().toLowerCase()).filter(Boolean),
    wordCount: calculateWordCount(draft.content),
    createdAt: now,
    updatedAt: now,
  };

  await setDoc(newDocRef, entryData);
  return newDocRef.id;
}

export async function updateJournalEntry(uid, entryId, draft) {
  if (!uid || !entryId) throw new Error('Authentication & Entry ID required');

  const entryRef = doc(db, 'users', uid, 'entries', entryId);
  const now = Date.now();

  const updates = {
    updatedAt: now,
  };

  if (draft.title !== undefined) updates.title = draft.title.trim() || 'Untitled Entry';
  if (draft.content !== undefined) {
    updates.content = draft.content;
    updates.wordCount = calculateWordCount(draft.content);
  }
  if (draft.mood !== undefined) updates.mood = draft.mood;
  if (draft.tags !== undefined) {
    updates.tags = draft.tags.map((t) => t.trim().toLowerCase()).filter(Boolean);
  }

  await updateDoc(entryRef, updates);
}

export async function deleteJournalEntry(uid, entryId) {
  if (!uid || !entryId) throw new Error('Authentication & Entry ID required');
  const entryRef = doc(db, 'users', uid, 'entries', entryId);
  await deleteDoc(entryRef);
}

export async function fetchUserEntryById(uid, entryId) {
  if (!uid || !entryId) return null;
  const entryRef = doc(db, 'users', uid, 'entries', entryId);
  const snap = await getDoc(entryRef);
  if (!snap.exists()) return null;

  const data = snap.data();
  return {
    id: snap.id,
    userId: uid,
    title: data.title || 'Untitled Entry',
    content: data.content || '',
    mood: data.mood || 'neutral',
    tags: Array.isArray(data.tags) ? data.tags : [],
    wordCount: typeof data.wordCount === 'number' ? data.wordCount : calculateWordCount(data.content || ''),
    createdAt: data.createdAt || Date.now(),
    updatedAt: data.updatedAt || Date.now(),
    summary: data.summary,
    reflectionPrompt: data.reflectionPrompt,
  };
}

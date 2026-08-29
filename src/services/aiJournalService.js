import { getCurrentUserIdToken } from '../lib/firebase';

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || '';

/**
 * Helper to execute authenticated requests to the backend server.
 * Never exposes API keys to the browser.
 * Relies on Firebase ID token verified on the server.
 */
async function fetchWithAuth(endpoint, options = {}) {
  const token = await getCurrentUserIdToken();
  if (!token) {
    throw new Error('Authentication token not available. Please sign in.');
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `Server error (${response.status})`;
    try {
      const errorData = await response.json();
      if (errorData?.error) {
        errorMsg = errorData.error;
      }
    } catch {
      // Fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

/**
 * Ask My Journal with bounded retrieval and evidence verification.
 */
export async function askMyJournal(query) {
  return fetchWithAuth('/api/journal/ask', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

/**
 * Fetch synthesized, evidence-backed personal reflections.
 */
export async function getMyReflection() {
  return fetchWithAuth('/api/journal/reflect', {
    method: 'POST',
  });
}

/**
 * Send a multi-turn chat message to the mindful Journal Companion.
 */
export async function sendCompanionChatMessage(messages, currentDraft) {
  return fetchWithAuth('/api/journal/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, currentDraft }),
  });
}

/**
 * Automatically summarize a companion conversation into a structured journal draft.
 */
export async function summarizeCompanionConversation(messages) {
  return fetchWithAuth('/api/journal/summarize', {
    method: 'POST',
    body: JSON.stringify({ messages }),
  });
}

/**
 * Fetch server health status.
 */
export async function checkServerHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error('Server health check failed');
  }
  return res.json();
}

/**
 * Fetch extracted decisions with verified evidence citations.
 */
export async function getDecisionMemory() {
  return fetchWithAuth('/api/memory/decisions', {
    method: 'POST',
  });
}

/**
 * Detect evolving stances and potential contradictions with dual-entry verified evidence.
 */
export async function getContradictions() {
  return fetchWithAuth('/api/memory/contradictions', {
    method: 'POST',
  });
}

/**
 * Synthesize personal evolution trajectories backed by verified evidence.
 */
export async function getPersonalEvolution(query = '', timeframeDays = 90) {
  return fetchWithAuth('/api/memory/evolution', {
    method: 'POST',
    body: JSON.stringify({ query: query || null, timeframeDays }),
  });
}

/**
 * Fetch real-time Memory Integrity validation metrics.
 */
export async function getMemoryIntegrityStats() {
  return fetchWithAuth('/api/memory/integrity');
}

/**
 * Fetch Security SOC audit results and active security guardrails.
 */
export async function getSecuritySOCStatus() {
  return fetchWithAuth('/api/security/soc');
}


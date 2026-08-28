import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  Send, 
  FileText, 
  RotateCcw, 
  Bot, 
  User, 
  AlertCircle,
} from 'lucide-react';
import { sendCompanionChatMessage, summarizeCompanionConversation } from '../services/aiJournalService';

const STARTER_PROMPTS = [
  'Help me unpack what happened today and how I feel about it.',
  'I am feeling conflicted about a decision and want to explore my thoughts.',
  'Let us explore what I am most grateful for right now.',
  'Help me reflect on a recent milestone or personal achievement.',
];

export const CompanionChatView = ({ onDraftCreated }) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome-msg',
      role: 'model',
      content: 'Welcome to your private journaling space. I am your Gemini Journal Companion. What is on your mind today? We can explore your feelings, reflect on events, or unpack new ideas together.',
      timestamp: Date.now(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setError(null);
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      const payload = newMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await sendCompanionChatMessage(payload);
      
      const modelMsg = {
        id: `model-${Date.now()}`,
        role: 'model',
        content: res.content,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, modelMsg]);
    } catch (err) {
      setError(err?.message || 'Failed to reach companion. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarizeToEntry = async () => {
    if (messages.length <= 1) return;
    setIsSummarizing(true);
    setError(null);
    try {
      const payload = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const res = await summarizeCompanionConversation(payload);
      
      onDraftCreated({
        title: res.title || 'Conversation Reflection',
        content: res.content,
        mood: res.mood || 'reflective',
        tags: res.tags || ['reflection', 'companion'],
      });
    } catch (err) {
      setError(err?.message || 'Failed to synthesize conversation into an entry.');
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleResetChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'model',
        content: 'I am ready whenever you are. What would you like to reflect on today?',
        timestamp: Date.now(),
      },
    ]);
    setError(null);
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-120px)] max-w-4xl flex-col px-4 py-4 sm:px-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#27272A] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-serif text-lg font-bold text-[#EDEDED]">
              Journal Companion
            </h2>
            <p className="text-[11px] text-[#A1A1AA]">
              Multi-turn reflective dialogue • Convert to journal entry anytime
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {messages.length > 2 && (
            <button
              id="summarize-chat-btn"
              onClick={handleSummarizeToEntry}
              disabled={isSummarizing || isLoading}
              className="inline-flex items-center gap-1.5 rounded-xl bg-purple-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-purple-500 disabled:opacity-50"
            >
              {isSummarizing ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Synthesizing Entry...</span>
                </>
              ) : (
                <>
                  <FileText className="h-3.5 w-3.5" />
                  <span>Convert to Journal Entry</span>
                </>
              )}
            </button>
          )}

          <button
            onClick={handleResetChat}
            title="Start fresh conversation"
            className="rounded-lg p-2 text-[#71717A] hover:bg-[#1E1E22] hover:text-[#EDEDED]"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="my-2 rounded-lg border border-rose-900/60 bg-rose-950/30 p-3 text-xs text-rose-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 space-y-4 overflow-y-auto py-4 pr-1">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
                  isUser
                    ? 'bg-[#EDEDED] text-[#0F0F10]'
                    : 'bg-purple-950/70 text-purple-400 border border-purple-800/60'
                }`}
              >
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div
                className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                  isUser
                    ? 'bg-[#EDEDED] text-[#0F0F10]'
                    : 'border border-[#27272A] bg-[#161618] text-[#EDEDED]'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-purple-950/70 text-purple-400 border border-purple-800/60">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl border border-[#27272A] bg-[#161618] p-4 text-xs text-[#A1A1AA]">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 animate-bounce rounded-full bg-purple-400" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-purple-400 [animation-delay:0.2s]" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-purple-400 [animation-delay:0.4s]" />
                <span className="ml-1">Reflecting on your thoughts...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Starter Prompts (if chat is brand new) */}
      {messages.length === 1 && (
        <div className="mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#71717A]">
            Suggestions to begin:
          </span>
          <div className="mt-2 flex flex-wrap gap-2">
            {STARTER_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => handleSendMessage(p)}
                className="rounded-lg border border-[#27272A] bg-[#161618] px-2.5 py-1.5 text-xs text-[#A1A1AA] hover:border-[#3F3F46] hover:text-[#EDEDED]"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Composer */}
      <div className="border-t border-[#27272A] pt-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            id="companion-chat-input"
            type="text"
            placeholder="Share your thoughts or answer the companion..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            className="flex-1 rounded-xl border border-[#27272A] bg-[#161618] px-4 py-3 text-sm text-[#EDEDED] placeholder:text-[#71717A] focus:border-purple-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-purple-600 text-white transition hover:bg-purple-500 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { ChatMessage } from "@/types/chat";
import { sendChatMessage, checkBackendHealth } from "@/lib/api";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { WaitlistSection } from "@/components/WaitlistSection";
import { createClient } from "@/lib/supabase/client";

const SUGGESTED_PROMPTS = [
  {
    title: "Explain a difficult topic",
    description: "Break down complex academic theories into intuitive concepts with clear real-world analogies.",
    query: "Can you explain a difficult topic simply with practical examples and analogies? Start by breaking down how neural networks learn.",
    icon: (
      <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    title: "Summarize my syllabus",
    description: "Analyze course modules, key prerequisites, and examination weightings for this semester.",
    query: "Help me summarize my semester syllabus. What are the key core concepts and recommended milestones I should focus on?",
    icon: (
      <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    title: "Create a study plan",
    description: "Build a structured 4-week daily revision schedule leading up to exams.",
    query: "Create a realistic 4-week daily study schedule with spaced repetition and active recall sessions for university examinations.",
    icon: (
      <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: "Generate practice questions",
    description: "Generate conceptual self-assessment problems and model answers for revision.",
    query: "Generate 5 high-yield conceptual practice questions with step-by-step model answers to test my understanding of Operating System concurrency and deadlocks.",
    icon: (
      <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

const FEATURE_HIGHLIGHTS = [
  {
    title: "Academic Question Answering",
    description: "Deep conceptual explanations structured to clarify complex academic doubts across disciplines.",
    icon: (
      <svg className="h-5 w-5 text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    title: "Study Material Assistance",
    description: "Synthesize textbook chapters, lecture slides, and curriculum papers into clear revision notes.",
    icon: (
      <svg className="h-5 w-5 text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    title: "Exam Preparation",
    description: "Personalized revision roadmaps, active recall practice, and structured problem walkthroughs.",
    icon: (
      <svg className="h-5 w-5 text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: "Personalized Learning Support",
    description: "Adaptive guidance tailored to your academic pace, degree program, and research objectives.",
    icon: (
      <svg className="h-5 w-5 text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
];

export default function CampusPilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [visitorSessionId, setVisitorSessionId] = useState<string>("");
  const [visitorCount, setVisitorCount] = useState<number>(0);
  const [isLimitReached, setIsLimitReached] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize ephemeral visitor session
  useEffect(() => {
    let sid = sessionStorage.getItem("campuspilot_visitor_sid");
    if (!sid) {
      sid = "vis_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
      sessionStorage.setItem("campuspilot_visitor_sid", sid);
    }
    setVisitorSessionId(sid);

    const savedCount = parseInt(sessionStorage.getItem("campuspilot_visitor_count") || "0", 10);
    setVisitorCount(savedCount);
    if (savedCount >= 3) {
      setIsLimitReached(true);
    }
  }, []);

  // Check auth state
  useEffect(() => {
    try {
      const supabase = createClient();
      supabase.auth.getUser().then(({ data: { user } }) => {
        if (user) {
          setUserEmail(user.email || "Student");
        }
      });
    } catch {
      // Ignored if client not ready
    }
  }, []);

  // Check backend health on initial load
  useEffect(() => {
    async function verifyHealth() {
      try {
        const health = await checkBackendHealth();
        if (health.status === "healthy" || health.status === "ok") {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch {
        setBackendStatus("offline");
      }
    }
    verifyHealth();
  }, []);

  // Smooth scroll to newest message
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const handleSubmit = async (queryText?: string) => {
    if (isLimitReached) return;
    const textToSend = queryText || input.trim();
    if (!textToSend || loading) return;

    setErrorMsg(null);
    setInput("");

    const userMessage: ChatMessage = {
      role: "user",
      content: textToSend,
      timestamp: new Date().toISOString(),
    };

    const nextHistory = [...messages, userMessage];
    setMessages(nextHistory);
    setLoading(true);

    try {
      const response = await sendChatMessage(textToSend, messages, visitorSessionId);
      const assistantMessage: ChatMessage = {
        role: "model",
        content: response.reply,
        timestamp: response.timestamp,
      };
      setMessages([...nextHistory, assistantMessage]);

      const updatedCount = visitorCount + 1;
      setVisitorCount(updatedCount);
      sessionStorage.setItem("campuspilot_visitor_count", updatedCount.toString());

      const limit = response.visitor_limit || 3;
      if (updatedCount >= limit || (response.remaining_messages !== undefined && response.remaining_messages <= 0)) {
        setIsLimitReached(true);
      }
    } catch (err: unknown) {
      const errObj = err as Error & { status?: number; limitReached?: boolean };
      if (errObj.status === 429 || errObj.limitReached) {
        setIsLimitReached(true);
        setErrorMsg("Visitor preview limit reached. Please log in with your student account to continue unlimited academic chats.");
      } else {
        const errText = err instanceof Error ? err.message : "Failed to obtain response from CampusPilot AI.";
        setErrorMsg(errText);
      }
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setErrorMsg(null);
    setInput("");
  };

  const handleLogout = async () => {
    try {
      const supabase = createClient();
      await supabase.auth.signOut();
      setUserEmail(null);
      window.location.reload();
    } catch {
      // Ignore
    }
  };

  const isChatActive = messages.length > 0;

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA] text-[#1C1917] antialiased">
      {/* 1. Header */}
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-stone-200/80 bg-[#FBFBFA]/90 px-4 sm:px-8 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleNewChat}
            className="group flex items-center gap-3 text-left focus:outline-hidden"
            title="CampusPilot AI — Return to Home"
          >
            <div className="relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-stone-200 bg-white shadow-2xs transition-transform group-hover:scale-[1.02]">
              <Image
                src="/logo.jpg"
                alt="CampusPilot Emblem"
                width={40}
                height={40}
                className="object-cover"
                priority
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold tracking-tight text-stone-900">
                  CampusPilot AI
                </span>
                <span className="rounded-sm border border-stone-200 bg-stone-100 px-1.5 py-0.5 text-[10px] font-medium tracking-wider text-stone-600 uppercase">
                  Academic
                </span>
              </div>
              <p className="hidden text-[11px] text-stone-500 sm:block">
                Your AI Academic Companion
              </p>
            </div>
          </button>
        </div>

        {/* Status Indicator & Header Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1 shadow-2xs">
            <span
              className={`h-2 w-2 rounded-full ${
                backendStatus === "online"
                  ? "bg-emerald-600"
                  : backendStatus === "checking"
                  ? "bg-amber-500 animate-pulse"
                  : "bg-rose-500"
              }`}
            />
            <span className="text-xs font-medium text-stone-700">
              {backendStatus === "online"
                ? "Academic AI Online"
                : backendStatus === "checking"
                ? "Connecting to AI..."
                : "Service Offline"}
            </span>
          </div>

          {/* Visitor preview status indicator */}
          {!userEmail && (
            <div className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-stone-100/70 px-2.5 py-1 text-[11px] font-medium text-stone-600">
              <span>Preview:</span>
              <span className={`font-semibold ${visitorCount >= 3 ? "text-amber-700" : "text-stone-900"}`}>
                {Math.max(0, 3 - visitorCount)}/3 questions
              </span>
            </div>
          )}

          {/* Authentication-Aware Actions */}
          {userEmail ? (
            <div className="flex items-center gap-2">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1.5 rounded-lg bg-stone-900 px-3 py-1.5 text-xs font-medium text-white shadow-2xs transition-colors hover:bg-stone-800"
              >
                <span>Go to Dashboard</span>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-lg border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-medium text-stone-600 hover:bg-stone-50 hover:text-stone-900"
                title="Log out of student session"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <a
                href="#waitlist"
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 shadow-2xs hover:bg-stone-50"
              >
                Join Waitlist
              </a>
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-lg bg-stone-900 px-3.5 py-1.5 text-xs font-medium text-white shadow-2xs transition-colors hover:bg-stone-800"
              >
                <span>Student Login</span>
              </Link>
            </div>
          )}

          {isChatActive && (
            <button
              type="button"
              onClick={handleNewChat}
              className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 shadow-2xs transition-colors hover:bg-stone-50 hover:text-stone-900"
            >
              <svg className="h-3.5 w-3.5 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>New Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex flex-1 flex-col">
        {!isChatActive ? (
          /* =========================================================================
             2. LANDING PAGE EXPERIENCE (Hero + Prompt Box + Suggested + Features)
             ========================================================================= */
          <div className="flex flex-1 flex-col">
            <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4 pt-12 pb-16 sm:px-6">
              {/* Hero Section */}
              <div className="flex flex-col items-center text-center">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-stone-200 bg-white shadow-xs">
                  <Image
                    src="/logo.jpg"
                    alt="CampusPilot Emblem"
                    width={64}
                    height={64}
                    className="rounded-xl object-cover"
                  />
                </div>

                <div className="inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1 text-xs font-medium text-stone-600 shadow-2xs">
                  <span>CampusPilot AI</span>
                  <span className="text-stone-300">·</span>
                  <span className="text-stone-700">Academic Intelligence</span>
                </div>

                <h1 className="mt-5 max-w-2xl text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl md:text-[42px] md:leading-[1.15]">
                  Your Academic Journey, Made Smarter.
                </h1>

                <p className="mt-4 max-w-xl text-sm leading-relaxed text-stone-600 sm:text-base">
                  An intelligent academic assistant that helps students understand subjects,
                  explore study materials, and prepare for examinations.
                </p>

                {/* Primary Action Buttons for Unauthenticated vs Authenticated */}
                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  {userEmail ? (
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-stone-800 transition-colors"
                    >
                      <span>Open Student Dashboard</span>
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </Link>
                  ) : (
                    <>
                      <a
                        href="#waitlist"
                        className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-stone-800 transition-colors"
                      >
                        <span>Join the Waitlist</span>
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </a>
                      <Link
                        href="/login"
                        className="inline-flex items-center gap-1.5 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors"
                      >
                        <span>Student Login</span>
                      </Link>
                    </>
                  )}
                </div>

                {/* Large, Elegant Prompt Input Box or Visitor Limit Notice */}
                <div className="mt-8 w-full max-w-2xl">
                  {isLimitReached ? (
                    <div className="rounded-2xl border border-stone-200 bg-white p-6 text-center shadow-xs">
                      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-100 text-stone-800 mb-3 border border-stone-200">
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-semibold text-stone-900">
                        Visitor Preview Limit Reached (3/3 Questions)
                      </h4>
                      <p className="mt-1.5 text-xs text-stone-600 max-w-md mx-auto leading-relaxed">
                        You have explored the 3 preview questions. To unlock unlimited academic conversations, upload course syllabi and lecture PDFs, and keep persistent study history, please log in with your student credentials.
                      </p>
                      <div className="mt-5 flex items-center justify-center gap-3">
                        <Link
                          href="/login"
                          className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-stone-800 transition-colors"
                        >
                          <span>Student Login</span>
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                          </svg>
                        </Link>
                        <a
                          href="#waitlist"
                          className="inline-flex items-center gap-1.5 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors"
                        >
                          Join Waitlist
                        </a>
                      </div>
                    </div>
                  ) : (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSubmit();
                      }}
                      className="relative flex flex-col rounded-2xl border border-stone-300/90 bg-white p-3 shadow-sm transition-all focus-within:border-stone-500 focus-within:shadow-md"
                    >
                      <textarea
                        ref={inputRef}
                        rows={3}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                        placeholder="Ask CampusPilot to explain a concept, outline syllabus modules, or build an exam study schedule..."
                        className="w-full resize-none bg-transparent px-2.5 py-1.5 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-hidden disabled:opacity-50"
                      />

                      <div className="mt-2 flex items-center justify-between border-t border-stone-100 pt-2.5">
                        <div className="flex items-center gap-2 text-xs text-stone-600">
                          <span className="inline-flex items-center gap-1 rounded bg-stone-100 px-1.5 py-0.5 text-[10px] font-medium text-stone-600">
                            Visitor Preview · {Math.max(0, 3 - visitorCount)} left
                          </span>
                          <span className="hidden sm:inline text-[11px] text-stone-600">
                            Press <kbd className="rounded border border-stone-200 bg-stone-50 px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to submit
                          </span>
                        </div>

                        <button
                          type="submit"
                          disabled={!input.trim() || loading}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-4 py-2 text-xs font-medium text-white shadow-2xs transition-all hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          <span>Start Learning</span>
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                          </svg>
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>

              {/* 3. Suggested Prompts */}
              <div className="mt-12">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xs font-semibold tracking-wider text-stone-500 uppercase">
                    Suggested Learning Prompts
                  </h2>
                  <span className="text-xs text-stone-600">Click any card to start</span>
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {SUGGESTED_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSubmit(prompt.query)}
                      className="group flex flex-col items-start rounded-xl border border-stone-200 bg-white p-4 text-left shadow-2xs transition-all hover:border-stone-300 hover:shadow-xs active:bg-stone-50"
                    >
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-stone-100 bg-stone-50">
                          {prompt.icon}
                        </div>
                        <span className="text-xs font-semibold text-stone-800 group-hover:text-stone-900">
                          {prompt.title}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-stone-500 group-hover:text-stone-600">
                        {prompt.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {/* 4. Feature Highlights */}
              <div className="mt-16 border-t border-stone-200/80 pt-12">
                <div className="mb-6 text-center">
                  <h3 className="text-xs font-semibold tracking-wider text-stone-500 uppercase">
                    Engineered for Academic Excellence
                  </h3>
                  <p className="mt-1 text-base font-semibold text-stone-800">
                    Comprehensive assistance across your academic lifecycle
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {FEATURE_HIGHLIGHTS.map((feature, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col rounded-xl border border-stone-200/90 bg-white p-4 shadow-2xs"
                    >
                      <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg border border-stone-100 bg-stone-50">
                        {feature.icon}
                      </div>
                      <h4 className="text-xs font-semibold text-stone-900">
                        {feature.title}
                      </h4>
                      <p className="mt-1.5 text-xs leading-relaxed text-stone-500">
                        {feature.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Dedicated Waitlist Section */}
            <WaitlistSection />
          </div>
        ) : (
          /* =========================================================================
             CONVERSATION STREAM VIEW
             ========================================================================= */
          <div className="flex flex-1 flex-col">
            <div className="mx-auto flex-1 w-full max-w-3xl px-4 py-8">
              <div className="space-y-6">
                {messages.map((msg, index) => {
                  const isUser = msg.role === "user";
                  return (
                    <div
                      key={index}
                      className={`flex items-start gap-3.5 ${
                        isUser ? "flex-row-reverse" : "flex-row"
                      }`}
                    >
                      {/* Avatar */}
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-medium ${
                          isUser
                            ? "border border-stone-300 bg-stone-900 text-white"
                            : "border border-stone-200 bg-white text-stone-700 shadow-2xs"
                        }`}
                      >
                        {isUser ? (
                          "You"
                        ) : (
                          <Image
                            src="/logo.jpg"
                            alt="CampusPilot Emblem"
                            width={24}
                            height={24}
                            className="rounded-sm object-cover"
                          />
                        )}
                      </div>

                      {/* Message Bubble */}
                      <div
                        className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                          isUser
                            ? "bg-[#27272A] text-white shadow-2xs"
                            : "border border-stone-200 bg-white text-stone-900 shadow-2xs"
                        }`}
                      >
                        {isUser ? (
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        ) : (
                          <MarkdownRenderer content={msg.content} />
                        )}

                        {msg.timestamp && (
                          <div
                            className={`mt-2.5 flex items-center justify-between text-[10px] ${
                              isUser ? "text-stone-400" : "text-stone-400"
                            }`}
                          >
                            <span>
                              {new Date(msg.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                            {!isUser && (
                              <button
                                type="button"
                                onClick={() => navigator.clipboard.writeText(msg.content)}
                                className="inline-flex items-center gap-1 text-[10px] text-stone-400 transition-colors hover:text-stone-700"
                                title="Copy response text"
                              >
                                <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
                                  <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z" />
                                  <path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z" />
                                </svg>
                                <span>Copy</span>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Loading / Thinking State */}
                {loading && (
                  <div className="flex items-start gap-3.5">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-white shadow-2xs">
                      <Image
                        src="/logo.jpg"
                        alt="CampusPilot Emblem"
                        width={24}
                        height={24}
                        className="rounded-sm object-cover opacity-80"
                      />
                    </div>
                    <div className="flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-2xs">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500 [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500 [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500" />
                      <span className="ml-2 text-xs text-stone-500 font-medium">
                        Analyzing academic context...
                      </span>
                    </div>
                  </div>
                )}

                {/* Error Notice */}
                {errorMsg && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50/80 p-3.5 text-xs text-rose-800">
                    <span className="font-semibold">Error:</span> {errorMsg}
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Conversation Active Input Bar */}
            <div className="sticky bottom-0 border-t border-stone-200/90 bg-[#FBFBFA]/95 p-4 backdrop-blur-md">
              <div className="mx-auto max-w-3xl">
                {isLimitReached ? (
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 rounded-xl border border-stone-200 bg-white p-3.5 shadow-xs">
                    <div className="text-left">
                      <p className="text-xs font-semibold text-stone-900">
                        Visitor preview limit reached ({visitorCount}/3 questions used)
                      </p>
                      <p className="text-[11px] text-stone-600">
                        Log in with your student account to continue asking questions, upload documents, and preserve persistent chats.
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Link
                        href="/login"
                        className="inline-flex items-center gap-1.5 rounded-lg bg-stone-900 px-3.5 py-2 text-xs font-semibold text-white hover:bg-stone-800 transition-colors"
                      >
                        <span>Student Login</span>
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSubmit();
                    }}
                    className="flex items-center gap-2 rounded-xl border border-stone-300 bg-white p-1.5 shadow-xs transition-colors focus-within:border-stone-500"
                  >
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      disabled={loading}
                      placeholder="Ask follow-up questions, request practice problems, or revise..."
                      className="flex-1 bg-transparent px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-hidden disabled:opacity-50"
                    />
                    <button
                      type="submit"
                      disabled={!input.trim() || loading}
                      className="inline-flex h-9 items-center justify-center rounded-lg bg-stone-900 px-4 text-xs font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {loading ? "Thinking..." : "Send"}
                    </button>
                  </form>
                )}

                <p className="mt-2 text-center text-[11px] text-stone-600">
                  CampusPilot AI provides academic guidance · Visitor Preview ({Math.max(0, 3 - visitorCount)}/3 free turns remaining)
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 5. Footer */}
      <footer className="border-t border-stone-200/70 bg-[#FBFBFA] px-4 py-6 text-center text-xs text-stone-600 sm:px-8">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-2 sm:flex-row">
          <div className="flex items-center gap-2 text-stone-600">
            <span className="font-semibold text-stone-700">CampusPilot AI</span>
            <span>·</span>
            <span>Your AI Academic Companion</span>
          </div>
          <p className="text-[11px] text-stone-600">
            Designed for university curriculum assistance, study scheduling, and academic problem-solving.
          </p>
        </div>
      </footer>
    </div>
  );
}

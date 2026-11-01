"use client";

import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useDashboard } from "@/context/DashboardContext";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { SourceDetailModal, SourcesTray } from "@/components/CitationViewer";
import { Citation } from "@/types/database";

export default function ChatWorkspacePage() {
  const {
    currentConversation,
    messages,
    loading,
    chatInput,
    setChatInput,
    sendMessage,
    credits,
    subscription,
    setIsPricingModalOpen,
    documents,
    openAcademicUploadModal,
  } = useDashboard();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() && !selectedFile) return;

    const fileToSend = selectedFile;
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";

    try {
      setErrorMsg(null);
      await sendMessage(chatInput.trim(), fileToSend);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send message.");
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#FBFBFA]">
      {/* Top Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-stone-200/80 bg-white/80 px-4 sm:px-6 backdrop-blur-md">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-stone-100 text-stone-700">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-xs sm:text-sm font-semibold text-stone-900">
              {currentConversation?.title || "Academic Chat Workspace"}
            </h1>
          </div>
          <span className="hidden sm:inline-flex items-center rounded-md bg-stone-100 px-2 py-0.5 text-[10px] font-medium text-stone-600">
            Gemini 2.5 Flash • Academic RAG
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => openAcademicUploadModal()}
            className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-2.5 py-1 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors cursor-pointer"
          >
            <svg className="h-3.5 w-3.5 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Upload Document</span>
          </button>

          {(!subscription || !subscription.is_paid) && (
            <button
              type="button"
              onClick={() => setIsPricingModalOpen(true)}
              className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors cursor-pointer"
            >
              <span>Upgrade</span>
              <span className="text-[10px] text-emerald-600 font-normal">₹99/mo</span>
            </button>
          )}
        </div>
      </header>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* Low Credits Warning Banner */}
          {credits && !credits.is_paid_subscriber && credits.credits_balance <= 5 && (
            <div
              className={`flex items-center justify-between rounded-xl p-3 text-xs ${
                credits.credits_balance <= 0
                  ? "border border-rose-300 bg-rose-50 text-rose-800"
                  : "border border-amber-300 bg-amber-50 text-amber-800"
              }`}
            >
              <div>
                <span className="font-semibold">
                  {credits.credits_balance <= 0
                    ? "Zero credits remaining."
                    : `Low credits notice: ${credits.credits_balance} remaining.`}
                </span>{" "}
                <span>Upgrade to unlimited access for ₹99/month.</span>
              </div>
              <button
                type="button"
                onClick={() => setIsPricingModalOpen(true)}
                className="rounded-lg bg-stone-900 px-2.5 py-1 text-[11px] font-medium text-white shadow-2xs hover:bg-stone-800 shrink-0 cursor-pointer"
              >
                Upgrade Plan
              </button>
            </div>
          )}

          {/* Empty Chat State */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <Image
                  src="/logo.jpg"
                  alt="CampusPilot Logo"
                  width={48}
                  height={48}
                  className="rounded-xl object-cover"
                />
              </div>
              <h3 className="mt-4 text-base font-semibold text-stone-900">
                CampusPilot Academic Assistant
              </h3>
              <p className="mt-1 max-w-md text-xs leading-relaxed text-stone-500">
                Ask questions regarding BCA Semester V & VI course syllabi, examination preparation, algorithms, or attach an academic PDF to begin.
              </p>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg text-left">
                <button
                  type="button"
                  onClick={() => {
                    setChatInput("Can you break down how gradient descent optimizes neural network parameters in AI?");
                  }}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-700 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer text-left"
                >
                  <p className="font-semibold text-stone-900">Explain gradient descent optimization</p>
                  <p className="text-[11px] text-stone-500 mt-0.5">BCA 502 Introduction to AI</p>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setChatInput("Explain the difference between supervised and unsupervised learning algorithms with examples.");
                  }}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-700 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer text-left"
                >
                  <p className="font-semibold text-stone-900">Supervised vs Unsupervised Learning</p>
                  <p className="text-[11px] text-stone-500 mt-0.5">BCA 503 Introduction to Data Science</p>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setChatInput("How does Java implement multi-threading and what is synchronization in Java Enterprise?");
                  }}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-700 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer text-left"
                >
                  <p className="font-semibold text-stone-900">Java Multithreading & Synchronization</p>
                  <p className="text-[11px] text-stone-500 mt-0.5">BCA 501 Java Programming</p>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setChatInput("Summarize the 14-section BCA 603 Major Project report format guidelines.");
                  }}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-700 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer text-left"
                >
                  <p className="font-semibold text-stone-900">Major Project Guidelines & Rubric</p>
                  <p className="text-[11px] text-stone-500 mt-0.5">BCA 603 Project Submission</p>
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id || index}
                  className={`flex items-start gap-3.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
                >
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
                        alt="CampusPilot Logo"
                        width={24}
                        height={24}
                        className="rounded-sm object-cover"
                      />
                    )}
                  </div>

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
                      <>
                        <MarkdownRenderer
                          content={msg.content}
                          citations={msg.citations}
                          onSelectCitation={(c) => setSelectedCitation(c)}
                        />
                        <SourcesTray
                          citations={msg.citations}
                          onSelectCitation={(c) => setSelectedCitation(c)}
                        />
                      </>
                    )}

                    {msg.created_at && (
                      <div className="mt-2.5 flex items-center justify-between text-[10px] text-stone-400">
                        <span>
                          {new Date(msg.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        {!isUser && (
                          <button
                            type="button"
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                            className="inline-flex items-center gap-1 text-[10px] text-stone-400 hover:text-stone-700 cursor-pointer"
                            title="Copy response"
                          >
                            Copy
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex items-start gap-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-white shadow-2xs">
                <Image
                  src="/logo.jpg"
                  alt="CampusPilot Logo"
                  width={24}
                  height={24}
                  className="rounded-sm object-cover opacity-80"
                />
              </div>
              <div className="flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-2xs">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500 [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500 [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-500" />
                <span className="ml-2 text-xs font-medium text-stone-500">
                  Formulating grounded academic response...
                </span>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="rounded-xl border border-rose-200 bg-rose-50/90 p-3.5 text-xs text-rose-800">
              <span className="font-semibold">Notice:</span> {errorMsg}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar */}
      <div className="border-t border-stone-200/80 bg-white/90 p-4 backdrop-blur-md">
        <div className="mx-auto max-w-3xl">
          {selectedFile && (
            <div className="mb-2 flex items-center justify-between rounded-xl border border-stone-200 bg-stone-50 px-3 py-2 text-xs">
              <div className="flex items-center gap-2 truncate">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-stone-900 text-[10px] font-bold text-white">
                  PDF
                </div>
                <span className="truncate font-medium text-stone-900">{selectedFile.name}</span>
                <span className="text-[11px] text-stone-400">
                  ({(selectedFile.size / 1024).toFixed(0)} KB)
                </span>
              </div>

              <button
                type="button"
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="rounded-md p-1 text-stone-400 hover:bg-stone-200/60 hover:text-stone-700 cursor-pointer"
                title="Remove attached PDF"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          <form
            onSubmit={handleFormSubmit}
            className="flex items-center gap-1.5 rounded-2xl border border-stone-300 bg-white p-1.5 shadow-xs focus-within:border-stone-500"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  if (
                    file.type !== "application/pdf" &&
                    !file.name.toLowerCase().endsWith(".pdf")
                  ) {
                    setErrorMsg("Only PDF documents are supported.");
                    return;
                  }
                  setSelectedFile(file);
                  setErrorMsg(null);
                }
              }}
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-stone-500 hover:bg-stone-100 hover:text-stone-800 disabled:opacity-40 transition-colors cursor-pointer"
              title="Attach academic PDF"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>

            <input
              id="chat-input"
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={loading}
              placeholder={
                selectedFile
                  ? "Add questions about this PDF or press Send to analyze..."
                  : "Ask CampusPilot AI an academic question or discuss course materials..."
              }
              className="flex-1 bg-transparent px-2 py-2 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 focus:outline-hidden disabled:opacity-50"
            />

            <button
              type="submit"
              disabled={(!chatInput.trim() && !selectedFile) || loading}
              className="inline-flex h-9 items-center justify-center rounded-xl bg-stone-900 px-4 text-xs font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer shadow-2xs"
            >
              {loading ? (
                <div className="flex items-center gap-1.5">
                  <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Thinking</span>
                </div>
              ) : (
                "Send"
              )}
            </button>
          </form>
        </div>
      </div>

      {selectedCitation && (
        <SourceDetailModal
          citation={selectedCitation}
          isOpen={Boolean(selectedCitation)}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
}

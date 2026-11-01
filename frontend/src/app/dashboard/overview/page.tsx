"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDashboard } from "@/context/DashboardContext";

export default function OverviewPage() {
  const router = useRouter();
  const {
    profile,
    userEmail,
    subscription,
    credits,
    documents,
    conversations,
    selectChat,
    createNewChat,
    askAboutDocument,
    openAcademicUploadModal,
    setIsPricingModalOpen,
  } = useDashboard();

  const handleStartChat = async () => {
    await createNewChat();
    router.push("/dashboard");
  };

  const handleOpenConversation = async (id: string) => {
    await selectChat(id);
    router.push("/dashboard");
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Header Greeting */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200/80 pb-6">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
              Welcome back, {profile?.full_name || "Student"}
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-stone-500">
              BCA Semester V & VI academic assistant, documents, and syllabus copilot.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={handleStartChat}
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>New Chat</span>
            </button>
            <button
              type="button"
              onClick={() => openAcademicUploadModal()}
              className="inline-flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-xs font-semibold text-stone-800 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer"
            >
              <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
                Plan Status
              </span>
              <span className="rounded-full bg-stone-100 px-2 py-0.5 text-[10px] font-bold text-stone-600 uppercase">
                {subscription?.plan || "Free"}
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold capitalize text-stone-900">
                {subscription?.is_paid ? "Pro Tier" : "Free Tier"}
              </span>
            </div>
            <p className="mt-2 text-xs text-stone-500">
              {subscription?.is_paid
                ? `${subscription.remaining_days || 0} days remaining`
                : "20 monthly free credits"}
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
                Credits Balance
              </span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                Active
              </span>
            </div>
            <div className="mt-3 text-2xl font-bold text-stone-900">
              {credits?.is_paid_subscriber ? "∞ Unlimited" : `${credits?.credits_balance ?? 20} / 20`}
            </div>
            <p className="mt-2 text-xs text-stone-500">
              {credits?.is_paid_subscriber ? "Full Pro access unlocked" : "1 credit per AI answer"}
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
                Stored Documents
              </span>
              <Link href="/dashboard/documents" className="text-[11px] font-semibold text-stone-700 hover:text-stone-950">
                View all →
              </Link>
            </div>
            <div className="mt-3 text-2xl font-bold text-stone-900">{documents.length}</div>
            <p className="mt-2 text-xs text-stone-500">
              {documents.filter((d) => d.scope === "shared").length} shared university docs
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
                Active Chats
              </span>
              <Link href="/dashboard" className="text-[11px] font-semibold text-stone-700 hover:text-stone-950">
                Workspace →
              </Link>
            </div>
            <div className="mt-3 text-2xl font-bold text-stone-900">{conversations.length}</div>
            <p className="mt-2 text-xs text-stone-500">Persistent saved sessions</p>
          </div>
        </div>

        {/* Upgrade Banner for Free Users */}
        {(!subscription || !subscription.is_paid) && (
          <div className="rounded-2xl border border-stone-900 bg-stone-900 p-6 text-white shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-5">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="rounded bg-amber-400 text-stone-950 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                  Upgrade
                </span>
                <span className="text-xs text-stone-300 font-medium">BCA Examination Preparation</span>
              </div>
              <h3 className="text-lg font-bold text-white tracking-tight">
                Get Unlimited Grounded AI Answers & Document Queries
              </h3>
              <p className="text-xs text-stone-300 max-w-xl">
                Unlimited questions, full syllabus coverage for Semester V & VI, personal notes indexing, and priority response generation.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsPricingModalOpen(true)}
              className="rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-stone-900 shadow-sm hover:bg-stone-100 transition-colors shrink-0 cursor-pointer"
            >
              Upgrade to Pro (₹99/mo)
            </button>
          </div>
        )}

        {/* Quick Links & Learning Preview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/dashboard/learning"
            className="group rounded-2xl border border-stone-200/80 bg-white p-5 shadow-2xs hover:border-stone-300 hover:shadow-xs transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-stone-100 text-stone-800 group-hover:scale-105 transition-transform">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-stone-900">BCA Curriculum & Subjects</h4>
            <p className="mt-1 text-xs text-stone-500 leading-relaxed">
              Browse Semester V & VI subjects, unit syllabi, Java lab practicals, and Major Project guidelines.
            </p>
            <span className="mt-3 inline-flex items-center text-xs font-semibold text-stone-900 group-hover:underline">
              Open My Learning →
            </span>
          </Link>

          <Link
            href="/dashboard/documents"
            className="group rounded-2xl border border-stone-200/80 bg-white p-5 shadow-2xs hover:border-stone-300 hover:shadow-xs transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-stone-100 text-stone-800 group-hover:scale-105 transition-transform">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-stone-900">Academic Documents</h4>
            <p className="mt-1 text-xs text-stone-500 leading-relaxed">
              Upload, search, filter and download your personal course materials and university PDFs.
            </p>
            <span className="mt-3 inline-flex items-center text-xs font-semibold text-stone-900 group-hover:underline">
              Manage Documents →
            </span>
          </Link>

          <Link
            href="/dashboard/billing"
            className="group rounded-2xl border border-stone-200/80 bg-white p-5 shadow-2xs hover:border-stone-300 hover:shadow-xs transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-stone-100 text-stone-800 group-hover:scale-105 transition-transform">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-stone-900">Plan & Billing</h4>
            <p className="mt-1 text-xs text-stone-500 leading-relaxed">
              Review current credit quota, view subscription renewal date, and inspect Razorpay payment receipts.
            </p>
            <span className="mt-3 inline-flex items-center text-xs font-semibold text-stone-900 group-hover:underline">
              View Billing →
            </span>
          </Link>
        </div>

        {/* Dual Lists: Recent Chats & Recent Documents */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Recent Conversations */}
          <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-stone-900">Recent Conversations</h3>
                <span className="rounded bg-stone-100 px-1.5 py-0.5 text-[10px] font-medium text-stone-600">
                  {conversations.length}
                </span>
              </div>
              <button
                type="button"
                onClick={handleStartChat}
                className="text-xs font-semibold text-stone-700 hover:text-stone-950 cursor-pointer"
              >
                + New Chat
              </button>
            </div>

            <div className="mt-3 divide-y divide-stone-100">
              {conversations.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-xs text-stone-400">No chat sessions yet</p>
                  <button
                    type="button"
                    onClick={handleStartChat}
                    className="mt-2 text-xs font-semibold text-stone-900 underline"
                  >
                    Start your first academic chat
                  </button>
                </div>
              ) : (
                conversations.slice(0, 5).map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => handleOpenConversation(conv.id)}
                    className="flex items-center justify-between py-3 hover:bg-stone-50 px-2 rounded-xl cursor-pointer transition-colors group"
                  >
                    <div className="truncate mr-3">
                      <p className="truncate text-xs font-semibold text-stone-900 group-hover:text-stone-950">
                        {conv.title || "Untitled Conversation"}
                      </p>
                      <p className="text-[10px] text-stone-400 mt-0.5">
                        {new Date(conv.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <span className="text-xs font-medium text-stone-400 group-hover:text-stone-700 group-hover:translate-x-0.5 transition-all">
                      Open →
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Academic Documents */}
          <div className="rounded-2xl border border-stone-200/80 bg-white p-5 shadow-2xs">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-stone-900">Recent Documents</h3>
                <span className="rounded bg-stone-100 px-1.5 py-0.5 text-[10px] font-medium text-stone-600">
                  {documents.length}
                </span>
              </div>
              <Link
                href="/dashboard/documents"
                className="text-xs font-semibold text-stone-700 hover:text-stone-950"
              >
                View Library →
              </Link>
            </div>

            <div className="mt-3 divide-y divide-stone-100">
              {documents.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-xs text-stone-400">No documents stored</p>
                  <button
                    type="button"
                    onClick={() => openAcademicUploadModal()}
                    className="mt-2 text-xs font-semibold text-stone-900 underline"
                  >
                    Upload a syllabus or notes PDF
                  </button>
                </div>
              ) : (
                documents.slice(0, 5).map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between py-2.5 px-2">
                    <div className="truncate mr-3">
                      <p className="truncate text-xs font-semibold text-stone-900" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <p className="text-[10px] text-stone-400 capitalize mt-0.5">
                        {doc.scope || "personal"} •{" "}
                        {doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB` : "PDF"} •{" "}
                        <span className={doc.processing_status === "completed" ? "text-emerald-600" : "text-amber-600"}>
                          {doc.processing_status}
                        </span>
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => askAboutDocument(doc)}
                      className="rounded-lg border border-stone-200 bg-white px-2.5 py-1 text-[11px] font-medium text-stone-700 hover:bg-stone-50 transition-colors cursor-pointer shrink-0"
                    >
                      Ask AI
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

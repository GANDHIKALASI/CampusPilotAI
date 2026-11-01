"use client";

import React, { useRef, useState } from "react";
import { DashboardProvider, useDashboard } from "@/context/DashboardContext";
import { StudentSidebar } from "@/components/dashboard/StudentSidebar";
import { PricingModal } from "@/components/PricingModal";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const {
    isSidebarOpen,
    setIsSidebarOpen,
    authToken,
    userEmail,
    subscription,
    refreshBillingAndCredits,
    isPricingModalOpen,
    setIsPricingModalOpen,
    showDeleteAccountModal,
    setShowDeleteAccountModal,
    handleDeleteAccount,
    showUploadAcademicModal,
    setShowUploadAcademicModal,
    uploadModalFile,
    setUploadModalFile,
    uploadSemesterId,
    setUploadSemesterId,
    uploadSubjectId,
    setUploadSubjectId,
    uploadUnitId,
    setUploadUnitId,
    uploadModalError,
    uploadModalLoading,
    handleAcademicModalSubmit,
    curriculum,
  } = useDashboard();

  const [deleteConfirmationInput, setDeleteConfirmationInput] = useState("");
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const modalFileInputRef = useRef<HTMLInputElement>(null);

  // Computed options for the academic upload modal
  const selectedSemester = curriculum.find((s) => s.id === uploadSemesterId);
  const availableUploadSubjects = selectedSemester?.subjects || [];
  const selectedSubject = availableUploadSubjects.find((s) => s.id === uploadSubjectId);
  const availableUploadUnits = selectedSubject?.units || [];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#FBFBFA] text-stone-900 font-sans">
      {/* Shared Student Sidebar */}
      <StudentSidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0 h-screen overflow-hidden">
        {/* Mobile Top Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-stone-200/80 bg-white px-4 md:hidden">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="rounded-lg p-1.5 text-stone-600 hover:bg-stone-100"
              aria-label="Open sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="font-semibold text-sm tracking-tight text-stone-900">
              CampusPilot AI
            </span>
          </div>
          <button
            type="button"
            onClick={() => setIsPricingModalOpen(true)}
            className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700 border border-emerald-200/60"
          >
            Upgrade
          </button>
        </header>

        {/* Page Container */}
        <main className="flex-1 min-w-0 overflow-y-auto bg-[#FBFBFA]">
          {children}
        </main>
      </div>

      {/* Global Modals */}

      {/* 1. Razorpay Pricing & Billing Modal */}
      <PricingModal
        isOpen={isPricingModalOpen}
        onClose={() => setIsPricingModalOpen(false)}
        authToken={authToken}
        userEmail={userEmail || undefined}
        subscription={subscription}
        onSubscriptionUpdated={() => refreshBillingAndCredits()}
      />

      {/* 2. Academic Document Upload Modal */}
      {showUploadAcademicModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-700">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-stone-900">Upload & Associate Document</h3>
                  <p className="text-xs text-stone-500">Associate syllabus PDFs or notes with a semester, subject, and unit</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadAcademicModal(false)}
                className="rounded-lg p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-600 cursor-pointer"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleAcademicModalSubmit} className="space-y-4">
              {/* File Selection */}
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                  Select PDF Document *
                </label>
                <input
                  ref={modalFileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) setUploadModalFile(f);
                  }}
                />
                <div
                  onClick={() => modalFileInputRef.current?.click()}
                  className="rounded-xl border-2 border-dashed border-stone-200 bg-stone-50/50 p-4 text-center hover:border-stone-400 hover:bg-stone-50 transition cursor-pointer"
                >
                  {uploadModalFile ? (
                    <div className="flex items-center justify-center gap-2 text-xs font-medium text-stone-800">
                      <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="truncate max-w-[280px]">{uploadModalFile.name}</span>
                      <span className="text-[11px] text-stone-400 font-mono">
                        ({(uploadModalFile.size / 1024).toFixed(0)} KB)
                      </span>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-stone-700">Click to choose a PDF file</p>
                      <p className="text-[11px] text-stone-400">PDF up to 10 MB</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Semester Selection */}
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                  Semester *
                </label>
                <select
                  value={uploadSemesterId}
                  onChange={(e) => {
                    const newSemId = e.target.value;
                    setUploadSemesterId(newSemId);
                    const sem = curriculum.find((s) => s.id === newSemId);
                    if (sem && sem.subjects.length > 0) {
                      setUploadSubjectId(sem.subjects[0].id);
                    } else {
                      setUploadSubjectId("");
                    }
                    setUploadUnitId("");
                  }}
                  className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs text-stone-800 focus:border-stone-400 focus:outline-hidden"
                  required
                >
                  {curriculum.map((sem) => (
                    <option key={sem.id} value={sem.id}>
                      {sem.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Subject Selection */}
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                  Subject *
                </label>
                <select
                  value={uploadSubjectId}
                  onChange={(e) => {
                    setUploadSubjectId(e.target.value);
                    setUploadUnitId("");
                  }}
                  className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs text-stone-800 focus:border-stone-400 focus:outline-hidden"
                  required
                >
                  {availableUploadSubjects.map((subj) => (
                    <option key={subj.id} value={subj.id}>
                      {subj.code ? `${subj.code}: ` : ""}{subj.name} ({subj.subject_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Unit Selection (Optional) */}
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                  Unit (Optional)
                </label>
                <select
                  value={uploadUnitId}
                  onChange={(e) => setUploadUnitId(e.target.value)}
                  className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs text-stone-800 focus:border-stone-400 focus:outline-hidden"
                >
                  <option value="">Whole Subject / General Academic Reference</option>
                  {availableUploadUnits.map((u) => (
                    <option key={u.id} value={u.id}>
                      Unit {u.unit_number}: {u.title}
                    </option>
                  ))}
                </select>
              </div>

              {uploadModalError && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                  {uploadModalError}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setShowUploadAcademicModal(false)}
                  disabled={uploadModalLoading}
                  className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadModalLoading || !uploadModalFile}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-4 py-2 text-xs font-medium text-white shadow-2xs hover:bg-stone-800 disabled:opacity-50 cursor-pointer"
                >
                  {uploadModalLoading ? (
                    <>
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      <span>Saving & Indexing...</span>
                    </>
                  ) : (
                    <span>Save & Associate Document</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Delete Account Danger Modal */}
      {showDeleteAccountModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-rose-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-900">Confirm Account Deletion</h3>
                <p className="text-xs text-stone-500">This action cannot be undone.</p>
              </div>
            </div>

            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 space-y-1">
              <p className="font-semibold">The following data will be permanently removed:</p>
              <ul className="list-disc list-inside text-[11px] space-y-0.5 text-rose-700">
                <li>All personal PDF documents and vector chunk indexes</li>
                <li>All conversation threads and chat history</li>
                <li>Your student profile and authentication record</li>
                <li>All remaining credits and subscription records</li>
              </ul>
            </div>

            {deleteError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                {deleteError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">
                To confirm, type <span className="font-mono text-rose-600 font-bold">DELETE</span> below:
              </label>
              <input
                type="text"
                value={deleteConfirmationInput}
                onChange={(e) => setDeleteConfirmationInput(e.target.value)}
                placeholder="Type DELETE"
                className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs text-stone-900 focus:border-rose-500 focus:outline-hidden"
              />
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteAccountModal(false)}
                disabled={isDeletingAccount}
                className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    setIsDeletingAccount(true);
                    setDeleteError(null);
                    await handleDeleteAccount(deleteConfirmationInput);
                  } catch (err: any) {
                    setDeleteError(err.message || "Failed to delete account");
                    setIsDeletingAccount(false);
                  }
                }}
                disabled={deleteConfirmationInput !== "DELETE" || isDeletingAccount}
                className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-rose-700 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isDeletingAccount ? "Deleting Account..." : "Permanently Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <React.Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center bg-[#FBFBFA]">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-900 border-t-transparent" />
        </div>
      }
    >
      <DashboardProvider>
        <DashboardShell>{children}</DashboardShell>
      </DashboardProvider>
    </React.Suspense>
  );
}

"use client";

import React, { useState, useMemo } from "react";
import { useDashboard } from "@/context/DashboardContext";
import { StoredDocument } from "@/types/database";

export default function MyDocumentsPage() {
  const {
    documents,
    deleteDocument,
    downloadDocument,
    askAboutDocument,
    openAcademicUploadModal,
    initialLoading,
  } = useDashboard();

  const [searchQuery, setSearchQuery] = useState("");
  const [filterScope, setFilterScope] = useState<"all" | "personal" | "shared">("all");
  const [selectedPreviewDoc, setSelectedPreviewDoc] = useState<StoredDocument | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Filtered documents
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Search matching
      const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());

      // Scope matching
      if (filterScope === "personal") {
        return matchesSearch && doc.scope !== "shared";
      }
      if (filterScope === "shared") {
        return matchesSearch && doc.scope === "shared";
      }
      return matchesSearch;
    });
  }, [documents, searchQuery, filterScope]);

  const handleDownload = async (doc: StoredDocument) => {
    try {
      setActionLoadingId(doc.id);
      await downloadDocument(doc.id, doc.filename);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDelete = async (doc: StoredDocument) => {
    if (confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
      try {
        setActionLoadingId(doc.id);
        await deleteDocument(doc.id, doc.filename);
        if (selectedPreviewDoc?.id === doc.id) {
          setSelectedPreviewDoc(null);
        }
      } finally {
        setActionLoadingId(null);
      }
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "Unknown size";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200/80 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
                My Documents
              </h1>
              <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-semibold text-stone-700">
                {documents.length} Files
              </span>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-stone-500">
              Manage personal course materials, lecture notes, and university curriculum PDFs.
            </p>
          </div>

          <button
            type="button"
            onClick={() => openAcademicUploadModal()}
            className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer shrink-0"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Upload Academic PDF</span>
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Scope Tabs */}
          <div className="flex items-center gap-1 rounded-xl border border-stone-200/80 bg-white p-1 shadow-2xs">
            <button
              type="button"
              onClick={() => setFilterScope("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                filterScope === "all"
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              All ({documents.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterScope("personal")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                filterScope === "personal"
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              Personal Uploads ({documents.filter((d) => d.scope !== "shared").length})
            </button>
            <button
              type="button"
              onClick={() => setFilterScope("shared")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                filterScope === "shared"
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              University Syllabus ({documents.filter((d) => d.scope === "shared").length})
            </button>
          </div>

          {/* Search Input */}
          <div className="relative sm:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents by name..."
              className="w-full rounded-xl border border-stone-200/80 bg-white pl-9 pr-4 py-2 text-xs text-stone-900 placeholder:text-stone-400 focus:border-stone-400 focus:outline-hidden shadow-2xs"
            />
            <svg
              className="absolute left-3 top-2.5 h-4 w-4 text-stone-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-2.5 text-stone-400 hover:text-stone-600"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Document Content List / Table */}
        {initialLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-900 border-t-transparent" />
            <p className="mt-3 text-xs text-stone-500">Loading stored documents...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-600">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="mt-4 text-sm font-semibold text-stone-900">
              {searchQuery ? "No matching documents found" : "No academic documents yet"}
            </h3>
            <p className="mt-1 text-xs text-stone-500 max-w-sm mx-auto">
              {searchQuery
                ? `No documents match "${searchQuery}". Try a different keyword or reset filters.`
                : "Upload semester syllabi, question papers, or notes to ground your AI queries in verified course materials."}
            </p>
            {!searchQuery && (
              <button
                type="button"
                onClick={() => openAcademicUploadModal()}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer"
              >
                Upload First Document
              </button>
            )}
          </div>
        ) : (
          <div className="rounded-2xl border border-stone-200/90 bg-white shadow-2xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-stone-200/80 bg-stone-50/70 text-[11px] font-semibold text-stone-600 uppercase tracking-wider">
                    <th className="px-5 py-3">Document Name</th>
                    <th className="px-4 py-3">Scope / Type</th>
                    <th className="px-4 py-3">Uploaded Date</th>
                    <th className="px-4 py-3">File Size</th>
                    <th className="px-4 py-3">Processing Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 text-xs">
                  {filteredDocuments.map((doc) => {
                    const isProcessing = doc.processing_status === "processing";
                    const isFailed = doc.processing_status === "failed";
                    const isCompleted = doc.processing_status === "completed";

                    return (
                      <tr key={doc.id} className="hover:bg-stone-50/60 transition-colors">
                        {/* Name & Icon */}
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-700">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                              </svg>
                            </div>
                            <div className="min-w-0 max-w-xs sm:max-w-md">
                              <p className="truncate font-semibold text-stone-900" title={doc.filename}>
                                {doc.filename}
                              </p>
                              {doc.subject_id && (
                                <p className="text-[10px] text-stone-400 truncate mt-0.5">
                                  Linked to subject
                                </p>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Scope */}
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                              doc.scope === "shared"
                                ? "bg-purple-50 text-purple-700 border border-purple-200/60"
                                : "bg-stone-100 text-stone-700"
                            }`}
                          >
                            {doc.scope === "shared" ? "University" : "Personal"}
                          </span>
                        </td>

                        {/* Upload Date */}
                        <td className="px-4 py-3.5 text-stone-500 text-[11px] whitespace-nowrap">
                          {new Date(doc.created_at).toLocaleDateString(undefined, {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          })}
                        </td>

                        {/* File Size */}
                        <td className="px-4 py-3.5 font-mono text-[11px] text-stone-500 whitespace-nowrap">
                          {formatFileSize(doc.file_size)}
                        </td>

                        {/* Status */}
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                              isCompleted
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                                : isProcessing
                                ? "bg-amber-50 text-amber-700 border border-amber-200/60"
                                : "bg-rose-50 text-rose-700 border border-rose-200/60"
                            }`}
                          >
                            <span
                              className={`h-1.5 w-1.5 rounded-full ${
                                isCompleted
                                  ? "bg-emerald-600"
                                  : isProcessing
                                  ? "bg-amber-600 animate-pulse"
                                  : "bg-rose-600"
                              }`}
                            />
                            <span className="capitalize">{doc.processing_status}</span>
                          </span>
                        </td>

                        {/* Actions */}
                        <td className="px-5 py-3.5 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Ask AI */}
                            <button
                              type="button"
                              onClick={() => askAboutDocument(doc)}
                              className="rounded-lg bg-stone-900 px-2.5 py-1 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer"
                              title="Ask AI questions grounded in this document"
                            >
                              Ask AI
                            </button>

                            {/* Preview / Metadata */}
                            <button
                              type="button"
                              onClick={() => setSelectedPreviewDoc(doc)}
                              className="rounded-lg border border-stone-200 bg-white px-2 py-1 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors cursor-pointer"
                              title="Inspect document metadata & preview"
                            >
                              Details
                            </button>

                            {/* Download */}
                            <button
                              type="button"
                              onClick={() => handleDownload(doc)}
                              disabled={actionLoadingId === doc.id}
                              className="rounded-lg border border-stone-200 bg-white p-1 text-stone-600 hover:bg-stone-50 hover:text-stone-900 transition-colors cursor-pointer disabled:opacity-50"
                              title="Download PDF"
                            >
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            </button>

                            {/* Delete (Personal only) */}
                            {doc.scope !== "shared" && (
                              <button
                                type="button"
                                onClick={() => handleDelete(doc)}
                                disabled={actionLoadingId === doc.id}
                                className="rounded-lg border border-stone-200 bg-white p-1 text-stone-400 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition-colors cursor-pointer disabled:opacity-50"
                                title="Delete personal document"
                              >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Document Details & Preview Drawer / Modal */}
        {selectedPreviewDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
            <div className="w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-700">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-stone-900 truncate max-w-sm">
                      {selectedPreviewDoc.filename}
                    </h3>
                    <p className="text-[11px] text-stone-500">Document Metadata & Verification</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedPreviewDoc(null)}
                  className="rounded-lg p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-600"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3 rounded-xl bg-stone-50 p-3 border border-stone-100">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">Scope</span>
                    <p className="mt-0.5 font-semibold text-stone-800 capitalize">
                      {selectedPreviewDoc.scope || "personal"}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">File Size</span>
                    <p className="mt-0.5 font-semibold text-stone-800 font-mono">
                      {formatFileSize(selectedPreviewDoc.file_size)}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">Status</span>
                    <p className="mt-0.5 font-semibold text-emerald-700 capitalize">
                      {selectedPreviewDoc.processing_status}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">Created</span>
                    <p className="mt-0.5 font-semibold text-stone-800">
                      {new Date(selectedPreviewDoc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-stone-200 bg-white p-3 space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">Storage Path</span>
                  <p className="font-mono text-[11px] text-stone-600 break-all">
                    {selectedPreviewDoc.storage_path || "Stored securely in Supabase Storage"}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setSelectedPreviewDoc(null)}
                  className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => handleDownload(selectedPreviewDoc)}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-stone-300 bg-white px-4 py-2 text-xs font-semibold text-stone-800 hover:bg-stone-50 cursor-pointer"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Download</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const doc = selectedPreviewDoc;
                    setSelectedPreviewDoc(null);
                    askAboutDocument(doc);
                  }}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 cursor-pointer"
                >
                  <span>Ask AI about this Document</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

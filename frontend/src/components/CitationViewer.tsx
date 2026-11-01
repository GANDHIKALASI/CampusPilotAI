"use client";

import React, { useState } from "react";
import { Citation } from "@/types/database";

interface CitationViewerProps {
  citation: Citation;
  isOpen: boolean;
  onClose: () => void;
}

export function SourceDetailModal({ citation, isOpen, onClose }: CitationViewerProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (citation.snippet) {
      navigator.clipboard.writeText(citation.snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const relevancePercent = citation.similarity_score
    ? Math.round(citation.similarity_score * 100)
    : null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="source-detail-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-stone-200/80 bg-stone-50/70 px-5 py-4">
          <div className="flex items-center gap-2.5 min-w-0 pr-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800 border border-emerald-200">
                  Source {citation.source_id}
                </span>
                {relevancePercent && (
                  <span className="text-[11px] font-medium text-stone-500">
                    {relevancePercent}% Match
                  </span>
                )}
              </div>
              <h2
                id="source-detail-title"
                className="mt-1 truncate text-sm font-semibold text-stone-900"
                title={citation.filename}
              >
                {citation.filename}
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-stone-400 hover:bg-stone-200/60 hover:text-stone-700 transition-colors cursor-pointer"
            aria-label="Close source details"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
          {/* Metadata badges */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-stone-600">
            <span className="inline-flex items-center gap-1 rounded-md bg-stone-100 px-2 py-1 font-medium text-stone-700">
              <svg className="h-3 w-3 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Page {citation.page_number}
            </span>

            <span className="inline-flex items-center gap-1 rounded-md bg-stone-100 px-2 py-1 font-medium text-stone-700 capitalize">
              {citation.scope === "shared" ? "🏛️ Shared Curriculum" : "👤 Personal Document"}
            </span>

            {citation.academic_context && (
              <>
                {citation.academic_context.semester_id && (
                  <span className="rounded-md bg-stone-100 px-2 py-1 font-medium text-stone-700">
                    Semester {citation.academic_context.semester_id}
                  </span>
                )}
                {citation.academic_context.subject_name && (
                  <span className="rounded-md bg-stone-100 px-2 py-1 font-medium text-stone-700">
                    {citation.academic_context.subject_name}
                  </span>
                )}
              </>
            )}
          </div>

          {/* Excerpt Passage */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                Verified Document Excerpt
              </h3>
              {citation.snippet && (
                <button
                  type="button"
                  onClick={handleCopy}
                  className="text-[11px] font-medium text-emerald-700 hover:text-emerald-800 transition-colors cursor-pointer"
                >
                  {copied ? "✓ Copied" : "Copy Excerpt"}
                </button>
              )}
            </div>
            <div className="rounded-xl border border-stone-200 bg-stone-50/80 p-3.5 text-xs leading-relaxed text-stone-800 font-serif whitespace-pre-wrap max-h-56 overflow-y-auto">
              {citation.snippet || "Relevant passage extracted during verified semantic search."}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end border-t border-stone-200/80 bg-stone-50/50 px-5 py-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-stone-200 bg-white px-3.5 py-1.5 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors cursor-pointer shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

interface SourcesTrayProps {
  citations?: Citation[];
  onSelectCitation: (citation: Citation) => void;
}

export function SourcesTray({ citations, onSelectCitation }: SourcesTrayProps) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3.5 pt-3 border-t border-stone-200/70">
      <div className="flex items-center gap-1.5 mb-2 text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
        <svg className="h-3 w-3 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span>Sources ({citations.length})</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {citations.map((c) => (
          <button
            key={c.source_id + c.document_id}
            type="button"
            onClick={() => onSelectCitation(c)}
            className="group inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50/90 px-2.5 py-1 text-xs text-stone-700 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-900 transition-all cursor-pointer shadow-2xs"
            title={`View citation from ${c.filename} (Page ${c.page_number})`}
          >
            <span className="font-semibold text-emerald-800 text-[11px]">
              [{c.source_id}]
            </span>
            <span className="max-w-[140px] sm:max-w-[180px] truncate font-medium">
              {c.filename}
            </span>
            <span className="text-[10px] text-stone-400 group-hover:text-emerald-600">
              p.{c.page_number}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

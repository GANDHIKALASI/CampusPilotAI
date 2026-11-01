"use client";

import React, { useState, useRef } from "react";
import { DocumentExtractionResponse, ExtractedPage } from "@/types/document";
import { extractDocumentText } from "@/lib/api";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertTextIntoChat?: (text: string) => void;
}

export function DocumentUploadModal({
  isOpen,
  onClose,
  onInsertTextIntoChat,
}: DocumentUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentExtractionResponse | null>(null);
  const [selectedPageNumber, setSelectedPageNumber] = useState<number>(1);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    setResult(null);
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Please select a valid PDF file (.pdf extension).");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("File exceeds the 10 MB upload limit.");
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMsg(null);

    try {
      const data = await extractDocumentText(selectedFile);
      setResult(data);
      if (data.pages.length > 0) {
        setSelectedPageNumber(1);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to extract text from PDF.";
      setErrorMsg(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUsePageInChat = (page: ExtractedPage) => {
    if (onInsertTextIntoChat) {
      const formattedSnippet = `Regarding ${result?.filename} (Page ${page.page_number}):\n\n"${page.content}"\n\nCan you summarize and explain this?`;
      onInsertTextIntoChat(formattedSnippet);
      onClose();
    }
  };

  const handleUseEntireDocument = () => {
    if (onInsertTextIntoChat && result) {
      const combined = result.pages
        .filter((p) => p.has_text)
        .map((p) => `--- Page ${p.page_number} ---\n${p.content}`)
        .join("\n\n");
      const promptText = `I have uploaded ${result.filename} (${result.total_pages} pages). Here is the extracted syllabus/notes content:\n\n${combined}\n\nCan you analyze this material and outline key exam takeaways?`;
      onInsertTextIntoChat(promptText);
      onClose();
    }
  };

  const selectedPage = result?.pages.find((p) => p.page_number === selectedPageNumber) || result?.pages[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 p-4 backdrop-blur-xs">
      <div className="relative flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-stone-200 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-700">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-tight text-stone-900">
                Upload Document (PDF)
              </h3>
              <p className="text-[11px] text-stone-500">
                In-memory page-by-page text extraction powered by PyMuPDF (10 MB limit)
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {!result ? (
            /* Upload State */
            <div className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-stone-200 bg-stone-50/60 p-8 text-center transition-colors hover:border-stone-300 hover:bg-stone-50"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-2xs">
                  <svg className="h-5 w-5 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-xs font-semibold text-stone-800">
                  {selectedFile ? selectedFile.name : "Click to select a syllabus, notes, or assignment PDF"}
                </p>
                <p className="mt-1 text-[11px] text-stone-500">
                  {selectedFile
                    ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                    : "Maximum file size: 10 MB. In-memory processing only."}
                </p>
              </div>

              {errorMsg && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                  <span className="font-semibold">Error:</span> {errorMsg}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-stone-200 px-3.5 py-2 text-xs font-medium text-stone-600 hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!selectedFile || isUploading}
                  onClick={handleUpload}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-stone-900 px-4 py-2 text-xs font-medium text-white transition-opacity hover:bg-stone-800 disabled:opacity-40"
                >
                  {isUploading ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      <span>Extracting with PyMuPDF...</span>
                    </>
                  ) : (
                    <>
                      <span>Extract Document Text</span>
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Results View State */
            <div className="space-y-4">
              {/* Summary Banner */}
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200 bg-stone-50 p-3.5">
                <div>
                  <h4 className="text-xs font-semibold text-stone-900">
                    {result.filename}
                  </h4>
                  <p className="text-[11px] text-stone-500">
                    {result.total_pages} total pages · {result.extracted_pages} pages with text · {(result.file_size_bytes / 1024).toFixed(1)} KB
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="rounded-lg border border-stone-200 bg-white px-2.5 py-1 text-[11px] font-medium text-stone-600 hover:bg-stone-50"
                  >
                    Upload Another
                  </button>
                  {onInsertTextIntoChat && (
                    <button
                      type="button"
                      onClick={handleUseEntireDocument}
                      className="rounded-lg bg-stone-900 px-3 py-1 text-[11px] font-medium text-white hover:bg-stone-800"
                    >
                      Ask AI About All Pages
                    </button>
                  )}
                </div>
              </div>

              {/* Page Selector Tabs */}
              <div>
                <span className="text-[11px] font-medium text-stone-500 uppercase tracking-wider">
                  Select Page to Inspect:
                </span>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {result.pages.map((p) => (
                    <button
                      key={p.page_number}
                      type="button"
                      onClick={() => setSelectedPageNumber(p.page_number)}
                      className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                        selectedPageNumber === p.page_number
                          ? "border-stone-900 bg-stone-900 text-white"
                          : p.has_text
                          ? "border-stone-200 bg-white text-stone-700 hover:bg-stone-50"
                          : "border-stone-200 bg-stone-100 text-stone-400 italic"
                      }`}
                    >
                      Page {p.page_number} {!p.has_text && "(empty)"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Extracted Page Text Preview */}
              {selectedPage && (
                <div className="rounded-xl border border-stone-200 bg-white p-4">
                  <div className="mb-2 flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-xs font-semibold text-stone-800">
                      Page {selectedPage.page_number} of {result.total_pages} ({selectedPage.character_count} chars)
                    </span>
                    {onInsertTextIntoChat && selectedPage.has_text && (
                      <button
                        type="button"
                        onClick={() => handleUsePageInChat(selectedPage)}
                        className="text-[11px] font-medium text-stone-900 underline underline-offset-2 hover:text-stone-600"
                      >
                        Send Page {selectedPage.page_number} to Chat →
                      </button>
                    )}
                  </div>
                  <pre className="max-h-60 overflow-y-auto whitespace-pre-wrap font-mono text-[12px] leading-relaxed text-stone-700">
                    {selectedPage.content}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

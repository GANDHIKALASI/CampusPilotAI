"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useDashboard } from "@/context/DashboardContext";
import { getSubjectDetail, getSubjectDocuments } from "@/lib/api";
import { SubjectDetailResponse, StoredDocument } from "@/types/database";

export default function SubjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const subjectId = params.subjectId as string;

  const {
    authToken,
    askAboutSubject,
    askAboutDocument,
    openAcademicUploadModal,
    downloadDocument,
  } = useDashboard();

  const [subject, setSubject] = useState<SubjectDetailResponse | null>(null);
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"units" | "practicals" | "project" | "documents">("units");

  useEffect(() => {
    if (!subjectId) return;

    let isMounted = true;
    const loadSubjectData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [subjectData, subjectDocs] = await Promise.all([
          getSubjectDetail(subjectId, authToken),
          getSubjectDocuments(subjectId, authToken).catch(() => []),
        ]);

        if (isMounted) {
          setSubject(subjectData);
          setDocuments(subjectDocs || []);

          // Choose default tab based on subject type
          if (subjectData.subject_type === "project") {
            setActiveTab("project");
          } else if (subjectData.subject_type === "practical") {
            setActiveTab("practicals");
          } else {
            setActiveTab("units");
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to load subject details.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadSubjectData();

    return () => {
      isMounted = false;
    };
  }, [subjectId, authToken]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="h-7 w-7 animate-spin rounded-full border-2 border-stone-900 border-t-transparent" />
        <p className="mt-3 text-xs text-stone-500 font-medium">Loading subject syllabus & modules...</p>
      </div>
    );
  }

  if (error || !subject) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-xs text-rose-800">
          <p className="font-semibold">Unable to load subject</p>
          <p className="mt-1">{error || "Subject not found."}</p>
        </div>
        <Link
          href="/dashboard/learning"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-900 underline"
        >
          ← Back to My Learning
        </Link>
      </div>
    );
  }

  const hasPracticals = subject.practicals && subject.practicals.length > 0;
  const hasProject = Boolean(subject.project_guidelines);
  const units = subject.units || [];

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-stone-500">
          <Link href="/dashboard/learning" className="hover:text-stone-900 transition-colors">
            My Learning
          </Link>
          <span>/</span>
          <span className="font-semibold text-stone-900">{subject.name}</span>
        </div>

        {/* Subject Header Card */}
        <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-stone-900 px-2 py-0.5 font-mono text-xs font-bold text-white shadow-2xs">
                  {subject.code || "BCA"}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                    subject.subject_type === "theory"
                      ? "bg-blue-50 text-blue-700 border border-blue-200/60"
                      : subject.subject_type === "practical"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                      : "bg-purple-50 text-purple-700 border border-purple-200/60"
                  }`}
                >
                  {subject.subject_type}
                </span>
              </div>

              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
                {subject.name}
              </h1>

              {subject.description && (
                <p className="text-xs sm:text-sm text-stone-600 max-w-2xl leading-relaxed">
                  {subject.description}
                </p>
              )}
            </div>

            {/* Header Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => askAboutSubject(subject.name, subject.code || undefined)}
                className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <span>Ask AI about this Subject</span>
              </button>

              <button
                type="button"
                onClick={() => openAcademicUploadModal(subject.id, subject.semester_id)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs font-semibold text-stone-800 shadow-2xs hover:bg-stone-50 transition-colors cursor-pointer"
                title="Associate notes or syllabus PDF with this subject"
              >
                <svg className="h-4 w-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Upload Document</span>
              </button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mt-6 flex items-center gap-1 border-t border-stone-100 pt-4">
            {units.length > 0 && (
              <button
                type="button"
                onClick={() => setActiveTab("units")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                  activeTab === "units"
                    ? "bg-stone-900 text-white shadow-2xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
                }`}
              >
                Syllabus Units ({units.length})
              </button>
            )}

            {hasPracticals && (
              <button
                type="button"
                onClick={() => setActiveTab("practicals")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                  activeTab === "practicals"
                    ? "bg-stone-900 text-white shadow-2xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
                }`}
              >
                Practical Exercises ({subject.practicals.length})
              </button>
            )}

            {hasProject && (
              <button
                type="button"
                onClick={() => setActiveTab("project")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                  activeTab === "project"
                    ? "bg-stone-900 text-white shadow-2xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
                }`}
              >
                Project Guidelines & Rubric
              </button>
            )}

            <button
              type="button"
              onClick={() => setActiveTab("documents")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === "documents"
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
              }`}
            >
              Related Documents ({documents.length})
            </button>
          </div>
        </div>

        {/* Tab 1: Syllabus Units */}
        {activeTab === "units" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-stone-900">
                Course Syllabus & Unit Breakdown
              </h2>
              <span className="text-xs text-stone-500">4 Formal Syllabus Units</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {units.map((unit) => (
                <div
                  key={unit.id}
                  className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="rounded-md bg-stone-100 px-2 py-0.5 text-[11px] font-bold text-stone-800">
                        Unit {unit.unit_number}
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          askAboutSubject(
                            `${subject.name} - Unit ${unit.unit_number}: ${unit.title}`,
                            subject.code || undefined
                          )
                        }
                        className="text-[11px] font-semibold text-stone-700 hover:text-stone-950 underline cursor-pointer"
                      >
                        Ask AI about Unit {unit.unit_number} →
                      </button>
                    </div>

                    <h3 className="text-sm font-bold text-stone-900">
                      {unit.title}
                    </h3>

                    {unit.topics && (
                      <div className="rounded-xl bg-stone-50/70 p-3 border border-stone-100">
                        <p className="text-[10px] uppercase font-bold text-stone-400 tracking-wider mb-1">
                          Key Curriculum Topics
                        </p>
                        <p className="text-xs text-stone-700 leading-relaxed whitespace-pre-line">
                          {unit.topics}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: Practical Exercises */}
        {activeTab === "practicals" && hasPracticals && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-stone-900">
                  Laboratory Programs & Practical Exercises
                </h2>
                <p className="text-xs text-stone-500">
                  Official university lab exercise problem statements and requirements.
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/60">
                {subject.practicals.length} Programs
              </span>
            </div>

            <div className="divide-y divide-stone-100 rounded-2xl border border-stone-200/90 bg-white shadow-2xs overflow-hidden">
              {subject.practicals.map((prac) => (
                <div key={prac.id} className="p-4 sm:p-5 hover:bg-stone-50/60 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-stone-100 px-2 py-0.5 font-mono text-[11px] font-bold text-stone-800">
                          Program {prac.exercise_number}
                        </span>
                        <h3 className="text-xs sm:text-sm font-bold text-stone-900">
                          {prac.title}
                        </h3>
                      </div>
                      {prac.description && (
                        <p className="text-xs text-stone-600 leading-relaxed pl-1">
                          {prac.description}
                        </p>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        askAboutSubject(
                          `${subject.name} Lab Exercise ${prac.exercise_number}: ${prac.title}. Can you explain how to implement this program step-by-step with clean code?`,
                          subject.code || undefined
                        )
                      }
                      className="rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-xs font-semibold text-stone-800 hover:bg-stone-50 transition-colors cursor-pointer shrink-0"
                    >
                      Explain Program in AI
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Project Guidelines */}
        {activeTab === "project" && hasProject && subject.project_guidelines && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-2xs space-y-4">
              <h2 className="text-base font-bold text-stone-900">
                {subject.project_guidelines.title || "Project Guidelines & Requirements"}
              </h2>
              {subject.project_guidelines.description && (
                <p className="text-xs sm:text-sm text-stone-600 leading-relaxed">
                  {subject.project_guidelines.description}
                </p>
              )}
            </div>

            {/* 14 Report Sections */}
            {subject.project_guidelines.report_sections &&
              subject.project_guidelines.report_sections.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-stone-900">
                      Standard Project Report Structure ({subject.project_guidelines.report_sections.length} Sections)
                    </h3>
                    <span className="text-xs text-stone-500">Formal Academic Report Order</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {subject.project_guidelines.report_sections.map((sec) => (
                      <div
                        key={sec.section_number}
                        className="rounded-xl border border-stone-200/90 bg-white p-3.5 shadow-2xs flex items-start gap-3"
                      >
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-stone-100 text-xs font-bold text-stone-700">
                          {sec.section_number}
                        </span>
                        <div>
                          <p className="text-xs font-bold text-stone-900">{sec.title}</p>
                          {sec.description && (
                            <p className="text-[11px] text-stone-500 mt-0.5">{sec.description}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* 5 Evaluation Rubric Criteria */}
            {subject.project_guidelines.evaluation_criteria &&
              subject.project_guidelines.evaluation_criteria.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-stone-900">
                    Evaluation Rubric & Weightage
                  </h3>
                  <div className="divide-y divide-stone-100 rounded-2xl border border-stone-200/90 bg-white shadow-2xs overflow-hidden">
                    {subject.project_guidelines.evaluation_criteria.map((crit, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 text-xs">
                        <div>
                          <p className="font-bold text-stone-900">
                            {crit.title || crit.criterion || `Criterion ${crit.criteria_number || idx + 1}`}
                          </p>
                          {crit.description && (
                            <p className="text-[11px] text-stone-500 mt-0.5">{crit.description}</p>
                          )}
                        </div>
                        {crit.weight && (
                          <span className="rounded-md bg-stone-100 px-2 py-1 font-mono text-xs font-bold text-stone-800 shrink-0">
                            {crit.weight}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Tab 4: Related Documents */}
        {activeTab === "documents" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-stone-900">
                  Subject Documents & Resources
                </h2>
                <p className="text-xs text-stone-500">
                  Materials associated with {subject.name}.
                </p>
              </div>

              <button
                type="button"
                onClick={() => openAcademicUploadModal(subject.id, subject.semester_id)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-3.5 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Upload Document</span>
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center space-y-3">
                <p className="text-xs font-semibold text-stone-800">
                  No documents associated with this subject yet
                </p>
                <p className="text-[11px] text-stone-500 max-w-sm mx-auto">
                  Upload syllabus PDFs, question papers, or personal lecture notes for {subject.name} to ground AI answers in verified files.
                </p>
                <button
                  type="button"
                  onClick={() => openAcademicUploadModal(subject.id, subject.semester_id)}
                  className="rounded-xl border border-stone-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-stone-800 hover:bg-stone-50 transition-colors cursor-pointer"
                >
                  Upload First Document
                </button>
              </div>
            ) : (
              <div className="divide-y divide-stone-100 rounded-2xl border border-stone-200/90 bg-white shadow-2xs overflow-hidden">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-4 hover:bg-stone-50/60 transition-colors">
                    <div className="truncate mr-3">
                      <p className="truncate text-xs font-bold text-stone-900" title={doc.filename}>
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

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => askAboutDocument(doc)}
                        className="rounded-lg bg-stone-900 px-3 py-1.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 cursor-pointer"
                      >
                        Ask AI
                      </button>
                      <button
                        type="button"
                        onClick={() => downloadDocument(doc.id, doc.filename)}
                        className="rounded-lg border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
                      >
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

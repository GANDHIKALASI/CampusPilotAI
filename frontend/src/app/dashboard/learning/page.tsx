"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDashboard } from "@/context/DashboardContext";
import { SubjectItem } from "@/types/database";

export default function MyLearningPage() {
  const router = useRouter();
  const { curriculum, askAboutSubject, initialLoading } = useDashboard();
  const [activeSemFilter, setActiveSemFilter] = useState<number | "all">("all");

  const semestersToDisplay = curriculum.filter((sem) => {
    if (activeSemFilter === "all") return true;
    return (sem.semester_number ?? (sem.name.includes("VI") ? 6 : 5)) === activeSemFilter;
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200/80 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
                My Learning
              </h1>
              <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-semibold text-stone-700">
                BCA Curriculum
              </span>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-stone-500">
              Official university curriculum, 4-unit syllabus breakdowns, practical programs, and project rubrics.
            </p>
          </div>

          {/* Semester Filter Tabs */}
          <div className="flex items-center gap-1 rounded-xl border border-stone-200/80 bg-white p-1 shadow-2xs self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setActiveSemFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                activeSemFilter === "all"
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              All Semesters
            </button>
            <button
              type="button"
              onClick={() => setActiveSemFilter(5)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                activeSemFilter === 5
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              Semester V
            </button>
            <button
              type="button"
              onClick={() => setActiveSemFilter(6)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                activeSemFilter === 6
                  ? "bg-stone-900 text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
              }`}
            >
              Semester VI
            </button>
          </div>
        </div>

        {/* Curriculum Sections */}
        {initialLoading && curriculum.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-900 border-t-transparent" />
            <p className="mt-3 text-xs text-stone-500">Loading BCA academic curriculum...</p>
          </div>
        ) : semestersToDisplay.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-12 text-center">
            <p className="text-sm font-semibold text-stone-900">No curriculum data available</p>
            <p className="mt-1 text-xs text-stone-500">Ensure academic data has been seeded.</p>
          </div>
        ) : (
          <div className="space-y-10">
            {semestersToDisplay.map((sem) => (
              <section key={sem.id} className="space-y-4">
                {/* Semester Header */}
                <div className="flex items-center justify-between border-b border-stone-200 pb-2">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-stone-900 text-xs font-bold text-white shadow-2xs">
                      {sem.semester_number ?? (sem.name.includes("VI") ? "VI" : "V")}
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-stone-900 tracking-tight">
                        {sem.name}
                      </h2>
                    </div>
                  </div>
                  <span className="text-xs text-stone-500 font-medium">
                    {sem.subjects.length} Subjects
                  </span>
                </div>

                {/* Subject Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {sem.subjects.map((subject: SubjectItem) => {
                    const isTheory = subject.subject_type === "theory";
                    const isPractical = subject.subject_type === "practical";
                    const isProject = subject.subject_type === "project";

                    return (
                      <div
                        key={subject.id}
                        className="group relative flex flex-col justify-between rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs hover:border-stone-300 hover:shadow-xs transition-all"
                      >
                        <div>
                          {/* Subject Header */}
                          <div className="flex items-start justify-between gap-2">
                            <span className="rounded-md bg-stone-100 px-2 py-0.5 font-mono text-[11px] font-bold text-stone-800">
                              {subject.code || "BCA"}
                            </span>
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                                isTheory
                                  ? "bg-blue-50 text-blue-700 border border-blue-200/60"
                                  : isPractical
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                                  : "bg-purple-50 text-purple-700 border border-purple-200/60"
                              }`}
                            >
                              {subject.subject_type}
                            </span>
                          </div>

                          {/* Title */}
                          <h3 className="mt-3 text-sm font-bold text-stone-900 group-hover:text-stone-950">
                            {subject.name}
                          </h3>

                          {/* Quick summary metrics */}
                          <p className="mt-1 text-xs text-stone-500 leading-relaxed">
                            {subject.units && subject.units.length > 0
                              ? `${subject.units.length} Units Syllabus`
                              : isPractical
                              ? "Practical Lab Exercises"
                              : isProject
                              ? "Formal Project Guidelines"
                              : "Core Subject Syllabus"}
                          </p>

                          {/* Unit Pill Preview if available */}
                          {subject.units && subject.units.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1.5">
                              {subject.units.slice(0, 4).map((u) => (
                                <span
                                  key={u.id}
                                  className="rounded bg-stone-50 px-2 py-0.5 text-[10px] text-stone-600 border border-stone-100"
                                  title={u.title}
                                >
                                  U{u.unit_number}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Action buttons */}
                        <div className="mt-5 flex items-center justify-between border-t border-stone-100 pt-3">
                          <Link
                            href={`/dashboard/learning/${subject.id}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-stone-900 hover:text-stone-700 group-hover:underline"
                          >
                            <span>Explore Details</span>
                            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </Link>

                          <button
                            type="button"
                            onClick={() => askAboutSubject(subject.name, subject.code || undefined)}
                            className="rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-medium text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer"
                            title="Ask AI questions about this subject"
                          >
                            Ask AI
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

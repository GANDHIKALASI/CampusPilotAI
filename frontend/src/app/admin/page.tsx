"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import {
  getPlatformMetrics,
  listAdminStudents,
  createStudentAccount,
  updateStudentStatus,
  assignStudentPlan,
  listAdminPayments,
  listAdminSubscriptions,
  resolveSubscription,
  listAdminWaitlist,
  updateWaitlistStatus,
  listDocuments,
  uploadDocumentAuthenticated,
  deleteSharedDocument,
  deleteAdminStudent,
  deleteMyAccount,
} from "@/lib/api";
import {
  PlatformMetrics,
  AdminStudentItem,
  StoredDocument,
  WaitlistAdminItem,
} from "@/types/database";

type AdminTab =
  | "overview"
  | "students"
  | "documents"
  | "payments"
  | "subscriptions"
  | "waitlist"
  | "analytics"
  | "settings";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [authToken, setAuthToken] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Data states
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [students, setStudents] = useState<AdminStudentItem[]>([]);
  const [searchStudent, setSearchStudent] = useState("");
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [waitlist, setWaitlist] = useState<WaitlistAdminItem[]>([]);

  // Modals
  const [isCreateStudentOpen, setIsCreateStudentOpen] = useState(false);
  const [newStudentForm, setNewStudentForm] = useState({
    email: "",
    password: "",
    full_name: "",
    institution: "",
  });

  const [isAssignPlanOpen, setIsAssignPlanOpen] = useState(false);
  const [assignPlanTarget, setAssignPlanTarget] = useState<AdminStudentItem | null>(null);
  const [assignPlanForm, setAssignPlanForm] = useState<{ plan: "monthly" | "yearly"; days: number; reason: string }>({
    plan: "monthly",
    days: 30,
    reason: "Administrative academic plan grant",
  });

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.push("/login?redirectedFrom=/admin");
        return;
      }
      setAuthToken(session.access_token);
      setUserEmail(session.user.email || "Admin");

      // Verify administrative access strictly via backend verification endpoint
      try {
        const m = await getPlatformMetrics(session.access_token);
        setMetrics(m);
        setIsAuthorized(true);
        loadTabData("overview", session.access_token);
      } catch (err: any) {
        setIsAuthorized(false);
        setLoading(false);
      }
    });
  }, [router]);

  const loadTabData = async (tab: AdminTab, token?: string) => {
    const t = token || authToken;
    if (!t) return;
    setLoading(true);
    setNotice(null);

    try {
      if (tab === "overview") {
        const m = await getPlatformMetrics(t);
        setMetrics(m);
      } else if (tab === "students") {
        const st = await listAdminStudents(searchStudent, t);
        setStudents(st);
      } else if (tab === "documents") {
        const docs = await listDocuments(t);
        setDocuments(docs.filter((d) => d.scope === "shared"));
      } else if (tab === "payments") {
        const pays = await listAdminPayments(t);
        setPayments(pays);
      } else if (tab === "subscriptions") {
        const subs = await listAdminSubscriptions(t);
        setSubscriptions(subs);
      } else if (tab === "waitlist") {
        const wl = await listAdminWaitlist(undefined, t);
        setWaitlist(wl);
      } else if (tab === "analytics") {
        const [m, st, pays, subs] = await Promise.all([
          getPlatformMetrics(t),
          listAdminStudents(undefined, t),
          listAdminPayments(t),
          listAdminSubscriptions(t),
        ]);
        setMetrics(m);
        setStudents(st);
        setPayments(pays);
        setSubscriptions(subs);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load tab data.";
      setNotice({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: AdminTab) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
    loadTabData(tab);
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStudentForm.email || !newStudentForm.password || !newStudentForm.full_name) return;
    setActionLoading(true);

    try {
      await createStudentAccount(newStudentForm, authToken);
      setNotice({ type: "success", message: `Account created for ${newStudentForm.email} with 20 free credits.` });
      setIsCreateStudentOpen(false);
      setNewStudentForm({ email: "", password: "", full_name: "", institution: "" });
      loadTabData("students");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create account.";
      setNotice({ type: "error", message: msg });
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleStudentStatus = async (student: AdminStudentItem) => {
    const nextStatus = student.status === "active" ? "suspended" : "active";
    if (!confirm(`Are you sure you want to mark ${student.full_name} as ${nextStatus}?`)) return;

    try {
      await updateStudentStatus(student.id, nextStatus as any, authToken);
      setNotice({ type: "success", message: `Updated student status to ${nextStatus}.` });
      loadTabData("students");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update status.";
      setNotice({ type: "error", message: msg });
    }
  };

  const handleAssignPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignPlanTarget) return;
    setActionLoading(true);

    try {
      await assignStudentPlan(
        assignPlanTarget.id,
        assignPlanForm.plan,
        Number(assignPlanForm.days),
        assignPlanForm.reason,
        authToken
      );
      setNotice({ type: "success", message: `Assigned ${assignPlanForm.plan} plan to ${assignPlanTarget.full_name}.` });
      setIsAssignPlanOpen(false);
      setAssignPlanTarget(null);
      loadTabData("students");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to assign plan.";
      setNotice({ type: "error", message: msg });
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadSharedDocument = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setActionLoading(true);
    setNotice(null);

    try {
      await uploadDocumentAuthenticated(file, authToken, "shared");
      setNotice({ type: "success", message: `Uploaded and indexed shared document: ${file.name}` });
      loadTabData("documents");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload shared document.";
      setNotice({ type: "error", message: msg });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteSharedDoc = async (docId: string, filename: string) => {
    if (!confirm(`Delete shared academic document "${filename}" and its vector chunks?`)) return;
    try {
      await deleteSharedDocument(docId, authToken);
      setNotice({ type: "success", message: `Deleted ${filename}.` });
      loadTabData("documents");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete document.";
      setNotice({ type: "error", message: msg });
    }
  };

  const handleDeleteStudent = async (student: AdminStudentItem) => {
    if (!confirm(`Permanently delete student account for "${student.full_name}" (${student.email})? All associated personal documents, conversations, and records will be deleted.`)) return;
    try {
      await deleteAdminStudent(student.id, authToken);
      setNotice({ type: "success", message: `Permanently deleted account for ${student.full_name}.` });
      loadTabData("students");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete student account.";
      setNotice({ type: "error", message: msg });
    }
  };

  const handleUpdateWaitlist = async (entryId: string, status: "pending" | "approved" | "rejected" | "contacted") => {
    try {
      await updateWaitlistStatus(entryId, status, authToken);
      setNotice({ type: "success", message: `Waitlist entry updated to ${status}.` });
      loadTabData("waitlist");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update waitlist entry.";
      setNotice({ type: "error", message: msg });
    }
  };

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  };

  // 1. Access Denied State (Strictly enforced when backend verifies non-admin)
  if (isAuthorized === false) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#FBFBFA] px-4 text-center">
        <div className="rounded-2xl border border-rose-200 bg-white p-8 max-w-md shadow-xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-rose-50 text-rose-600">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="mt-4 text-base font-semibold text-stone-900">Access Denied</h2>
          <p className="mt-1.5 text-xs text-stone-500 leading-relaxed">
            Your authenticated account does not possess administrative privileges. This area is strictly reserved for campus administrators.
          </p>
          <div className="mt-6 flex flex-col gap-2">
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 cursor-pointer"
            >
              Return to Student Workspace
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-xs font-medium text-stone-600 hover:bg-stone-50 cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  const navItems: { id: AdminTab; label: string; icon: React.ReactNode }[] = [
    {
      id: "overview",
      label: "Platform Overview",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      id: "students",
      label: "Student Management",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ),
    },
    {
      id: "documents",
      label: "Academic Documents",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
        </svg>
      ),
    },
    {
      id: "payments",
      label: "Payments",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
    },
    {
      id: "subscriptions",
      label: "Subscriptions",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
    },
    {
      id: "waitlist",
      label: "Waitlist Management",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: "settings",
      label: "Admin Settings",
      icon: (
        <svg className="h-4 w-4 shrink-0 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#FBFBFA] text-[#1C1917] antialiased">
      {/* =====================================================================
          1. DEDICATED ADMIN SHELL: LIGHT-THEMED SIDEBAR
          ===================================================================== */}
      <aside
        className={`border-r border-stone-200 bg-[#F7F7F5] flex flex-col justify-between transition-all duration-300 ease-in-out shrink-0 select-none ${
          isSidebarOpen ? "w-64 sm:w-72 p-3.5 opacity-100" : "w-0 p-0 border-r-0 overflow-hidden opacity-0 pointer-events-none"
        }`}
      >
        <div className="flex flex-col space-y-4">
          {/* Top Branding & Admin Identity */}
          <div className="flex items-center justify-between pb-3 border-b border-stone-200">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-stone-200 bg-white shadow-2xs">
                <Image src="/logo.jpg" alt="CampusPilot Logo" width={32} height={32} className="rounded-md object-cover" />
              </div>
              <div>
                <span className="text-xs font-semibold tracking-tight text-stone-900 block leading-tight">
                  CampusPilot AI
                </span>
                <span className="inline-block rounded bg-amber-100/80 border border-amber-200 px-1.5 py-0.2 text-[9px] font-bold text-amber-900 uppercase tracking-wider">
                  Admin Platform
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsSidebarOpen(false)}
              className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-200/60 hover:text-stone-700 transition-colors cursor-pointer"
              title="Close sidebar"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <rect x="3" y="3" width="18" height="18" rx="2" strokeWidth={1.75} />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 3v18M14 9l-3 3 3 3" />
              </svg>
            </button>
          </div>

          {/* Navigation Links (Purely Administrative) */}
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleTabChange(item.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                    isActive
                      ? "bg-white text-stone-900 font-semibold shadow-2xs border border-stone-200"
                      : "text-stone-600 hover:bg-stone-200/60 hover:text-stone-900"
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Administrator Identity & Logout */}
        <div className="border-t border-stone-200 pt-3 space-y-2">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2 truncate">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-stone-900 text-[11px] font-bold text-white shadow-2xs">
                AD
              </div>
              <div className="truncate text-left leading-tight">
                <span className="block truncate text-xs font-semibold text-stone-900">
                  {userEmail}
                </span>
                <span className="block text-[10px] text-amber-700 font-medium">
                  Administrator
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg p-1.5 text-stone-400 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer"
              title="Sign out of admin console"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* =====================================================================
          2. MAIN ADMINISTRATIVE CONTENT AREA
          ===================================================================== */}
      <main className="flex flex-1 flex-col overflow-hidden bg-[#FBFBFA]">
        {/* Top Header Bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-stone-200/80 bg-white/80 px-4 sm:px-6 backdrop-blur-md">
          <div className="flex items-center gap-3">
            {!isSidebarOpen && (
              <button
                type="button"
                onClick={() => setIsSidebarOpen(true)}
                className="flex items-center justify-center rounded-lg p-1.5 text-stone-600 hover:bg-stone-100 hover:text-stone-900 transition-colors cursor-pointer"
                title="Open sidebar"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <rect x="3" y="3" width="18" height="18" rx="2" strokeWidth={1.75} />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 3v18M13 15l3-3-3-3" />
                </svg>
              </button>
            )}

            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold text-stone-900 capitalize">
                {activeTab === "overview"
                  ? "Platform Telemetry & Overview"
                  : activeTab === "students"
                  ? "Student Account Management"
                  : activeTab === "documents"
                  ? "Campus Shared Documents"
                  : activeTab === "payments"
                  ? "Payment Transaction Logs"
                  : activeTab === "subscriptions"
                  ? "Subscriptions Ledger"
                  : activeTab === "waitlist"
                  ? "Waitlist Application Triage"
                  : activeTab === "analytics"
                  ? "Platform Analytics & Growth"
                  : "Platform & Security Settings"}
              </h1>
              <span className="rounded bg-amber-50 border border-amber-200 px-1.5 py-0.5 text-[9px] font-bold text-amber-800 uppercase tracking-wider">
                Admin Area
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => loadTabData(activeTab)}
              className="rounded-xl border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 shadow-2xs hover:bg-stone-50 cursor-pointer"
            >
              ↻ Refresh
            </button>
          </div>
        </header>

        {/* Scrollable Main Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-8">
          {/* Notice Alert */}
          {notice && (
            <div
              className={`mb-6 rounded-xl border p-3.5 text-xs ${
                notice.type === "success"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              {notice.message}
            </div>
          )}

          {/* ===================================================================
              TAB 1: OVERVIEW
              =================================================================== */}
          {activeTab === "overview" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Platform Overview
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Key administrative metrics across student accounts, verified subscriptions, and repository ingestion.
                </p>
              </div>

              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Total Students
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {metrics?.total_students ?? 0}
                  </div>
                  <span className="text-[10px] text-stone-400">Created accounts</span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Active Subscriptions
                  </span>
                  <div className="mt-2 text-2xl font-bold text-emerald-700">
                    {metrics?.active_subscriptions ?? 0}
                  </div>
                  <span className="text-[10px] text-emerald-600 font-medium">Pro paid access</span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Expired Plans
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-700">
                    {metrics?.expired_subscriptions ?? 0}
                  </div>
                  <span className="text-[10px] text-stone-400">Reverted to free</span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Documents Indexed
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {metrics?.total_documents ?? 0}
                  </div>
                  <span className="text-[10px] text-stone-400">Syllabi & PDFs</span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Total Revenue
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    ₹{metrics?.total_payments_inr?.toFixed(0) ?? "0"}
                  </div>
                  <span className="text-[10px] text-stone-400">
                    {metrics?.total_transactions_count ?? 0} transactions
                  </span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div
                  onClick={() => handleTabChange("students")}
                  className="cursor-pointer rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs hover:border-stone-400 transition-all"
                >
                  <div className="font-semibold text-xs text-stone-900">Invite New Student →</div>
                  <p className="mt-1 text-xs text-stone-500 leading-relaxed">
                    Provision student credentials with 20 initial free credits automatically.
                  </p>
                </div>

                <div
                  onClick={() => handleTabChange("documents")}
                  className="cursor-pointer rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs hover:border-stone-400 transition-all"
                >
                  <div className="font-semibold text-xs text-stone-900">Upload Shared PDF →</div>
                  <p className="mt-1 text-xs text-stone-500 leading-relaxed">
                    Index syllabus or lecture slides accessible to all students.
                  </p>
                </div>

                <div
                  onClick={() => handleTabChange("waitlist")}
                  className="cursor-pointer rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs hover:border-stone-400 transition-all"
                >
                  <div className="font-semibold text-xs text-stone-900">Triage Waitlist →</div>
                  <p className="mt-1 text-xs text-stone-500 leading-relaxed">
                    Review student waitlist applications and approve access invitations.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 2: STUDENT MANAGEMENT
              =================================================================== */}
          {activeTab === "students" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-stone-900">
                    Student Accounts
                  </h2>
                  <p className="mt-1 text-xs text-stone-500">
                    Create invite-only student accounts, suspend access, and grant plans.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCreateStudentOpen(true)}
                  className="rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 cursor-pointer"
                >
                  + Create Student Account
                </button>
              </div>

              {/* Search */}
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={searchStudent}
                  onChange={(e) => setSearchStudent(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadTabData("students")}
                  placeholder="Search by student name or email..."
                  className="w-full max-w-sm rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs text-stone-900 placeholder:text-stone-400 focus:outline-hidden"
                />
                <button
                  type="button"
                  onClick={() => loadTabData("students")}
                  className="rounded-xl border border-stone-200 bg-white px-3.5 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 shadow-2xs cursor-pointer"
                >
                  Search
                </button>
              </div>

              {/* Table */}
              <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                  <thead className="bg-[#F7F7F5] text-stone-600">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Student</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Credits</th>
                      <th className="px-4 py-3 font-semibold">Plan</th>
                      <th className="px-4 py-3 font-semibold">Plan Expiry</th>
                      <th className="px-4 py-3 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {students.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-stone-400 italic">
                          No students found matching query.
                        </td>
                      </tr>
                    ) : (
                      students.map((st) => (
                        <tr key={st.id} className="hover:bg-stone-50/60 transition-colors">
                          <td className="px-4 py-3">
                            <div className="font-medium text-stone-900">{st.full_name}</div>
                            <div className="text-[11px] text-stone-400">{st.email}</div>
                            {st.institution && (
                              <div className="text-[10px] text-stone-500 italic">{st.institution}</div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                                st.status === "active"
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : "bg-rose-50 text-rose-700 border border-rose-200"
                              }`}
                            >
                              {st.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-semibold text-stone-900">{st.credits_balance}</span>
                            <span className="text-[10px] text-stone-400 ml-1">credits</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-semibold uppercase tracking-wider text-xs">
                              {st.plan}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-stone-500">
                            {st.subscription_expiry
                              ? new Date(st.subscription_expiry).toLocaleDateString()
                              : "—"}
                          </td>
                          <td className="px-4 py-3 text-right space-x-2">
                            <button
                              type="button"
                              onClick={() => {
                                setAssignPlanTarget(st);
                                setIsAssignPlanOpen(true);
                              }}
                              className="font-medium text-stone-700 hover:text-stone-950 underline cursor-pointer"
                            >
                              Assign Plan
                            </button>
                            <button
                              type="button"
                              onClick={() => handleToggleStudentStatus(st)}
                              className={`font-medium cursor-pointer ${
                                st.status === "active"
                                  ? "text-rose-600 hover:text-rose-800"
                                  : "text-emerald-700 hover:text-emerald-900"
                              }`}
                            >
                              {st.status === "active" ? "Suspend" : "Activate"}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteStudent(st)}
                              className="font-medium text-rose-600 hover:text-rose-800 hover:underline cursor-pointer"
                              title="Permanently delete student account"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 3: ACADEMIC DOCUMENTS
              =================================================================== */}
          {activeTab === "documents" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-stone-900">
                    Campus Shared Academic Library
                  </h2>
                  <p className="mt-1 text-xs text-stone-500">
                    Upload and manage shared syllabus and lecture notes accessible by all students.
                  </p>
                </div>

                <label className="inline-flex items-center gap-1.5 rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 cursor-pointer">
                  <input
                    type="file"
                    accept="application/pdf"
                    className="hidden"
                    onChange={handleUploadSharedDocument}
                    disabled={actionLoading}
                  />
                  <span>{actionLoading ? "Uploading & Indexing..." : "+ Upload Shared PDF"}</span>
                </label>
              </div>

              <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                  <thead className="bg-[#F7F7F5] text-stone-600">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Document Name</th>
                      <th className="px-4 py-3 font-semibold">Scope</th>
                      <th className="px-4 py-3 font-semibold">File Size</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Date Uploaded</th>
                      <th className="px-4 py-3 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {documents.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-stone-400 italic">
                          No shared academic documents uploaded yet.
                        </td>
                      </tr>
                    ) : (
                      documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-stone-50/60 transition-colors">
                          <td className="px-4 py-3 font-medium text-stone-900">{doc.filename}</td>
                          <td className="px-4 py-3">
                            <span className="rounded-full bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[9px] font-bold text-indigo-700 uppercase">
                              Shared Library
                            </span>
                          </td>
                          <td className="px-4 py-3 text-stone-500">
                            {(doc.file_size / 1024).toFixed(0)} KB
                          </td>
                          <td className="px-4 py-3">
                            <span className="rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[9px] font-semibold">
                              {doc.processing_status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-stone-500">
                            {new Date(doc.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              type="button"
                              onClick={() => handleDeleteSharedDoc(doc.id, doc.filename)}
                              className="font-medium text-rose-600 hover:text-rose-800 cursor-pointer"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 4: PAYMENTS
              =================================================================== */}
          {activeTab === "payments" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Payment Transactions
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Transaction receipts verified via Razorpay Standard Checkout.
                </p>
              </div>

              <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                  <thead className="bg-[#F7F7F5] text-stone-600">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Date</th>
                      <th className="px-4 py-3 font-semibold">Plan</th>
                      <th className="px-4 py-3 font-semibold">Amount</th>
                      <th className="px-4 py-3 font-semibold">Order ID</th>
                      <th className="px-4 py-3 font-semibold">Payment ID</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {payments.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-stone-400 italic">
                          No transactions recorded yet.
                        </td>
                      </tr>
                    ) : (
                      payments.map((p, idx) => (
                        <tr key={p.id || idx} className="hover:bg-stone-50/60">
                          <td className="px-4 py-3 text-stone-600">
                            {p.created_at ? new Date(p.created_at).toLocaleString() : "—"}
                          </td>
                          <td className="px-4 py-3 font-medium uppercase text-stone-900">{p.plan}</td>
                          <td className="px-4 py-3 font-semibold text-stone-900">
                            ₹{p.amount_inr || (p.amount_paise ? p.amount_paise / 100 : 0)}
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-stone-500">
                            {p.razorpay_order_id}
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-stone-500">
                            {p.razorpay_payment_id || "—"}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                                p.status === "captured"
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : "bg-stone-100 text-stone-600"
                              }`}
                            >
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 5: SUBSCRIPTIONS
              =================================================================== */}
          {activeTab === "subscriptions" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Active Subscriptions Ledger
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Review student access periods, expiry schedules, and manual renewal grants.
                </p>
              </div>

              <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                  <thead className="bg-[#F7F7F5] text-stone-600">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Student ID</th>
                      <th className="px-4 py-3 font-semibold">Plan</th>
                      <th className="px-4 py-3 font-semibold">Period Start</th>
                      <th className="px-4 py-3 font-semibold">Period End</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {subscriptions.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-stone-400 italic">
                          No subscription records found.
                        </td>
                      </tr>
                    ) : (
                      subscriptions.map((s, idx) => (
                        <tr key={s.id || idx} className="hover:bg-stone-50/60">
                          <td className="px-4 py-3 font-mono text-[11px] text-stone-600">
                            {s.user_id}
                          </td>
                          <td className="px-4 py-3 font-semibold uppercase text-stone-900">
                            {s.plan}
                          </td>
                          <td className="px-4 py-3 text-stone-500">
                            {s.current_period_start ? new Date(s.current_period_start).toLocaleDateString() : "—"}
                          </td>
                          <td className="px-4 py-3 text-stone-500">
                            {s.current_period_end ? new Date(s.current_period_end).toLocaleDateString() : "—"}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                                s.status === "active"
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : "bg-stone-100 text-stone-600"
                              }`}
                            >
                              {s.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              type="button"
                              onClick={async () => {
                                const days = prompt("Enter additional days to grant access:", "30");
                                if (!days || isNaN(Number(days))) return;
                                try {
                                  await resolveSubscription(s.user_id, s.plan || "monthly", Number(days), "Manual admin renewal", authToken);
                                  setNotice({ type: "success", message: `Extended subscription by ${days} days.` });
                                  loadTabData("subscriptions");
                                } catch (err: any) {
                                  setNotice({ type: "error", message: err.message || "Failed to extend subscription." });
                                }
                              }}
                              className="font-medium text-stone-700 hover:text-stone-950 underline cursor-pointer"
                            >
                              Extend Days
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 6: WAITLIST MANAGEMENT
              =================================================================== */}
          {activeTab === "waitlist" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Student Waitlist Applications
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Triage incoming student registration requests and approve invitation access.
                </p>
              </div>

              <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xs">
                <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                  <thead className="bg-[#F7F7F5] text-stone-600">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Applicant</th>
                      <th className="px-4 py-3 font-semibold">Institution</th>
                      <th className="px-4 py-3 font-semibold">Date Applied</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {waitlist.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-stone-400 italic">
                          No waitlist applications found.
                        </td>
                      </tr>
                    ) : (
                      waitlist.map((w) => (
                        <tr key={w.id} className="hover:bg-stone-50/60 transition-colors">
                          <td className="px-4 py-3">
                            <div className="font-medium text-stone-900">{w.full_name}</div>
                            <div className="text-[11px] text-stone-400">{w.email}</div>
                          </td>
                          <td className="px-4 py-3 text-stone-600">{w.institution || "—"}</td>
                          <td className="px-4 py-3 text-stone-500">
                            {new Date(w.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase ${
                                w.status === "approved"
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : w.status === "contacted"
                                  ? "bg-amber-50 text-amber-800 border border-amber-200"
                                  : "bg-stone-100 text-stone-600"
                              }`}
                            >
                              {w.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right space-x-2">
                            <button
                              type="button"
                              onClick={() => handleUpdateWaitlist(w.id, "approved")}
                              className="font-medium text-emerald-700 hover:text-emerald-900 cursor-pointer"
                            >
                              Approve
                            </button>
                            <button
                              type="button"
                              onClick={() => handleUpdateWaitlist(w.id, "contacted")}
                              className="font-medium text-stone-600 hover:text-stone-900 cursor-pointer"
                            >
                              Contacted
                            </button>
                            <button
                              type="button"
                              onClick={() => handleUpdateWaitlist(w.id, "rejected")}
                              className="font-medium text-rose-600 hover:text-rose-800 cursor-pointer"
                            >
                              Reject
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 7: ANALYTICS
              =================================================================== */}
          {activeTab === "analytics" && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Platform Telemetry & Growth
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Conversion metrics, revenue distribution, and document indexing volume.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Paid Conversion Rate
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {metrics && metrics.total_students > 0
                      ? `${((metrics.active_subscriptions / metrics.total_students) * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                  <span className="text-[10px] text-stone-400">
                    {metrics?.active_subscriptions ?? 0} subscribers of {metrics?.total_students ?? 0} students
                  </span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Average Revenue Per Student
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    ₹{metrics && metrics.total_students > 0
                      ? (metrics.total_payments_inr / metrics.total_students).toFixed(0)
                      : "0"}
                  </div>
                  <span className="text-[10px] text-stone-400">Across all provisioned students</span>
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-2xs">
                  <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider">
                    Total Ingested Documents
                  </span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {metrics?.total_documents ?? 0}
                  </div>
                  <span className="text-[10px] text-stone-400">Vectorized chunk repository</span>
                </div>
              </div>

              <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-2xs space-y-4">
                <h3 className="text-sm font-semibold text-stone-900">Plan Structure & Pricing Ratios</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-stone-200 p-4 bg-[#F7F7F5]">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-stone-900">Monthly Plan (₹99)</span>
                      <span className="rounded bg-stone-200 px-2 py-0.5 text-[10px] font-bold">30 Days</span>
                    </div>
                    <p className="mt-1 text-xs text-stone-500">
                      Standard student tier for modular exam preparation.
                    </p>
                  </div>

                  <div className="rounded-xl border border-stone-200 p-4 bg-[#F7F7F5]">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-stone-900">Yearly Plan (₹999)</span>
                      <span className="rounded bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold">365 Days</span>
                    </div>
                    <p className="mt-1 text-xs text-stone-500">
                      Annual university coursework tier (saves ₹189/yr).
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              TAB 8: ADMIN SETTINGS
              =================================================================== */}
          {activeTab === "settings" && (
            <div className="space-y-6 max-w-3xl mx-auto">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">
                  Administrative Settings
                </h2>
                <p className="mt-1 text-xs text-stone-500">
                  Identity verification, connected cloud services, and security enforcement.
                </p>
              </div>

              <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-2xs space-y-4">
                <h3 className="text-sm font-semibold text-stone-900">Admin Account Identity</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[10px] font-semibold text-stone-400 uppercase">Authenticated Email</span>
                    <p className="font-medium text-stone-900 mt-1">{userEmail}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-stone-400 uppercase">Verification Level</span>
                    <p className="font-medium text-emerald-700 mt-1">Backend Verified Administrator</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-2xs space-y-4">
                <h3 className="text-sm font-semibold text-stone-900">System Environment & Services</h3>
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-stone-600">Authentication & Database</span>
                    <span className="rounded bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 text-[10px] font-medium">Supabase Connected</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-stone-600">AI Intelligence Model</span>
                    <span className="font-mono text-[11px] text-stone-800">gemini-3.5-flash-lite</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-stone-600">Payment Gateway</span>
                    <span className="font-mono text-[11px] text-stone-800">Razorpay Standard Checkout</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-stone-600">Initial Free Student Credits</span>
                    <span className="font-semibold text-stone-900">20 Credits / Student</span>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-6 shadow-2xs flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-rose-900">Sign Out of Admin Console</h4>
                  <p className="text-[11px] text-stone-500 mt-0.5">End your privileged administrative session on this device.</p>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-xl border border-rose-300 bg-white px-4 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-50 cursor-pointer"
                >
                  Sign Out
                </button>
              </div>

              {/* DANGER ZONE: DELETE ADMIN ACCOUNT */}
              <div className="rounded-2xl border border-rose-200 bg-rose-50/40 p-6 shadow-2xs space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-rose-100 text-rose-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 border border-rose-200">
                        Danger Zone
                      </span>
                      <h4 className="text-xs font-semibold text-rose-950">Delete Administrator Account</h4>
                    </div>
                    <p className="text-[11px] text-stone-600 mt-1 max-w-md">
                      Permanently delete this administrative account and credentials from Supabase authentication. You will lose privileged administrative console access immediately.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      if (!confirm("Are you sure you want to permanently delete your administrator account? This will revoke your access immediately.")) return;
                      try {
                        await deleteMyAccount(authToken);
                        const supabase = createClient();
                        await supabase.auth.signOut();
                        router.push("/login?message=admin_deleted");
                      } catch (err: unknown) {
                        const msg = err instanceof Error ? err.message : "Failed to delete administrator account.";
                        setNotice({ type: "error", message: msg });
                      }
                    }}
                    className="shrink-0 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-rose-700 transition cursor-pointer"
                  >
                    Delete Admin Account
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* =====================================================================
          MODAL: CREATE STUDENT ACCOUNT
          ===================================================================== */}
      {isCreateStudentOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-stone-900">Provision Student Account</h3>
            <p className="mt-1 text-xs text-stone-500">
              Create student credentials. Account is granted 20 initial free credits automatically.
            </p>

            <form onSubmit={handleCreateStudent} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={newStudentForm.full_name}
                  onChange={(e) => setNewStudentForm({ ...newStudentForm, full_name: e.target.value })}
                  placeholder="e.g. Alex Kumar"
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={newStudentForm.email}
                  onChange={(e) => setNewStudentForm({ ...newStudentForm, email: e.target.value })}
                  placeholder="student@university.edu"
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Confidential Password</label>
                <input
                  type="password"
                  required
                  value={newStudentForm.password}
                  onChange={(e) => setNewStudentForm({ ...newStudentForm, password: e.target.value })}
                  placeholder="Minimum 8 characters"
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Institution (Optional)</label>
                <input
                  type="text"
                  value={newStudentForm.institution}
                  onChange={(e) => setNewStudentForm({ ...newStudentForm, institution: e.target.value })}
                  placeholder="e.g. Indian Institute of Technology"
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateStudentOpen(false)}
                  className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white hover:bg-stone-800 disabled:opacity-50 cursor-pointer"
                >
                  {actionLoading ? "Creating..." : "Create Account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL: ASSIGN PLAN
          ===================================================================== */}
      {isAssignPlanOpen && assignPlanTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-stone-900">
              Assign Access Plan to {assignPlanTarget.full_name}
            </h3>
            <p className="mt-1 text-xs text-stone-500">
              Manually grant or extend subscription access duration for this student.
            </p>

            <form onSubmit={handleAssignPlan} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Plan Tier</label>
                <select
                  value={assignPlanForm.plan}
                  onChange={(e) => setAssignPlanForm({ ...assignPlanForm, plan: e.target.value as any })}
                  className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                >
                  <option value="monthly">Monthly Access (30 Days)</option>
                  <option value="yearly">Yearly Access (365 Days)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Duration (Days)</label>
                <input
                  type="number"
                  min="1"
                  max="730"
                  value={assignPlanForm.days}
                  onChange={(e) => setAssignPlanForm({ ...assignPlanForm, days: Number(e.target.value) })}
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Administrative Reason</label>
                <input
                  type="text"
                  required
                  value={assignPlanForm.reason}
                  onChange={(e) => setAssignPlanForm({ ...assignPlanForm, reason: e.target.value })}
                  placeholder="e.g. Scholarship grant or manual invoice"
                  className="w-full rounded-xl border border-stone-300 px-3 py-2 text-xs text-stone-900 focus:outline-hidden"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAssignPlanOpen(false)}
                  className="rounded-xl border border-stone-200 px-4 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="rounded-xl bg-stone-900 px-4 py-2 text-xs font-semibold text-white hover:bg-stone-800 disabled:opacity-50 cursor-pointer"
                >
                  {actionLoading ? "Assigning..." : "Assign Plan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

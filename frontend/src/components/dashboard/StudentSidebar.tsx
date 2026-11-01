"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useDashboard } from "@/context/DashboardContext";

export function StudentSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    userEmail,
    profile,
    subscription,
    credits,
    conversations,
    currentConversation,
    selectChat,
    createNewChat,
    renameChat,
    deleteChat,
    isSidebarOpen,
    setIsSidebarOpen,
    setIsPricingModalOpen,
    handleLogout,
  } = useDashboard();

  // Local state for chat search and editing
  const [chatSearch, setChatSearch] = useState("");
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Close profile menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        profileMenuRef.current &&
        !profileMenuRef.current.contains(event.target as Node)
      ) {
        setIsProfileMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter conversations
  const filteredConversations = conversations.filter((c) =>
    (c.title || "Untitled Chat").toLowerCase().includes(chatSearch.toLowerCase())
  );

  const navItems = [
    {
      name: "Chat Workspace",
      href: "/dashboard",
      exact: true,
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
    },
    {
      name: "Overview",
      href: "/dashboard/overview",
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      ),
    },
    {
      name: "My Documents",
      href: "/dashboard/documents",
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      name: "My Learning",
      href: "/dashboard/learning",
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
    },
    {
      name: "Plan & Billing",
      href: "/dashboard/billing",
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
    },
  ];

  const handleStartRename = (chatId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChatId(chatId);
    setEditingTitle(currentTitle);
  };

  const handleSaveRename = async (chatId: string, e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (editingTitle.trim()) {
      await renameChat(chatId, editingTitle.trim());
    }
    setEditingChatId(null);
  };

  const handleDeleteChatClick = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this conversation?")) {
      await deleteChat(chatId);
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-stone-900/30 backdrop-blur-xs md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-stone-200/90 bg-[#FBFBFA] transition-transform duration-200 ease-in-out md:static md:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* App Header Branding */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-stone-200/70 px-5">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-stone-900 text-white shadow-xs group-hover:scale-105 transition-transform">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-sm tracking-tight text-stone-900 font-sans">
                  CampusPilot
                </span>
                <span className="rounded bg-stone-200/80 px-1.5 py-0.5 text-[9px] font-bold text-stone-700 uppercase tracking-wider">
                  AI
                </span>
              </div>
              <p className="text-[10px] text-stone-500 font-medium">BCA Student Copilot</p>
            </div>
          </Link>

          {/* Close Sidebar (Mobile only) */}
          <button
            type="button"
            onClick={() => setIsSidebarOpen(false)}
            className="md:hidden rounded-lg p-1.5 text-stone-400 hover:bg-stone-200/60 hover:text-stone-700"
            aria-label="Close sidebar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Primary Action: 1. New Chat Button */}
        <div className="p-3 pb-2">
          <button
            type="button"
            onClick={async () => {
              await createNewChat();
              if (pathname !== "/dashboard") {
                router.push("/dashboard");
              }
              if (window.innerWidth < 768) {
                setIsSidebarOpen(false);
              }
            }}
            className="flex w-full items-center justify-between rounded-xl bg-stone-900 px-3.5 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer group"
          >
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-stone-300 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M12 4v16m8-8H4" />
              </svg>
              <span>New Chat</span>
            </div>
            <kbd className="hidden sm:inline-block rounded bg-stone-800 px-1.5 py-0.5 text-[10px] text-stone-300 font-mono">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Primary Navigation Items: 2. Chat Workspace, 3. Overview, 4. My Documents, 5. My Learning, 6. Plan & Billing */}
        <div className="px-3 py-1 space-y-0.5">
          {navItems.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => {
                  if (window.innerWidth < 768) {
                    setIsSidebarOpen(false);
                  }
                }}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-white text-stone-950 font-semibold shadow-2xs border border-stone-200/80"
                    : "text-stone-600 hover:bg-stone-200/40 hover:text-stone-900"
                }`}
              >
                <span
                  className={isActive ? "text-stone-900" : "text-stone-400 group-hover:text-stone-600"}
                >
                  {item.icon}
                </span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>

        <div className="my-2 border-t border-stone-200/70" />

        {/* Recent Chats Section - Independently scrollable */}
        <div className="flex flex-1 flex-col overflow-hidden px-3">
          <div className="flex items-center justify-between px-1 py-1 text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
            <span>Recent Chats</span>
            {conversations.length > 3 && (
              <span className="text-[10px] text-stone-400 font-normal">
                {conversations.length}
              </span>
            )}
          </div>

          {/* Search bar inside chats if user has chats */}
          {conversations.length > 5 && (
            <div className="relative my-1">
              <input
                type="text"
                value={chatSearch}
                onChange={(e) => setChatSearch(e.target.value)}
                placeholder="Search chats..."
                className="w-full rounded-lg border border-stone-200/80 bg-white px-2.5 py-1 text-[11px] text-stone-800 placeholder-stone-400 focus:border-stone-400 focus:outline-hidden"
              />
              {chatSearch && (
                <button
                  type="button"
                  onClick={() => setChatSearch("")}
                  className="absolute right-2 top-1.5 text-stone-400 hover:text-stone-600"
                >
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* Scrollable chat list */}
          <div className="flex-1 overflow-y-auto space-y-0.5 pr-1 text-xs">
            {conversations.length === 0 ? (
              <div className="py-6 text-center">
                <p className="text-[11px] text-stone-400">No conversations yet</p>
                <p className="text-[10px] text-stone-400 mt-0.5">Start a new chat above</p>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="py-4 text-center">
                <p className="text-[11px] text-stone-400">No matching chats</p>
              </div>
            ) : (
              filteredConversations.map((chat) => {
                const isSelected =
                  pathname === "/dashboard" && currentConversation?.id === chat.id;

                if (editingChatId === chat.id) {
                  return (
                    <form
                      key={chat.id}
                      onSubmit={(e) => handleSaveRename(chat.id, e)}
                      className="px-1 py-1"
                    >
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleSaveRename(chat.id)}
                        autoFocus
                        className="w-full rounded-lg border border-stone-400 bg-white px-2 py-1 text-xs text-stone-900 focus:outline-hidden"
                      />
                    </form>
                  );
                }

                return (
                  <div
                    key={chat.id}
                    onClick={async () => {
                      await selectChat(chat.id);
                      if (pathname !== "/dashboard") {
                        router.push("/dashboard");
                      }
                      if (window.innerWidth < 768) {
                        setIsSidebarOpen(false);
                      }
                    }}
                    className={`group relative flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-white text-stone-900 font-medium shadow-2xs border border-stone-200/80"
                        : "text-stone-600 hover:bg-stone-200/40 hover:text-stone-900"
                    }`}
                  >
                    <span className="truncate pr-2 max-w-[170px]">
                      {chat.title || "Untitled Conversation"}
                    </span>

                    {/* Chat quick actions */}
                    <div className="hidden items-center gap-1 group-hover:flex shrink-0">
                      <button
                        type="button"
                        onClick={(e) => handleStartRename(chat.id, chat.title || "Untitled Conversation", e)}
                        title="Rename conversation"
                        className="rounded p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
                      >
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteChatClick(chat.id, e)}
                        title="Delete conversation"
                        className="rounded p-1 text-stone-400 hover:bg-rose-50 hover:text-rose-600"
                      >
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Account / Subscription Section */}
        <div className="p-3 border-t border-stone-200/70">
          <div className="rounded-xl border border-stone-200/80 bg-white p-3 shadow-2xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-stone-800">
                {subscription?.plan ? `${subscription.plan.toUpperCase()} PLAN` : "FREE TIER"}
              </span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200/60">
                {credits?.credits_balance ?? 0} Credits
              </span>
            </div>

            <p className="text-[10px] text-stone-500 mb-2 leading-tight">
              {subscription?.status === "active"
                ? "Active subscription plan"
                : "Free monthly student quota"}
            </p>

            <button
              type="button"
              onClick={() => setIsPricingModalOpen(true)}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-stone-200 bg-stone-50 py-1.5 text-xs font-medium text-stone-800 hover:bg-stone-100 transition-colors cursor-pointer"
            >
              <svg className="h-3.5 w-3.5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span>{subscription?.status === "active" ? "Manage Plan" : "Upgrade Plan"}</span>
            </button>
          </div>
        </div>

        {/* User Profile & Settings Menu at Bottom */}
        <div className="relative border-t border-stone-200/70 p-3" ref={profileMenuRef}>
          {/* Profile Popover / Dropdown Menu */}
          {isProfileMenuOpen && (
            <div className="absolute bottom-16 left-3 right-3 rounded-2xl border border-stone-200 bg-white p-2 shadow-xl space-y-1 z-50">
              <div className="px-3 py-2 border-b border-stone-100">
                <p className="text-xs font-semibold text-stone-900 truncate">
                  {profile?.full_name || "BCA Student"}
                </p>
                <p className="text-[11px] text-stone-500 truncate">{userEmail}</p>
                {profile?.institution && (
                  <p className="text-[10px] text-stone-400 truncate mt-0.5">
                    {profile.institution}
                  </p>
                )}
              </div>

              <Link
                href="/dashboard/settings"
                onClick={() => setIsProfileMenuOpen(false)}
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 hover:text-stone-900 transition-colors"
              >
                <svg className="h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Account & Profile Settings</span>
              </Link>

              <Link
                href="/dashboard/billing"
                onClick={() => setIsProfileMenuOpen(false)}
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 hover:text-stone-900 transition-colors"
              >
                <svg className="h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                <span>Plan & Billing</span>
              </Link>

              <button
                type="button"
                onClick={async () => {
                  setIsProfileMenuOpen(false);
                  await handleLogout();
                }}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
              >
                <svg className="h-4 w-4 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span>Sign Out</span>
              </button>
            </div>
          )}

          {/* User Profile Button */}
          <button
            type="button"
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            className="flex w-full items-center justify-between rounded-xl p-2 text-left hover:bg-stone-200/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-stone-900 text-xs font-semibold text-white shadow-2xs">
                {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : "S"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-stone-900 group-hover:text-stone-950">
                  {profile?.full_name || "BCA Student"}
                </p>
                <p className="truncate text-[10px] text-stone-500 font-mono">
                  {userEmail || "student@campuspilot.ai"}
                </p>
              </div>
            </div>
            <svg
              className={`h-4 w-4 text-stone-400 group-hover:text-stone-600 transition-transform ${
                isProfileMenuOpen ? "rotate-180" : ""
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </aside>
    </>
  );
}

"use client";

import React, { useState } from "react";
import { useDashboard } from "@/context/DashboardContext";
import { createClient } from "@/lib/supabase/client";

export default function AccountSettingsPage() {
  const {
    userEmail,
    profile,
    updateProfile,
    setShowDeleteAccountModal,
    handleLogout,
  } = useDashboard();

  const [fullName, setFullName] = useState(profile?.full_name || "");
  const [institution, setInstitution] = useState(profile?.institution || "");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Update profile handler
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setProfileSaving(true);
      setProfileMsg(null);
      await updateProfile(fullName, institution);
      setProfileMsg({ type: "success", text: "Profile details updated successfully." });
    } catch (err: any) {
      setProfileMsg({ type: "error", text: err.message || "Failed to update profile." });
    } finally {
      setProfileSaving(false);
    }
  };

  // Password update handler
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setPasswordMsg({ type: "error", text: "Password must be at least 8 characters long." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: "error", text: "Passwords do not match." });
      return;
    }

    try {
      setPasswordSaving(true);
      setPasswordMsg(null);
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;

      setPasswordMsg({ type: "success", text: "Password updated successfully." });
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordMsg({ type: "error", text: err.message || "Failed to update password." });
    } finally {
      setPasswordSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-3xl space-y-8">
        {/* Header */}
        <div className="border-b border-stone-200/80 pb-6">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
            Account & Profile Settings
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-stone-500">
            Manage your personal academic identity, credentials, and account settings.
          </p>
        </div>

        {/* 1. Profile Information */}
        <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-2xs space-y-5">
          <div>
            <h2 className="text-sm font-bold text-stone-900">Student Identity</h2>
            <p className="text-xs text-stone-500">Update your student name and university/college name.</p>
          </div>

          {profileMsg && (
            <div
              className={`rounded-xl p-3 text-xs ${
                profileMsg.type === "success"
                  ? "border border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              {profileMsg.text}
            </div>
          )}

          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Student Full Name"
                className="w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs text-stone-900 focus:border-stone-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                value={userEmail || ""}
                disabled
                className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-xs text-stone-500 cursor-not-allowed font-mono"
              />
              <p className="text-[10px] text-stone-400 mt-1">Email address is managed by your authentication provider.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Institution / University / College
              </label>
              <input
                type="text"
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                placeholder="e.g. BCA Department, University of Technology"
                className="w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs text-stone-900 focus:border-stone-500 focus:outline-hidden"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={profileSaving}
                className="rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 disabled:opacity-50 cursor-pointer"
              >
                {profileSaving ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </form>
        </div>

        {/* 2. Change Password */}
        <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-2xs space-y-5">
          <div>
            <h2 className="text-sm font-bold text-stone-900">Security & Credentials</h2>
            <p className="text-xs text-stone-500">Update your account login password.</p>
          </div>

          {passwordMsg && (
            <div
              className={`rounded-xl p-3 text-xs ${
                passwordMsg.type === "success"
                  ? "border border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              {passwordMsg.text}
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs text-stone-900 focus:border-stone-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
                className="w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs text-stone-900 focus:border-stone-500 focus:outline-hidden"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={passwordSaving || !newPassword}
                className="rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 disabled:opacity-50 cursor-pointer"
              >
                {passwordSaving ? "Updating Password..." : "Update Password"}
              </button>
            </div>
          </form>
        </div>

        {/* 3. Session Sign Out */}
        <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-2xs flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-stone-900">Sign Out of Session</h3>
            <p className="text-xs text-stone-500 mt-0.5">End your current session on this device.</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-xs font-semibold text-stone-700 hover:bg-stone-50 cursor-pointer"
          >
            Sign Out
          </button>
        </div>

        {/* 4. Danger Zone: Delete Account */}
        <div className="rounded-2xl border border-rose-200 bg-rose-50/40 p-6 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-rose-100 text-rose-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 border border-rose-200">
                  Danger Zone
                </span>
                <h3 className="text-sm font-bold text-rose-950">Delete Account & Academic Data</h3>
              </div>
              <p className="text-xs text-stone-600 mt-1 max-w-md">
                Permanently delete your student profile, all personal documents, chunk indexes, conversation history, and credit balance. This action cannot be reversed.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowDeleteAccountModal(true)}
              className="shrink-0 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-rose-700 transition cursor-pointer"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

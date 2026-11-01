"use client";

import React, { useState } from "react";
import { submitWaitlist } from "@/lib/api";

export function WaitlistSection() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [institution, setInstitution] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "info" | "error";
    text: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim() || loading) return;

    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setStatusMessage({
        type: "error",
        text: "Please enter a valid email address.",
      });
      return;
    }

    setLoading(true);
    setStatusMessage(null);

    try {
      const res = await submitWaitlist(fullName.trim(), email.trim(), institution.trim());
      if (res.status === "already_registered") {
        setStatusMessage({
          type: "info",
          text: res.message || "You are already on the CampusPilot waitlist!",
        });
      } else {
        setStatusMessage({
          type: "success",
          text: res.message || "Thank you for joining the CampusPilot waitlist! We will notify you when access is available.",
        });
        setFullName("");
        setEmail("");
        setInstitution("");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to join waitlist. Please try again later.";
      setStatusMessage({
        type: "error",
        text: msg,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="waitlist" className="w-full border-t border-stone-200/80 bg-white py-16 sm:py-24">
      <div className="mx-auto max-w-xl px-4 sm:px-6">
        <div className="text-center">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-medium text-stone-600">
            <span>Invite-Only Access</span>
            <span className="text-stone-300">·</span>
            <span className="text-stone-900 font-semibold">Limited Seats</span>
          </div>

          <h2 className="mt-4 text-2xl font-semibold tracking-tight text-stone-900 sm:text-3xl">
            Join the CampusPilot Waitlist
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-stone-600">
            Get early access to CampusPilot AI. Join the waitlist and be notified when access becomes available.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label htmlFor="fullName" className="block text-xs font-semibold text-stone-800">
              Full Name <span className="text-rose-500">*</span>
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Alex Morgan"
              className="mt-1.5 w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:outline-hidden"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs font-semibold text-stone-800">
              Email Address <span className="text-rose-500">*</span>
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. alex.morgan@university.edu"
              className="mt-1.5 w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:outline-hidden"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="institution" className="block text-xs font-semibold text-stone-800">
              College or Institution <span className="text-stone-400 font-normal">(Optional)</span>
            </label>
            <input
              id="institution"
              type="text"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              placeholder="e.g. Stanford University / MIT"
              className="mt-1.5 w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:outline-hidden"
              disabled={loading}
            />
          </div>

          {statusMessage && (
            <div
              className={`rounded-xl border p-3.5 text-xs ${
                statusMessage.type === "success"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : statusMessage.type === "info"
                  ? "border-blue-200 bg-blue-50 text-blue-800"
                  : "border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              {statusMessage.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !fullName.trim() || !email.trim()}
            className="w-full rounded-xl bg-stone-900 py-3 text-xs font-medium text-white shadow-2xs transition-all hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? "Submitting..." : "Join Waitlist"}
          </button>
        </form>

        <p className="mt-4 text-center text-[11px] text-stone-500">
          CampusPilot is strictly invite-only. Student accounts are manually provisioned by the campus administrator.
        </p>
      </div>
    </section>
  );
}

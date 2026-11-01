"use client";

import React from "react";
import { useDashboard } from "@/context/DashboardContext";

export default function PlanAndBillingPage() {
  const {
    subscription,
    credits,
    payments,
    setIsPricingModalOpen,
    refreshBillingAndCredits,
    initialLoading,
  } = useDashboard();

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200/80 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-stone-900">
                Plan & Billing
              </h1>
              <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-semibold text-stone-700">
                {subscription?.plan ? `${subscription.plan.toUpperCase()}` : "FREE"}
              </span>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-stone-500">
              Manage your CampusPilot AI subscription, credit allowance, and payment receipts.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsPricingModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors cursor-pointer self-start sm:self-auto"
          >
            <svg className="h-4 w-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span>{subscription?.status === "active" ? "Change / Renew Plan" : "Upgrade to Pro Plan"}</span>
          </button>
        </div>

        {/* Current Plan Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <span className="text-[11px] font-semibold uppercase text-stone-500 tracking-wider">
              Current Membership
            </span>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold capitalize text-stone-900">
                {subscription?.plan ? `${subscription.plan} Plan` : "Free Student Tier"}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                  subscription?.status === "active"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-stone-100 text-stone-600"
                }`}
              >
                {subscription?.status === "active" ? "Active" : "Free"}
              </span>
            </div>
            <p className="mt-2 text-xs text-stone-500">
              {subscription?.status === "active"
                ? `${subscription.remaining_days || 0} days remaining until renewal`
                : "Standard free student quota"}
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <span className="text-[11px] font-semibold uppercase text-stone-500 tracking-wider">
              Available Credits
            </span>
            <div className="mt-3 text-2xl font-bold text-stone-900">
              {credits?.is_paid_subscriber ? "∞ Unlimited" : `${credits?.credits_balance ?? 0}`}
            </div>
            <p className="mt-2 text-xs text-stone-500">
              {credits?.is_paid_subscriber
                ? "No rate limits on answers"
                : "1 credit deducted per question response"}
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-2xs">
            <span className="text-[11px] font-semibold uppercase text-stone-500 tracking-wider">
              Next Billing Event
            </span>
            <div className="mt-3 text-2xl font-bold text-stone-900">
              {subscription?.current_period_end
                ? new Date(subscription.current_period_end).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })
                : "N/A"}
            </div>
            <p className="mt-2 text-xs text-stone-500">
              {subscription?.status === "active"
                ? "Automatic non-recurring expiry control"
                : "Upgrade anytime for unlimited academic usage"}
            </p>
          </div>
        </div>

        {/* Pro Plan Feature Comparison Box */}
        <div className="rounded-2xl border border-stone-900 bg-stone-900 p-6 sm:p-8 text-white shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="rounded bg-amber-400 text-stone-950 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                Full Pro Copilot
              </span>
              <h2 className="mt-2 text-xl font-bold text-white tracking-tight">
                CampusPilot Pro for BCA Students
              </h2>
              <p className="mt-1 text-xs sm:text-sm text-stone-300">
                Designed specifically for semester examinations, lab evaluations, and project defense.
              </p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-extrabold text-white">₹99</span>
              <span className="text-xs text-stone-300"> / month</span>
              <p className="text-[11px] text-amber-300 mt-0.5">Or ₹999/yr (2 months free)</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 border-t border-stone-800 pt-6">
            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Unlimited AI Questions</p>
                <p className="text-[11px] text-stone-400 mt-0.5">No daily or monthly credit exhaustion limits.</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Syllabus Grounded Retrieval</p>
                <p className="text-[11px] text-stone-400 mt-0.5">High precision vector retrieval with pgvector.</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Document Indexing</p>
                <p className="text-[11px] text-stone-400 mt-0.5">Upload personal lecture notes and question banks.</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Lab Practicals & Code</p>
                <p className="text-[11px] text-stone-400 mt-0.5">Complete 21 Java programs and 12 Algo practicals.</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Project Report Guidance</p>
                <p className="text-[11px] text-stone-400 mt-0.5">Rubrics and 14 report sections for Major Project.</p>
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <svg className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-xs font-bold text-white">Secure Razorpay Checkout</p>
                <p className="text-[11px] text-stone-400 mt-0.5">UPI, Cards, and NetBanking supported.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Payment History Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-stone-900">Payment & Transaction Receipts</h3>
            <button
              type="button"
              onClick={() => refreshBillingAndCredits()}
              className="text-xs text-stone-500 hover:text-stone-900 cursor-pointer"
            >
              Refresh ↻
            </button>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white shadow-2xs overflow-hidden">
            {payments.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-xs text-stone-400">No payment records found.</p>
                <p className="text-[11px] text-stone-400 mt-0.5">
                  When you purchase a subscription through Razorpay, receipts will appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-stone-100 bg-stone-50/70 text-[10px] font-semibold uppercase tracking-wider text-stone-500">
                      <th className="px-5 py-3">Order ID</th>
                      <th className="px-4 py-3">Plan</th>
                      <th className="px-4 py-3">Amount</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {payments.map((p) => (
                      <tr key={p.id} className="hover:bg-stone-50/50">
                        <td className="px-5 py-3 font-mono text-[11px] text-stone-700">
                          {p.razorpay_order_id || p.id}
                        </td>
                        <td className="px-4 py-3 font-semibold text-stone-900 capitalize">
                          {p.plan}
                        </td>
                        <td className="px-4 py-3 font-mono text-stone-900">
                          ₹{p.amount_inr}
                        </td>
                        <td className="px-4 py-3 text-stone-500 text-[11px]">
                          {new Date(p.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                              p.status === "captured"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                                : "bg-stone-100 text-stone-700"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

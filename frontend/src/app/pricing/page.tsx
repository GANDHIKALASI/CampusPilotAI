"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { getCurrentSubscription } from "@/lib/api";
import { SubscriptionStatus } from "@/types/database";
import { PricingModal } from "@/components/PricingModal";

export default function PricingPage() {
  const router = useRouter();
  const [authToken, setAuthToken] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isPricingModalOpen, setIsPricingModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setAuthToken(session.access_token);
        setUserEmail(session.user.email || null);
        getCurrentSubscription(session.access_token)
          .then((sub) => setSubscription(sub as SubscriptionStatus))
          .catch(() => {})
          .finally(() => setLoading(false));
      } else {
        setLoading(false);
      }
    });
  }, []);

  const refreshSub = () => {
    if (authToken) {
      getCurrentSubscription(authToken)
        .then((sub) => setSubscription(sub as SubscriptionStatus))
        .catch(() => {});
    }
  };

  const isCurrentPaid = subscription?.is_active && subscription?.is_paid;

  return (
    <div className="min-h-screen bg-[#FBFBFA] text-[#1C1917] antialiased">
      {/* Top Navigation */}
      <header className="border-b border-stone-200/80 bg-white/80 px-6 py-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-stone-200 bg-white shadow-2xs">
              <Image src="/logo.jpg" alt="CampusPilot Logo" width={32} height={32} className="rounded-lg object-cover" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-stone-900">
              CampusPilot AI
            </span>
          </Link>

          <div className="flex items-center gap-3">
            {authToken ? (
              <Link
                href="/dashboard"
                className="rounded-xl border border-stone-200 bg-white px-3.5 py-1.5 text-xs font-medium text-stone-700 shadow-2xs hover:bg-stone-50"
              >
                Go to Workspace →
              </Link>
            ) : (
              <Link
                href="/login"
                className="rounded-xl bg-stone-900 px-3.5 py-1.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800"
              >
                Student Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <div className="text-center">
          <span className="rounded-full bg-stone-100 border border-stone-200 px-3 py-1 text-[11px] font-semibold text-stone-700 uppercase tracking-wider">
            Academic Access Plans
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">
            Simple, Transparent Academic Pricing
          </h1>
          <p className="mt-2 text-sm text-stone-500 max-w-lg mx-auto">
            Fixed-duration access. Grounded in your university course materials. One-time payment via Razorpay.
          </p>

          {/* Current Plan Status for Logged-in Students */}
          {authToken && (
            <div className="mt-6 inline-block text-left">
              <div className={`rounded-2xl border px-4 py-3 text-xs flex items-center gap-3 ${
                isCurrentPaid ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-stone-200 bg-white text-stone-700 shadow-2xs"
              }`}>
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${isCurrentPaid ? "bg-emerald-600" : "bg-amber-500"}`} />
                  <span>
                    Logged in as <strong>{userEmail}</strong> — Current Plan:{" "}
                    <strong className="uppercase">{subscription?.plan || "Free"}</strong>
                  </span>
                </div>
                {subscription?.current_period_end && isCurrentPaid && (
                  <span className="text-[11px] text-emerald-700">
                    (Valid until {new Date(subscription.current_period_end).toLocaleDateString()})
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Plan Cards Grid */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* MONTHLY PLAN */}
          <div className="rounded-2xl border border-stone-200 bg-white p-7 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-stone-500">
                  Monthly Access
                </span>
                {subscription?.plan === "monthly" && isCurrentPaid && (
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                    Current Plan
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold tracking-tight text-stone-900">₹99</span>
                <span className="text-sm font-medium text-stone-500">/ month</span>
              </div>
              <p className="mt-2 text-xs text-stone-500 leading-relaxed">
                Ideal for preparing for an upcoming examination or completing semester project modules.
              </p>

              <hr className="my-6 border-stone-100" />

              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 block mb-3">
                Included in Monthly:
              </span>
              <ul className="space-y-2.5 text-xs text-stone-700">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Full AI academic chat
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> PDF uploads
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Document-grounded answers
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Chat history
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> MCQ and revision assistance
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Personal document library
                </li>
              </ul>
            </div>

            <div className="mt-8">
              <button
                type="button"
                onClick={() => {
                  if (!authToken) {
                    router.push("/login?redirectedFrom=/pricing");
                  } else {
                    setIsPricingModalOpen(true);
                  }
                }}
                className="w-full rounded-xl border border-stone-300 bg-white py-2.5 text-xs font-semibold text-stone-900 shadow-2xs hover:bg-stone-50 transition-colors"
              >
                {authToken ? "Subscribe Monthly (₹99)" : "Sign In to Upgrade"}
              </button>
            </div>
          </div>

          {/* YEARLY PLAN */}
          <div className="relative rounded-2xl border-2 border-stone-900 bg-white p-7 shadow-xs flex flex-col justify-between">
            <span className="absolute -top-3 right-6 rounded-full bg-stone-900 px-3 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
              Save ₹189 / year
            </span>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-stone-900">
                  Yearly Access
                </span>
                {subscription?.plan === "yearly" && isCurrentPaid && (
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                    Current Plan
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold tracking-tight text-stone-900">₹999</span>
                <span className="text-sm font-medium text-stone-500">/ year</span>
              </div>
              <p className="mt-2 text-xs text-stone-500 leading-relaxed">
                Full 365 days of continuous academic assistance (equivalent to ₹83/month).
              </p>

              <hr className="my-6 border-stone-100" />

              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-900 block mb-3">
                Included in Yearly:
              </span>
              <ul className="space-y-2.5 text-xs text-stone-700">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Full AI academic chat
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> PDF uploads
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Document-grounded answers
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Chat history
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> MCQ and revision assistance
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-700 font-bold">✓</span> Personal document library
                </li>
              </ul>
            </div>

            <div className="mt-8">
              <button
                type="button"
                onClick={() => {
                  if (!authToken) {
                    router.push("/login?redirectedFrom=/pricing");
                  } else {
                    setIsPricingModalOpen(true);
                  }
                }}
                className="w-full rounded-xl bg-stone-900 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 transition-colors"
              >
                {authToken ? "Subscribe Yearly (₹999)" : "Sign In to Upgrade"}
              </button>
            </div>
          </div>
        </div>

        {/* Guarantee Note */}
        <p className="mt-12 text-center text-xs text-stone-500">
          Secure payment processed via Razorpay. UPI, Debit/Credit Cards & NetBanking accepted. Access is activated immediately upon successful payment verification.
        </p>
      </main>

      {/* Pricing Modal */}
      <PricingModal
        isOpen={isPricingModalOpen}
        onClose={() => setIsPricingModalOpen(false)}
        authToken={authToken}
        userEmail={userEmail || undefined}
        subscription={subscription}
        onSubscriptionUpdated={refreshSub}
      />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import Image from "next/image";
import { createPaymentOrder, verifyPayment } from "@/lib/api";
import { SubscriptionStatus } from "@/types/database";

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
  authToken?: string;
  userEmail?: string;
  subscription?: SubscriptionStatus | null;
  onSubscriptionUpdated?: () => void;
}

export function PricingModal({
  isOpen,
  onClose,
  authToken,
  userEmail,
  subscription,
  onSubscriptionUpdated,
}: PricingModalProps) {
  const [selectedPlan, setSelectedPlan] = useState<"monthly" | "yearly">("yearly");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const loadRazorpayScript = (): Promise<boolean> => {
    return new Promise((resolve) => {
      if ((window as any).Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleSubscribe = async () => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const isScriptLoaded = await loadRazorpayScript();
      if (!isScriptLoaded) {
        throw new Error("Razorpay checkout failed to load. Please check your internet connection.");
      }

      // Step 1: Create trusted server-side order
      const order = await createPaymentOrder(selectedPlan, authToken);

      // Step 2: Configure Razorpay Checkout options
      const options = {
        key: order.key_id || "rzp_test_placeholder",
        amount: order.amount_paise,
        currency: order.currency || "INR",
        name: "CampusPilot AI",
        description: selectedPlan === "monthly" ? "Monthly Academic Access (30 Days)" : "Yearly Academic Access (365 Days)",
        image: "/logo.jpg",
        order_id: order.order_id,
        prefill: {
          email: userEmail || "",
        },
        theme: {
          color: "#1C1917", // CampusPilot stone-900
        },
        handler: async function (response: any) {
          try {
            setLoading(true);
            const verifyRes = await verifyPayment(
              {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              },
              authToken
            );
            setSuccessMsg(verifyRes.message || "Plan activated successfully!");
            if (onSubscriptionUpdated) {
              onSubscriptionUpdated();
            }
            setTimeout(() => {
              onClose();
            }, 2000);
          } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Payment verification failed.";
            setErrorMsg(msg);
          } finally {
            setLoading(false);
          }
        },
        modal: {
          ondismiss: function () {
            setLoading(false);
          },
        },
      };

      // Open Razorpay Standard Checkout
      const rzp = new (window as any).Razorpay(options);
      rzp.on("payment.failed", function (response: any) {
        setErrorMsg(response.error?.description || "Payment was cancelled or failed.");
        setLoading(false);
      });
      rzp.open();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to initiate payment.";
      setErrorMsg(msg);
      setLoading(false);
    }
  };

  const isCurrentPlanActive = subscription?.is_active && subscription?.is_paid;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs antialiased animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl sm:p-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
          title="Close pricing modal"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-stone-200 bg-[#F7F7F5] shadow-2xs">
            <Image src="/logo.jpg" alt="CampusPilot Logo" width={32} height={32} className="rounded-lg object-cover" />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight text-stone-900">
              CampusPilot AI Academic Access
            </h3>
            <p className="text-xs text-stone-500">
              Unlimited document analysis, active recall study schedules & AI guidance.
            </p>
          </div>
        </div>

        {/* Current Plan Indicator if logged in */}
        {isCurrentPlanActive && (
          <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/80 px-3.5 py-2.5 text-xs text-emerald-800 flex items-center justify-between">
            <div>
              <span className="font-semibold">Current Active Plan:</span>{" "}
              <span className="uppercase font-bold tracking-wider">{subscription?.plan}</span>
              {subscription?.current_period_end && (
                <span className="text-emerald-700 ml-1">
                  (Expires: {new Date(subscription.current_period_end).toLocaleDateString()})
                </span>
              )}
            </div>
            <span className="rounded-full bg-emerald-200/70 px-2 py-0.5 text-[10px] font-bold text-emerald-900">
              Active
            </span>
          </div>
        )}

        {/* Error / Success Notifications */}
        {errorMsg && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2 text-xs text-rose-800">
            {errorMsg}
          </div>
        )}
        {successMsg && (
          <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2 text-xs text-emerald-800">
            {successMsg}
          </div>
        )}

        {/* Plan Cards */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {/* Monthly Plan */}
          <div
            onClick={() => setSelectedPlan("monthly")}
            className={`cursor-pointer rounded-xl border p-4.5 transition-all ${
              selectedPlan === "monthly"
                ? "border-stone-900 bg-stone-50/60 shadow-xs"
                : "border-stone-200 hover:border-stone-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider uppercase text-stone-600">
                Monthly
              </span>
              <input
                type="radio"
                checked={selectedPlan === "monthly"}
                onChange={() => setSelectedPlan("monthly")}
                className="h-3.5 w-3.5 text-stone-900 focus:ring-0"
              />
            </div>
            <div className="mt-2.5 flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight text-stone-900">₹99</span>
              <span className="text-xs text-stone-500">/ month</span>
            </div>
            <p className="mt-1 text-[11px] text-stone-500 leading-tight">
              30 days of full, uninterrupted academic AI assistance.
            </p>
          </div>

          {/* Yearly Plan */}
          <div
            onClick={() => setSelectedPlan("yearly")}
            className={`relative cursor-pointer rounded-xl border p-4.5 transition-all ${
              selectedPlan === "yearly"
                ? "border-stone-900 bg-stone-50/60 shadow-xs"
                : "border-stone-200 hover:border-stone-300"
            }`}
          >
            <span className="absolute -top-2.5 right-3 rounded-full bg-stone-900 px-2 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider">
              Save ₹189/yr
            </span>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider uppercase text-stone-600">
                Yearly
              </span>
              <input
                type="radio"
                checked={selectedPlan === "yearly"}
                onChange={() => setSelectedPlan("yearly")}
                className="h-3.5 w-3.5 text-stone-900 focus:ring-0"
              />
            </div>
            <div className="mt-2.5 flex items-baseline gap-1">
              <span className="text-2xl font-bold tracking-tight text-stone-900">₹999</span>
              <span className="text-xs text-stone-500">/ year</span>
            </div>
            <p className="mt-1 text-[11px] text-stone-500 leading-tight">
              365 days of academic access (equivalent to ₹83/month).
            </p>
          </div>
        </div>

        {/* Feature List */}
        <div className="mt-5 rounded-xl border border-stone-100 bg-[#FBFBFA] p-3.5">
          <span className="text-[10px] font-semibold tracking-wider uppercase text-stone-500 block mb-2">
            Both plans include:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs text-stone-700">
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> Full AI academic chat
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> PDF uploads
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> Document-grounded answers
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> Persistent chat history
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> MCQ & revision assistance
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-700">✓</span> Personal document library
            </div>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-stone-200 px-4 py-2.5 text-xs font-medium text-stone-700 hover:bg-stone-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubscribe}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-stone-900 px-5 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-stone-800 disabled:opacity-50 transition-colors"
          >
            {loading ? "Connecting Gateway..." : `Pay ₹${selectedPlan === "monthly" ? "99" : "999"} via Razorpay`}
          </button>
        </div>

        <p className="mt-3 text-center text-[10px] text-stone-600">
          Fixed-duration academic access. One-time payment via UPI, Cards, NetBanking. No recurring auto-debit.
        </p>
      </div>
    </div>
  );
}

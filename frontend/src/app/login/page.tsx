"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const checkRoleAndRedirect = (user: any) => {
    const adminList = ["buggandhi@proton.me", "admin@campuspilot.ai", "administrator@campuspilot.ai"];
    const appMeta = (user.app_metadata || {}) as Record<string, unknown>;
    const userEmail = (user.email || "").toLowerCase();
    const isAdminUser = adminList.includes(userEmail) || appMeta.role === "admin";

    const params = new URLSearchParams(window.location.search);
    const redirectedFrom = params.get("redirectedFrom");

    if (isAdminUser) {
      router.push(redirectedFrom && redirectedFrom.startsWith("/admin") ? redirectedFrom : "/admin");
    } else {
      router.push(redirectedFrom && !redirectedFrom.startsWith("/admin") ? redirectedFrom : "/dashboard");
    }
  };

  // If already authenticated, redirect to appropriate workspace
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        checkRoleAndRedirect(user);
      }
    });
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim() || loading) return;

    setLoading(true);
    setErrorMsg(null);

    try {
      const supabase = createClient();
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password: password.trim(),
      });

      if (error) {
        if (error.message.toLowerCase().includes("invalid login credentials")) {
          setErrorMsg("Invalid email or password. Please verify your credentials or contact your administrator.");
        } else {
          setErrorMsg(error.message);
        }
        return;
      }

      if (data.user) {
        checkRoleAndRedirect(data.user);
        router.refresh();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed. Please try again.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-[#FBFBFA] px-4 py-12 text-[#1C1917] sm:px-6 lg:px-8 antialiased">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Link href="/" className="flex flex-col items-center gap-2 group">
            <div className="relative flex h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xs transition-transform group-hover:scale-105">
              <Image
                src="/logo.jpg"
                alt="CampusPilot Emblem"
                width={56}
                height={56}
                className="object-cover"
                priority
              />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-base font-semibold tracking-tight text-stone-900">
                CampusPilot AI
              </span>
              <span className="rounded-sm border border-stone-200 bg-stone-100 px-1.5 py-0.5 text-[10px] font-medium tracking-wider text-stone-600 uppercase">
                Student Portal
              </span>
            </div>
          </Link>
        </div>

        <h2 className="mt-6 text-center text-2xl font-semibold tracking-tight text-stone-900">
          Sign In to Your Academic Workspace
        </h2>
        <p className="mt-2 text-center text-xs text-stone-500">
          Invite-only platform. Use the registered credentials issued by your campus administrator.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="rounded-2xl border border-stone-200/90 bg-white px-6 py-8 shadow-xs sm:px-10">
          <form className="space-y-4" onSubmit={handleLogin}>
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-stone-800">
                Student Email
              </label>
              <div className="mt-1.5">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@university.edu"
                  className="block w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:outline-hidden"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-stone-800">
                Password
              </label>
              <div className="mt-1.5">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:outline-hidden"
                  disabled={loading}
                />
              </div>
            </div>

            {errorMsg && (
              <div className="rounded-xl border border-rose-200 bg-rose-50/90 p-3.5 text-xs text-rose-800">
                <span className="font-semibold">Error:</span> {errorMsg}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading || !email.trim() || !password.trim()}
                className="flex w-full justify-center rounded-xl bg-stone-900 px-4 py-2.5 text-xs font-medium text-white shadow-2xs transition-all hover:bg-stone-800 focus:outline-hidden disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? "Authenticating..." : "Sign In"}
              </button>
            </div>
          </form>

          <div className="mt-6 border-t border-stone-100 pt-5 text-center text-xs text-stone-500">
            <span>Don&apos;t have an invite yet? </span>
            <Link href="/#waitlist" className="font-medium text-stone-900 underline underline-offset-2 hover:text-stone-700">
              Join the Waitlist →
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-xs text-stone-500 hover:text-stone-800 transition-colors"
          >
            ← Return to CampusPilot AI Overview
          </Link>
        </div>
      </div>
    </div>
  );
}

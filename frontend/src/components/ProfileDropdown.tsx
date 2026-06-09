"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useUser, useClerk } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  FolderOpen,
  Settings,
  LogOut,
  CreditCard,
  PenLine,
  ChevronDown,
} from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const MENU_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/build-resume", label: "AI Resume Builder", icon: PenLine },
  { href: "/dashboard/portfolios", label: "My Portfolios", icon: FolderOpen },
  { href: "/dashboard/settings/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function ProfileDropdown() {
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();
  const router = useRouter();
  const { isLight } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  if (!isLoaded) {
    return (
      <div className="flex items-center gap-2">
        <div
          className="h-8 w-8 animate-pulse rounded-full"
          style={{ background: isLight ? "#e5e5ea" : "var(--pf-accent-soft)" }}
        />
        <div
          className="hidden h-4 w-16 animate-pulse rounded sm:block"
          style={{ background: isLight ? "#e5e5ea" : "var(--pf-accent-soft)" }}
        />
      </div>
    );
  }

  if (!user) return null;

  const name = user.firstName ?? user.username ?? "User";
  const email = user.primaryEmailAddress?.emailAddress ?? "";
  const avatarUrl = user.imageUrl;

  const handleSignOut = async () => {
    setOpen(false);
    await signOut();
    router.push("/");
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2.5 transition-all duration-200"
        style={{
          background: open
            ? isLight
              ? "var(--pf-border-subtle)"
              : "var(--pf-accent-subtle)"
            : "transparent",
        }}
      >
        {avatarUrl ? (
          <Image
            src={avatarUrl}
            alt={name}
            width={32}
            height={32}
            className={`rounded-full ring-2 transition-all ${
              open
                ? "ring-[var(--pf-accent)]"
                : isLight
                  ? "ring-[rgba(0,0,0,0.06)]"
                  : "ring-[var(--pf-border-light)]"
            }`}
          />
        ) : (
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold text-white"
            style={{ background: "var(--pf-accent)" }}
          >
            {name.charAt(0).toUpperCase()}
          </div>
        )}
        <span
          className="hidden text-sm font-medium sm:block"
          style={{ color: isLight ? "#1a1a2e" : "var(--pf-text)" }}
        >
          {name}
        </span>
        <ChevronDown
          className="h-3.5 w-3.5 transition-transform duration-200"
          style={{
            color: isLight ? "#666688" : "var(--pf-muted)",
            transform: open ? "rotate(180deg)" : "rotate(0)",
          }}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 top-full mt-2 w-64 overflow-hidden rounded-xl border shadow-xl"
            style={{
              background: isLight ? "#ffffff" : "var(--pf-surface)",
              borderColor: isLight ? "rgba(0,0,0,0.08)" : "var(--pf-accent-soft)",
              boxShadow: isLight
                ? "0 20px 60px rgba(0,0,0,0.12)"
                : "0 20px 60px rgba(0,0,0,0.5)",
            }}
          >
            {}
            <div
              className="border-b px-4 py-3"
              style={{ borderColor: isLight ? "rgba(0,0,0,0.06)" : "var(--pf-border-dim)" }}
            >
              <div className="flex items-center gap-3">
                {avatarUrl ? (
                  <Image
                    src={avatarUrl}
                    alt={name}
                    width={40}
                    height={40}
                    className="rounded-full"
                  />
                ) : (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--pf-accent)] text-sm font-bold text-white">
                    {name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p
                    className="truncate text-sm font-semibold"
                    style={{ color: isLight ? "#1a1a2e" : "var(--pf-text)" }}
                  >
                    {user.fullName ?? name}
                  </p>
                  <p
                    className="truncate text-xs"
                    style={{ color: isLight ? "#888" : "var(--pf-muted)" }}
                  >
                    {email}
                  </p>
                </div>
              </div>
            </div>

            {}
            <div className="py-1.5">
              {MENU_ITEMS.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors"
                  style={{ color: isLight ? "#444" : "#c8c8e8" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = isLight
                      ? "var(--pf-border-faint)"
                      : "var(--pf-border-subtle)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  <Icon className="h-4 w-4" style={{ color: isLight ? "#888" : "var(--pf-muted)" }} />
                  {label}
                </Link>
              ))}
            </div>

            {}
            <div
              className="border-t py-1.5"
              style={{ borderColor: isLight ? "rgba(0,0,0,0.06)" : "var(--pf-border-dim)" }}
            >
              <button
                onClick={handleSignOut}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors"
                style={{ color: "#ff4d4d" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(255,77,77,0.06)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

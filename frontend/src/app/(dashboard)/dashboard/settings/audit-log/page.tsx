"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { ShieldCheck } from "lucide-react";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";

interface AuditRow {
  id: string;
  action: string;
  actor_user_id: string | null;
  target_type: string | null;
  target_id: string | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";

const COLUMNS: Column<AuditRow>[] = [
  {
    key: "created_at",
    header: "When",
    accessor: (r) => new Date(r.created_at).toLocaleString(),
    sortBy: (r) => new Date(r.created_at),
  },
  {
    key: "action",
    header: "Action",
    accessor: (r) => (
      <code className="rounded bg-[var(--pf-surface2)] px-1.5 py-0.5 text-xs">
        {r.action}
      </code>
    ),
    sortBy: (r) => r.action,
  },
  {
    key: "target",
    header: "Target",
    accessor: (r) =>
      r.target_type
        ? `${r.target_type} · ${r.target_id?.slice(0, 8) ?? ""}`
        : "—",
  },
  {
    key: "actor",
    header: "Actor",
    accessor: (r) => (r.actor_user_id ? r.actor_user_id.slice(0, 8) : "system"),
  },
];

export default function AuditLogPage() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AuditRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        
        const orgsRes = await fetch(`${API_URL}/organizations`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!orgsRes.ok) throw new Error("Failed to list organizations");
        const orgs = (await orgsRes.json()) as { id: string }[];
        if (orgs.length === 0) {
          if (alive) setRows([]);
          return;
        }
        const orgId = orgs[0].id;
        const logRes = await fetch(
          `${API_URL}/organizations/${orgId}/audit-log?limit=200`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (!logRes.ok) throw new Error("Failed to load audit log");
        const data = (await logRes.json()) as { items: AuditRow[] };
        if (alive) setRows(data.items);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      alive = false;
    };
  }, [getToken]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-h1 text-[var(--pf-text)]">Audit log</h1>
        <p className="mt-1 text-sm text-[var(--pf-muted)]">
          Who did what in your workspace. Admins and owners can see this page.
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {rows === null && !error && (
        <div className="text-sm text-[var(--pf-muted)]">Loading…</div>
      )}

      {rows && rows.length === 0 && !error && (
        <EmptyState
          icon={ShieldCheck}
          title="No audit events yet"
          description="When you invite teammates, publish portfolios, or change billing, those events will appear here."
        />
      )}

      {rows && rows.length > 0 && (
        <DataTable
          rows={rows}
          columns={COLUMNS}
          rowKey={(r) => r.id}
          filterKeys={["action", "target_type"]}
          initialPageSize={20}
        />
      )}
    </div>
  );
}

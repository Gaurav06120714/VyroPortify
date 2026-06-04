"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortBy?: (row: T) => string | number | Date;
  className?: string;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  filterKeys?: (keyof T | ((row: T) => string))[];
  emptyState?: React.ReactNode;
  rowKey: (row: T) => string;
  initialPageSize?: number;
}

// Lightweight client-side data table. Sort + filter + paginate without
// pulling in tanstack-table. Replace later if column resize / virtualization
// becomes a need.
export function DataTable<T>({
  rows,
  columns,
  filterKeys,
  emptyState,
  rowKey,
  initialPageSize = 10,
}: DataTableProps<T>) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (!q || !filterKeys) return rows;
    const needle = q.toLowerCase();
    return rows.filter((r) =>
      filterKeys.some((k) => {
        const val =
          typeof k === "function" ? k(r) : (r as Record<string, unknown>)[k as string];
        return String(val ?? "").toLowerCase().includes(needle);
      }),
    );
  }, [rows, q, filterKeys]);

  const sorted = useMemo(() => {
    if (!sort) return filtered;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortBy) return filtered;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = col.sortBy!(a);
      const bv = col.sortBy!(b);
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });
  }, [filtered, sort, columns]);

  const pages = Math.max(1, Math.ceil(sorted.length / initialPageSize));
  const pageRows = sorted.slice(
    page * initialPageSize,
    (page + 1) * initialPageSize,
  );

  function toggleSort(key: string) {
    setSort((cur) => {
      if (!cur || cur.key !== key) return { key, dir: "asc" };
      if (cur.dir === "asc") return { key, dir: "desc" };
      return null;
    });
  }

  return (
    <div className="space-y-3">
      {filterKeys && (
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--pf-muted)]"
            aria-hidden
          />
          <Input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            placeholder="Filter…"
            className="pl-9"
            aria-label="Filter rows"
          />
        </div>
      )}

      <div className="overflow-x-auto rounded-2xl border border-[var(--pf-border-light)]">
        <table className="w-full text-sm">
          <thead className="bg-[var(--pf-surface2)]">
            <tr>
              {columns.map((c) => {
                const sortable = !!c.sortBy;
                const active = sort?.key === c.key;
                const Icon = !active
                  ? ArrowUpDown
                  : sort?.dir === "asc"
                  ? ArrowUp
                  : ArrowDown;
                return (
                  <th
                    key={c.key}
                    scope="col"
                    className={cn(
                      "px-4 py-3 text-left font-semibold text-[var(--pf-text-dim)]",
                      sortable && "cursor-pointer select-none",
                      c.className,
                    )}
                    onClick={sortable ? () => toggleSort(c.key) : undefined}
                  >
                    <span className="inline-flex items-center gap-1.5">
                      {c.header}
                      {sortable && (
                        <Icon
                          className={cn(
                            "h-3.5 w-3.5",
                            active
                              ? "text-[var(--pf-accent)]"
                              : "text-[var(--pf-muted)]",
                          )}
                          aria-hidden
                        />
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center">
                  {emptyState ?? (
                    <span className="text-sm text-[var(--pf-muted)]">
                      No rows
                    </span>
                  )}
                </td>
              </tr>
            )}
            {pageRows.map((r) => (
              <tr
                key={rowKey(r)}
                className="border-t border-[var(--pf-border-subtle)] hover:bg-[var(--pf-surface2)]"
              >
                {columns.map((c) => (
                  <td key={c.key} className={cn("px-4 py-3 text-[var(--pf-text)]", c.className)}>
                    {c.accessor(r)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sorted.length > initialPageSize && (
        <div className="flex items-center justify-between text-xs text-[var(--pf-muted)]">
          <span>
            {page * initialPageSize + 1}–
            {Math.min((page + 1) * initialPageSize, sorted.length)} of {sorted.length}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 0))}
              disabled={page === 0}
              className="rounded-md border border-[var(--pf-border-light)] px-2 py-1 disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, pages - 1))}
              disabled={page === pages - 1}
              className="rounded-md border border-[var(--pf-border-light)] px-2 py-1 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

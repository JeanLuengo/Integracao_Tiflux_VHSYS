import type { PaginationState } from '@tanstack/react-table'

/** Evita re-render quando TanStack dispara reset com os mesmos valores. */
export function applyPaginationUpdate(
  prev: PaginationState,
  updater: PaginationState | ((p: PaginationState) => PaginationState),
): PaginationState {
  const next = typeof updater === 'function' ? updater(prev) : updater
  if (next.pageIndex === prev.pageIndex && next.pageSize === prev.pageSize) return prev
  return next
}

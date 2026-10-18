export function Pagination({ offset, limit, count, onChange }: { offset: number; limit: number; count: number; onChange: (offset: number) => void }) {
  return <nav className="pagination" aria-label="Scientific record pagination"><button type="button" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>Previous</button><span>Showing {count} record{count === 1 ? "" : "s"}; page size {limit}</span><button type="button" disabled={count < limit} onClick={() => onChange(offset + limit)}>Next</button></nav>;
}

import { useState, useMemo } from 'react';

export default function Table({
  columns = [],
  data = [],
  pageSize = 10,
  sortable = true,
  emptyText = 'Veri bulunamadi.',
}) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);

  function handleSort(key) {
    if (!sortable) return;
    if (sortKey === key) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
    setPage(1);
  }

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey];
      if (va == null) return 1;
      if (vb == null) return -1;
      const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="card overflow-hidden">
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            {columns.map(col => (
              <th
                key={col.key}
                onClick={() => col.sortable !== false && handleSort(col.key)}
                style={{
                  textAlign: col.align || 'left',
                  padding: '10px 16px',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#6b7280',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: sortable && col.sortable !== false ? 'pointer' : 'default',
                  userSelect: 'none',
                }}
              >
                {col.label}
                {sortKey === col.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paged.length === 0 && (
            <tr>
              <td colSpan={columns.length} style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>
                {emptyText}
              </td>
            </tr>
          )}
          {paged.map((row, i) => (
            <tr key={row.id || i} style={{ borderBottom: '1px solid #f9fafb' }}>
              {columns.map(col => (
                <td key={col.key} style={{ padding: '12px 16px', textAlign: col.align || 'left' }}>
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 16px', borderTop: '1px solid #f3f4f6' }}>
          <button
            className="btn-secondary"
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            style={{ fontSize: 12, padding: '4px 10px' }}
          >
            ←
          </button>
          <span style={{ fontSize: 12, color: '#6b7280', padding: '4px 8px' }}>
            {page}/{totalPages}
          </span>
          <button
            className="btn-secondary"
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            style={{ fontSize: 12, padding: '4px 10px' }}
          >
            →
          </button>
        </div>
      )}
    </div>
  );
}

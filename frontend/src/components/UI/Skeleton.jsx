import clsx from 'clsx';

export default function Skeleton({ width, height = '1rem', rounded = 'md', className }) {
  const radiusMap = { sm: 'rounded', md: 'rounded-md', lg: 'rounded-lg', full: 'rounded-full' };
  return (
    <div
      className={clsx(
        'animate-pulse bg-gray-200',
        radiusMap[rounded] || 'rounded-md',
        className,
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3">
      <Skeleton width="40%" height="0.75rem" />
      <Skeleton width="60%" height="1.75rem" />
      <Skeleton width="30%" height="0.625rem" />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="card overflow-hidden">
      <div className="p-4 space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: cols }).map((_, j) => (
              <Skeleton key={j} width={`${100 / cols}%`} height="1rem" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

import clsx from 'clsx';

export default function Input({
  label,
  error,
  icon,
  className,
  id,
  ...props
}) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className={clsx('w-full', className)}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
            {icon}
          </span>
        )}
        <input
          id={inputId}
          className={clsx(
            'block w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all',
            'focus:ring-2 focus:ring-brand-600/25 focus:border-brand-600',
            'disabled:bg-gray-50 disabled:text-gray-500',
            error ? 'border-red-400 focus:ring-red-400/25' : 'border-gray-300',
            icon && 'pl-9',
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-xs text-red-500">{error}</p>
      )}
    </div>
  );
}

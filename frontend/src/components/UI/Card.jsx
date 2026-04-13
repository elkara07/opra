import clsx from 'clsx';

export default function Card({ header, footer, children, className, ...props }) {
  return (
    <div
      className={clsx(
        'bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden',
        className,
      )}
      {...props}
    >
      {header && (
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          {typeof header === 'string' ? (
            <h3 className="text-sm font-semibold text-gray-700">{header}</h3>
          ) : header}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
          {footer}
        </div>
      )}
    </div>
  );
}

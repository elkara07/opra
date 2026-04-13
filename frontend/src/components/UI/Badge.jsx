import clsx from 'clsx';

const colorMap = {
  success: 'bg-green-50 text-green-700 border-green-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  error:   'bg-red-50 text-red-700 border-red-200',
  info:    'bg-blue-50 text-blue-700 border-blue-200',
  neutral: 'bg-gray-100 text-gray-600 border-gray-200',
  brand:   'bg-brand-50 text-brand-700 border-brand-200',
  vip:     'bg-yellow-50 text-yellow-800 border-yellow-300',
  gold:    'bg-yellow-50 text-yellow-700 border-yellow-200',
  silver:  'bg-slate-100 text-slate-600 border-slate-300',
};

export default function Badge({ color = 'neutral', children, className }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
        colorMap[color] || colorMap.neutral,
        className,
      )}
    >
      {children}
    </span>
  );
}

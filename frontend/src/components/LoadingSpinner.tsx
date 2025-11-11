/**
 * LoadingSpinner Component
 * Reusable loading spinner
 */

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  fullScreen?: boolean;
}

export default function LoadingSpinner({
  size = 'md',
  message,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center">
      <div
        className={`${sizes[size]} border-4 border-blue-600 border-t-transparent rounded-full animate-spin`}
      />
      {message && (
        <p className="mt-4 text-slate-600 dark:text-slate-400 text-center">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-50 dark:bg-slate-900 z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export function PageLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <LoadingSpinner size="lg" message={message} />
    </div>
  );
}

export function InlineLoader({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center p-8">
      <LoadingSpinner size="md" message={message} />
    </div>
  );
}

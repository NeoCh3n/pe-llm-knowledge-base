import React, { useState, useEffect } from 'react';
import { Monitor, X } from 'lucide-react';

export function MobileResponsiveNotice() {
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    const checkViewport = () => {
      if (window.innerWidth < 1024 && !isDismissed) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    checkViewport();
    window.addEventListener('resize', checkViewport);
    return () => window.removeEventListener('resize', checkViewport);
  }, [isDismissed]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/90 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-6 text-center">
        <div className="flex justify-end">
          <button
            onClick={() => {
              setIsDismissed(true);
              setIsVisible(false);
            }}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Dismiss notice"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mb-4">
          <Monitor size={48} className="mx-auto text-blue-600" />
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Desktop Optimized
        </h2>

        <p className="text-gray-600 mb-6">
          PE Memory OS is optimized for desktop use (1024px+). Some features may not work correctly on smaller screens.
        </p>

        <button
          onClick={() => {
            setIsDismissed(true);
            setIsVisible(false);
          }}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Continue Anyway
        </button>
      </div>
    </div>
  );
}

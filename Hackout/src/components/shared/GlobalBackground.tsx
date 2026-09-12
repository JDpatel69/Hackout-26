import { useLocation } from 'react-router-dom';
import { SylvaLivingWorldScene } from '@designcodeio/threeui/components/SylvaLivingWorldScene';
import { useMemo, useState, useEffect } from 'react';

/**
 * Fixed full-viewport 3D background rendered once, shared across all pages.
 * On the landing page it shows with minimal overlay; on all other pages
 * a stronger blur + dark scrim keeps data/text readable.
 */
export function GlobalBackground() {
  const { pathname } = useLocation();
  const isLanding = pathname === '/';

  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    if (!isLanding) return;
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    // Initialize on mount
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isLanding]);

  const lowEnd = useMemo(() => {
    if (typeof navigator === 'undefined') return false;
    const nav = navigator as Navigator & { deviceMemory?: number };
    const cores = nav.hardwareConcurrency ?? 8;
    const mem = nav.deviceMemory ?? 8;
    return cores < 4 || mem < 4;
  }, []);

  const renderScene = !lowEnd;

  // Fade in the dark blur overlay between 100px and 600px of scroll
  const landingOpacity = Math.max(0, Math.min((scrollY - 100) / 500, 1));

  return (
    <div className="global-bg" aria-hidden="true">
      <div className="global-bg__scene">
        {renderScene ? (
          <SylvaLivingWorldScene />
        ) : (
          <div className="global-bg__fallback" />
        )}
      </div>
      
      {!isLanding && <div className="global-bg__overlay global-bg__overlay--page" />}
      {isLanding && (
        <div 
          className="global-bg__overlay global-bg__overlay--page" 
          style={{ opacity: landingOpacity }} 
        />
      )}
    </div>
  );
}

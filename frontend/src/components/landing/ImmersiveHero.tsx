import type { ReactNode } from 'react';
import { useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  motion,
  MotionConfig,
  useMotionValue,
  useSpring,
  useTransform,
  type MotionValue,
} from 'framer-motion';
import { ArrowRight, ChevronDown, Leaf, ShieldCheck, Sprout, CheckCircle2 } from 'lucide-react';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { FloatingDock } from './FloatingDock';
import './landing.css';

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

/** Staggered "rise" entrance preset for DOM/typography. */
const rise = (delay: number) => ({
  initial: { opacity: 0, y: 26 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.72, ease: EASE },
});

/** Smooth pointer-driven parallax value pair, springed. Disabled => stays 0. */
function usePointerParallax(enabled: boolean) {
  const px = useMotionValue(0);
  const py = useMotionValue(0);
  const sx = useSpring(px, { stiffness: 55, damping: 18, mass: 0.7 });
  const sy = useSpring(py, { stiffness: 55, damping: 18, mass: 0.7 });

  useEffect(() => {
    if (!enabled) {
      px.set(0);
      py.set(0);
      return;
    }
    const onMove = (e: PointerEvent) => {
      px.set(e.clientX / window.innerWidth - 0.5);
      py.set(e.clientY / window.innerHeight - 0.5);
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, [enabled, px, py]);

  return { sx, sy };
}

/**
 * A floating card: an absolutely-placed slot whose transforms compose across
 * nested layers — pointer parallax, one-shot entrance, and a perpetual ambient
 * drift — so none of them fight over `transform`.
 */
function FloatCard({
  slotClass,
  px,
  py,
  delay,
  float,
  children,
}: {
  slotClass: string;
  px: MotionValue<number>;
  py: MotionValue<number>;
  delay: number;
  float?: { range: number[]; dur: number; delay?: number };
  children: ReactNode;
}) {
  return (
    <div className={`tl-card-slot ${slotClass}`}>
      <motion.div style={{ x: px, y: py }}>
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.965 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay, duration: 0.75, ease: EASE }}
        >
          <motion.div
            animate={float ? { y: float.range } : undefined}
            transition={
              float
                ? { duration: float.dur, delay: float.delay ?? 0, repeat: Infinity, ease: 'easeInOut' }
                : undefined
            }
          >
            {children}
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}

/** Decorative, unlabeled sparkline (no axes/values — it asserts no metric). */
function Sparkline() {
  const data = [10, 13, 9, 16, 14, 21, 18, 27, 24, 33];
  const max = Math.max(...data);
  const stepX = 100 / (data.length - 1);
  const line = data.map((v, i) => `${(i * stepX).toFixed(1)},${(40 - (v / max) * 34 - 3).toFixed(1)}`).join(' ');
  return (
    <svg className="tl-card__spark" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="tlSparkFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#22c55e" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,40 ${line} 100,40`} fill="url(#tlSparkFill)" />
      <polyline points={line} fill="none" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ImmersiveHero() {
  const reduced = useMediaQuery('(prefers-reduced-motion: reduce)');
  const isTablet = useMediaQuery('(max-width: 1024px)');

  const parallaxOn = !reduced && !isTablet;

  const { sx, sy } = usePointerParallax(parallaxOn);

  // Per-layer depth: nearer cards move more.
  const leadX = useTransform(sx, (v) => v * -12);
  const leadY = useTransform(sy, (v) => v * -8);
  const metricX = useTransform(sx, (v) => v * 34);
  const metricY = useTransform(sy, (v) => v * 24);
  const verifyX = useTransform(sx, (v) => v * 22);
  const verifyY = useTransform(sy, (v) => v * 16);
  const chipX = useTransform(sx, (v) => v * 12);
  const chipY = useTransform(sy, (v) => v * 9);

  return (
    <MotionConfig reducedMotion="user">
      <section className="tl-hero" aria-label="TerraLedger — verified climate impact">
        {/* 
          Layer 0 — the living environment is now rendered globally by <GlobalBackground />.
          The hero is transparent and sits on top of the fixed global scene.
        */}

        {/* Layer 1 — atmosphere / legibility */}
        <div className="tl-hero__scrim tl-hero__scrim--top" aria-hidden="true" />

        {/* Layer 2 — editorial lead */}
        <div className="tl-hero__content">
          <motion.div className="tl-hero__lead" style={{ x: leadX, y: leadY }}>
            <motion.span className="tl-hero__eyebrow" {...rise(0.35)}>
              <Sprout size={13} /> Agricultural carbon, made credible
            </motion.span>
            <motion.h1 className="tl-hero__title" {...rise(0.5)}>
              Climate impact you can <em>measure, verify, and&nbsp;grow.</em>
            </motion.h1>
            <motion.p className="tl-hero__sub" {...rise(0.72)}>
              TerraLedger connects regenerative farms, independent verification, climate research,
              and impact capital in one transparent carbon-credit ecosystem.
            </motion.p>
            <motion.div className="tl-hero__actions" {...rise(0.9)}>
              <Link to="/role-selection" className="tl-btn tl-btn--primary">
                Get started <ArrowRight size={17} />
              </Link>
              <Link to="/how-it-works" className="tl-btn tl-btn--ghost">
                See how it works
              </Link>
            </motion.div>
          </motion.div>
        </div>

        {/* Foreground — floating MRV / environmental data cards (real data) */}
        <div className="tl-hero__cards">
          <FloatCard
            slotClass="tl-card-slot--metric"
            px={metricX}
            py={metricY}
            delay={1.05}
            float={{ range: [0, -9, 0], dur: 7 }}
          >
            <article className="tl-card tl-card--metric">
              <div className="tl-card__head">
                <span className="tl-card__icon"><Leaf size={17} /></span>
                <span className="tl-card__label">CO₂e verified</span>
              </div>
              <p className="tl-card__value">28,460<span>t</span></p>
              <span className="tl-card__trend"><ArrowRight size={13} style={{ transform: 'rotate(-45deg)' }} /> 18.2% this quarter</span>
              <Sparkline />
            </article>
          </FloatCard>

          <FloatCard
            slotClass="tl-card-slot--verify"
            px={verifyX}
            py={verifyY}
            delay={1.2}
            float={{ range: [0, -7, 0], dur: 8, delay: 0.6 }}
          >
            <article className="tl-card tl-card--verify">
              <div className="tl-card__head">
                <span className="tl-card__icon"><ShieldCheck size={17} /></span>
                <span className="tl-card__label">Independent verification</span>
              </div>
              <h3 className="tl-card__title">Green Valley Rice Farm</h3>
              <p className="tl-card__meta">Punjab, India · no-till &amp; cover-crop transition</p>
              <div className="tl-card__bar"><i style={{ width: '82%' }} /></div>
              <div className="tl-card__foot"><CheckCircle2 size={14} /> 126.4 tCO₂e verified · 2026</div>
            </article>
          </FloatCard>
        </div>

        {/* Scroll cue */}
        <motion.div
          className="tl-scrollcue"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6, duration: 0.8 }}
        >
          Explore the platform <ChevronDown size={15} />
        </motion.div>
      </section>

      {/* Floating navigation dock (moved outside tl-hero to avoid stacking context clipping) */}
      <FloatingDock />
    </MotionConfig>
  );
}

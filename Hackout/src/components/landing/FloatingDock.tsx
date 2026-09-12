import { Link, NavLink } from 'react-router-dom';
import { Sprout, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

/**
 * Floating glass navigation dock for the immersive landing page.
 * Uses TerraLedger's real routes (mirrors the standard <Navbar/>) so all
 * existing navigation behaviour is preserved — it is only restyled to feel
 * like a dock hovering inside the 3D world.
 */
export function FloatingDock() {
  return (
    <motion.nav
      className="tl-dock"
      aria-label="Primary"
      initial={{ y: -26, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.55, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      <Link to="/" className="tl-dock__brand">
        <span className="tl-dock__mark"><Sprout size={17} /></span>
        <span>TerraLedger</span>
      </Link>

      <div className="tl-dock__links">
        <NavLink to="/about">About</NavLink>
        <NavLink to="/how-it-works">How it works</NavLink>
        <NavLink to="/impact">Impact</NavLink>
        <NavLink to="/contact">Contact</NavLink>
      </div>

      <Link to="/auth/signin" className="tl-dock__cta">
        Sign in <ArrowRight size={15} />
      </Link>
    </motion.nav>
  );
}

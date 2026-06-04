// Light-mode-only build (Jun 2026).
// The Light / Dark / System switcher was removed: product decision is to
// lock the app to a single light theme so we maintain one visual surface.
// The PaletteToggle (Aurora vs Clarity) remains the canonical theming
// control.
//
// This file is preserved as a no-op default export so existing imports
// (Sidebar, marketing nav, etc.) don't need to be rewritten in lockstep.
// Safe to delete once those call sites are cleaned up.
interface Props {
  compact?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function ThemeToggle(_props: Props = {}) {
  return null;
}

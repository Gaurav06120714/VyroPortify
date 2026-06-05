# Theme

## 🎨 Theme System

VyroPortify ships with a full **Light / Dark / System** theme:

- CSS custom properties (`--pf-*`) defined for both modes in `globals.css`
- `ThemeContext` applies the `dark` class to `<html>` and persists to `localStorage`
- Anti-flash inline script in `layout.tsx` resolves theme before first paint
- Smooth 200ms transitions across all color properties


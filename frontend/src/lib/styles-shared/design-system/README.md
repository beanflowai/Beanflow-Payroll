# Beanflow Design System

Modular, maintainable design system for the Beanflow financial application.

## 📁 Architecture

```
design-system/
├── index.css           # Main entry point (imports all modules)
├── 01-fonts.css        # Font declarations (@font-face)
├── 02-tokens.css       # Design tokens (colors, typography, spacing, etc.)
├── 03-typography.css   # Typography utility classes
├── 04-colors.css       # Color utility classes
├── 05-buttons.css      # Button components
├── 06-forms.css        # Form components
├── 07-cards.css        # Card components
├── 08-layout.css       # Layout utility classes
├── 09-animations.css   # Animation keyframes and utilities
├── 10-utilities.css    # Miscellaneous utilities
└── 11-reports.css      # Financial report styling
```

## ⚠️ Token Synchronization

### Important: Tokens are Intentionally Duplicated

Design tokens are maintained in **two locations**:

1. **`02-tokens.css`** (`:root` block) - **SINGLE SOURCE OF TRUTH**
   - Primary definition for all design tokens
   - Used by custom component classes throughout the design system
   - Examples: `.btn-fill`, `.card`, `.form-control`

2. **`../../app.css`** (`@theme` block) - TailwindCSS Configuration
   - Required by TailwindCSS v4 to generate utility classes
   - Examples: `text-primary-500`, `bg-surface-100`, `rounded-lg`

### Why Two Copies?

**Technical Reason:**

- TailwindCSS v4 requires tokens in `@theme` block to generate utilities
- Custom components use CSS variables from `:root` block
- Both systems need access to the same token values

**Usage Pattern:**

```css
/* Custom component (uses :root tokens) */
.btn-fill {
  background: var(--color-primary-500);
  color: white;
}

/* Svelte component (uses TailwindCSS utilities) */
<button class="text-primary-500 bg-surface-100 rounded-lg">
```

## 🔄 How to Update Tokens

### Step-by-Step Process

1. **Edit `02-tokens.css` first**

   ```css
   :root {
   	--color-primary-500: #9810fa; /* Update here */
   }
   ```

2. **Copy changes to `../../app.css` `@theme` block**

   ```css
   @theme {
   	--color-primary-500: #9810fa; /* Copy here */
   }
   ```

3. **Run build to verify**

   ```bash
   npm run build
   ```

4. **Test both systems**
   - Custom components: Check `.btn-fill`, `.card`, etc.
   - TailwindCSS utilities: Check `text-primary-500`, `bg-*`, etc.

### Common Token Updates

#### Updating Colors

```css
/* 02-tokens.css */
--color-primary-500: #9810fa; /* Update */
--color-success-500: #6ec02b; /* Update */

/* Copy to app.css @theme */
--color-primary-500: #9810fa;
--color-success-500: #6ec02b;
```

#### Updating Typography

```css
/* 02-tokens.css */
--font-size-body-content: 14px; /* Update */
--line-height-body-content: 18px; /* Update */

/* Copy to app.css @theme */
--font-size-body-content: 14px;
--line-height-body-content: 18px;
```

#### Updating Spacing

```css
/* 02-tokens.css */
--spacing-4: 16px; /* Update */

/* Copy to app.css @theme */
--spacing-4: 16px;
```

## 📦 Module Overview

### Foundation Layer

#### `01-fonts.css`

- SF Pro Text `@font-face` declarations (300-800 weights)
- Font stack variables
- Loading optimizations

#### `02-tokens.css`

- **Single source of truth** for all design tokens
- Colors (Primary, Secondary, Surface, Success, Warning, Error)
- Typography scale (12 levels)
- Spacing system (8px grid)
- Border radius, shadows, animations
- Button tokens, z-index scale

### Utility Layer

#### `03-typography.css`

Typography utility classes following Figma standards:

- `.text-headline-large`, `.text-title-medium`, etc.
- `.text-body-content`, `.text-caption-text`
- Financial-specific: `.text-transaction-data`

#### `04-colors.css`

Color utility classes:

- Text colors: `.text-primary-500`, `.text-surface-900`
- Background colors: `.bg-surface-100`, `.bg-primary-500`
- Financial colors: `.text-amount-positive`, `.text-amount-negative`

#### `08-layout.css`

Layout utilities:

- Flexbox: `.flex`, `.flex-col`, `.items-center`
- Spacing: `.p-4`, `.m-2`, `.gap-6`
- Border radius: `.rounded-lg`, `.rounded-full`
- Shadows: `.shadow-md3-2`

#### `10-utilities.css`

Miscellaneous utilities:

- Focus states, hover effects
- Responsive breakpoints
- Tooltips
- Accessibility utilities

### Component Layer

#### `05-buttons.css`

Button components:

- `.btn-fill` - Solid background button
- `.btn-border` - Outlined button
- `.btn-text` - Text-only button
- `.btn-success` - Green success button
- Size variants: `.btn-small`, `.btn-medium`, `.btn-large`

#### `06-forms.css`

Form components:

- `.form-control` - Base input/select/textarea
- `.form-label` - Form labels
- `.form-select` - Dropdown styles
- State variants: `.is-valid`, `.is-invalid`, `.is-warning`

#### `07-cards.css`

Card components:

- `.card` - Base card with hover effects
- `.card-elevated` - Card with backdrop blur
- Icon containers

### Animation Layer

#### `09-animations.css`

Animation system:

- `@keyframes` definitions: `fadeInUp`, `pulse`, `spin`
- Animation utilities: `.animate-fade-in-up`
- Transition utilities: `.transition-fast`

### Domain Layer

#### `11-reports.css`

Financial report styling:

- Report table structure
- Hierarchy levels (`.report-level-0` through `.report-level-5`)
- Financial amount styling
- Print-optimized styles

## 🎨 Design Principles

### Color System

- Figma Design System based (migrated from Material Design 3)
- 9-step scale for each color family (50-900)
- Optimized for financial applications (high contrast)
- WCAG AA compliant

### Typography

- Figma Standard 12-level system
- SF Pro Text font family
- Financial application specific sizes
- Mobile-friendly (16px+ for inputs)

### Spacing

- 8px base grid system
- Consistent rhythm across components
- Responsive scaling

### Components

- Figma-based design tokens
- Accessible by default
- Hover, focus, and disabled states
- Mobile-responsive

## 🚀 Usage Examples

### Using Custom Components

```html
<button class="btn-fill btn-medium">Save Transaction</button>
<div class="card p-6">Card content</div>
<input class="form-control" type="text" />
```

### Using TailwindCSS Utilities

```html
<div class="flex items-center gap-4 rounded-lg bg-surface-100 p-6">
	<span class="text-title-large text-primary-500">Title</span>
</div>
```

### Mixing Both Systems

```html
<button class="btn-fill text-body-large flex items-center gap-2">
	<Icon name="check" />
	Approve
</button>
```

## 📝 Maintenance Checklist

### When Adding New Tokens

- [ ] Add to `02-tokens.css` `:root` block
- [ ] Copy to `../../app.css` `@theme` block
- [ ] Document usage in this README
- [ ] Update related utility classes if needed
- [ ] Run `npm run build` to verify
- [ ] Test in actual components

### When Adding New Components

- [ ] Choose appropriate module (05-buttons.css, 06-forms.css, etc.)
- [ ] Use existing tokens (don't hardcode values)
- [ ] Add hover, focus, disabled states
- [ ] Test accessibility (keyboard, screen readers)
- [ ] Document in this README

### When Refactoring

- [ ] Check both custom components and TailwindCSS utilities
- [ ] Update token synchronization if structure changes
- [ ] Run full build and visual regression tests
- [ ] Update documentation

## 🔗 Related Documentation

- **Figma Design System**: Internal design file
- **TailwindCSS v4 Docs**: https://tailwindcss.com/docs
- **Material Design 3**: https://m3.material.io/ (Historical reference - migrated to Figma Design System)

## 📞 Support

For questions or issues with the design system:

1. Check this README first
2. Review token synchronization guide above
3. Check git history for recent changes
4. Contact the frontend team

---

**Last Updated**: 2025-11-06
**Version**: 2.0 (Modular Architecture)

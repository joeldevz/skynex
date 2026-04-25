---
description: @clasing/ui design tokens — semantic colors, typography scale, font weights
globs: ["**/*.tsx", "**/*.jsx", "**/*.css"]
alwaysApply: false
---

# Design Tokens: Colors, Typography, Font Weights

## Semantic Colors — Always Use These

### ✅ Correct: Semantic Tokens (Dark Mode Automatic)

```typescript
// Backgrounds
className="bg-background"           // Main page/card background
className="bg-card"                 // Card/panel surface
className="bg-muted"                // Disabled, secondary backgrounds
className="bg-primary"              // Primary actions (blue)
className="bg-destructive"          // Danger states (red)
className="bg-accent"               // Highlights, focus states
className="bg-info"                 // Info messages
className="bg-success"              // Success states
className="bg-warning"              // Warning states

// Text Colors
className="text-foreground"         // Primary text (dark on light, light on dark)
className="text-card-foreground"    // Text on card surfaces
className="text-muted-foreground"   // Secondary/disabled text
className="text-primary-foreground" // Text on primary backgrounds
className="text-destructive-foreground" // Text on destructive backgrounds
className="text-accent-foreground"  // Text on accent backgrounds

// Borders
className="border border-border"    // Structural borders
className="bg-border"               // Full bg as border color
```

### ❌ WRONG: Raw Tailwind Colors (Break Dark Mode)

```typescript
className="bg-neutral-900"          // ✗ Raw color bypasses design system
className="bg-blue-600"             // ✗ Raw brand color
className="text-gray-400"           // ✗ Raw gray
className="dark:bg-slate-800"       // ✗ Manual dark: (tokens handle it)
className="bg-white"                // ✗ Raw white (use bg-background)
className="text-black"              // ✗ Raw black (use text-foreground)
```

### ✅ Example: Complete Card

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@clasing/ui/card'

export function UserCard() {
  return (
    <Card className="bg-card border border-border">
      <CardHeader>
        <CardTitle className="text-foreground">User Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Secondary information</p>
        <div className="mt-4 p-2 bg-muted rounded-md">
          <p className="text-foreground">Muted background content</p>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Typography Scale — Composite Classes Only

### ✅ Correct: Typography Scales

```typescript
// Display (Large headlines, ~28-48px)
className="display-sm"   // font-semibold, ~28px
className="display-lg"   // font-semibold, ~48px

// Title (Section headers, ~18-32px)
className="title-2xs"    // font-semibold, ~18px
className="title-xs"     // font-semibold, ~20px
className="title-sm"     // font-semibold, ~22px
className="title-md"     // font-semibold, ~24px
className="title-lg"     // font-semibold, ~28px
className="title-xl"     // font-semibold, ~32px

// Label (Form labels, UI labels, ~12-24px)
className="label-xs"     // font-medium, ~12px
className="label-sm"     // font-medium, ~13px
className="label-md"     // font-medium, ~14px
className="label-lg"     // font-medium, ~16px
className="label-xl"     // font-medium, ~18px
className="label-2xl"    // font-semibold, ~20px
className="label-3xl"    // font-semibold, ~24px

// Paragraph (Body text, ~12-20px)
className="paragraph-xs" // font-regular, ~12px
className="paragraph-sm" // font-regular, ~13px
className="paragraph-md" // font-regular, ~14px
className="paragraph-lg" // font-regular, ~16px
```

### ❌ WRONG: Raw text-* Classes

```typescript
className="text-lg font-bold"       // ✗ Raw classes, inconsistent sizing
className="text-xl font-semibold"   // ✗ Breaks design system
className="text-2xl"                // ✗ No weight, unspecified sizing
className="text-base"               // ✗ Not part of our scale
```

### ✅ Example: Typography Hierarchy

```typescript
export function ArticleSection() {
  return (
    <section>
      <h1 className="display-lg text-foreground mb-4">Main Article Title</h1>
      <h2 className="title-lg text-foreground mb-2">Section Header</h2>
      <label className="label-md text-muted-foreground">Metadata:</label>
      <p className="paragraph-md text-foreground">
        Body text using paragraph-md for comfortable reading at standard sizes.
      </p>
    </section>
  )
}
```

---

## Font Weights — Only 3 Available

### ✅ Correct: Supported Weights Only

```typescript
className="font-regular"   // 400 (default, body text)
className="font-medium"    // 500 (medium emphasis)
className="font-semibold"  // 600 (strong emphasis, headings)
```

### ❌ WRONG: Unsupported Weights (Not in DM Sans)

```typescript
className="font-bold"      // ✗ 700 not provided
className="font-light"     // ✗ 300 not provided
className="font-thin"      // ✗ 100 not provided
className="font-normal"    // ✗ Use font-regular instead
className="font-black"     // ✗ 900 not provided
className="font-extrabold" // ✗ Not provided
```

### ✅ Weight Overrides on Typography Scales

Composite typography classes include weights, but override when needed:

```typescript
className="title-lg"                    // Default: font-semibold
className="title-lg font-regular"       // Override: lighter heading
className="paragraph-md font-medium"    // Override: slightly bolder paragraph
className="label-sm font-semibold"      // Override: stronger label
```

### ✅ Example: Typography with Weight Control

```typescript
export function ControlPanel() {
  return (
    <div>
      <h1 className="title-xl font-semibold text-foreground">Settings</h1>
      <h2 className="title-sm font-medium text-muted-foreground">General</h2>
      <p className="paragraph-md font-regular text-foreground">Adjust app settings below.</p>
    </div>
  )
}
```

---

## Color + Typography Combined

### ✅ Example: Balanced Semantic Use

```typescript
export function Alert() {
  return (
    <div className="bg-info border border-border rounded-lg p-4">
      <h3 className="title-sm text-foreground font-semibold">Info</h3>
      <p className="paragraph-sm text-muted-foreground mt-1">
        This is an informational message with semantic colors.
      </p>
    </div>
  )
}
```

### ❌ Example: Anti-Pattern (Mixed Raw & Semantic)

```typescript
// ✗ Mixing raw colors and tokens
export function BadAlert() {
  return (
    <div className="bg-blue-100 border border-blue-300 rounded-lg p-4">
      <h3 className="text-lg font-bold text-blue-900">Info</h3>
      <p className="text-sm text-blue-700 dark:text-blue-300">
        Message (dark: manual variant breaks system)
      </p>
    </div>
  )
}
```

---

## Spacing & Sizing (Tailwind Base)

### ✅ Standard Tailwind Units

```typescript
// Spacing: standard Tailwind scale
className="p-4"          // padding
className="m-2"          // margin
className="gap-3"        // gap
className="rounded-md"   // border-radius (md, lg, xl, full)
className="shadow-lg"    // shadows (xs, sm, md, lg, xl, 2xl)
```

---

## Common Token Mistakes

| Issue | ✗ Wrong | ✓ Correct |
|-------|---------|-----------|
| **Background** | `bg-neutral-900` | `bg-background` |
| **Text on bg** | `text-gray-400` | `text-muted-foreground` |
| **Borders** | `border-slate-300` | `border-border` |
| **Dark mode** | `dark:bg-gray-900` | `bg-background` (automatic) |
| **Heading** | `text-3xl font-bold` | `display-lg` or `title-lg` |
| **Body** | `text-base` | `paragraph-md` |
| **Font weight** | `font-bold`, `font-light` | `font-semibold`, `font-regular` |
| **Card text** | `text-gray-900 dark:text-white` | `text-card-foreground` |

---
description: @clasing/ui import rules and component usage for React/Next.js consumer projects
globs: ["**/*.tsx", "**/*.jsx"]
alwaysApply: false
---

# @clasing/ui Component Imports & Usage Rules

## CRITICAL: Per-Component Entry Points Only

### ✅ Correct Imports

```typescript
// Single component imports
import { Button } from '@clasing/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@clasing/ui/card'
import { Dialog, DialogContent, DialogTrigger } from '@clasing/ui/dialog'

// Blocks and hooks
import { InteractiveCard } from '@clasing/ui/blocks/interactive-card'
import { useOutsideClick } from '@clasing/ui/hooks/useOutsideClick'
import { Option } from '@clasing/ui/utils/types'
```

### ❌ WRONG: Barrel Imports (These Do Not Exist)

```typescript
// ✗ Fails at runtime — @clasing/ui root exports nothing
import { Button, Card, Dialog } from '@clasing/ui'

// ✗ Fails — no namespace exports
import * as UI from '@clasing/ui'
```

---

## `use client` Directive Checklist

### ✅ Add `'use client'` for These Components:

Interactive Radix-based components in any consumer file:
- **Dialogs:** Dialog, AlertDialog, Drawer, Sheet
- **Selects:** Select, MultiSelect, DropdownMenu, ContextMenu, Menubar
- **Toggles:** Checkbox, RadioGroup, Toggle, ToggleGroup, Switch
- **Data:** Table (interactive), Calendar, InputOTP, Slider, ScrollArea
- **Navigation:** Tabs, Accordion, Collapsible, NavigationMenu (interactive), Sidebar, Tree
- **Tooltips:** Tooltip, HoverCard, Popover
- **Forms:** Form, Field (with react-hook-form)
- **Specialized:** Command (searchable), ResizablePanels, Avatar (with logic), Progress, Chart
- **Toast:** Sonner (Toaster provider)

### ✅ NO `'use client'` for These:

Static/display-only components can be Server Components:
- Card, Alert, Badge, Button (static), Input (uncontrolled), Chip, Divider, ButtonGroup, Kbd, Skeleton, Breadcrumb, Label, Textarea (uncontrolled), Pagination (static), ClasingIcon, InteractiveCard, SelectableChips

### ✅ Correct: Server Component with Static UI

```typescript
// app/dashboard/page.tsx (no 'use client')
import { Card, CardContent, CardTitle } from '@clasing/ui/card'
import { Badge } from '@clasing/ui/badge'

export default function Dashboard() {
  return (
    <Card>
      <CardTitle>Dashboard</CardTitle>
      <CardContent>
        <Badge>Active</Badge>
      </CardContent>
    </Card>
  )
}
```

### ✅ Correct: Client Component with Interactive UI

```typescript
// app/components/filter-dialog.tsx
'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogTrigger } from '@clasing/ui/dialog'
import { Button } from '@clasing/ui/button'

export function FilterDialog() {
  const [open, setOpen] = useState(false)
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Filters</Button>
      </DialogTrigger>
      <DialogContent>{/* content */}</DialogContent>
    </Dialog>
  )
}
```

### ❌ WRONG: Interactive Component Without `'use client'`

```typescript
// ✗ Missing 'use client' — useState won't work on server
export function SelectValue() {
  const [value, setValue] = useState('')  // Error: Hooks can't run on server
  return <select onChange={(e) => setValue(e.target.value)} />
}
```

---

## cn() Utility — Consumer Ownership

### ✅ Correct: Import from Consumer's @/lib/utils

```typescript
import { cn } from '@/lib/utils'

export function MyComponent() {
  return <div className={cn('px-4 py-2', 'bg-primary', 'rounded-md')} />
}
```

### ❌ WRONG: Expecting cn() from @clasing/ui

```typescript
// ✗ @clasing/ui/utils only exports { Option } type
import { cn } from '@clasing/ui/utils'  // File exists but cn() not exported
```

**Why:** @clasing/ui is a compiled library. Consumer projects manage their own utility functions via clsx, classnames, or class-variance-authority (CVA).

---

## Component Composition Patterns

### ✅ Correct: Compose with Sub-Components

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@clasing/ui/card'
import { Button } from '@clasing/ui/button'

export function MyCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Content here</p>
        <Button>Action</Button>
      </CardContent>
    </Card>
  )
}
```

### ❌ WRONG: Treating Compound Components as Single Import

```typescript
// ✗ CardHeader, CardTitle don't have separate entry points
import { CardHeader } from '@clasing/ui/card-header'  // Wrong path

// ✓ Correct: All exported from card entry point
import { Card, CardHeader, CardTitle } from '@clasing/ui/card'
```

---

## All 56 Entry Points (Quick Reference)

**Core (53):** accordion, alert, alert-dialog, avatar, badge, breadcrumb, button, button-group, calendar, card, chart, checkbox, chip, clasing-icon, collapsible, command, context-menu, dialog, divider, drawer, dropdown-menu, field, form, hover-card, input, input-otp, kbd, label, menubar, multi-select, navigation-menu, pagination, phone-input, popover, progress, radio-group, resizable, scroll-area, select, sheet, sidebar, skeleton, slider, sonner, switch, table, tabs, textarea, toggle, toggle-group, tooltip, tree

**Blocks (2):** blocks/interactive-card, blocks/selectable-chips

**Hooks (1):** hooks/useOutsideClick

**Utils (1):** utils/types (exports `Option` only)

---

## Icon Usage Rules

### ✅ Correct: @phosphor-icons/react Only

```typescript
import { User, Bell, Settings, Plus } from '@phosphor-icons/react'

export function Header() {
  return (
    <header className="flex gap-4">
      <User size={24} weight="regular" />
      <Bell size={20} weight="fill" />
      <Settings size={32} weight="bold" />
      <Plus size={16} />
    </header>
  )
}
```

### ❌ WRONG: Other Icon Libraries

```typescript
import { User } from 'lucide-react'        // ✗ Not in this project
import { FaUser } from 'react-icons/fa'    // ✗ Not in this project
```

---

## Common Mistakes Summary

| Issue | ✗ Wrong | ✓ Correct |
|-------|---------|-----------|
| Import strategy | `import { Button } from '@clasing/ui'` | `import { Button } from '@clasing/ui/button'` |
| cn() source | `import { cn } from '@clasing/ui/utils'` | `import { cn } from '@/lib/utils'` |
| Interactive without client | No `'use client'` on Dialog, Select | `'use client'` at top of file |
| Icon library | lucide-react, react-icons | @phosphor-icons/react |
| Compound sub-import | `from '@clasing/ui/card-header'` | `from '@clasing/ui/card'` |

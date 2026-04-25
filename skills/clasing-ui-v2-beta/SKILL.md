---
name: clasing-ui-v2-beta
description: "Expert guidance for consuming @clasing/ui v2.9.3 in React/Next.js projects. Use when writing, importing, styling, or debugging UI components from @clasing/ui. Covers: imports, component APIs, design tokens, typography, colors, icons, dark mode, and accessibility."
license: MIT
---

# @clasing/ui v2.9.3 Consumer Skill

## Role

You are an expert in **@clasing/ui v2.9.3**, a compiled React 19 component library built on Radix UI, Tailwind CSS v4, and CVA. You provide guidance on:
- Importing components correctly (per-component entry points only, no barrel imports)
- Using design tokens semantically (colors, typography, spacing)
- Setting up dark mode and styling
- Implementing form patterns with react-hook-form
- Accessing all 56 components and utilities
- Avoiding the 8 most common consumption mistakes

## When to Use This Skill

- Writing or importing components from `@clasing/ui`
- Applying design tokens (colors, typography, spacing, shadows)
- Implementing forms with `Form`, `Field`, and validation
- Debugging "component not found" or import errors
- Implementing dark mode or semantic color usage
- Using icons or typography utilities
- Building interactive components (dialogs, modals, selects, etc.)

## Setup

### Installation

```bash
pnpm add @clasing/ui
```

Install peer dependencies **only for components you use**:
```bash
pnpm add @phosphor-icons/react @radix-ui/react-dialog @radix-ui/react-select ...
```

### Styles Import (App Root)

Import once at your application root:
```typescript
// app/layout.tsx or pages/_app.tsx
import '@clasing/ui/styles'
```

### Font Setup

DM Sans (only weights: 400/500/600) is bundled. Include in your `next.config.js` or `tailwind.config.ts`:
```javascript
// next.config.js
const defaultFont = {
  fontFamily: 'DM Sans, ui-sans-serif, system-ui, -apple-system, ...',
}
```

---

## IMPORTING RULES — Critical First Step

### ✅ Correct: Per-Component Entry Points

```typescript
// Import individual components only
import { Button } from '@clasing/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@clasing/ui/card'
import { Dialog, DialogContent, DialogTrigger } from '@clasing/ui/dialog'
import { ClasingIcon } from '@clasing/ui/clasing-icon'
import { Badge } from '@clasing/ui/badge'
```

### ❌ WRONG: Barrel Imports (Don't Exist)

```typescript
// These will fail — @clasing/ui exports nothing at the root
import { Button, Card, Dialog } from '@clasing/ui'
import * as UI from '@clasing/ui'
```

### ✅ Blocks and Hooks

```typescript
// Special entry points for blocks and hooks
import { InteractiveCard } from '@clasing/ui/blocks/interactive-card'
import { SelectableChips } from '@clasing/ui/blocks/selectable-chips'
import { useOutsideClick } from '@clasing/ui/hooks/useOutsideClick'
import { Option } from '@clasing/ui/utils/types'
```

---

## cn() Utility — Consumer Project Only

### ✅ Correct: Use `@/lib/utils`

```typescript
import { cn } from '@/lib/utils'

export function MyButton() {
  return <button className={cn('px-4 py-2', 'bg-primary')}>Click</button>
}
```

### ❌ WRONG: @clasing/ui/utils (Doesn't Export cn())

```typescript
// This will fail — @clasing/ui/utils only exports { Option }
import { cn } from '@clasing/ui/utils'
```

**Why:** @clasing/ui is compiled; consumers manage their own `cn()` utility. Define it in `@/lib/utils` using clsx or classnames.

---

## `use client` Directive

### Components That REQUIRE `use client`:

Interactive Radix components. Add `'use client'` at the top of files consuming these:

**Dialogs & Popovers:**
- Dialog, AlertDialog, Drawer, Sheet

**Selects & Dropdowns:**
- Select, DropdownMenu, ContextMenu, Menubar, CommandPalette (if interactive)

**Form Controls:**
- Checkbox, RadioGroup, Toggle, ToggleGroup, Slider, Switch

**Data:**
- Table (with interactive cells), Calendar, InputOTP, MultiSelect

**Navigation & Menus:**
- NavigationMenu (interactive items), Tabs, Accordion, Collapsible

**Tooltips & Hints:**
- Tooltip, HoverCard, Popover

**Specialized:**
- ScrollArea, ResizablePanels, Sidebar, Tree, Command (search), Form (with fields)
- Avatar (with fallbacks), Progress, Chart, PhoneInput, Pagination

**Display/Toast:**
- Sonner (toast provider)

### Components That DON'T Need `use client`:

Static/display-only. Can live in Server Components:
- Card, Alert, Badge, Button (static), Input (uncontrolled), Chip, Divider
- ButtonGroup, Kbd, Skeleton, Breadcrumb, ClasingIcon, InteractiveCard, SelectableChips
- Label, Textarea (uncontrolled), Spinner, Separator

```typescript
// ✅ Server Component
import { Card, CardContent, CardTitle } from '@clasing/ui/card'
import { Badge } from '@clasing/ui/badge'

export default function MyPage() {
  return (
    <Card>
      <CardTitle>Static Content</CardTitle>
      <Badge>Active</Badge>
    </Card>
  )
}
```

```typescript
// ✅ Client Component (for interactivity)
'use client'

import { Dialog, DialogContent, DialogTrigger } from '@clasing/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@clasing/ui/select'

export function InteractivePanel() {
  const [open, setOpen] = useState(false)
  return <Dialog open={open}>{/* ... */}</Dialog>
}
```

---

## Design Tokens — Semantic Colors

### ✅ Correct: Semantic Tokens

Always use semantic color tokens. They handle dark mode automatically:

```typescript
// Background colors
className="bg-background"       // Main background
className="bg-card"             // Card surface
className="bg-muted"            // Muted/disabled backgrounds

// Content colors
className="text-foreground"     // Primary text
className="text-card-foreground" // Card text
className="text-muted-foreground" // Secondary text

// Semantic intent colors
className="bg-primary text-primary-foreground"       // Primary actions
className="bg-destructive text-destructive-foreground" // Danger
className="bg-accent text-accent-foreground"        // Highlights
className="bg-info"             // Informational
className="bg-success"          // Success state
className="bg-warning"          // Warning state

// Structural
className="border-border"       // Border color
```

### ❌ WRONG: Raw Tailwind Colors (Don't Use)

```typescript
// These bypass the design system and break dark mode
className="bg-neutral-900"      // ✗ Raw neutral
className="bg-blue-600"         // ✗ Raw blue
className="text-gray-400"       // ✗ Raw gray
className="dark:bg-slate-800"   // ✗ Manual dark: (tokens handle it)
```

### ✅ Correct: Borders & Dividers

```typescript
className="border border-border"
className="bg-gradient-to-r from-border to-transparent"
```

---

## Design Tokens — Typography Scale

### ✅ Correct: Composite Typography Classes

Never use raw `text-*` classes. Use composite typography scales:

```typescript
// Display (largest, ~28-48px)
className="display-sm"    // display-sm (font-semibold)
className="display-lg"    // display-lg (font-semibold)

// Title (headers, ~18-32px)
className="title-2xs"     // ~18px, font-semibold
className="title-xs"      // ~20px, font-semibold
className="title-sm"      // ~22px, font-semibold
className="title-md"      // ~24px, font-semibold
className="title-lg"      // ~28px, font-semibold
className="title-xl"      // ~32px, font-semibold

// Label (UI labels, ~12-20px)
className="label-xs"      // ~12px, font-medium
className="label-sm"      // ~13px, font-medium
className="label-md"      // ~14px, font-medium
className="label-lg"      // ~16px, font-medium
className="label-xl"      // ~18px, font-medium
className="label-2xl"     // ~20px, font-semibold
className="label-3xl"     // ~24px, font-semibold

// Paragraph (body text, ~12-20px)
className="paragraph-xs"  // ~12px, font-regular
className="paragraph-sm"  // ~13px, font-regular
className="paragraph-md"  // ~14px, font-regular
className="paragraph-lg"  // ~16px, font-regular
```

### ❌ WRONG: Raw Text-* Classes

```typescript
className="text-lg font-bold"         // ✗ Raw text-* + font-*
className="text-xl font-semibold"     // ✗ Mixes raw classes
className="text-2xl"                  // ✗ No weight specified
```

### Combining Weights (Optional Overrides)

Composite classes already include weights, but you can override:

```typescript
className="title-md font-regular"     // Override to regular weight
className="label-lg font-semibold"    // Override to semibold
className="paragraph-sm font-medium"  // Override to medium
```

---

## Font Weights — Only 3 Available

@clasing/ui only provides **3 weights**. Others will not work:

### ✅ Correct

```typescript
className="font-regular"     // 400
className="font-medium"      // 500
className="font-semibold"    // 600
```

### ❌ WRONG (Don't Exist)

```typescript
className="font-bold"        // ✗ Not available (no 700)
className="font-light"       // ✗ Not available (no 300)
className="font-normal"      // ✗ Use font-regular instead
className="font-thin"        // ✗ Not available
className="font-black"       // ✗ Not available
```

---

## Icons — @phosphor-icons/react Only

### ✅ Correct: Phosphor Icons

```typescript
import { User, Bell, Settings, Clock, CheckCircle } from '@phosphor-icons/react'

export function Header() {
  return (
    <div>
      <User size={24} weight="bold" />
      <Bell size={20} weight="regular" />
      <Settings size={32} weight="fill" />
    </div>
  )
}
```

Size and weight via props:

```typescript
<User
  size={24}           // 16, 20, 24, 32, 40, 48 (common)
  weight="regular"    // "thin", "light", "regular", "bold", "fill"
  color="currentColor" // Inherits text color by default
/>
```

### ❌ WRONG: Other Icon Libraries

```typescript
import { User } from 'lucide-react'                    // ✗ Not in this library
import { User } from 'react-icons/fa'                  // ✗ Not in this library
import { UserIcon } from '@clasing/ui/icons'           // ✗ Entry point doesn't exist
```

---

## Dark Mode — Automatic via Semantic Tokens

### ✅ Correct: Semantic Tokens Handle Dark Mode

Dark mode is managed by the design system. When `.dark` class is on the root, semantic tokens automatically adapt:

```typescript
// In client component or layout
'use client'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return (
    <button onClick={() => setIsDark(!isDark)}>
      Toggle {isDark ? 'light' : 'dark'} mode
    </button>
  )
}
```

Colors automatically swap:

```typescript
// In any component — bg-background and text-foreground adapt
<div className="bg-background text-foreground">
  Auto-adapts to dark mode when .dark class is present
</div>
```

### ❌ WRONG: Manual dark: Variants

```typescript
// ✗ Don't use dark: prefixes — tokens do it
className="bg-white dark:bg-gray-900"
className="text-gray-900 dark:text-white"

// Correct approach
className="bg-background text-foreground"  // ✓ Automatic
```

---

## All 56 Entry Points (Component Discovery)

### Core Components (53)

**Layout & Structure:**
- `card` — Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter
- `divider` — Divider
- `breadcrumb` — Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator
- `navigation-menu` — NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuItem, NavigationMenuList, NavigationMenuTrigger, NavigationMenuViewport

**Buttons & Controls:**
- `button` — Button
- `button-group` — ButtonGroup
- `kbd` — Kbd
- `badge` — Badge
- `chip` — Chip
- `clasing-icon` — ClasingIcon

**Forms:**
- `input` — Input
- `textarea` — Textarea
- `label` — Label
- `checkbox` — Checkbox
- `radio-group` — RadioGroup, RadioGroupItem
- `toggle` — Toggle
- `toggle-group` — ToggleGroup, ToggleGroupItem
- `switch` — Switch
- `field` — Field (wrapper for form field layout)
- `form` — Form, FormField, FormItem, FormLabel, FormControl, FormDescription, FormMessage (react-hook-form integration)
- `phone-input` — PhoneInput
- `input-otp` — InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator
- `select` — Select, SelectContent, SelectItem, SelectItemText, SelectTrigger, SelectValue, SelectGroup, SelectLabel
- `multi-select` — MultiSelect, MultiSelectContent, MultiSelectItem, MultiSelectTrigger, MultiSelectValue
- `command` — Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut

**Dialogs & Modals:**
- `dialog` — Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger
- `alert-dialog` — AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger
- `drawer` — Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger
- `sheet` — Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger

**Dropdowns & Menus:**
- `dropdown-menu` — DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuPortal, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuSub, DropdownMenuSubContent, DropdownMenuSubTrigger, DropdownMenuTrigger
- `context-menu` — ContextMenu, ContextMenuCheckboxItem, ContextMenuContent, ContextMenuGroup, ContextMenuItem, ContextMenuLabel, ContextMenuPortal, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger, ContextMenuTrigger
- `menubar` — Menubar, MenubarContent, MenubarItem, MenubarLabel, MenubarMenu, MenubarRadioGroup, MenubarRadioItem, MenubarSeparator, MenubarShortcut, MenubarSub, MenubarSubContent, MenubarSubTrigger, MenubarTrigger
- `popover` — Popover, PopoverContent, PopoverTrigger
- `hover-card` — HoverCard, HoverCardContent, HoverCardTrigger
- `tooltip` — Tooltip, TooltipContent, TooltipProvider, TooltipTrigger

**Data Display:**
- `table` — Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow
- `calendar` — Calendar
- `progress` — Progress
- `slider` — Slider
- `scroll-area` — ScrollArea, ScrollBar
- `skeleton` — Skeleton

**Specialized:**
- `accordion` — Accordion, AccordionContent, AccordionItem, AccordionTrigger
- `tabs` — Tabs, TabsContent, TabsList, TabsTrigger
- `collapsible` — Collapsible, CollapsibleContent, CollapsibleTrigger
- `avatar` — Avatar, AvatarFallback, AvatarImage
- `alert` — Alert, AlertDescription, AlertTitle
- `chart` — Chart (charting utilities)
- `sonner` — Toaster (toast provider from Sonner)
- `sidebar` — Sidebar components
- `tree` — Tree (hierarchical navigation)
- `pagination` — Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious
- `resizable` — Resizable, ResizableHandle, ResizablePanel

### Blocks (2)

- `blocks/interactive-card` — InteractiveCard
- `blocks/selectable-chips` — SelectableChips

### Hooks (1)

- `hooks/useOutsideClick` — useOutsideClick

### Utils (1)

- `utils/types` — exports only `Option` type

---

## Common Patterns

### Pattern 1: Form with Validation (react-hook-form + Zod)

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@clasing/ui/form'
import { Input } from '@clasing/ui/input'
import { Button } from '@clasing/ui/button'

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
})

export function LoginForm() {
  const form = useForm({ resolver: zodResolver(schema) })

  const onSubmit = (data) => {
    console.log(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="user@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

### Pattern 2: Dialog with Form

```typescript
'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@clasing/ui/dialog'
import { Button } from '@clasing/ui/button'
import { Input } from '@clasing/ui/input'

export function CreateUserDialog() {
  const [open, setOpen] = useState(false)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create User</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New User</DialogTitle>
        </DialogHeader>
        <form onSubmit={(e) => {
          e.preventDefault()
          setOpen(false)
        }}>
          <Input placeholder="Name" className="mb-4" />
          <Button type="submit" className="w-full">Create</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

### Pattern 3: Data Table with Actions

```typescript
'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@clasing/ui/table'
import { Button } from '@clasing/ui/button'
import { Badge } from '@clasing/ui/badge'

interface User {
  id: string
  name: string
  email: string
  status: 'active' | 'inactive'
}

export function UserTable({ users }: { users: User[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id}>
            <TableCell className="font-medium">{user.name}</TableCell>
            <TableCell>{user.email}</TableCell>
            <TableCell>
              <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                {user.status}
              </Badge>
            </TableCell>
            <TableCell>
              <Button size="sm">Edit</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

---

## Anti-Patterns Quick Reference

| Mistake | Wrong ✗ | Correct ✓ |
|---------|---------|-----------|
| **Imports** | `import { Button } from '@clasing/ui'` | `import { Button } from '@clasing/ui/button'` |
| **cn() utility** | `import { cn } from '@clasing/ui/utils'` | `import { cn } from '@/lib/utils'` |
| **Colors** | `className="bg-neutral-900 text-gray-400"` | `className="bg-background text-foreground"` |
| **Typography** | `className="text-lg font-bold"` | `className="title-lg"` or `className="paragraph-md"` |
| **Font weights** | `className="font-bold"` or `className="font-normal"` | `className="font-semibold"` or `className="font-regular"` |
| **Icons** | `import { User } from 'lucide-react'` | `import { User } from '@phosphor-icons/react'` |
| **Dark mode** | `className="bg-white dark:bg-gray-900"` | `className="bg-background text-foreground"` |
| **Interactive in Server** | `export default function Dialog() { return <Dialog /> }` | `'use client'` at top of file |

---

## Summary

- **Per-component imports only** — no barrel exports
- **Semantic tokens for colors** — they handle dark mode
- **Composite typography classes** — never raw text-*
- **@phosphor-icons/react for icons** — only option
- **use client where Radix components need interactivity** — static components don't
- **Font weights: regular/medium/semibold only** — no bold/light
- **cn() from consumer's @/lib/utils** — not from @clasing/ui
- **All 56 entry points available** — check the list above

---

## References

- [@clasing/ui NPM](https://npmjs.com/package/@clasing/ui)
- [Radix UI Documentation](https://www.radix-ui.com/)
- [Tailwind CSS v4](https://tailwindcss.com/)
- [@phosphor-icons/react](https://phosphoricons.com/)
- [CVA (Class Variance Authority)](https://cva.style/)

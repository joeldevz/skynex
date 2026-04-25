---
description: @clasing/ui Form component usage with react-hook-form and Zod validation
globs: ["**/*form*", "**/*Form*", "**/*login*", "**/*register*", "**/*signup*"]
alwaysApply: false
---

# Form Pattern: react-hook-form + Zod + @clasing/ui/form

## Setup (Required)

```bash
pnpm add react-hook-form @hookform/resolvers zod
pnpm add @clasing/ui  # already installed
```

---

## ✅ Correct: Complete Login Form Example

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@clasing/ui/form'
import { Input } from '@clasing/ui/input'
import { Button } from '@clasing/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@clasing/ui/card'

// 1. Define schema
const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be 6+ characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>

// 2. Create form component
export function LoginForm() {
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  // 3. Handle submit
  async function onSubmit(values: LoginFormValues) {
    console.log('Submitting:', values)
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify(values),
      })
      if (response.ok) {
        console.log('Login successful')
      }
    } catch (error) {
      console.error('Login failed:', error)
    }
  }

  // 4. Render form
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Login</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Email field */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="user@example.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Password field */}
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Submit button */}
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? 'Logging in...' : 'Login'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
```

---

## ✅ Correct: Registration Form with Multiple Field Types

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from '@clasing/ui/form'
import { Input } from '@clasing/ui/input'
import { Textarea } from '@clasing/ui/textarea'
import { Checkbox } from '@clasing/ui/checkbox'
import { RadioGroup, RadioGroupItem } from '@clasing/ui/radio-group'
import { Button } from '@clasing/ui/button'

const registerSchema = z.object({
  name: z.string().min(2, 'Name must be 2+ characters'),
  email: z.string().email('Invalid email'),
  bio: z.string().optional(),
  role: z.enum(['user', 'admin']),
  newsletter: z.boolean().default(false),
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterForm() {
  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: '',
      email: '',
      bio: '',
      role: 'user',
      newsletter: false,
    },
  })

  async function onSubmit(values: RegisterFormValues) {
    console.log(values)
    // Call API...
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Text input */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full Name</FormLabel>
              <FormControl>
                <Input placeholder="John Doe" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Email input */}
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="user@example.com" {...field} />
              </FormControl>
              <FormDescription>We'll never share your email.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Textarea */}
        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bio (Optional)</FormLabel>
              <FormControl>
                <Textarea placeholder="Tell us about yourself..." {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Radio group */}
        <FormField
          control={form.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <FormControl>
                <RadioGroup value={field.value} onValueChange={field.onChange}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="user" id="role-user" />
                    <label htmlFor="role-user">User</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="admin" id="role-admin" />
                    <label htmlFor="role-admin">Admin</label>
                  </div>
                </RadioGroup>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Checkbox */}
        <FormField
          control={form.control}
          name="newsletter"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center space-x-2">
              <FormControl>
                <Checkbox checked={field.value} onCheckedChange={field.onChange} />
              </FormControl>
              <FormLabel className="font-normal cursor-pointer">
                Subscribe to our newsletter
              </FormLabel>
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full">
          Create Account
        </Button>
      </form>
    </Form>
  )
}
```

---

## ✅ Correct: Select Field Pattern

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@clasing/ui/form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@clasing/ui/select'
import { Button } from '@clasing/ui/button'

const selectSchema = z.object({
  country: z.string().min(1, 'Country required'),
})

export function CountryForm() {
  const form = useForm({
    resolver: zodResolver(selectSchema),
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(console.log)}>
        <FormField
          control={form.control}
          name="country"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Country</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="us">United States</SelectItem>
                  <SelectItem value="uk">United Kingdom</SelectItem>
                  <SelectItem value="ca">Canada</SelectItem>
                </SelectContent>
              </Select>
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

---

## ❌ WRONG: Missing FormField, Direct Input

```typescript
// ✗ This bypasses form validation and error handling
export function BadForm() {
  const [email, setEmail] = useState('')

  return (
    <form>
      <Input
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      {/* No validation, no FormMessage */}
      <Button type="submit">Submit</Button>
    </form>
  )
}
```

---

## ❌ WRONG: Missing `'use client'` Directive

```typescript
// ✗ useForm() is a React hook — can't run on server
import { useForm } from 'react-hook-form'

export function MyForm() {
  const form = useForm() // Error: Hooks can't run on server
  return <form />
}
```

---

## Field Validation Rules (Zod Pattern)

### ✅ Correct: Common Validation Patterns

```typescript
const schema = z.object({
  // Text fields
  name: z.string().min(1, 'Required').max(100, 'Too long'),
  email: z.string().email('Invalid email'),
  username: z.string().regex(/^[a-z0-9_]+$/, 'Invalid characters'),

  // Numbers
  age: z.number().min(18).max(120),
  count: z.number().int('Must be integer'),

  // Passwords
  password: z.string().min(8, 'Min 8 characters').regex(/[A-Z]/, 'Need uppercase').regex(/[0-9]/, 'Need number'),
  confirmPassword: z.string(),

  // Selects
  country: z.enum(['us', 'uk', 'ca']),
  role: z.string().min(1, 'Role required'),

  // Checkboxes
  terms: z.boolean().refine((v) => v === true, 'Must accept terms'),

  // Optional fields
  bio: z.string().optional(),
  phone: z.string().optional().or(z.literal('')),
})
```

---

## Common Form Mistakes

| Issue | ✗ Wrong | ✓ Correct |
|-------|---------|-----------|
| Missing client directive | No `'use client'` | `'use client'` at top |
| Missing FormField wrapper | Direct `<Input />` | `<FormField><FormControl><Input /></FormControl></FormField>` |
| cn() source | `from '@clasing/ui/utils'` | `from '@/lib/utils'` |
| Input import | `from '@clasing/ui'` | `from '@clasing/ui/input'` |
| No error display | Omit FormMessage | Always include `<FormMessage />` |
| Manual validation | Custom state + validation | Use react-hook-form + zod |

---

## Summary

1. **Always use FormField + FormControl + FormMessage** — validates, displays errors
2. **Add `'use client'` to form components** — hooks need client-side runtime
3. **Define schema with Zod** — single source of truth for validation
4. **Spread field props** — `{...field}` connects input to form state
5. **Import from per-component entries** — `@clasing/ui/input`, `@clasing/ui/form`, etc.

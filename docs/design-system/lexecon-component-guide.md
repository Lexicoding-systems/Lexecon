# Lexecon Component Specification Guide

**Version:** 1.0.0
**Last Updated:** 2026-01-10
**For Developers:** Complete implementation specifications

---

## Table of Contents

1. [Button Component](#button-component)
2. [Input Component](#input-component)
3. [Card Component](#card-component)
4. [Badge Component](#badge-component)
5. [Alert Component](#alert-component)
6. [Modal Component](#modal-component)
7. [Table Component](#table-component)
8. [Select Component](#select-component)
9. [Checkbox Component](#checkbox-component)
10. [Tabs Component](#tabs-component)

---

## Button Component

### Purpose
Primary interactive element for triggering actions, submitting forms, and navigation.

### API Reference

```typescript
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
}
```

### Variants

#### Primary
**Purpose**: Main CTAs, high-emphasis actions
**Visual**:
- Background: `#6366F1` (brand.primary.500)
- Text: `#FFFFFF` (white)
- Hover: `#4F46E5` (brand.primary.600)
- Active: `#4338CA` (brand.primary.700)
- Focus: 2px ring `#6366F1` with 2px offset
- Disabled: 50% opacity

**When to use**:
- Primary page action (e.g., "Save", "Submit", "Approve")
- One primary button per screen section
- Action moves user forward in workflow

#### Secondary
**Purpose**: Supporting actions, medium emphasis
**Visual**:
- Background: `#F5F5F5` (neutral.100)
- Text: `#404040` (neutral.700)
- Border: 1px `#D4D4D4` (neutral.300)
- Hover: `#E5E5E5` (neutral.200)
- Active: `#D4D4D4` (neutral.300)

**When to use**:
- Secondary actions alongside primary
- "Cancel" buttons
- Less important actions

#### Danger
**Purpose**: Destructive actions requiring caution
**Visual**:
- Background: `#EF4444` (semantic.error.500)
- Text: `#FFFFFF` (white)
- Hover: `#DC2626` (semantic.error.600)
- Active: `#B91C1C` (semantic.error.700)

**When to use**:
- Delete operations
- Irreversible actions
- Denying decisions

#### Success
**Purpose**: Positive confirmations
**Visual**:
- Background: `#22C55E` (semantic.success.500)
- Text: `#FFFFFF` (white)
- Hover: `#16A34A` (semantic.success.600)

**When to use**:
- Approval actions
- Confirmations
- Positive outcomes

#### Ghost
**Purpose**: Tertiary actions, minimal visual weight
**Visual**:
- Background: `transparent`
- Text: `#4F46E5` (brand.primary.600)
- Hover: `#EEF2FF` (brand.primary.50)
- Active: `#E0E7FF` (brand.primary.100)

**When to use**:
- Inline actions
- Less important navigation
- Dense interfaces where visual weight matters

### Sizes

| Size | Height | H-Padding | V-Padding | Font Size | Min Touch |
|------|--------|-----------|-----------|-----------|-----------|
| sm | 32px | 12px | 6px | 14px (sm) | 44x44px* |
| md | 40px | 16px | 8px | 16px (base) | 44x44px |
| lg | 48px | 24px | 12px | 18px (lg) | 48x48px |

*Small buttons should have adequate spacing around them to meet touch target requirements.

### States

#### Default
- Base styling as per variant
- Cursor: pointer

#### Hover
- Background darkens 10%
- Smooth transition (200ms ease-out)
- Cursor: pointer

#### Active (Click/Press)
- Background darkens 15%
- Instant feedback (no transition delay)

#### Focus (Keyboard Navigation)
- 2px ring in variant color
- 2px offset from button edge
- Maintains hover state if mouse over
- Outline: none (replaced by ring)

#### Disabled
- Opacity: 50%
- Cursor: not-allowed
- No hover effects
- No click events

#### Loading
- Shows spinner icon (left side)
- Text changes to "Loading..." or remains
- Disabled click events
- Maintains visual feedback (not grayed out)
- Minimum display time: 300ms (prevent flash)

### Layout & Spacing

**Horizontal Spacing**:
- Between buttons: 12px (spacing.3)
- Button groups: wrap-reverse on mobile

**Vertical Spacing**:
- Below form fields: 16px (spacing.4)
- In button groups: 8px (spacing.2)

### Accessibility

**Keyboard Navigation**:
- Tab: Focus button
- Enter/Space: Trigger onClick
- Disabled buttons: Skip in tab order

**Screen Reader**:
- `aria-busy="true"` when loading
- `aria-disabled="true"` when disabled
- Button text should be descriptive ("Approve Decision", not "Click Here")

**ARIA Labels**:
```jsx
<Button aria-label="Approve decision #123">
  Approve
</Button>
```

### Code Examples

**Basic Usage**:
```jsx
<Button variant="primary" onClick={handleSubmit}>
  Submit
</Button>
```

**With Icon**:
```jsx
<Button
  variant="secondary"
  icon={<CheckIcon />}
  iconPosition="left"
>
  Approve
</Button>
```

**Loading State**:
```jsx
<Button variant="primary" loading={isSubmitting}>
  {isSubmitting ? 'Saving...' : 'Save Changes'}
</Button>
```

**Full Width**:
```jsx
<Button variant="primary" fullWidth>
  Continue
</Button>
```

### Edge Cases

**Long Text**:
- Buttons should wrap text if needed
- Prefer shorter, action-oriented labels
- Max width: 400px before wrapping

**Icon Only**:
- Use icon only for universally understood actions
- Must have aria-label
- Minimum 44x44px touch target

**Multiple Buttons**:
- Primary action on right (Western reading)
- Cancel/Secondary on left
- Danger actions require confirmation

---

## Input Component

### Purpose
Single-line text input for user data entry with validation support.

### API Reference

```typescript
interface InputProps {
  label?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url';
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
}
```

### Visual Specifications

**Dimensions**:
- Height: 44px (meets touch target)
- Horizontal padding: 16px (spacing.4)
- Vertical padding: 10px
- Border radius: 8px (border.radius.lg)

**Typography**:
- Font size: 16px (prevents zoom on iOS)
- Font weight: 400 (normal)
- Line height: 24px (1.5)

**Colors**:
- Background: `#FFFFFF` (white)
- Border (default): `#D4D4D4` (neutral.300)
- Border (focus): `#6366F1` (brand.primary.500)
- Border (error): `#EF4444` (semantic.error.500)
- Text: `#171717` (neutral.900)
- Placeholder: `#A3A3A3` (neutral.400)
- Disabled background: `#F5F5F5` (neutral.100)

### States

#### Default
- 1px border, neutral.300
- Background white
- Placeholder text in neutral.400

#### Hover
- Border color: neutral.400
- Cursor: text

#### Focus
- Border: 2px brand.primary.500
- Ring: 2px brand.primary.100
- Ring offset: 1px
- Outline: none

#### Error
- Border: 2px semantic.error.500
- Ring: 2px semantic.error.100
- Error message below (12px spacing)
- Error icon inline (optional)

#### Disabled
- Background: neutral.100
- Cursor: not-allowed
- Border: neutral.300
- Text: neutral.500

#### Filled (with value)
- Same as default
- Text in neutral.900

### Label & Helper Text

**Label**:
- Position: Above input (8px spacing)
- Font size: 14px (sm)
- Font weight: 500 (medium)
- Color: neutral.700
- Required indicator: Red asterisk (*) if required

**Helper Text**:
- Position: Below input (8px spacing)
- Font size: 14px (sm)
- Color: neutral.500
- Purpose: Provide guidance or context

**Error Message**:
- Replaces helper text when present
- Font size: 14px (sm)
- Color: semantic.error.600
- Icon: Optional error icon inline
- `role="alert"` for screen readers

### Validation

**Client-Side Validation**:
```jsx
const [email, setEmail] = useState('');
const [error, setError] = useState('');

const validateEmail = (value) => {
  if (!value) {
    setError('Email is required');
  } else if (!/\S+@\S+\.\S+/.test(value)) {
    setError('Please enter a valid email');
  } else {
    setError('');
  }
};

<Input
  label="Email"
  type="email"
  value={email}
  onChange={(e) => {
    setEmail(e.target.value);
    validateEmail(e.target.value);
  }}
  error={error}
  required
/>
```

### Accessibility

**Keyboard Navigation**:
- Tab: Focus input
- Type: Enter text
- ESC: Clear focus (browser default)

**ARIA Attributes**:
- `aria-label` or associated `<label>` (required)
- `aria-invalid="true"` when error present
- `aria-describedby` linking to helper/error text
- `aria-required="true"` if required

**Screen Reader**:
- Label announced on focus
- Error message announced when added
- Helper text announced on focus

### Code Examples

**Basic**:
```jsx
<Input
  label="Policy Name"
  value={policyName}
  onChange={(e) => setPolicyName(e.target.value)}
  placeholder="Enter policy name"
/>
```

**With Validation**:
```jsx
<Input
  label="Email Address"
  type="email"
  value={email}
  onChange={handleEmailChange}
  error={emailError}
  helperText="We'll never share your email"
  required
/>
```

**Disabled**:
```jsx
<Input
  label="User ID"
  value={userId}
  disabled
  helperText="This field cannot be edited"
/>
```

### Edge Cases

**Long Input Values**:
- Input scrolls horizontally
- Text ellipsis not used (user needs to see full value)

**Autofill**:
- Browser autofill styles respected
- Autocomplete attributes supported

**IME Input** (Asian languages):
- Composition events handled properly
- onChange fires after composition completes

---

## Card Component

### Purpose
Container for grouping related content with optional header and footer sections.

### API Reference

```typescript
interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: 'none' | 'compact' | 'default' | 'spacious';
}
```

### Variants

#### Default
- Background: white
- Border: 1px solid neutral.200
- Shadow: none
- Use: Standard content containers

#### Elevated
- Background: white
- Border: none
- Shadow: shadow.lg
- Use: Prominent cards, floating panels

#### Outlined
- Background: white
- Border: 2px solid brand.primary.200
- Shadow: none
- Use: Emphasis, selected state

### Padding Options

| Option | Padding | Usage |
|--------|---------|-------|
| none | 0px | Custom padding needed |
| compact | 16px | Dense interfaces, lists |
| default | 24px | Standard cards |
| spacious | 32px | Feature highlights, hero |

### Layout Specifications

**Card Structure**:
```
┌─────────────────────────────────┐
│ Header (if title/subtitle)      │
│   Title (text-xl, semibold)     │
│   Subtitle (text-sm, neutral.500)│
├─────────────────────────────────┤ ← 16px margin
│                                 │
│ Body Content                    │
│                                 │
├─────────────────────────────────┤ ← 1px border-t
│ Footer (if provided)            │ ← 16px padding-top
└─────────────────────────────────┘
```

**Spacing**:
- Border radius: 12px (border.radius.xl)
- Title to subtitle: 4px (spacing.1)
- Header to body: 16px (spacing.4)
- Body to footer: 16px (spacing.4)
- Footer top border: neutral.200

### Accessibility

**Semantic HTML**:
- Use `<article>` for standalone content
- Use `<section>` for related content groups
- Title should be `<h3>` or appropriate heading level

**ARIA**:
- `aria-labelledby` linking to title (if present)
- `role="region"` for landmark cards

### Code Examples

**Basic Card**:
```jsx
<Card title="Recent Decisions" subtitle="Last 24 hours">
  <DecisionsList />
</Card>
```

**With Footer**:
```jsx
<Card
  title="Policy Status"
  footer={
    <div className="flex justify-between">
      <Button variant="ghost">Details</Button>
      <Button variant="primary">Edit Policy</Button>
    </div>
  }
>
  <PolicySummary />
</Card>
```

**Elevated Variant**:
```jsx
<Card variant="elevated" padding="spacious">
  <FeatureHighlight />
</Card>
```

### Edge Cases

**Empty State**:
- Display empty state message in body
- Optional CTA to populate

**Long Titles**:
- Truncate after 2 lines with ellipsis
- Tooltip on hover shows full text

**Overflow Content**:
- Body scrolls if needed
- Max-height can be set externally

---

## Badge Component

### Purpose
Small status indicators for labels, counts, and state communication.

### API Reference

```typescript
interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}
```

### Visual Specifications

**Dimensions**:

| Size | Padding H | Padding V | Font Size | Height |
|------|-----------|-----------|-----------|--------|
| sm | 8px | 2px | 12px (xs) | ~16px |
| md | 10px | 4px | 14px (sm) | ~22px |
| lg | 12px | 6px | 16px (base) | ~28px |

**Border Radius**: 9999px (fully rounded)

**Colors by Variant**:

| Variant | Background | Text | Dot Color |
|---------|------------|------|-----------|
| default | neutral.100 | neutral.700 | neutral.700 |
| primary | brand.primary.100 | brand.primary.700 | brand.primary.500 |
| success | semantic.success.100 | semantic.success.700 | semantic.success.500 |
| warning | semantic.warning.100 | semantic.warning.700 | semantic.warning.500 |
| error | semantic.error.100 | semantic.error.700 | semantic.error.500 |
| info | semantic.info.100 | semantic.info.700 | semantic.info.500 |

### Dot Indicator

**Specifications**:
- Size: 6px diameter
- Position: 6px left of text
- Color: Current color (inherits from variant)
- Border radius: 50%

**When to use**:
- Live/active status
- Notification indicator
- Real-time state

### Accessibility

**Text**:
- Text must be readable (min 4.5:1 contrast)
- Font size should not go below 12px

**Screen Reader**:
- Badge content announced
- Consider aria-label for icon-only badges

### Code Examples

**Basic Badge**:
```jsx
<Badge variant="success">Active</Badge>
```

**With Dot**:
```jsx
<Badge variant="warning" dot>Pending</Badge>
```

**Status Badges**:
```jsx
const StatusBadge = ({ status }) => {
  const variants = {
    approved: 'success',
    denied: 'error',
    pending: 'warning',
    escalated: 'error'
  };

  return (
    <Badge variant={variants[status]}>
      {status.toUpperCase()}
    </Badge>
  );
};
```

### Edge Cases

**Long Text**:
- Should wrap if needed
- Prefer short labels (1-2 words)
- Max width: 200px before wrapping

**Count Badges**:
```jsx
<Badge variant="primary">{notificationCount}</Badge>
```

**Inline vs Block**:
- Inline: Use with text (aligned middle)
- Block: Use in lists or cards

---

## Alert Component

### Purpose
Contextual feedback messages for user actions and system states.

### API Reference

```typescript
interface AlertProps {
  children: React.ReactNode;
  title?: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
  dismissible?: boolean;
  onDismiss?: () => void;
  icon?: boolean;
}
```

### Variants

**Color Specifications**:

| Variant | Background | Border | Text | Icon |
|---------|------------|--------|------|------|
| info | info.50 | info.200 | info.800 | ℹ (info circle) |
| success | success.50 | success.200 | success.800 | ✓ (checkmark) |
| warning | warning.50 | warning.200 | warning.800 | ⚠ (warning triangle) |
| error | error.50 | error.200 | error.800 | ✕ (error X) |

### Layout Specifications

**Structure**:
```
┌──────────────────────────────────────────┐
│ [Icon] Title                         [X] │
│        Message content goes here         │
└──────────────────────────────────────────┘
```

**Spacing**:
- Padding: 16px (spacing.4)
- Icon to text: 12px (spacing.3)
- Title to message: 4px (spacing.1)
- Border radius: 8px (border.radius.lg)
- Border width: 1px

**Icon**:
- Size: 24px
- Position: Top-aligned with title
- Flex-shrink: 0 (doesn't shrink)

**Dismiss Button**:
- Size: 24x24px
- Position: Top-right corner
- Icon: ✕ (X)
- Hover: Opacity 70%

### Accessibility

**ARIA**:
- `role="alert"` for error/warning
- `role="status"` for info/success
- Live region for dynamic alerts

**Keyboard**:
- Dismiss button focusable via Tab
- Enter/Space: Dismiss alert

**Screen Reader**:
- Title and message announced
- Dismissible state announced

### Code Examples

**Basic Alert**:
```jsx
<Alert variant="info">
  Your changes have been saved.
</Alert>
```

**With Title**:
```jsx
<Alert variant="warning" title="Action Required">
  This decision requires human oversight before proceeding.
</Alert>
```

**Dismissible**:
```jsx
<Alert
  variant="success"
  dismissible
  onDismiss={() => setShowAlert(false)}
>
  Policy updated successfully.
</Alert>
```

**Without Icon**:
```jsx
<Alert variant="info" icon={false}>
  Informational message without icon.
</Alert>
```

### Usage Guidelines

**When to Use Each Variant**:

- **Info**: Neutral information, tips, guidance
- **Success**: Confirmations, completions, approvals
- **Warning**: Cautions, reversible issues, escalations
- **Error**: Failures, denials, critical problems

**Placement**:
- Top of content area: System-wide messages
- Inline with form: Field-specific errors
- Toast/notification: Temporary feedback

**Duration**:
- Info/Success: Auto-dismiss after 5 seconds (optional)
- Warning/Error: Manual dismiss only

### Edge Cases

**Long Messages**:
- Text wraps naturally
- No max-height (show full message)

**Multiple Alerts**:
- Stack vertically with 12px spacing
- Show most severe first (error > warning > info)

---

## Modal Component

### Purpose
Overlay dialog for focused interactions requiring user attention.

### API Reference

```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}
```

### Size Specifications

| Size | Max Width | Usage |
|------|-----------|-------|
| sm | 448px (28rem) | Confirmations, simple forms |
| md | 512px (32rem) | Default, most use cases |
| lg | 768px (48rem) | Complex forms, detailed content |
| xl | 1024px (64rem) | Rich content, multi-column |
| full | calc(100vw - 32px) | Maximum content (rare) |

### Layout Structure

```
┌─────────────────────────────────┐
│ Header                      [X] │ ← 24px padding
├─────────────────────────────────┤ ← 1px border
│                                 │
│ Body Content                    │ ← 24px padding
│                                 │
│                                 │
├─────────────────────────────────┤ ← 1px border
│ Footer (optional)               │ ← 24px padding, neutral.50 bg
│                      [Cancel][OK]│
└─────────────────────────────────┘
```

**Spacing**:
- Header padding: 24px (spacing.6)
- Body padding: 24px (spacing.6)
- Footer padding: 24px (spacing.6)
- Border radius: 12px (border.radius.xl)

### Backdrop

**Visual**:
- Background: rgba(0, 0, 0, 0.5)
- Blur: 4px (optional)
- z-index: 1040
- Click: Closes modal (optional behavior)

### Animation

**Open Animation**:
- Duration: 200ms
- Easing: ease-out
- Transform: scale(0.95) → scale(1)
- Opacity: 0 → 1

**Close Animation**:
- Duration: 150ms
- Easing: ease-in
- Transform: scale(1) → scale(0.95)
- Opacity: 1 → 0

### Behavior

**Opening**:
1. Backdrop fades in
2. Modal animates in
3. Focus moves to first focusable element
4. Scroll locked on body

**Closing**:
1. Modal animates out
2. Backdrop fades out
3. Focus returns to trigger element
4. Scroll restored on body

**ESC Key**:
- Closes modal
- Can be disabled for critical confirmations

**Click Outside**:
- Closes modal (default)
- Can be disabled for required interactions

### Accessibility

**Focus Management**:
- Focus trapped within modal
- Tab cycles through focusable elements
- Shift+Tab: Reverse cycle
- Focus returns to trigger on close

**ARIA**:
- `role="dialog"`
- `aria-modal="true"`
- `aria-labelledby` (title ID)
- `aria-describedby` (content ID, optional)

**Keyboard**:
- ESC: Close modal
- Tab: Navigate forward
- Shift+Tab: Navigate backward

### Code Examples

**Basic Modal**:
```jsx
const [isOpen, setIsOpen] = useState(false);

<Button onClick={() => setIsOpen(true)}>Open Modal</Button>

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Action"
>
  <p>Are you sure you want to proceed?</p>
</Modal>
```

**With Footer Actions**:
```jsx
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Delete Policy"
  footer={
    <>
      <Button variant="secondary" onClick={handleClose}>
        Cancel
      </Button>
      <Button variant="danger" onClick={handleDelete}>
        Delete
      </Button>
    </>
  }
>
  <p>This action cannot be undone. Are you sure?</p>
</Modal>
```

**Large Size**:
```jsx
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Policy Details"
  size="lg"
>
  <PolicyDetailView />
</Modal>
```

### Edge Cases

**Nested Modals**:
- Avoid if possible
- If needed: Increase z-index, manage focus carefully

**Long Content**:
- Body scrolls independently
- Header/footer remain fixed
- Scroll shadows indicate more content

**Mobile**:
- Full-screen on small devices
- Bottom sheet alternative (optional)

---

## Table Component

### Purpose
Display structured data in rows and columns with sorting and selection.

### API Reference

```typescript
interface Column {
  header: string;
  key: string;
  render?: (value: any, row: any) => React.ReactNode;
}

interface TableProps {
  columns: Column[];
  data: any[];
  selectable?: boolean;
  onRowClick?: (row: any) => void;
}
```

### Visual Specifications

**Table Structure**:
```
┌────────────────────────────────────────┐
│ Column 1    │ Column 2    │ Column 3   │ ← Header (neutral.50 bg)
├─────────────┼─────────────┼────────────┤
│ Value 1     │ Value 2     │ Value 3    │
├─────────────┼─────────────┼────────────┤ ← Divider (neutral.200)
│ Value 1     │ Value 2     │ Value 3    │
└─────────────┴─────────────┴────────────┘
```

**Spacing**:
- Cell padding: 16px horizontal, 12px vertical
- Header padding: 16px horizontal, 12px vertical
- Row height: Auto (min 48px for touch target)

**Typography**:
- Header: 14px (sm), semibold (600), neutral.700
- Cell: 14px (sm), normal (400), neutral.600

**Colors**:
- Header background: neutral.50
- Header border: 2px neutral.200 (bottom)
- Row divider: 1px neutral.200
- Row hover: neutral.50 (if clickable)

### States

#### Default Row
- Background: white
- Text: neutral.600

#### Hover Row (if clickable)
- Background: neutral.50
- Cursor: pointer
- Smooth transition (150ms)

#### Selected Row
- Background: brand.primary.50
- Border-left: 4px brand.primary.500

#### Empty State
- Center-aligned message
- Optional illustration
- CTA to add data

### Selection

**Checkbox Column**:
- Width: 48px
- Header: Select all checkbox
- Rows: Individual checkboxes
- Selection state persists

### Responsive Behavior

**Desktop (1024px+)**:
- Standard table layout
- All columns visible
- Horizontal scroll if needed

**Tablet (768-1023px)**:
- Reduce padding
- Hide less important columns
- Horizontal scroll

**Mobile (<768px)**:
- Card-based layout (not table)
- Stack data vertically
- Show key columns only

### Accessibility

**Semantic HTML**:
- Use `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- `<th scope="col">` for column headers

**ARIA**:
- `aria-label` or `<caption>` for table purpose
- `aria-sort` for sortable columns
- Row selection announced

**Keyboard**:
- Tab: Navigate cells
- Space: Toggle checkbox
- Enter: Trigger row click

### Code Examples

**Basic Table**:
```jsx
<Table
  columns={[
    { header: 'ID', key: 'id' },
    { header: 'Name', key: 'name' },
    { header: 'Status', key: 'status' }
  ]}
  data={decisions}
/>
```

**With Custom Rendering**:
```jsx
<Table
  columns={[
    { header: 'Decision ID', key: 'id' },
    {
      header: 'Risk Level',
      key: 'risk',
      render: (value) => <Badge variant={getRiskVariant(value)}>{value}</Badge>
    },
    {
      header: 'Date',
      key: 'createdAt',
      render: (value) => new Date(value).toLocaleDateString()
    }
  ]}
  data={decisions}
/>
```

**With Selection**:
```jsx
<Table
  columns={columns}
  data={data}
  selectable
  onRowClick={(row) => viewDetails(row.id)}
/>
```

### Edge Cases

**Empty Data**:
```jsx
{data.length === 0 && (
  <div className="text-center py-12">
    <p className="text-neutral-500">No decisions found</p>
    <Button variant="primary">Create Decision</Button>
  </div>
)}
```

**Long Cell Values**:
- Truncate with ellipsis
- Tooltip on hover shows full value
- Max-width: 300px

**Many Columns**:
- Horizontal scroll
- Sticky first column (optional)
- Responsive: Hide less important columns

---

## Select Component

### Purpose
Dropdown selection from a list of options.

### API Reference

```typescript
interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label?: string;
  options: SelectOption[];
  value: string;
  onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
}
```

### Visual Specifications

**Same as Input Component** with additions:
- Dropdown icon: Chevron down (right-aligned, 16px)
- Dropdown icon color: neutral.400
- Dropdown icon rotates 180° when open

**Dimensions**:
- Height: 44px
- Padding: 16px horizontal
- Icon spacing: 12px from right edge

### States

Same as Input component plus:

#### Open (Dropdown Visible)
- Border: brand.primary.500
- Ring: brand.primary.100
- Chevron rotates 180°

### Dropdown Menu

**Visual**:
- Background: white
- Border: 1px neutral.200
- Shadow: shadow.lg
- Border radius: 8px
- Max height: 300px (scrolls if more)
- z-index: 1060

**Options**:
- Padding: 12px horizontal, 8px vertical
- Font size: 16px
- Hover: background neutral.50
- Selected: background brand.primary.50, checkmark icon

### Accessibility

Same as Input component plus:

**Keyboard**:
- Arrow Up/Down: Navigate options
- Enter/Space: Select option
- ESC: Close dropdown
- Type: Jump to option starting with letter

**ARIA**:
- `role="combobox"`
- `aria-expanded` when open
- `aria-activedescendant` for highlighted option

### Code Examples

**Basic Select**:
```jsx
<Select
  label="Risk Level"
  options={[
    { value: 'low', label: 'Low Risk' },
    { value: 'medium', label: 'Medium Risk' },
    { value: 'high', label: 'High Risk' }
  ]}
  value={riskLevel}
  onChange={(e) => setRiskLevel(e.target.value)}
/>
```

**With Validation**:
```jsx
<Select
  label="Policy Type"
  options={policyTypes}
  value={selectedType}
  onChange={handleChange}
  error={validationError}
  required
/>
```

### Edge Cases

**Long Option Labels**:
- Truncate with ellipsis in dropdown
- Full text on hover via tooltip

**Many Options**:
- Virtual scrolling for 100+ options
- Search/filter functionality (custom implementation)

**Grouped Options**:
- Use `<optgroup>` for native HTML
- Custom component for styled groups

---

## Checkbox Component

### Purpose
Binary selection for forms and lists.

### API Reference

```typescript
interface CheckboxProps {
  label?: string;
  checked: boolean;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  id?: string;
}
```

### Visual Specifications

**Dimensions**:
- Size: 16x16px
- Border radius: 4px
- Border width: 1px
- Touch target: 44x44px (padding added)

**Colors**:
- Border (unchecked): neutral.300
- Border (checked): brand.primary.500
- Background (checked): brand.primary.500
- Checkmark: white
- Focus ring: brand.primary.100

### States

#### Unchecked
- Background: white
- Border: 1px neutral.300

#### Checked
- Background: brand.primary.500
- Border: brand.primary.500
- Checkmark: white, 12px

#### Indeterminate (optional)
- Background: brand.primary.500
- Icon: Horizontal line (dash)

#### Hover
- Border: brand.primary.600

#### Focus
- Ring: 2px brand.primary.100
- Ring offset: 2px

#### Disabled
- Opacity: 50%
- Cursor: not-allowed

### Label

**Position**: Right of checkbox (8px spacing)
**Typography**: 14px (sm), neutral.700
**Clickable**: Clicking label toggles checkbox
**Alignment**: Center-aligned with checkbox

### Accessibility

**Keyboard**:
- Tab: Focus checkbox
- Space: Toggle checked state

**ARIA**:
- `aria-checked="true|false"`
- `aria-describedby` if helper text

**Screen Reader**:
- Label announced
- Checked state announced

### Code Examples

**Basic Checkbox**:
```jsx
<Checkbox
  label="I agree to the terms"
  checked={agreed}
  onChange={(e) => setAgreed(e.target.checked)}
/>
```

**Checkbox Group**:
```jsx
const [selectedItems, setSelectedItems] = useState([]);

<div>
  {items.map(item => (
    <Checkbox
      key={item.id}
      label={item.name}
      checked={selectedItems.includes(item.id)}
      onChange={(e) => {
        if (e.target.checked) {
          setSelectedItems([...selectedItems, item.id]);
        } else {
          setSelectedItems(selectedItems.filter(id => id !== item.id));
        }
      }}
    />
  ))}
</div>
```

### Edge Cases

**Long Labels**:
- Wrap to multiple lines
- Checkbox top-aligned

**Indeterminate State** (parent checkbox):
```jsx
<Checkbox
  label="Select All"
  checked={allChecked}
  indeterminate={someChecked}
  onChange={handleSelectAll}
/>
```

---

## Tabs Component

### Purpose
Navigate between different views or sections without changing routes.

### API Reference

```typescript
interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'line' | 'pills';
}
```

### Variants

#### Line Tabs
**Visual**:
- Container: Border-bottom 1px neutral.200
- Tab: No background, border-bottom 2px
- Active: Border-bottom brand.primary.500, text brand.primary.600
- Inactive: Border transparent, text neutral.500
- Hover: Border neutral.300, text neutral.700

**Usage**: Standard tabbed interfaces, content sections

#### Pill Tabs
**Visual**:
- Container: No border, flex gap 8px
- Tab: Rounded-lg, padding 8px 16px
- Active: Background brand.primary.500, text white
- Inactive: Text neutral.500
- Hover: Background neutral.100

**Usage**: Toggle between views, filter controls

### Visual Specifications

**Line Tabs**:
- Tab padding: 16px horizontal, 8px vertical
- Active border: 2px solid
- Font size: 14px (sm)
- Font weight: 500 (medium)

**Pill Tabs**:
- Tab padding: 8px 16px
- Border radius: 8px (lg)
- Gap between pills: 8px
- Font size: 14px (sm)

### Behavior

**Tab Click**:
- Instant switch (no transition)
- Content updates immediately
- Active tab indicator moves smoothly (200ms)

**Content**:
- Managed externally (Tab component doesn't manage content)
- Use conditional rendering based on activeTab

### Accessibility

**Keyboard**:
- Tab: Focus tabs (not move between tabs)
- Arrow Left/Right: Move between tabs
- Home/End: Jump to first/last tab
- Enter/Space: Activate focused tab

**ARIA**:
- `role="tablist"` on container
- `role="tab"` on each tab
- `aria-selected="true"` on active tab
- `aria-controls` linking to content panel
- Content panel: `role="tabpanel"`

### Code Examples

**Line Tabs**:
```jsx
const [activeTab, setActiveTab] = useState('overview');

<Tabs
  tabs={[
    { id: 'overview', label: 'Overview' },
    { id: 'details', label: 'Details' },
    { id: 'audit', label: 'Audit Trail' }
  ]}
  activeTab={activeTab}
  onChange={setActiveTab}
  variant="line"
/>

{activeTab === 'overview' && <OverviewView />}
{activeTab === 'details' && <DetailsView />}
{activeTab === 'audit' && <AuditView />}
```

**Pill Tabs**:
```jsx
<Tabs
  tabs={[
    { id: 'all', label: 'All' },
    { id: 'approved', label: 'Approved' },
    { id: 'denied', label: 'Denied' }
  ]}
  activeTab={filter}
  onChange={setFilter}
  variant="pills"
/>
```

### Edge Cases

**Many Tabs**:
- Horizontal scroll on overflow
- Scroll active tab into view

**Long Labels**:
- Truncate with ellipsis
- Tooltip shows full label

**Icon Tabs**:
```jsx
<Tabs
  tabs={[
    { id: 'list', label: <ListIcon />, ariaLabel: 'List View' },
    { id: 'grid', label: <GridIcon />, ariaLabel: 'Grid View' }
  ]}
  activeTab={viewMode}
  onChange={setViewMode}
/>
```

---

## Implementation Checklist

Before shipping components:

### Code Quality
- [ ] TypeScript types defined
- [ ] PropTypes validated (if not using TS)
- [ ] Default props set appropriately
- [ ] All states implemented
- [ ] Edge cases handled

### Accessibility
- [ ] Keyboard navigation works
- [ ] ARIA attributes added
- [ ] Screen reader tested
- [ ] Focus management implemented
- [ ] Color contrast validated

### Visual
- [ ] Design tokens used exclusively
- [ ] Responsive behavior defined
- [ ] All variants implemented
- [ ] Animations smooth
- [ ] Loading states designed

### Testing
- [ ] Unit tests written
- [ ] Interaction tests added
- [ ] Accessibility tests passing
- [ ] Visual regression tests
- [ ] Cross-browser tested

### Documentation
- [ ] Props documented
- [ ] Usage examples provided
- [ ] Edge cases noted
- [ ] A11y notes included
- [ ] Component spec updated

---

## Support

For questions or issues with these specifications:
- Review design system documentation
- Check design tokens file
- Reference component library code
- Consult with design team

---

**Last Updated**: 2026-01-10
**Version**: 1.0.0
**Maintained By**: Lexecon Design Team

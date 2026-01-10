# Lexecon Design System

**Version:** 1.0.0
**Last Updated:** 2026-01-10
**Platform:** Enterprise AI Governance

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Visual Language](#visual-language)
4. [Design Tokens](#design-tokens)
5. [Component Library](#component-library)
6. [Layout Patterns](#layout-patterns)
7. [Accessibility](#accessibility)
8. [Usage Guidelines](#usage-guidelines)
9. [Developer Handoff](#developer-handoff)

---

## Overview

### Purpose

The Lexecon Design System is a comprehensive design language and component library built specifically for enterprise AI governance platforms. It provides the foundation for creating consistent, accessible, and professional interfaces that communicate trust, security, and compliance.

### Goals

- **Consistency**: Unified visual language across all platform features
- **Accessibility**: WCAG AA compliant components for inclusive design
- **Efficiency**: Reusable components that accelerate development
- **Scalability**: Token-based system that adapts to future needs
- **Trust**: Professional aesthetic that communicates reliability and security

### System Architecture

```
Lexecon Design System
├── Design Tokens (Foundation)
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   ├── Shadows
│   └── Animation
├── Component Library (Building Blocks)
│   ├── Primitives (Button, Input, etc.)
│   ├── Compositions (Card, Modal, etc.)
│   └── Patterns (Tables, Forms, etc.)
└── Governance Patterns (Domain-Specific)
    ├── Audit Interfaces
    ├── Policy Builders
    └── Decision Workflows
```

---

## Design Principles

### 1. Trust Through Transparency

**Principle**: Every interface element should communicate clarity and honesty.

**Application**:
- Clear hierarchy with no hidden information
- Explicit state indicators (loading, error, success)
- Honest progress indicators (no fake loading)
- Transparent data visualization

### 2. Security-First Aesthetic

**Principle**: Visual design should reinforce security and compliance.

**Application**:
- Professional, subdued color palette
- Structured layouts with clear boundaries
- Cryptographic integrity indicators
- Audit trail visibility

### 3. Information Density with Clarity

**Principle**: Enterprise users need dense information without overwhelm.

**Application**:
- Progressive disclosure (show details on demand)
- Data tables with smart filtering/sorting
- Scannable typography hierarchy
- White space that guides attention

### 4. Accessibility as Standard

**Principle**: All users must have equal access to governance tools.

**Application**:
- WCAG AA minimum (AAA where possible)
- Keyboard navigation for all interactions
- Screen reader optimization
- Color-blind safe palettes

### 5. Consistent but Adaptive

**Principle**: Components behave predictably across contexts.

**Application**:
- Reusable components with consistent APIs
- Token-based theming for brand adaptation
- Responsive layouts that adapt gracefully
- Context-appropriate component variants

---

## Visual Language

### Color Strategy

#### Brand Colors

**Primary (Indigo)**
- **Purpose**: Main CTAs, links, interactive elements
- **Values**: `#6366F1` (500), with 50-950 scale
- **Usage**: Buttons, focused states, selected items
- **Accessibility**: Passes WCAG AA at 500 on white

**Secondary (Teal)**
- **Purpose**: Success states, approvals, confirmations
- **Values**: `#14B8A6` (500), with 50-950 scale
- **Usage**: Approval badges, success alerts
- **Accessibility**: Passes WCAG AA at 600 on white

#### Neutral Palette

**Gray Scale**
- **Purpose**: Text, borders, backgrounds
- **Range**: 0 (white) to 950 (near black)
- **Usage**:
  - 900-950: Headings, strong emphasis
  - 600-700: Body text
  - 400-500: Secondary text, placeholders
  - 100-300: Borders, dividers, disabled states
  - 0-50: Backgrounds, cards

#### Semantic Colors

**Success (Green)**
- Primary: `#22C55E`
- Usage: Approvals, confirmations, positive outcomes

**Warning (Amber)**
- Primary: `#F59E0B`
- Usage: Escalations, pending approvals, cautions

**Error (Red)**
- Primary: `#EF4444`
- Usage: Denials, failures, critical alerts

**Info (Blue)**
- Primary: `#3B82F6`
- Usage: Informational messages, tips, guidance

#### Governance-Specific Colors

**Policy States**
- Active: Green `#22C55E`
- Draft: Gray `#94A3B8`
- Deprecated: Amber `#F59E0B`
- Archived: Slate `#64748B`

**Decision Outcomes**
- Approved: Green `#22C55E`
- Denied: Red `#EF4444`
- Escalated: Amber `#F59E0B`
- Pending: Blue `#3B82F6`
- Override: Purple `#8B5CF6`

**Risk Levels**
- Minimal: Green `#22C55E`
- Low: Lime `#84CC16`
- Medium: Amber `#F59E0B`
- High: Orange `#F97316`
- Critical: Red `#EF4444`

### Typography

#### Font Families

**Primary (Inter)**
- **Usage**: All UI text, body copy, headings
- **Rationale**: Excellent readability, extensive weight range, open source
- **Fallback**: System UI fonts (San Francisco, Segoe UI, Roboto)

**Monospace (JetBrains Mono)**
- **Usage**: Code snippets, hashes, cryptographic signatures
- **Rationale**: Clear character distinction, optimized for technical content
- **Fallback**: SF Mono, Monaco, Cascadia Code

#### Type Scale

Based on **Major Third (1.250)** modular scale:

| Size | Rem | Px | Usage |
|------|-----|-------|-------|
| xs | 0.75rem | 12px | Fine print, captions |
| sm | 0.875rem | 14px | Secondary text, table data |
| base | 1rem | 16px | Body text (default) |
| lg | 1.125rem | 18px | Large body, subheadings |
| xl | 1.25rem | 20px | Section headings |
| 2xl | 1.5rem | 24px | Page headings |
| 3xl | 1.875rem | 30px | Major headings |
| 4xl | 2.25rem | 36px | Display headings |
| 5xl | 3rem | 48px | Hero headings |

#### Font Weights

- **Normal (400)**: Body text
- **Medium (500)**: Emphasis, buttons
- **Semibold (600)**: Subheadings
- **Bold (700)**: Headings

#### Line Heights

- **Tight (1.25)**: Headings, compact text
- **Normal (1.5)**: Body text (optimal readability)
- **Relaxed (1.625)**: Long-form content

### Spacing System

**4px Grid System**

All spacing uses multiples of 4px for visual harmony:

| Token | Rem | Px | Usage |
|-------|-----|-------|-------|
| 1 | 0.25rem | 4px | Micro spacing |
| 2 | 0.5rem | 8px | Icon gaps, tight padding |
| 3 | 0.75rem | 12px | Component internal spacing |
| 4 | 1rem | 16px | Base unit, standard gaps |
| 6 | 1.5rem | 24px | Section spacing |
| 8 | 2rem | 32px | Large section spacing |
| 12 | 3rem | 48px | Major section breaks |
| 16 | 4rem | 64px | Page-level spacing |

**Common Patterns**:
- Button padding: `16px horizontal, 12px vertical` (4 × 3)
- Card padding: `24px` (6)
- Section spacing: `48px` (12)
- Page margins: `64px` (16)

### Shadows & Elevation

**Elevation Levels**

| Level | Shadow | Usage |
|-------|--------|-------|
| 0 (Flat) | none | Inline content |
| 1 (Subtle) | sm | Borders, dividers |
| 2 (Card) | base | Cards, containers |
| 3 (Elevated) | md | Dropdowns, popovers |
| 4 (Floating) | lg | Modals, overlays |
| 5 (Prominent) | xl | Notifications |

**Shadow Values**:
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-base: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
```

### Animation & Motion

#### Principles

1. **Purposeful**: Animations guide attention or provide feedback
2. **Subtle**: Enterprise interfaces avoid flashy animations
3. **Fast**: Transitions complete in 150-300ms
4. **Respectful**: Honor `prefers-reduced-motion` preference

#### Duration

- **Instant** (0ms): No animation
- **Fast** (150ms): Hover states, focus rings
- **Normal** (200ms): Default transitions, modals
- **Slow** (300ms): Complex animations, page transitions

#### Easing

- **Ease-out** (default): Interactive elements (buttons, links)
- **Ease-in**: Dismissing elements (closing modals)
- **Ease-in-out**: Emphasis transitions

```css
--easing-default: cubic-bezier(0.4, 0, 0.2, 1);
--easing-in: cubic-bezier(0.4, 0, 1, 1);
--easing-out: cubic-bezier(0, 0, 0.2, 1);
```

---

## Design Tokens

### What Are Design Tokens?

Design tokens are the **atomic design decisions** that power the entire system. They are named, reusable values that replace hard-coded values in designs and code.

### Token Categories

#### 1. Color Tokens

```javascript
// Brand primary
tokens.colors.brand.primary[500]  // #6366F1

// Semantic success
tokens.colors.semantic.success[500]  // #22C55E

// Neutral text
tokens.colors.neutral[700]  // #404040
```

#### 2. Typography Tokens

```javascript
// Font family
tokens.typography.fontFamily.sans  // 'Inter, ...'

// Font size
tokens.typography.fontSize.base  // 1rem (16px)

// Font weight
tokens.typography.fontWeight.semibold  // 600
```

#### 3. Spacing Tokens

```javascript
// Standard spacing
tokens.spacing[4]  // 1rem (16px)

// Section spacing
tokens.spacing[12]  // 3rem (48px)
```

#### 4. Shadow Tokens

```javascript
// Card shadow
tokens.shadows.base  // 0 1px 3px rgba(...)

// Modal shadow
tokens.shadows.xl  // 0 20px 25px rgba(...)
```

### Using Tokens in Code

#### React/JSX
```jsx
import { tokens } from './lexecon-design-tokens';

<button style={{
  backgroundColor: tokens.colors.brand.primary[500],
  padding: `${tokens.spacing[3]} ${tokens.spacing[4]}`,
  fontSize: tokens.typography.fontSize.base,
  borderRadius: tokens.border.radius.lg
}}>
  Click Me
</button>
```

#### CSS/SCSS
```css
.button-primary {
  background-color: var(--color-brand-primary-500);
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-base);
  border-radius: var(--border-radius-lg);
}
```

---

## Component Library

### Component Hierarchy

```
Primitives (Atomic)
├── Button
├── Input
├── Checkbox
├── Radio
├── Select
└── Badge

Compositions (Molecular)
├── Card
├── Alert
├── Modal
├── Tabs
└── Table

Patterns (Organisms)
├── Forms
├── Data Tables
├── Navigation
└── Governance Widgets
```

### Core Components

#### Button

**Variants**:
- Primary: Main CTAs, high emphasis
- Secondary: Supporting actions
- Ghost: Tertiary actions, inline
- Danger: Destructive actions
- Success: Confirmations

**Sizes**:
- Small (32px height): Compact interfaces
- Medium (40px height): Default
- Large (48px height): Hero CTAs

**States**:
- Default, Hover, Active, Focus, Disabled, Loading

**Usage**:
```jsx
<Button variant="primary" size="md" onClick={handleApprove}>
  Approve Decision
</Button>
```

#### Input

**Types**:
- Text, Email, Password, Number, Search

**Features**:
- Label support
- Helper text
- Error states
- Disabled states
- Required indicator

**Usage**:
```jsx
<Input
  label="Policy Name"
  value={policyName}
  onChange={(e) => setPolicyName(e.target.value)}
  error={errors.policyName}
  required
/>
```

#### Card

**Variants**:
- Default: Standard elevation
- Elevated: Higher shadow
- Outlined: Border emphasis

**Features**:
- Optional title/subtitle
- Optional footer
- Configurable padding

**Usage**:
```jsx
<Card
  title="Recent Decisions"
  subtitle="Last 24 hours"
  footer={<Button>View All</Button>}
>
  {decisionsList}
</Card>
```

#### Badge

**Variants**:
- Default, Primary, Success, Warning, Error, Info

**Features**:
- Dot indicator option
- Multiple sizes
- Status communication

**Usage**:
```jsx
<Badge variant="success" dot>
  Approved
</Badge>
```

#### Alert

**Variants**:
- Info, Success, Warning, Error

**Features**:
- Optional title
- Dismissible
- Icon support

**Usage**:
```jsx
<Alert variant="warning" title="Escalation Required" dismissible>
  This decision requires human oversight due to high risk score.
</Alert>
```

#### Modal

**Sizes**:
- Small (max-w-md)
- Medium (max-w-lg) - Default
- Large (max-w-2xl)
- Extra Large (max-w-4xl)

**Features**:
- Backdrop overlay
- ESC key to close
- Optional footer
- Accessible (ARIA)

**Usage**:
```jsx
<Modal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  title="Approve Decision"
  footer={
    <>
      <Button variant="secondary" onClick={handleCancel}>Cancel</Button>
      <Button variant="primary" onClick={handleApprove}>Approve</Button>
    </>
  }
>
  <p>Are you sure you want to approve this decision?</p>
</Modal>
```

#### Table

**Features**:
- Sortable columns
- Selectable rows
- Row click handlers
- Responsive scrolling

**Usage**:
```jsx
<Table
  columns={[
    { header: 'Decision ID', key: 'id' },
    { header: 'Risk Level', key: 'risk', render: (value) => <Badge variant={getRiskVariant(value)}>{value}</Badge> },
    { header: 'Date', key: 'date' }
  ]}
  data={decisions}
  selectable
  onRowClick={(row) => viewDecision(row.id)}
/>
```

#### Select

**Features**:
- Label and error states
- Disabled state
- Required indicator
- Placeholder support

**Usage**:
```jsx
<Select
  label="Risk Level"
  options={[
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' }
  ]}
  value={riskLevel}
  onChange={(e) => setRiskLevel(e.target.value)}
  required
/>
```

#### Checkbox

**Features**:
- Label support
- Disabled state
- Controlled component

**Usage**:
```jsx
<Checkbox
  label="I acknowledge this decision"
  checked={acknowledged}
  onChange={(e) => setAcknowledged(e.target.checked)}
/>
```

#### Tabs

**Variants**:
- Line: Underline active tab
- Pills: Filled background

**Usage**:
```jsx
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
```

---

## Layout Patterns

### Grid System

**12-Column Grid**
- Desktop (1280px+): 12 columns, 24px gutters
- Tablet (768-1279px): 8 columns, 16px gutters
- Mobile (<768px): 4 columns, 16px gutters

### Common Layouts

#### Dashboard Layout

```
┌─────────────────────────────────────┐
│ Top Navigation Bar                  │
├─────────┬───────────────────────────┤
│         │                           │
│ Sidebar │ Main Content Area         │
│         │                           │
│         │                           │
│         │                           │
└─────────┴───────────────────────────┘
```

#### Detail View Layout

```
┌─────────────────────────────────────┐
│ Breadcrumb Navigation               │
├─────────────────────────────────────┤
│ Page Header                         │
│ Title, Actions                      │
├──────────────────┬──────────────────┤
│                  │                  │
│ Primary Content  │ Sidebar/Meta     │
│                  │                  │
│                  │                  │
└──────────────────┴──────────────────┘
```

#### Modal/Form Layout

```
┌─────────────────────────────────────┐
│ Modal Header                        │
├─────────────────────────────────────┤
│                                     │
│ Form Fields                         │
│ [Label]                             │
│ [Input]                             │
│                                     │
│ [Label]                             │
│ [Input]                             │
│                                     │
├─────────────────────────────────────┤
│ Footer Actions         [Cancel] [OK]│
└─────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Min Width | Max Width | Columns | Gutter |
|------------|-----------|-----------|---------|--------|
| Mobile | 0px | 767px | 4 | 16px |
| Tablet | 768px | 1023px | 8 | 16px |
| Laptop | 1024px | 1279px | 12 | 24px |
| Desktop | 1280px | 1535px | 12 | 24px |
| Large | 1536px+ | - | 12 | 24px |

---

## Accessibility

### WCAG AA Compliance

**Color Contrast**
- Normal text (16px): 4.5:1 minimum
- Large text (18px+): 3:1 minimum
- UI components: 3:1 minimum

**Keyboard Navigation**
- All interactive elements accessible via Tab
- Logical tab order (left-to-right, top-to-bottom)
- Visible focus indicators (2px ring)
- ESC key closes modals/dropdowns

**Screen Reader Support**
- Semantic HTML (nav, main, section, article)
- ARIA labels for icons and custom controls
- ARIA live regions for dynamic content
- Alt text for all images

**Touch Targets**
- Minimum 44x44px (iOS/Web)
- Minimum 48x48px (Android)
- Adequate spacing between targets

### Accessibility Checklist

- [ ] All colors pass WCAG AA contrast requirements
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible and distinct
- [ ] All images have descriptive alt text
- [ ] Forms have associated labels
- [ ] Error messages announced to screen readers
- [ ] Loading states announced
- [ ] Modals trap focus appropriately
- [ ] Touch targets meet minimum size
- [ ] Motion respects `prefers-reduced-motion`

---

## Usage Guidelines

### Do's

✅ **Do** use design tokens for all styling
✅ **Do** use semantic component variants
✅ **Do** provide clear labels and helper text
✅ **Do** test keyboard navigation
✅ **Do** validate color contrast
✅ **Do** use consistent spacing (4px grid)
✅ **Do** provide feedback for all actions
✅ **Do** handle loading and error states

### Don'ts

❌ **Don't** use hard-coded colors or spacing
❌ **Don't** create custom components when library components exist
❌ **Don't** ignore accessibility requirements
❌ **Don't** use animations excessively
❌ **Don't** hide critical information behind clicks
❌ **Don't** use placeholder text as labels
❌ **Don't** forget mobile/responsive behavior
❌ **Don't** skip error handling

### Component Selection Guide

**Need user input?**
- Text: Use `Input`
- Selection from list: Use `Select`
- Yes/No choice: Use `Checkbox` or `Radio`
- Multi-selection: Use `Checkbox` group

**Need to display information?**
- Status/label: Use `Badge`
- Feedback message: Use `Alert`
- Grouped content: Use `Card`
- Tabular data: Use `Table`

**Need user action?**
- Primary action: Use `Button` variant="primary"
- Secondary action: Use `Button` variant="secondary"
- Destructive action: Use `Button` variant="danger"
- Navigation: Use `Tabs` or links

**Need to organize content?**
- Related content: Use `Card`
- Multiple views: Use `Tabs`
- Focused interaction: Use `Modal`

---

## Developer Handoff

### File Structure

```
design-system/
├── lexecon-design-tokens.js      # Design tokens
├── lexecon-components.jsx        # Component library
├── lexecon-design-system.md      # This documentation
└── lexecon-component-guide.md    # Component specifications
```

### Integration Steps

1. **Install Dependencies**
   ```bash
   npm install react react-dom
   # Tailwind CSS optional but recommended
   npm install -D tailwindcss
   ```

2. **Import Design Tokens**
   ```javascript
   import { tokens } from './lexecon-design-tokens';
   ```

3. **Import Components**
   ```javascript
   import { Button, Input, Card } from './lexecon-components';
   ```

4. **Use Components**
   ```jsx
   function App() {
     return (
       <Card title="Welcome">
         <Input label="Name" />
         <Button variant="primary">Submit</Button>
       </Card>
     );
   }
   ```

### Customization

**Theme Customization**
```javascript
// Create custom theme extending base tokens
const customTheme = {
  ...tokens,
  colors: {
    ...tokens.colors,
    brand: {
      ...tokens.colors.brand,
      primary: {
        ...tokens.colors.brand.primary,
        500: '#YOUR_BRAND_COLOR'
      }
    }
  }
};
```

**Component Customization**
```jsx
// Extend base component
const CustomButton = ({ children, ...props }) => (
  <Button
    className="custom-additional-styles"
    {...props}
  >
    {children}
  </Button>
);
```

### Browser Support

- **Chrome/Edge**: Last 2 versions
- **Firefox**: Last 2 versions
- **Safari**: Last 2 versions
- **Mobile Safari**: iOS 14+
- **Chrome Android**: Last 2 versions

### Performance Considerations

- Components use CSS-in-JS for scoping
- Minimal JavaScript footprint
- Tree-shakeable exports
- No external dependencies (except React)
- Optimized for code splitting

---

## Governance-Specific Patterns

### Risk Visualization

**Risk Badge Pattern**
```jsx
const RiskBadge = ({ level }) => {
  const variants = {
    minimal: 'success',
    low: 'success',
    medium: 'warning',
    high: 'warning',
    critical: 'error'
  };

  return (
    <Badge variant={variants[level]} dot>
      {level.toUpperCase()}
    </Badge>
  );
};
```

### Decision Outcome Pattern

```jsx
const DecisionOutcome = ({ outcome }) => {
  const config = {
    approved: { variant: 'success', icon: '✓', label: 'Approved' },
    denied: { variant: 'error', icon: '✕', label: 'Denied' },
    escalated: { variant: 'warning', icon: '⚠', label: 'Escalated' },
    pending: { variant: 'info', icon: '○', label: 'Pending' }
  };

  const { variant, icon, label } = config[outcome];

  return (
    <div className="flex items-center gap-2">
      <span className="text-xl">{icon}</span>
      <Badge variant={variant}>{label}</Badge>
    </div>
  );
};
```

### Audit Trail Entry Pattern

```jsx
const AuditEntry = ({ entry }) => (
  <Card padding="compact">
    <div className="flex justify-between items-start mb-2">
      <div>
        <span className="text-sm font-mono text-neutral-500">
          {entry.timestamp}
        </span>
        <h4 className="font-semibold text-neutral-800">
          {entry.action}
        </h4>
      </div>
      <Badge variant="default">{entry.actor}</Badge>
    </div>
    <p className="text-sm text-neutral-600">{entry.description}</p>
    {entry.signature && (
      <div className="mt-2 pt-2 border-t border-neutral-200">
        <span className="text-xs font-mono text-neutral-400">
          Signature: {entry.signature.substring(0, 16)}...
        </span>
      </div>
    )}
  </Card>
);
```

---

## Changelog

### Version 1.0.0 (2026-01-10)

**Initial Release**
- Complete design token system
- 10 core components
- Comprehensive documentation
- Accessibility guidelines
- Governance-specific patterns

---

## Support & Contribution

### Getting Help

- **Documentation**: This file
- **Component Specs**: See `lexecon-component-guide.md`
- **Design Tokens**: See `lexecon-design-tokens.js`
- **Examples**: See component library file

### Contributing

When adding new components:
1. Follow existing component patterns
2. Use design tokens exclusively
3. Ensure WCAG AA compliance
4. Add PropTypes/TypeScript types
5. Include usage examples
6. Update this documentation

---

## License

Proprietary - Lexecon Enterprise AI Governance Platform

© 2026 Lexecon. All rights reserved.

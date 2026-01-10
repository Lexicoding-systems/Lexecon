# Audit Dashboard - Design Specification

**Feature:** Audit Dashboard Interface
**Version:** 1.0.0
**Last Updated:** 2026-01-10
**For:** Enterprise Compliance Officers & Auditors

---

## Table of Contents

1. [Overview](#overview)
2. [User Flows](#user-flows)
3. [Layout & Structure](#layout--structure)
4. [Component Specifications](#component-specifications)
5. [Interactions & Animations](#interactions--animations)
6. [Data Requirements](#data-requirements)
7. [Edge Cases](#edge-cases)
8. [Accessibility](#accessibility)
9. [Performance Requirements](#performance-requirements)
10. [Implementation Notes](#implementation-notes)

---

## Overview

### Purpose

The Audit Dashboard is the primary interface for compliance officers and auditors to:
- View tamper-evident decision ledger with cryptographic verification
- Search and filter audit entries
- Export audit packages for regulatory submissions
- Verify ledger integrity
- Analyze decision patterns and trends

### Key Features

✅ **Decision Ledger**: Complete audit trail with cryptographic signatures
✅ **Real-time Filtering**: Search, risk level, outcome, date range filters
✅ **Verification Tools**: Validate signatures and hash chain integrity
✅ **Export Functionality**: Generate compliant audit packages (JSON, CSV, PDF)
✅ **Analytics**: Decision trends, risk distribution, policy usage
✅ **Timeline View**: Chronological decision flow visualization

### User Personas

**Primary**: Compliance Officer
- **Goals**: Ensure regulatory compliance, prepare audit reports
- **Pain Points**: Manual audit trail collection, verification complexity
- **Needs**: Quick access to verified data, export capabilities

**Secondary**: External Auditor
- **Goals**: Validate governance controls, verify decision integrity
- **Pain Points**: Incomplete audit trails, trust in data validity
- **Needs**: Cryptographic proof, downloadable evidence

---

## User Flows

### Flow 1: View Recent Decisions

```
1. User lands on Audit Dashboard
2. Sees stats summary (total decisions, verified entries, escalations, high-risk)
3. Views Decision Ledger tab (default view)
4. Sees table of recent decisions with:
   - Decision ID
   - Timestamp
   - Action description
   - Risk level badge
   - Outcome badge
   - Verification status
5. Can click any row to see full details
```

### Flow 2: Filter & Search Decisions

```
1. User enters search term in filter bar
2. Selects risk level filter (e.g., "High")
3. Selects outcome filter (e.g., "Escalated")
4. Selects date range (e.g., "Last 7 Days")
5. Optionally checks "Verified only"
6. Table updates instantly with matching results
7. Can clear filters to reset view
```

### Flow 3: View Decision Details

```
1. User clicks decision row in table
2. Modal opens showing:
   - Decision overview (ID, timestamp, risk, outcome, actor)
   - Action description
   - Cryptographic verification (signature, hash chain status)
   - Applied policies and results
3. User can:
   - Download evidence artifacts
   - Verify signature independently
   - Close modal to return to table
```

### Flow 4: Export Audit Package

```
1. User clicks "Export Audit" button
2. Modal opens with export configuration:
   - Format selection (JSON, CSV, PDF)
   - Date range (from/to dates)
   - Options (include signatures, include evidence)
3. User configures export and clicks "Generate Export"
4. System creates deterministic, signed audit package
5. User navigates to "Audit Exports" tab
6. Sees export in "Processing" status
7. When complete, clicks "Download" to retrieve package
```

### Flow 5: Verify Ledger Integrity

```
1. User clicks "Verify Integrity" button
2. Modal opens explaining verification process
3. User clicks "Start Verification"
4. System checks:
   - Ed25519 signatures for all entries
   - Hash chain integrity
   - Ledger consistency
5. Progress indicator shows verification in progress
6. Results displayed:
   - Total entries checked
   - Verified count
   - Failed count (if any)
   - Chain integrity status
   - Signature validity status
7. User sees success message if all checks pass
8. User closes modal
```

---

## Layout & Structure

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
│ Audit Dashboard                  [Verify] [Export Audit]    │
│ Tamper-evident decision ledger...                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ STATS CARDS (4 cards in grid)                               │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                        │
│ │Total │ │Verify│ │Escal.│ │High  │                        │
│ │Decis.│ │Entry │ │      │ │Risk  │                        │
│ └──────┘ └──────┘ └──────┘ └──────┘                        │
│                                                              │
│ TABS                                                         │
│ [Decision Ledger] [Timeline] [Analytics] [Exports]          │
│ ━━━━━━━━━━━━━━━━                                            │
│                                                              │
│ FILTERS BAR                                                  │
│ [Search] [Risk Level] [Outcome] [Date Range] [✓ Verified]   │
│                                                              │
│ ALERT (Verification Status)                                 │
│ ✓ Ledger Verified - All entries have valid signatures      │
│                                                              │
│ DECISION TABLE                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ID │ Timestamp │ Action │ Risk │ Outcome │ Verified  │   │
│ ├───────────────────────────────────────────────────────┤   │
│ │ ... │ ... │ ... │ ... │ ... │ ... │                    │   │
│ │ ... │ ... │ ... │ ... │ ... │ ... │                    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Responsive Behavior

**Desktop (1280px+)**
- 4-column stats grid
- Full table with all columns
- Side-by-side filters

**Tablet (768-1279px)**
- 2-column stats grid
- Table scrolls horizontally
- Stacked filters (2 per row)

**Mobile (<768px)**
- 1-column stats grid
- Card-based decision list (not table)
- Stacked filters (1 per row)
- Full-screen modals

---

## Component Specifications

### Header

**Visual**:
- Background: White (#FFFFFF)
- Border-bottom: 1px solid neutral.200
- Height: Auto (min 88px)
- Padding: 24px vertical, 32px horizontal

**Content**:
- Title: "Audit Dashboard" (text-3xl, font-bold, neutral.900)
- Subtitle: Descriptive text (text-base, neutral.600)
- Actions: Two buttons right-aligned
  - "Verify Integrity" (secondary variant)
  - "Export Audit" (primary variant)

**Layout**:
- Flexbox: space-between
- Max-width: 1440px
- Centered with auto margins

### Stats Cards

**Grid**:
- Desktop: 4 columns, 24px gap
- Tablet: 2 columns, 16px gap
- Mobile: 1 column, 16px gap

**Card Structure**:
```
┌─────────────────────────────┐
│ Label                   Icon│
│                             │
│ Value (Large)               │
│ Change/Status (Small)       │
└─────────────────────────────┘
```

**Visual**:
- Card variant: elevated
- Padding: 24px (default)
- Label: text-sm, medium, neutral.600
- Value: text-3xl, bold, neutral.900
- Change: text-sm, colored based on type
  - Positive: success.600
  - Negative: error.600
  - Neutral: neutral.500
- Icon: text-3xl, positioned top-right

**Stats Shown**:
1. Total Decisions - Count with percentage change
2. Verified Entries - Count with integrity status
3. Escalations - Count with trend
4. High Risk - Count with context

### Tabs Navigation

**Visual**:
- Variant: line
- Container: border-bottom 1px neutral.200
- Tab padding: 16px horizontal, 8px vertical
- Active tab: border-bottom 2px brand.primary.500, text brand.primary.600
- Inactive tab: text neutral.500, hover text neutral.700

**Tabs**:
1. Decision Ledger (default)
2. Timeline View
3. Analytics
4. Audit Exports

### Filters Bar

**Container**:
- Card padding: default (24px)
- Grid layout: 5 columns on desktop, 2 on tablet, 1 on mobile
- Gap: 16px

**Filters**:
1. **Search Input**
   - Label: "Search"
   - Placeholder: "Search decisions..."
   - Type: text
   - Width: Full

2. **Risk Level Select**
   - Label: "Risk Level"
   - Options: All Levels, Minimal, Low, Medium, High, Critical
   - Default: "All Levels"

3. **Outcome Select**
   - Label: "Outcome"
   - Options: All Outcomes, Approved, Denied, Escalated, Override
   - Default: "All Outcomes"

4. **Date Range Select**
   - Label: "Date Range"
   - Options: Last 24 Hours, Last 7 Days, Last 30 Days, Last 90 Days, All Time
   - Default: "Last 7 Days"

5. **Verified Checkbox**
   - Label: "Verified only"
   - Alignment: Flex-end (bottom-aligned)
   - Default: unchecked

### Alert (Verification Status)

**Visual**:
- Variant: success
- Icon: true (✓)
- Dismissible: false (always shown)
- Margin-bottom: 24px

**Content**:
- Title: "Ledger Verified"
- Message: "All X entries have valid cryptographic signatures and hash chains."
- X: Dynamic count of total entries

**States**:
- Success: All entries verified
- Warning: Some entries unverified (show count)
- Error: Verification failed (show details)

### Decision Table

**Container**:
- Card with padding: none
- Overflow-x: auto (horizontal scroll if needed)

**Table Structure**:

| Column | Width | Alignment | Content |
|--------|-------|-----------|---------|
| Decision ID | 120px | Left | Monospace font, brand.primary.600 |
| Timestamp | 180px | Left | Monospace font, neutral.600, small |
| Action | Auto | Left | Primary text + actor (smaller, below) |
| Risk | 100px | Left | Badge component |
| Outcome | 120px | Left | Badge component with dot |
| Verified | 100px | Left | ✓/✕ icon + text |
| Actions | 120px | Left | "View Details" ghost button |

**Header**:
- Background: neutral.50
- Border-bottom: 2px solid neutral.200
- Padding: 16px horizontal, 12px vertical
- Text: text-sm, semibold, neutral.700

**Rows**:
- Padding: 24px horizontal, 16px vertical
- Border-bottom: 1px solid neutral.200
- Hover: background neutral.50
- Cursor: pointer
- Transition: background 150ms ease

**Risk Level Badge Colors**:
- Minimal/Low: success variant
- Medium: warning variant
- High/Critical: error variant

**Outcome Badge Colors**:
- Approved: success variant with dot
- Denied: error variant with dot
- Escalated: warning variant with dot
- Override: primary variant with dot

### Decision Detail Modal

**Size**: lg (max-w-2xl)

**Header**:
- Title: "Decision Details: {decision.id}"
- Close button (X)

**Body Sections**:

1. **Decision Overview** (grid 2 columns)
   - Decision ID (mono)
   - Timestamp (mono)
   - Risk Level (badge)
   - Outcome (badge)
   - Actor
   - Policy Version (mono)

2. **Action**
   - Text description of the action

3. **Cryptographic Verification**
   - Ed25519 Signature (code block, monospace, scrollable)
   - Verification status icons:
     - ✓ Signature verified successfully
     - ✓ Hash chain integrity confirmed

4. **Applied Policies**
   - List of policies with pass/fail badges
   - Policy name
   - Result badge (success/error)

**Footer**:
- Left: "Close" button (secondary)
- Right: "Download Evidence" (secondary), "Verify Signature" (primary)

**Visual**:
- Section spacing: 24px
- Label text: text-xs, medium, neutral.600
- Value text: text-sm, neutral.800
- Code blocks: background neutral.50, padding 12px, rounded

### Export Modal

**Size**: md (max-w-lg)

**Header**:
- Title: "Export Audit Package"

**Body**:
1. Info alert about deterministic exports
2. Format select (JSON, CSV, PDF)
3. Date range inputs (From/To)
4. Checkboxes:
   - Include cryptographic signatures (checked by default)
   - Include evidence artifacts (unchecked by default)

**Footer**:
- "Cancel" (secondary)
- "Generate Export" (primary)

### Verify Modal

**Size**: md (max-w-lg)

**Header**:
- Title: "Verify Ledger Integrity"

**Body**:

**Before Verification**:
- Info alert explaining verification
- Instruction text

**During Verification**:
- Loading icon (🔐)
- "Verifying cryptographic signatures..." text
- (2-second delay)

**After Verification**:
- Success alert: "Verification Complete"
- Results table:
  - Total Entries: 2,847
  - Verified Entries: 2,847 (green)
  - Failed Entries: 0 (green if 0, red otherwise)
  - Hash Chain Integrity: Valid (green)
  - Signature Validity: Valid (green)

**Footer**:
- "Close" (secondary)
- "Start Verification" (primary, becomes loading during verification)

### Timeline View

**Layout**:
- Vertical timeline with connecting lines
- Each entry:
  - Time badge (left)
  - Colored dot indicator (risk-based color)
  - Vertical line connecting to next entry
  - Entry card (right):
    - Title (action)
    - Description
    - Signature (truncated)

**Colors**:
- Success outcomes: Green dot
- Warning outcomes: Amber dot
- Error outcomes: Red dot
- Line: neutral.200

**Spacing**:
- Entry gap: 24px vertical
- Dot size: 12px
- Line width: 2px

### Analytics View

**Grid**: 2 columns on desktop, 1 on mobile

**Cards**:
1. **Decision Outcomes** (Pie Chart)
   - Shows percentage distribution
   - Approved, Denied, Escalated, Override

2. **Risk Distribution** (Bar Chart)
   - Shows count by risk level
   - Minimal, Low, Medium, High, Critical

3. **Decision Volume** (Line Chart)
   - Trend over last 30 days
   - Daily decision count

4. **Top Policies** (List with Progress Bars)
   - Policy name
   - Count and percentage
   - Visual progress bar (brand.primary.500)

**Chart Placeholders**:
- 256px height
- Centered icon and text
- Background: neutral.50
- Text: neutral.400

### Exports View

**Table**:
Similar structure to Decision Table

**Columns**:
- Export ID (mono, brand.primary.600)
- Date Range
- Format (badge)
- Entries (count, mono)
- Size (file size, mono)
- Status (badge: ready/processing)
- Actions (Download button if ready)

**Status Badges**:
- Ready: success variant with dot
- Processing: warning variant

---

## Interactions & Animations

### Table Row Hover

**Trigger**: Mouse enters table row
**Animation**:
- Duration: 150ms
- Easing: ease-out
- Property: background-color
- From: transparent
- To: neutral.50

### Modal Open

**Trigger**: Modal opens
**Animation**:
- Duration: 200ms
- Easing: ease-out
- Transform: scale(0.95) → scale(1)
- Opacity: 0 → 1
- Backdrop: fade in simultaneously

### Modal Close

**Trigger**: Modal closes
**Animation**:
- Duration: 150ms
- Easing: ease-in
- Transform: scale(1) → scale(0.95)
- Opacity: 1 → 0
- Backdrop: fade out simultaneously

### Filter Changes

**Trigger**: User changes filter
**Behavior**:
- Instant table update (no loading delay)
- Row count updates immediately
- If no results: Show empty state
- Maintain scroll position if possible

### Tab Switch

**Trigger**: User clicks tab
**Animation**:
- Active indicator slides to new tab (200ms ease-out)
- Content fades out (100ms) then fades in (100ms)
- No full page reload

### Button Loading State

**Trigger**: Async action initiated
**Behavior**:
- Button text changes (optional)
- Spinner appears (left of text)
- Button disabled
- Cursor: not-allowed
- Minimum display: 300ms (prevent flash)

### Verification Progress

**Trigger**: Verification starts
**Animation**:
- Loading icon appears
- Text updates
- 2-second simulation delay
- Results fade in smoothly

---

## Data Requirements

### Decision Entry Object

```typescript
interface DecisionEntry {
  id: string;                    // e.g., "DEC-2847"
  timestamp: string;              // ISO 8601 format
  action: string;                 // Description of action
  actor: string;                  // Email or system identifier
  riskLevel: 'minimal' | 'low' | 'medium' | 'high' | 'critical';
  outcome: 'approved' | 'denied' | 'escalated' | 'override';
  signature: string;              // Ed25519 signature (hex)
  policyVersion: string;          // e.g., "v2.1.0"
  verified: boolean;              // Signature verification status
  evidenceIds?: string[];         // Optional evidence artifact IDs
  appliedPolicies?: AppliedPolicy[];
}

interface AppliedPolicy {
  name: string;
  result: 'passed' | 'failed';
  details?: string;
}
```

### Stats Data

```typescript
interface AuditStats {
  totalDecisions: number;
  totalDecisionsChange: string;   // e.g., "+12%"
  verifiedEntries: number;
  verifiedPercentage: number;     // Should be 100 for valid ledger
  escalations: number;
  escalationsChange: string;
  highRiskCount: number;
  highRiskStatus: string;
}
```

### Export Object

```typescript
interface AuditExport {
  id: string;                     // e.g., "EXP-001"
  createdAt: string;              // ISO 8601 timestamp
  dateRange: string;              // Human-readable range
  format: 'json' | 'csv' | 'pdf';
  size: string;                   // e.g., "2.4 MB"
  status: 'ready' | 'processing' | 'failed';
  entries: number;                // Count of decisions included
  downloadUrl?: string;           // If ready
}
```

### API Endpoints

```
GET  /api/v1/audit/decisions           - List decisions
GET  /api/v1/audit/decisions/:id       - Get decision details
GET  /api/v1/audit/stats               - Get dashboard stats
POST /api/v1/audit/verify              - Verify ledger integrity
POST /api/v1/audit/export              - Create audit export
GET  /api/v1/audit/exports             - List exports
GET  /api/v1/audit/exports/:id/download - Download export
```

---

## Edge Cases

### No Decisions Found

**Scenario**: Filters return 0 results

**Display**:
```
┌─────────────────────────────────┐
│                                 │
│           📋                    │
│                                 │
│    No decisions found           │
│                                 │
│    Try adjusting your filters  │
│    or search criteria          │
│                                 │
│    [Clear Filters]             │
│                                 │
└─────────────────────────────────┘
```

**Actions**:
- Show "Clear Filters" button
- Provide helpful suggestion text
- Maintain filter UI (don't hide it)

### Very Long Decision Actions

**Scenario**: Action description exceeds display space

**Behavior**:
- Truncate after 2 lines with ellipsis (...)
- Show full text in detail modal
- Optionally: Tooltip on hover shows full text

### Signature Verification Failure

**Scenario**: One or more signatures invalid

**Alert**:
- Variant: error
- Title: "Ledger Integrity Compromised"
- Message: "X entries failed signature verification. Immediate investigation required."
- Action: "View Failed Entries" button

**Table**:
- Failed entries highlighted with error background (error.50)
- Verified column shows red ✕ icon
- Click to see failure details in modal

### Large Result Sets

**Scenario**: Thousands of decisions to display

**Implementation**:
- Pagination: 50 entries per page
- Page controls: Previous/Next, page number input
- Total count displayed: "Showing 1-50 of 2,847"
- Virtual scrolling (optional, advanced)

### Slow Network / Loading States

**Scenario**: API request takes >500ms

**Behavior**:
- Show skeleton screens (not spinners)
- Skeleton maintains layout (prevents jump)
- Minimum display: 300ms (prevent flash)
- Timeout: 30 seconds, then error state

**Skeleton Design**:
- Gray animated rectangles (neutral.200)
- Pulse animation (opacity 1 → 0.5 → 1)
- Same dimensions as actual content

### Export Generation Failure

**Scenario**: Export creation fails

**Alert**:
- Variant: error
- Message: "Export generation failed. Please try again or contact support."
- Action: "Retry" button

**Exports Table**:
- Status badge: error variant
- Actions column: "Retry" button instead of "Download"

### Concurrent Users / Real-time Updates

**Scenario**: New decisions added while user viewing

**Behavior**:
- Option 1: Manual refresh (show "New entries available" banner)
- Option 2: Auto-refresh every 30 seconds
- Option 3: WebSocket real-time updates (advanced)

**Recommended**: Manual refresh with notification

### Mobile View

**Scenario**: User on mobile device

**Layout Changes**:
- Stats: 1 column, stacked
- Filters: 1 column, stacked, collapsible
- Table → Card list:
  ```
  ┌─────────────────────────┐
  │ DEC-2847        [High]  │
  │ 14:32:15 UTC            │
  │ Model inference...      │
  │ [APPROVED]  ✓ Verified  │
  └─────────────────────────┘
  ```
- Modals: Full-screen
- Tabs: Scrollable horizontal

---

## Accessibility

### Keyboard Navigation

**Table**:
- Tab: Focus first row
- Arrow Down/Up: Navigate rows
- Enter: Open detail modal
- Arrow Left/Right: Navigate table cells (if needed)

**Filters**:
- Tab: Move through filter inputs
- Enter: Submit/apply filter
- Escape: Clear focused filter

**Modals**:
- Tab: Cycle through focusable elements
- Shift+Tab: Reverse cycle
- Escape: Close modal
- Focus trap: Can't tab outside modal

**Tabs**:
- Tab: Focus tab group
- Arrow Left/Right: Switch between tabs
- Enter/Space: Activate focused tab
- Home: First tab
- End: Last tab

### ARIA Attributes

**Table**:
```html
<table role="table" aria-label="Decision ledger">
  <thead>
    <tr role="row">
      <th role="columnheader" scope="col">Decision ID</th>
      ...
    </tr>
  </thead>
  <tbody role="rowgroup">
    <tr role="row" aria-selected="false">
      <td role="cell">DEC-2847</td>
      ...
    </tr>
  </tbody>
</table>
```

**Modals**:
```html
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h3 id="modal-title">Decision Details</h3>
  ...
</div>
```

**Alerts**:
```html
<div role="alert" aria-live="polite">
  Ledger verified successfully
</div>
```

**Tabs**:
```html
<div role="tablist">
  <button role="tab" aria-selected="true" aria-controls="panel-1">
    Decision Ledger
  </button>
  ...
</div>
<div role="tabpanel" id="panel-1" aria-labelledby="tab-1">
  ...
</div>
```

### Screen Reader Support

**Announcements**:
- Filter changes: "Showing X filtered results"
- Loading: "Loading decisions..."
- Verification complete: "Ledger verification complete. All entries verified."
- Export ready: "Audit export EXP-001 is ready for download"

**Labels**:
- All inputs have associated labels
- Icon buttons have aria-label
- Table columns have meaningful headers
- Status badges include text (not just color)

### Color Contrast

All color combinations meet WCAG AA:

| Element | Foreground | Background | Ratio | Pass |
|---------|------------|------------|-------|------|
| Body text | neutral.600 | white | 7.0:1 | ✓ AAA |
| Headings | neutral.900 | white | 15.5:1 | ✓ AAA |
| Links | brand.primary.600 | white | 4.8:1 | ✓ AA |
| Success badge text | success.700 | success.100 | 6.2:1 | ✓ AAA |
| Error badge text | error.700 | error.100 | 6.5:1 | ✓ AAA |
| Warning badge text | warning.700 | warning.100 | 5.8:1 | ✓ AAA |

### Focus Indicators

- All interactive elements have visible focus
- Focus ring: 2px solid brand.primary.500
- Focus ring offset: 2px
- Focus ring on dark backgrounds: white ring

---

## Performance Requirements

### Load Times

| Metric | Target | Critical |
|--------|--------|----------|
| Initial Page Load | < 2s | < 4s |
| Time to Interactive | < 3s | < 5s |
| Filter Application | < 200ms | < 500ms |
| Table Render (50 rows) | < 100ms | < 300ms |
| Modal Open | < 150ms | < 300ms |

### Optimizations

**Code Splitting**:
- Lazy load Analytics charts
- Lazy load Timeline view
- Lazy load Export view
- Main ledger view loads immediately

**Data Fetching**:
- Pagination: 50 entries per page
- Infinite scroll (optional)
- Debounce search input (300ms)
- Cache filter results (5 minutes)

**Rendering**:
- Virtual scrolling for 100+ rows (optional)
- Memoize table rows (React.memo)
- Debounce window resize (150ms)
- Use CSS transforms for animations (GPU-accelerated)

**Assets**:
- No images required (emoji/icons only)
- Inline SVG for icons
- Tree-shake unused components
- Minify and compress JavaScript

### Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari: iOS 14+
- Chrome Android: Last 2 versions

---

## Implementation Notes

### Technology Stack

**Required**:
- React 18+
- Lexecon Design System (tokens + components)

**Optional**:
- React Query (data fetching)
- Recharts / Chart.js (analytics charts)
- date-fns (date formatting)

### File Structure

```
audit-dashboard/
├── index.js                    # Main export
├── AuditDashboard.jsx          # Main component
├── components/
│   ├── AuditDashboardHeader.jsx
│   ├── AuditStatsGrid.jsx
│   ├── StatCard.jsx
│   ├── DecisionLedgerView.jsx
│   ├── FiltersBar.jsx
│   ├── DecisionRow.jsx
│   ├── DecisionDetailModal.jsx
│   ├── ExportAuditModal.jsx
│   ├── VerifyLedgerModal.jsx
│   ├── TimelineView.jsx
│   ├── TimelineEntry.jsx
│   ├── AnalyticsView.jsx
│   └── ExportsView.jsx
├── hooks/
│   ├── useDecisions.js         # Fetch decisions
│   ├── useFilters.js           # Filter logic
│   └── useVerification.js      # Verification logic
└── utils/
    ├── formatters.js           # Date, number formatting
    └── validators.js           # Data validation
```

### State Management

**Component State** (useState):
- Active tab
- Selected decision (for modal)
- Modal open/close states
- Filter values
- Verification results

**Server State** (React Query recommended):
- Decisions list
- Stats data
- Exports list
- Verification status

**URL State** (query params):
- Active tab (`?tab=ledger`)
- Filters (`?risk=high&outcome=escalated`)
- Page number (`?page=2`)

### Data Fetching Pattern

```javascript
// Example using React Query
const useDecisions = (filters) => {
  return useQuery({
    queryKey: ['decisions', filters],
    queryFn: () => fetchDecisions(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false
  });
};

// Usage in component
const { data, isLoading, error } = useDecisions(filters);
```

### Error Handling

**API Errors**:
- Network error: Show alert with retry button
- 404: "No decisions found" empty state
- 500: "Server error" alert with support contact
- Timeout: "Request timed out" alert with retry

**Client Errors**:
- Invalid date range: Inline validation error
- Missing required field: Form validation
- Browser not supported: Banner at top

### Security Considerations

**Data Protection**:
- Signatures shown but not editable
- Download requires authentication
- Rate limiting on export generation
- Audit trail of who viewed what (optional)

**XSS Prevention**:
- All user input sanitized
- React automatically escapes JSX
- No dangerouslySetInnerHTML usage
- Content Security Policy headers

### Testing Requirements

**Unit Tests**:
- Filter logic (all combinations)
- Date formatting
- Risk level badge selection
- Outcome badge selection

**Integration Tests**:
- Filter + table interaction
- Modal open/close
- Tab switching
- Export generation flow

**E2E Tests**:
- Complete audit flow (view → filter → detail → export)
- Verification flow
- Error states

**Accessibility Tests**:
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
- Focus management

---

## Changelog

### Version 1.0.0 (2026-01-10)

**Initial Release**
- Complete audit dashboard interface
- Decision ledger with filtering
- Cryptographic verification
- Audit export functionality
- Timeline and analytics views
- Full accessibility support

---

## Support

For questions or implementation help:
- Review design system documentation
- Check component library code
- Reference this specification
- Contact design team

---

**Document Status**: Production Ready
**Approved By**: Design Team
**Implementation Ready**: Yes

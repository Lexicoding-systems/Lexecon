# Lexecon Frontend

Enterprise-grade React frontend for the Lexecon AI Governance Platform.

## What's Included

### Design System
- **Design Tokens** (`src/design-system/lexecon-design-tokens.js`): Complete token system (colors, typography, spacing, shadows, animations)
- **Component Library** (`src/design-system/lexecon-components.jsx`): 10 production-ready React components (Button, Input, Card, Badge, Alert, Modal, Table, Select, Checkbox, Tabs)
- **Documentation** (`/docs/design-system/`): Complete design system documentation and component specifications

### Audit Dashboard
- **Component** (`src/components/AuditDashboard.jsx`): Complete audit dashboard implementation
- **Documentation** (`/docs/audit-dashboard/`): Design specifications and integration guide

Features:
- Decision ledger with cryptographic verification
- Advanced filtering (risk, outcome, date range)
- Export audit packages (JSON, CSV, PDF)
- Analytics and insights
- Timeline view
- WCAG AA accessibility compliant

## Quick Start

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm start
```

Opens at http://localhost:3000

### Production Build

```bash
npm run build
```

Creates optimized build in `build/` directory.

## Project Structure

```
frontend/
├── public/
│   └── index.html           # HTML entry point
├── src/
│   ├── design-system/
│   │   ├── lexecon-design-tokens.js    # Design tokens
│   │   └── lexecon-components.jsx      # Component library
│   ├── components/
│   │   └── AuditDashboard.jsx          # Audit dashboard
│   ├── App.jsx              # Main app component
│   ├── index.js             # React entry point
│   └── index.css            # Global styles
├── package.json             # Dependencies
└── README.md                # This file
```

## Integration with Backend

### API Configuration

The audit dashboard expects these API endpoints:

```
GET  /api/v1/audit/decisions
GET  /api/v1/audit/decisions/:id
GET  /api/v1/audit/stats
POST /api/v1/audit/verify
POST /api/v1/audit/export
GET  /api/v1/audit/exports
GET  /api/v1/audit/exports/:id/download
```

### Environment Variables

Create `.env` file:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1
```

### Connecting to Lexecon Backend

Update API calls in `AuditDashboard.jsx` to use real endpoints:

```javascript
// Replace sample data with API calls
const fetchDecisions = async (filters) => {
  const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/audit/decisions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters)
  });
  return response.json();
};
```

## Component Usage

### Import Design System Components

```javascript
import { Button, Card, Badge, Alert, Modal, Table } from './design-system/lexecon-components';
import { tokens } from './design-system/lexecon-design-tokens';

function MyComponent() {
  return (
    <Card title="Example">
      <Badge variant="success">Active</Badge>
      <Button variant="primary">Click Me</Button>
    </Card>
  );
}
```

### Using Design Tokens

```javascript
import { tokens } from './design-system/lexecon-design-tokens';

const customStyle = {
  backgroundColor: tokens.colors.brand.primary[500],
  padding: `${tokens.spacing[3]} ${tokens.spacing[4]}`,
  borderRadius: tokens.border.radius.lg
};
```

## Documentation

- **Design System**: `/docs/design-system/README.md`
- **Audit Dashboard**: `/docs/audit-dashboard/README.md`
- **Component Guide**: `/docs/design-system/lexecon-component-guide.md`
- **Design Tokens**: `/docs/design-system/lexecon-design-tokens.js`

## Deployment

### Build for Production

```bash
npm run build
```

### Serve Static Build

```bash
# Using Python (from Lexecon root)
cd frontend/build
python -m http.server 3000

# Using Node.js serve
npx serve -s build -p 3000
```

### Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari: iOS 14+

## Accessibility

All components are WCAG AA compliant with:
- Keyboard navigation
- Screen reader support
- High color contrast (4.5:1 minimum)
- Focus indicators
- ARIA labels and roles

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Score: 90+

## Next Steps

1. **Connect to Backend**: Update API calls to use real Lexecon endpoints
2. **Add Authentication**: Integrate with Lexecon auth system
3. **Add More Features**: Policy management, decision workflows, compliance reporting
4. **Customize Theme**: Modify design tokens for your brand

## License

Proprietary - Lexecon Enterprise AI Governance Platform

© 2026 Lexecon. All rights reserved.

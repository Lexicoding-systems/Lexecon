/**
 * Lexecon Audit Dashboard
 *
 * Complete audit trail interface for compliance officers and auditors.
 * Displays tamper-evident decision ledger with cryptographic verification.
 *
 * Version: 1.0.0
 * Last Updated: 2026-01-10
 */

import React, { useState, useEffect } from 'react';
import {
  Button,
  Input,
  Card,
  Badge,
  Alert,
  Modal,
  Table,
  Select,
  Checkbox,
  Tabs
} from '../lexecon-design-system-production-011026/lexecon-components';
import { tokens } from '../lexecon-design-system-production-011026/lexecon-design-tokens';

// ============================================================================
// MAIN AUDIT DASHBOARD COMPONENT
// ============================================================================

export const AuditDashboard = () => {
  const [activeTab, setActiveTab] = useState('ledger');
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    riskLevel: 'all',
    outcome: 'all',
    dateRange: '7days',
    verified: false
  });

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Page Header */}
      <AuditDashboardHeader
        onExport={() => setShowExportModal(true)}
        onVerify={() => setShowVerifyModal(true)}
      />

      {/* Main Content */}
      <div className="max-w-[1440px] mx-auto px-8 py-6">
        {/* Stats Cards */}
        <AuditStatsGrid />

        {/* Tabs Navigation */}
        <div className="mt-8">
          <Tabs
            tabs={[
              { id: 'ledger', label: 'Decision Ledger' },
              { id: 'timeline', label: 'Timeline View' },
              { id: 'analytics', label: 'Analytics' },
              { id: 'exports', label: 'Audit Exports' }
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
            variant="line"
          />
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'ledger' && (
            <DecisionLedgerView
              filters={filters}
              onFiltersChange={setFilters}
              onSelectDecision={setSelectedDecision}
            />
          )}
          {activeTab === 'timeline' && (
            <TimelineView filters={filters} />
          )}
          {activeTab === 'analytics' && (
            <AnalyticsView />
          )}
          {activeTab === 'exports' && (
            <ExportsView />
          )}
        </div>
      </div>

      {/* Modals */}
      <DecisionDetailModal
        decision={selectedDecision}
        isOpen={!!selectedDecision}
        onClose={() => setSelectedDecision(null)}
      />

      <ExportAuditModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
      />

      <VerifyLedgerModal
        isOpen={showVerifyModal}
        onClose={() => setShowVerifyModal(false)}
      />
    </div>
  );
};

// ============================================================================
// HEADER COMPONENT
// ============================================================================

const AuditDashboardHeader = ({ onExport, onVerify }) => (
  <div
    className="border-b"
    style={{
      backgroundColor: tokens.colors.neutral[0],
      borderColor: tokens.colors.neutral[200]
    }}
  >
    <div className="max-w-[1440px] mx-auto px-8 py-6">
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-3xl font-bold"
            style={{ color: tokens.colors.neutral[900] }}
          >
            Audit Dashboard
          </h1>
          <p
            className="mt-1 text-base"
            style={{ color: tokens.colors.neutral[600] }}
          >
            Tamper-evident decision ledger with cryptographic verification
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={onVerify}>
            <span className="mr-2">🔐</span>
            Verify Integrity
          </Button>
          <Button variant="primary" onClick={onExport}>
            <span className="mr-2">📥</span>
            Export Audit
          </Button>
        </div>
      </div>
    </div>
  </div>
);

// ============================================================================
// STATS GRID COMPONENT
// ============================================================================

const AuditStatsGrid = () => {
  const stats = [
    {
      label: 'Total Decisions',
      value: '2,847',
      change: '+12% from last week',
      changeType: 'positive',
      icon: '📊'
    },
    {
      label: 'Verified Entries',
      value: '2,847',
      change: '100% integrity',
      changeType: 'positive',
      icon: '✓'
    },
    {
      label: 'Escalations',
      value: '23',
      change: '-8% from last week',
      changeType: 'positive',
      icon: '⚠'
    },
    {
      label: 'High Risk',
      value: '156',
      change: 'Requiring oversight',
      changeType: 'neutral',
      icon: '🎯'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
};

const StatCard = ({ label, value, change, changeType, icon }) => (
  <Card padding="default" variant="elevated">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <p
          className="text-sm font-medium"
          style={{ color: tokens.colors.neutral[600] }}
        >
          {label}
        </p>
        <p
          className="mt-2 text-3xl font-bold"
          style={{ color: tokens.colors.neutral[900] }}
        >
          {value}
        </p>
        <p
          className="mt-1 text-sm"
          style={{
            color:
              changeType === 'positive'
                ? tokens.colors.semantic.success[600]
                : changeType === 'negative'
                ? tokens.colors.semantic.error[600]
                : tokens.colors.neutral[500]
          }}
        >
          {change}
        </p>
      </div>
      <div className="text-3xl">{icon}</div>
    </div>
  </Card>
);

// ============================================================================
// DECISION LEDGER VIEW
// ============================================================================

const DecisionLedgerView = ({ filters, onFiltersChange, onSelectDecision }) => {
  // Sample data - in production, this would come from API
  const decisions = [
    {
      id: 'DEC-2847',
      timestamp: '2026-01-10 14:32:15 UTC',
      action: 'Model inference request approved',
      actor: 'system@lexecon.ai',
      riskLevel: 'low',
      outcome: 'approved',
      signature: 'a4f3e8d2c9b1a7f5e3d1c9a7b5f3e1d9c7a5b3f1e9d7c5a3b1f9e7d5c3a1b9f7',
      policyVersion: 'v2.1.0',
      verified: true
    },
    {
      id: 'DEC-2846',
      timestamp: '2026-01-10 14:28:03 UTC',
      action: 'High-risk decision escalated to human oversight',
      actor: 'ai-agent-prod-01',
      riskLevel: 'high',
      outcome: 'escalated',
      signature: 'b5g4f9e3d0c2b8a6f4e2d0c8b6a4f2e0d8c6a4b2f0e8d6c4a2b0f8e6d4c2a0b8',
      policyVersion: 'v2.1.0',
      verified: true
    },
    {
      id: 'DEC-2845',
      timestamp: '2026-01-10 14:15:47 UTC',
      action: 'Request denied - policy violation detected',
      actor: 'ai-agent-prod-02',
      riskLevel: 'critical',
      outcome: 'denied',
      signature: 'c6h5g0f4e1d3c9b7a5f3e1d9c7b5a3f1e9d7c5a3b1f9e7d5c3a1b9f7e5d3c1a9',
      policyVersion: 'v2.1.0',
      verified: true
    },
    {
      id: 'DEC-2844',
      timestamp: '2026-01-10 13:58:22 UTC',
      action: 'Model inference request approved',
      actor: 'system@lexecon.ai',
      riskLevel: 'minimal',
      outcome: 'approved',
      signature: 'd7i6h1g5f2e4d0c8b6a4f2e0d8c6a4b2f0e8d6c4a2b0f8e6d4c2a0b8f6e4d2c0',
      policyVersion: 'v2.1.0',
      verified: true
    },
    {
      id: 'DEC-2843',
      timestamp: '2026-01-10 13:42:09 UTC',
      action: 'Override approved by compliance officer',
      actor: 'jane.smith@company.com',
      riskLevel: 'medium',
      outcome: 'override',
      signature: 'e8j7i2h6g3f5e1d9c7b5a3f1e9d7c5a3b1f9e7d5c3a1b9f7e5d3c1a9f7e5d3c1',
      policyVersion: 'v2.0.8',
      verified: true
    }
  ];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <FiltersBar filters={filters} onFiltersChange={onFiltersChange} />

      {/* Alert for verification status */}
      <Alert variant="success" icon={true}>
        <strong>Ledger Verified</strong> - All {decisions.length} entries have valid cryptographic signatures and hash chains.
      </Alert>

      {/* Decision Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead
              style={{
                backgroundColor: tokens.colors.neutral[50],
                borderBottom: `2px solid ${tokens.colors.neutral[200]}`
              }}
            >
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Decision ID
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Timestamp
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Action
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Risk
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Outcome
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Verified
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody style={{ borderTop: `1px solid ${tokens.colors.neutral[200]}` }}>
              {decisions.map((decision) => (
                <DecisionRow
                  key={decision.id}
                  decision={decision}
                  onClick={() => onSelectDecision(decision)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

// ============================================================================
// FILTERS BAR
// ============================================================================

const FiltersBar = ({ filters, onFiltersChange }) => (
  <Card padding="default">
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      <Input
        label="Search"
        placeholder="Search decisions..."
        value={filters.search}
        onChange={(e) =>
          onFiltersChange({ ...filters, search: e.target.value })
        }
      />

      <Select
        label="Risk Level"
        options={[
          { value: 'all', label: 'All Levels' },
          { value: 'minimal', label: 'Minimal' },
          { value: 'low', label: 'Low' },
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
          { value: 'critical', label: 'Critical' }
        ]}
        value={filters.riskLevel}
        onChange={(e) =>
          onFiltersChange({ ...filters, riskLevel: e.target.value })
        }
      />

      <Select
        label="Outcome"
        options={[
          { value: 'all', label: 'All Outcomes' },
          { value: 'approved', label: 'Approved' },
          { value: 'denied', label: 'Denied' },
          { value: 'escalated', label: 'Escalated' },
          { value: 'override', label: 'Override' }
        ]}
        value={filters.outcome}
        onChange={(e) =>
          onFiltersChange({ ...filters, outcome: e.target.value })
        }
      />

      <Select
        label="Date Range"
        options={[
          { value: '24hours', label: 'Last 24 Hours' },
          { value: '7days', label: 'Last 7 Days' },
          { value: '30days', label: 'Last 30 Days' },
          { value: '90days', label: 'Last 90 Days' },
          { value: 'all', label: 'All Time' }
        ]}
        value={filters.dateRange}
        onChange={(e) =>
          onFiltersChange({ ...filters, dateRange: e.target.value })
        }
      />

      <div className="flex items-end">
        <Checkbox
          label="Verified only"
          checked={filters.verified}
          onChange={(e) =>
            onFiltersChange({ ...filters, verified: e.target.checked })
          }
        />
      </div>
    </div>
  </Card>
);

// ============================================================================
// DECISION ROW
// ============================================================================

const DecisionRow = ({ decision, onClick }) => {
  const riskVariants = {
    minimal: 'success',
    low: 'success',
    medium: 'warning',
    high: 'warning',
    critical: 'error'
  };

  const outcomeVariants = {
    approved: 'success',
    denied: 'error',
    escalated: 'warning',
    override: 'primary'
  };

  return (
    <tr
      className="border-b transition-colors cursor-pointer"
      style={{
        borderColor: tokens.colors.neutral[200]
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = tokens.colors.neutral[50];
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      <td className="px-6 py-4">
        <span className="font-mono text-sm font-medium" style={{ color: tokens.colors.brand.primary[600] }}>
          {decision.id}
        </span>
      </td>
      <td className="px-6 py-4">
        <span className="text-sm font-mono" style={{ color: tokens.colors.neutral[600] }}>
          {decision.timestamp}
        </span>
      </td>
      <td className="px-6 py-4">
        <span className="text-sm" style={{ color: tokens.colors.neutral[700] }}>
          {decision.action}
        </span>
        <br />
        <span className="text-xs" style={{ color: tokens.colors.neutral[500] }}>
          by {decision.actor}
        </span>
      </td>
      <td className="px-6 py-4">
        <Badge variant={riskVariants[decision.riskLevel]} size="sm">
          {decision.riskLevel.toUpperCase()}
        </Badge>
      </td>
      <td className="px-6 py-4">
        <Badge variant={outcomeVariants[decision.outcome]} size="sm" dot>
          {decision.outcome.toUpperCase()}
        </Badge>
      </td>
      <td className="px-6 py-4">
        {decision.verified ? (
          <span style={{ color: tokens.colors.semantic.success[600] }}>✓ Verified</span>
        ) : (
          <span style={{ color: tokens.colors.semantic.error[600] }}>✕ Invalid</span>
        )}
      </td>
      <td className="px-6 py-4">
        <Button variant="ghost" size="sm">
          View Details
        </Button>
      </td>
    </tr>
  );
};

// ============================================================================
// TIMELINE VIEW
// ============================================================================

const TimelineView = ({ filters }) => (
  <div className="space-y-6">
    <Alert variant="info">
      Timeline view shows decision flow in chronological order with visual connections.
    </Alert>

    <Card padding="default">
      <div className="space-y-6">
        {/* Sample timeline entries */}
        <TimelineEntry
          time="14:32:15"
          title="Model Inference Approved"
          description="Low-risk decision automatically approved by policy engine"
          type="success"
          signature="a4f3e8d2..."
        />
        <TimelineEntry
          time="14:28:03"
          title="Decision Escalated"
          description="High-risk score triggered human oversight workflow"
          type="warning"
          signature="b5g4f9e3..."
        />
        <TimelineEntry
          time="14:15:47"
          title="Request Denied"
          description="Policy violation detected - insufficient permissions"
          type="error"
          signature="c6h5g0f4..."
        />
      </div>
    </Card>
  </div>
);

const TimelineEntry = ({ time, title, description, type, signature }) => {
  const colors = {
    success: tokens.colors.semantic.success[500],
    warning: tokens.colors.semantic.warning[500],
    error: tokens.colors.semantic.error[500]
  };

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: colors[type] }}
        />
        <div
          className="w-0.5 flex-1 mt-2"
          style={{ backgroundColor: tokens.colors.neutral[200] }}
        />
      </div>
      <div className="flex-1 pb-8">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-sm font-mono" style={{ color: tokens.colors.neutral[500] }}>
              {time}
            </span>
            <h4 className="text-lg font-semibold mt-1" style={{ color: tokens.colors.neutral[800] }}>
              {title}
            </h4>
            <p className="text-sm mt-1" style={{ color: tokens.colors.neutral[600] }}>
              {description}
            </p>
            <code className="text-xs font-mono mt-2 block" style={{ color: tokens.colors.neutral[400] }}>
              Signature: {signature}
            </code>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// ANALYTICS VIEW
// ============================================================================

const AnalyticsView = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <Card title="Decision Outcomes" subtitle="Last 30 days">
      <div className="h-64 flex items-center justify-center" style={{ color: tokens.colors.neutral[400] }}>
        📊 Chart: Pie chart showing approved, denied, escalated, override percentages
      </div>
    </Card>

    <Card title="Risk Distribution" subtitle="Current period">
      <div className="h-64 flex items-center justify-center" style={{ color: tokens.colors.neutral[400] }}>
        📈 Chart: Bar chart showing risk level distribution
      </div>
    </Card>

    <Card title="Decision Volume" subtitle="Trend over time">
      <div className="h-64 flex items-center justify-center" style={{ color: tokens.colors.neutral[400] }}>
        📉 Chart: Line chart showing decision volume over time
      </div>
    </Card>

    <Card title="Top Policies" subtitle="Most frequently triggered">
      <div className="space-y-3">
        <PolicyUsageItem policy="Data Access Control" count={847} percentage={29.7} />
        <PolicyUsageItem policy="Model Risk Assessment" count={623} percentage={21.9} />
        <PolicyUsageItem policy="PII Protection" count={512} percentage={18.0} />
        <PolicyUsageItem policy="Escalation Threshold" count={398} percentage={14.0} />
        <PolicyUsageItem policy="Override Authorization" count={467} percentage={16.4} />
      </div>
    </Card>
  </div>
);

const PolicyUsageItem = ({ policy, count, percentage }) => (
  <div>
    <div className="flex justify-between items-center mb-1">
      <span className="text-sm font-medium" style={{ color: tokens.colors.neutral[700] }}>
        {policy}
      </span>
      <span className="text-sm font-mono" style={{ color: tokens.colors.neutral[600] }}>
        {count} ({percentage}%)
      </span>
    </div>
    <div
      className="h-2 rounded-full"
      style={{ backgroundColor: tokens.colors.neutral[200] }}
    >
      <div
        className="h-2 rounded-full"
        style={{
          width: `${percentage}%`,
          backgroundColor: tokens.colors.brand.primary[500]
        }}
      />
    </div>
  </div>
);

// ============================================================================
// EXPORTS VIEW
// ============================================================================

const ExportsView = () => {
  const exports = [
    {
      id: 'EXP-001',
      createdAt: '2026-01-09 10:23:00 UTC',
      dateRange: '2025-12-01 to 2026-01-01',
      format: 'JSON',
      size: '2.4 MB',
      status: 'ready',
      entries: 1247
    },
    {
      id: 'EXP-002',
      createdAt: '2026-01-05 14:15:00 UTC',
      dateRange: '2025-11-01 to 2025-12-01',
      format: 'CSV',
      size: '1.8 MB',
      status: 'ready',
      entries: 923
    },
    {
      id: 'EXP-003',
      createdAt: '2026-01-10 09:00:00 UTC',
      dateRange: '2026-01-01 to 2026-01-10',
      format: 'JSON',
      size: '892 KB',
      status: 'processing',
      entries: 421
    }
  ];

  return (
    <div className="space-y-6">
      <Alert variant="info">
        Audit exports are deterministic and cryptographically signed packages suitable for regulatory submissions.
      </Alert>

      <Card padding="none">
        <table className="w-full">
          <thead style={{ backgroundColor: tokens.colors.neutral[50] }}>
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Export ID
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Date Range
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Format
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Entries
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Size
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Status
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: tokens.colors.neutral[700] }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {exports.map((exp) => (
              <tr
                key={exp.id}
                className="border-b"
                style={{ borderColor: tokens.colors.neutral[200] }}
              >
                <td className="px-6 py-4">
                  <span className="font-mono text-sm" style={{ color: tokens.colors.brand.primary[600] }}>
                    {exp.id}
                  </span>
                  <br />
                  <span className="text-xs" style={{ color: tokens.colors.neutral[500] }}>
                    {exp.createdAt}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm" style={{ color: tokens.colors.neutral[600] }}>
                  {exp.dateRange}
                </td>
                <td className="px-6 py-4">
                  <Badge variant="default" size="sm">{exp.format}</Badge>
                </td>
                <td className="px-6 py-4 text-sm font-mono" style={{ color: tokens.colors.neutral[600] }}>
                  {exp.entries.toLocaleString()}
                </td>
                <td className="px-6 py-4 text-sm font-mono" style={{ color: tokens.colors.neutral[600] }}>
                  {exp.size}
                </td>
                <td className="px-6 py-4">
                  {exp.status === 'ready' ? (
                    <Badge variant="success" size="sm" dot>READY</Badge>
                  ) : (
                    <Badge variant="warning" size="sm">PROCESSING</Badge>
                  )}
                </td>
                <td className="px-6 py-4">
                  {exp.status === 'ready' ? (
                    <Button variant="ghost" size="sm">Download</Button>
                  ) : (
                    <span className="text-sm" style={{ color: tokens.colors.neutral[400] }}>Processing...</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

// ============================================================================
// DECISION DETAIL MODAL
// ============================================================================

const DecisionDetailModal = ({ decision, isOpen, onClose }) => {
  if (!decision) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Decision Details: ${decision.id}`}
      size="lg"
      footer={
        <div className="flex justify-between w-full">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <div className="flex gap-2">
            <Button variant="secondary">
              Download Evidence
            </Button>
            <Button variant="primary">
              Verify Signature
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Decision Overview */}
        <div>
          <h4 className="text-sm font-semibold mb-3" style={{ color: tokens.colors.neutral[700] }}>
            Decision Overview
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <DetailField label="Decision ID" value={decision.id} mono />
            <DetailField label="Timestamp" value={decision.timestamp} mono />
            <DetailField
              label="Risk Level"
              value={<Badge variant="warning">{decision.riskLevel.toUpperCase()}</Badge>}
            />
            <DetailField
              label="Outcome"
              value={<Badge variant="success" dot>{decision.outcome.toUpperCase()}</Badge>}
            />
            <DetailField label="Actor" value={decision.actor} />
            <DetailField label="Policy Version" value={decision.policyVersion} mono />
          </div>
        </div>

        {/* Action Details */}
        <div>
          <h4 className="text-sm font-semibold mb-2" style={{ color: tokens.colors.neutral[700] }}>
            Action
          </h4>
          <p className="text-sm" style={{ color: tokens.colors.neutral[600] }}>
            {decision.action}
          </p>
        </div>

        {/* Cryptographic Verification */}
        <div>
          <h4 className="text-sm font-semibold mb-3" style={{ color: tokens.colors.neutral[700] }}>
            Cryptographic Verification
          </h4>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium" style={{ color: tokens.colors.neutral[600] }}>
                Ed25519 Signature
              </label>
              <code
                className="block mt-1 p-3 rounded text-xs font-mono break-all"
                style={{
                  backgroundColor: tokens.colors.neutral[50],
                  color: tokens.colors.neutral[700]
                }}
              >
                {decision.signature}
              </code>
            </div>
            <div className="flex items-center gap-2">
              <span style={{ color: tokens.colors.semantic.success[600], fontSize: '20px' }}>✓</span>
              <span className="text-sm" style={{ color: tokens.colors.semantic.success[700] }}>
                Signature verified successfully
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span style={{ color: tokens.colors.semantic.success[600], fontSize: '20px' }}>✓</span>
              <span className="text-sm" style={{ color: tokens.colors.semantic.success[700] }}>
                Hash chain integrity confirmed
              </span>
            </div>
          </div>
        </div>

        {/* Policy Context */}
        <div>
          <h4 className="text-sm font-semibold mb-2" style={{ color: tokens.colors.neutral[700] }}>
            Applied Policies
          </h4>
          <div className="space-y-2">
            <PolicyTag name="Data Access Control" result="passed" />
            <PolicyTag name="Risk Assessment" result="passed" />
            <PolicyTag name="Compliance Check" result="passed" />
          </div>
        </div>
      </div>
    </Modal>
  );
};

const DetailField = ({ label, value, mono = false }) => (
  <div>
    <label className="text-xs font-medium" style={{ color: tokens.colors.neutral[600] }}>
      {label}
    </label>
    <div className={`mt-1 text-sm ${mono ? 'font-mono' : ''}`} style={{ color: tokens.colors.neutral[800] }}>
      {value}
    </div>
  </div>
);

const PolicyTag = ({ name, result }) => (
  <div
    className="flex items-center justify-between p-2 rounded"
    style={{ backgroundColor: tokens.colors.neutral[50] }}
  >
    <span className="text-sm" style={{ color: tokens.colors.neutral[700] }}>{name}</span>
    {result === 'passed' ? (
      <Badge variant="success" size="sm">Passed</Badge>
    ) : (
      <Badge variant="error" size="sm">Failed</Badge>
    )}
  </div>
);

// ============================================================================
// EXPORT AUDIT MODAL
// ============================================================================

const ExportAuditModal = ({ isOpen, onClose }) => {
  const [exportConfig, setExportConfig] = useState({
    format: 'json',
    dateFrom: '',
    dateTo: '',
    includeSignatures: true,
    includeEvidence: false
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Export Audit Package"
      size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary">
            Generate Export
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Alert variant="info">
          Audit exports are deterministic and cryptographically signed for regulatory compliance.
        </Alert>

        <Select
          label="Export Format"
          options={[
            { value: 'json', label: 'JSON (Developer-friendly)' },
            { value: 'csv', label: 'CSV (Spreadsheet-friendly)' },
            { value: 'pdf', label: 'PDF (Human-readable report)' }
          ]}
          value={exportConfig.format}
          onChange={(e) => setExportConfig({ ...exportConfig, format: e.target.value })}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="From Date"
            type="date"
            value={exportConfig.dateFrom}
            onChange={(e) => setExportConfig({ ...exportConfig, dateFrom: e.target.value })}
          />
          <Input
            label="To Date"
            type="date"
            value={exportConfig.dateTo}
            onChange={(e) => setExportConfig({ ...exportConfig, dateTo: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Checkbox
            label="Include cryptographic signatures"
            checked={exportConfig.includeSignatures}
            onChange={(e) => setExportConfig({ ...exportConfig, includeSignatures: e.target.checked })}
          />
          <Checkbox
            label="Include evidence artifacts"
            checked={exportConfig.includeEvidence}
            onChange={(e) => setExportConfig({ ...exportConfig, includeEvidence: e.target.checked })}
          />
        </div>
      </div>
    </Modal>
  );
};

// ============================================================================
// VERIFY LEDGER MODAL
// ============================================================================

const VerifyLedgerModal = ({ isOpen, onClose }) => {
  const [verifying, setVerifying] = useState(false);
  const [verificationResults, setVerificationResults] = useState(null);

  const handleVerify = () => {
    setVerifying(true);
    // Simulate verification
    setTimeout(() => {
      setVerificationResults({
        totalEntries: 2847,
        verified: 2847,
        failed: 0,
        chainIntegrity: true,
        signatureValidity: true
      });
      setVerifying(false);
    }, 2000);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Verify Ledger Integrity"
      size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button
            variant="primary"
            onClick={handleVerify}
            loading={verifying}
            disabled={verifying}
          >
            {verifying ? 'Verifying...' : 'Start Verification'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Alert variant="info">
          Cryptographic verification checks Ed25519 signatures and hash chain integrity for all ledger entries.
        </Alert>

        {!verificationResults && !verifying && (
          <p className="text-sm" style={{ color: tokens.colors.neutral[600] }}>
            Click "Start Verification" to validate all ledger entries and hash chains.
          </p>
        )}

        {verifying && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🔐</div>
            <p className="text-sm" style={{ color: tokens.colors.neutral[600] }}>
              Verifying cryptographic signatures...
            </p>
          </div>
        )}

        {verificationResults && (
          <div className="space-y-4">
            <Alert variant="success" title="Verification Complete">
              All ledger entries have been successfully verified.
            </Alert>

            <div className="space-y-3">
              <VerificationItem
                label="Total Entries"
                value={verificationResults.totalEntries.toLocaleString()}
                status="info"
              />
              <VerificationItem
                label="Verified Entries"
                value={verificationResults.verified.toLocaleString()}
                status="success"
              />
              <VerificationItem
                label="Failed Entries"
                value={verificationResults.failed}
                status={verificationResults.failed === 0 ? 'success' : 'error'}
              />
              <VerificationItem
                label="Hash Chain Integrity"
                value={verificationResults.chainIntegrity ? 'Valid' : 'Invalid'}
                status={verificationResults.chainIntegrity ? 'success' : 'error'}
              />
              <VerificationItem
                label="Signature Validity"
                value={verificationResults.signatureValidity ? 'Valid' : 'Invalid'}
                status={verificationResults.signatureValidity ? 'success' : 'error'}
              />
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

const VerificationItem = ({ label, value, status }) => {
  const colors = {
    success: tokens.colors.semantic.success[600],
    error: tokens.colors.semantic.error[600],
    info: tokens.colors.neutral[600]
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm" style={{ color: tokens.colors.neutral[700] }}>
        {label}
      </span>
      <span className="font-semibold" style={{ color: colors[status] }}>
        {value}
      </span>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default AuditDashboard;

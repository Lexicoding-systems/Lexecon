"""
Audit Export Service - Comprehensive governance data export pipeline.

Provides regulatory-ready audit packages that integrate:
- Risk assessments (Phase 1)
- Escalations (Phase 2)
- Overrides (Phase 3)
- Evidence artifacts (Phase 4)
- Compliance mappings (Phase 7)
- Decision logs
- Cryptographic verification
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import json
import csv
import io
import uuid
import hashlib


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"


class ExportScope(Enum):
    """Scope of data to export."""
    ALL = "all"
    RISK_ONLY = "risk_only"
    ESCALATION_ONLY = "escalation_only"
    OVERRIDE_ONLY = "override_only"
    EVIDENCE_ONLY = "evidence_only"
    COMPLIANCE_ONLY = "compliance_only"
    DECISION_LOG_ONLY = "decision_log_only"


class ExportStatus(Enum):
    """Status of export operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExportRequest:
    """Request for audit export."""
    export_id: str
    requester: str
    purpose: str
    scope: ExportScope
    format: ExportFormat
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_deleted: bool = False
    include_signatures: bool = True
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ExportStatus = ExportStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExportPackage:
    """Complete audit export package."""
    export_id: str
    request: ExportRequest
    generated_at: datetime
    data: Dict[str, Any]
    format: ExportFormat
    content: str
    checksum: str
    signature: Optional[str] = None
    size_bytes: int = 0
    record_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExportStatistics:
    """Statistics about exported data."""
    total_risks: int = 0
    total_escalations: int = 0
    total_overrides: int = 0
    total_evidence: int = 0
    total_mappings: int = 0
    total_decisions: int = 0
    total_controls: int = 0
    frameworks_covered: List[str] = field(default_factory=list)
    date_range: Optional[Dict[str, str]] = None
    export_size_bytes: int = 0


class AuditExportService:
    """
    Service for exporting comprehensive governance audit data.

    Integrates data from all governance services and generates
    regulatory-ready audit packages with cryptographic verification.
    """

    def __init__(self):
        """Initialize audit export service."""
        self._exports: Dict[str, ExportPackage] = {}
        self._requests: Dict[str, ExportRequest] = {}

    def create_export_request(
        self,
        requester: str,
        purpose: str,
        scope: ExportScope = ExportScope.ALL,
        format: ExportFormat = ExportFormat.JSON,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExportRequest:
        """
        Create a new export request.

        Args:
            requester: User or system requesting export
            purpose: Purpose of the export
            scope: Scope of data to export
            format: Output format
            start_date: Optional start date filter
            end_date: Optional end date filter
            include_deleted: Whether to include deleted records
            metadata: Optional additional metadata

        Returns:
            ExportRequest object
        """
        export_id = f"exp_{uuid.uuid4().hex[:12]}"

        request = ExportRequest(
            export_id=export_id,
            requester=requester,
            purpose=purpose,
            scope=scope,
            format=format,
            start_date=start_date,
            end_date=end_date,
            include_deleted=include_deleted,
            metadata=metadata
        )

        self._requests[export_id] = request
        return request

    def generate_export(
        self,
        request: ExportRequest,
        risk_service=None,
        escalation_service=None,
        override_service=None,
        evidence_service=None,
        compliance_service=None,
        ledger=None
    ) -> ExportPackage:
        """
        Generate audit export package from governance services.

        Args:
            request: Export request
            risk_service: Risk assessment service
            escalation_service: Escalation service
            override_service: Override service
            evidence_service: Evidence service
            compliance_service: Compliance mapping service
            ledger: Decision ledger

        Returns:
            ExportPackage with complete audit data
        """
        request.status = ExportStatus.IN_PROGRESS

        # Collect data from all services
        data = {
            "export_metadata": {
                "export_id": request.export_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "requester": request.requester,
                "purpose": request.purpose,
                "scope": request.scope.value,
                "format": request.format.value,
                "date_range": {
                    "start": request.start_date.isoformat() if request.start_date else None,
                    "end": request.end_date.isoformat() if request.end_date else None,
                }
            }
        }

        # Collect risk assessments
        if request.scope in [ExportScope.ALL, ExportScope.RISK_ONLY] and risk_service:
            risks = self._collect_risks(risk_service, request.start_date, request.end_date)
            data["risks"] = risks

        # Collect escalations
        if request.scope in [ExportScope.ALL, ExportScope.ESCALATION_ONLY] and escalation_service:
            escalations = self._collect_escalations(escalation_service, request.start_date, request.end_date)
            data["escalations"] = escalations

        # Collect overrides
        if request.scope in [ExportScope.ALL, ExportScope.OVERRIDE_ONLY] and override_service:
            overrides = self._collect_overrides(override_service, request.start_date, request.end_date)
            data["overrides"] = overrides

        # Collect evidence artifacts
        if request.scope in [ExportScope.ALL, ExportScope.EVIDENCE_ONLY] and evidence_service:
            evidence = self._collect_evidence(evidence_service, request.start_date, request.end_date)
            data["evidence"] = evidence

        # Collect compliance mappings
        if request.scope in [ExportScope.ALL, ExportScope.COMPLIANCE_ONLY] and compliance_service:
            compliance = self._collect_compliance(compliance_service)
            data["compliance"] = compliance

        # Collect decision log
        if request.scope in [ExportScope.ALL, ExportScope.DECISION_LOG_ONLY] and ledger:
            decisions = self._collect_decisions(ledger, request.start_date, request.end_date)
            data["decisions"] = decisions

        # Calculate statistics
        stats = self._calculate_statistics(data)
        data["statistics"] = stats

        # Format the data
        content = self._format_data(data, request.format)

        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()

        # Create export package
        package = ExportPackage(
            export_id=request.export_id,
            request=request,
            generated_at=datetime.now(timezone.utc),
            data=data,
            format=request.format,
            content=content,
            checksum=checksum,
            size_bytes=len(content.encode()),
            record_count=self._count_records(data),
            metadata=request.metadata
        )

        request.status = ExportStatus.COMPLETED
        self._exports[request.export_id] = package

        return package

    def _collect_risks(
        self,
        risk_service,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Collect risk assessments from service."""
        risks = []

        # Get all risks from service
        all_risks = risk_service.list_risks() if hasattr(risk_service, 'list_risks') else []

        for risk in all_risks:
            # Filter by date if specified
            if start_date and risk.timestamp < start_date:
                continue
            if end_date and risk.timestamp > end_date:
                continue

            risks.append({
                "risk_id": risk.risk_id,
                "decision_id": risk.decision_id,
                "overall_score": risk.overall_score,
                "risk_level": risk.risk_level.value,
                "dimensions": {
                    "security": risk.dimensions.security,
                    "privacy": risk.dimensions.privacy,
                    "compliance": risk.dimensions.compliance,
                    "operational": risk.dimensions.operational,
                    "reputational": risk.dimensions.reputational,
                    "financial": risk.dimensions.financial,
                },
                "timestamp": risk.timestamp.isoformat(),
                "factors": risk.factors,
            })

        return risks

    def _collect_escalations(
        self,
        escalation_service,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Collect escalations from service."""
        escalations = []

        # Get all escalations
        all_escalations = escalation_service.list_escalations() if hasattr(escalation_service, 'list_escalations') else []

        for esc in all_escalations:
            # Filter by date
            if start_date and esc.created_at < start_date:
                continue
            if end_date and esc.created_at > end_date:
                continue

            esc_data = {
                "escalation_id": esc.escalation_id,
                "decision_id": esc.decision_id,
                "status": esc.status.value,
                "priority": esc.priority.value,
                "trigger": esc.trigger,
                "escalated_to": esc.escalated_to,
                "created_at": esc.created_at.isoformat(),
            }

            # Add optional fields if they exist
            if hasattr(esc, 'sla_deadline') and esc.sla_deadline:
                esc_data["sla_deadline"] = esc.sla_deadline.isoformat()
            if hasattr(esc, 'resolved_at') and esc.resolved_at:
                esc_data["resolved_at"] = esc.resolved_at.isoformat()
            if hasattr(esc, 'resolved_by'):
                esc_data["resolved_by"] = esc.resolved_by
            if hasattr(esc, 'outcome'):
                esc_data["outcome"] = esc.outcome

            escalations.append(esc_data)

        return escalations

    def _collect_overrides(
        self,
        override_service,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Collect overrides from service."""
        overrides = []

        # Get all overrides
        all_overrides = override_service.list_overrides() if hasattr(override_service, 'list_overrides') else []

        for ovr in all_overrides:
            # Filter by date
            if start_date and ovr.timestamp < start_date:
                continue
            if end_date and ovr.timestamp > end_date:
                continue

            overrides.append({
                "override_id": ovr.override_id,
                "decision_id": ovr.decision_id,
                "override_type": ovr.override_type.value,
                "authorized_by": ovr.authorized_by,
                "justification": ovr.justification,
                "timestamp": ovr.timestamp.isoformat(),
                "original_outcome": ovr.original_outcome.value if ovr.original_outcome else None,
                "new_outcome": ovr.new_outcome.value if ovr.new_outcome else None,
                "expires_at": ovr.expires_at.isoformat() if ovr.expires_at else None,
                "evidence_ids": ovr.evidence_ids,
            })

        return overrides

    def _collect_evidence(
        self,
        evidence_service,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Collect evidence artifacts from service."""
        evidence = []

        # Get all artifacts
        all_artifacts = evidence_service.list_artifacts() if hasattr(evidence_service, 'list_artifacts') else []

        for artifact in all_artifacts:
            # Filter by date
            if start_date and artifact.created_at < start_date:
                continue
            if end_date and artifact.created_at > end_date:
                continue

            evidence.append({
                "artifact_id": artifact.artifact_id,
                "artifact_type": artifact.artifact_type.value,
                "sha256_hash": artifact.sha256_hash,
                "created_at": artifact.created_at.isoformat(),
                "source": artifact.source,
                "content_type": artifact.content_type,
                "size_bytes": artifact.size_bytes,
                "related_decision_ids": artifact.related_decision_ids,
                "related_control_ids": artifact.related_control_ids,
                "retention_until": artifact.retention_until.isoformat() if artifact.retention_until else None,
                "is_immutable": artifact.is_immutable,
                "has_signature": artifact.digital_signature is not None,
            })

        return evidence

    def _collect_compliance(self, compliance_service) -> Dict[str, Any]:
        """Collect compliance mappings from service."""
        compliance_data = {
            "statistics": compliance_service.get_statistics(),
            "frameworks": {}
        }

        # Get data for each framework
        from lexecon.compliance_mapping.service import RegulatoryFramework

        for framework in [RegulatoryFramework.SOC2, RegulatoryFramework.ISO27001, RegulatoryFramework.GDPR]:
            controls = compliance_service.list_controls(framework)
            coverage = compliance_service.get_framework_coverage(framework)
            gaps = compliance_service.analyze_gaps(framework)

            compliance_data["frameworks"][framework.value] = {
                "controls": [
                    {
                        "control_id": c.control_id,
                        "title": c.title,
                        "category": c.category,
                        "status": c.status.value,
                        "last_verified": c.last_verified.isoformat() if c.last_verified else None,
                        "evidence_count": len(c.evidence_artifact_ids),
                    }
                    for c in controls
                ],
                "coverage": coverage,
                "gaps": gaps,
            }

        return compliance_data

    def _collect_decisions(
        self,
        ledger,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Collect decision log from ledger."""
        decisions = []

        # Get decision entries from ledger
        for entry in ledger.entries:
            if entry.event_type != "decision":
                continue

            # Parse timestamp
            try:
                entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                if entry_time.tzinfo is None:
                    entry_time = entry_time.replace(tzinfo=timezone.utc)
            except:
                continue

            # Filter by date
            if start_date and entry_time < start_date:
                continue
            if end_date and entry_time > end_date:
                continue

            decisions.append({
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp,
                "entry_hash": entry.entry_hash,
                "previous_hash": entry.previous_hash,
                "data": entry.data,
            })

        return decisions

    def _calculate_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from collected data."""
        stats = {
            "total_risks": len(data.get("risks", [])),
            "total_escalations": len(data.get("escalations", [])),
            "total_overrides": len(data.get("overrides", [])),
            "total_evidence": len(data.get("evidence", [])),
            "total_decisions": len(data.get("decisions", [])),
        }

        # Compliance statistics
        if "compliance" in data:
            compliance_stats = data["compliance"].get("statistics", {})
            stats["total_mappings"] = compliance_stats.get("total_mappings", 0)
            stats["total_controls"] = compliance_stats.get("total_controls", 0)
            stats["frameworks_covered"] = list(data["compliance"].get("frameworks", {}).keys())

        return stats

    def _count_records(self, data: Dict[str, Any]) -> int:
        """Count total records in export."""
        count = 0
        count += len(data.get("risks", []))
        count += len(data.get("escalations", []))
        count += len(data.get("overrides", []))
        count += len(data.get("evidence", []))
        count += len(data.get("decisions", []))
        return count

    def _format_data(self, data: Dict[str, Any], format: ExportFormat) -> str:
        """Format data according to requested format."""
        if format == ExportFormat.JSON:
            return self._format_json(data)
        elif format == ExportFormat.CSV:
            return self._format_csv(data)
        elif format == ExportFormat.MARKDOWN:
            return self._format_markdown(data)
        elif format == ExportFormat.HTML:
            return self._format_html(data)
        else:
            return json.dumps(data, indent=2, default=str)

    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)

    def _format_csv(self, data: Dict[str, Any]) -> str:
        """Format as CSV (multiple sections)."""
        output = io.StringIO()

        # Risks section
        if "risks" in data and data["risks"]:
            output.write("=== RISK ASSESSMENTS ===\n")
            writer = csv.DictWriter(
                output,
                fieldnames=["risk_id", "decision_id", "overall_score", "risk_level", "timestamp"]
            )
            writer.writeheader()
            for risk in data["risks"]:
                writer.writerow({
                    "risk_id": risk["risk_id"],
                    "decision_id": risk["decision_id"],
                    "overall_score": risk["overall_score"],
                    "risk_level": risk["risk_level"],
                    "timestamp": risk["timestamp"],
                })
            output.write("\n")

        # Escalations section
        if "escalations" in data and data["escalations"]:
            output.write("=== ESCALATIONS ===\n")
            writer = csv.DictWriter(
                output,
                fieldnames=["escalation_id", "decision_id", "status", "priority", "created_at"]
            )
            writer.writeheader()
            for esc in data["escalations"]:
                writer.writerow({
                    "escalation_id": esc["escalation_id"],
                    "decision_id": esc["decision_id"],
                    "status": esc["status"],
                    "priority": esc["priority"],
                    "created_at": esc["created_at"],
                })
            output.write("\n")

        # Overrides section
        if "overrides" in data and data["overrides"]:
            output.write("=== OVERRIDES ===\n")
            writer = csv.DictWriter(
                output,
                fieldnames=["override_id", "decision_id", "override_type", "authorized_by", "timestamp"]
            )
            writer.writeheader()
            for ovr in data["overrides"]:
                writer.writerow({
                    "override_id": ovr["override_id"],
                    "decision_id": ovr["decision_id"],
                    "override_type": ovr["override_type"],
                    "authorized_by": ovr["authorized_by"],
                    "timestamp": ovr["timestamp"],
                })
            output.write("\n")

        return output.getvalue()

    def _format_markdown(self, data: Dict[str, Any]) -> str:
        """Format as Markdown."""
        lines = []

        # Header
        lines.append("# Governance Audit Export")
        lines.append("")
        lines.append(f"**Export ID:** {data['export_metadata']['export_id']}")
        lines.append(f"**Generated:** {data['export_metadata']['generated_at']}")
        lines.append(f"**Requester:** {data['export_metadata']['requester']}")
        lines.append(f"**Purpose:** {data['export_metadata']['purpose']}")
        lines.append("")

        # Statistics
        if "statistics" in data:
            lines.append("## Summary Statistics")
            lines.append("")
            stats = data["statistics"]
            lines.append(f"- **Risk Assessments:** {stats.get('total_risks', 0)}")
            lines.append(f"- **Escalations:** {stats.get('total_escalations', 0)}")
            lines.append(f"- **Overrides:** {stats.get('total_overrides', 0)}")
            lines.append(f"- **Evidence Artifacts:** {stats.get('total_evidence', 0)}")
            lines.append(f"- **Decisions:** {stats.get('total_decisions', 0)}")
            lines.append(f"- **Compliance Controls:** {stats.get('total_controls', 0)}")
            lines.append("")

        # Risks
        if "risks" in data and data["risks"]:
            lines.append("## Risk Assessments")
            lines.append("")
            for risk in data["risks"][:10]:  # Limit to first 10
                lines.append(f"### {risk['risk_id']}")
                lines.append(f"- **Decision:** {risk['decision_id']}")
                lines.append(f"- **Risk Level:** {risk['risk_level']}")
                lines.append(f"- **Overall Score:** {risk['overall_score']}")
                lines.append(f"- **Timestamp:** {risk['timestamp']}")
                lines.append("")

        # Escalations
        if "escalations" in data and data["escalations"]:
            lines.append("## Escalations")
            lines.append("")
            for esc in data["escalations"][:10]:
                lines.append(f"### {esc['escalation_id']}")
                lines.append(f"- **Decision:** {esc['decision_id']}")
                lines.append(f"- **Status:** {esc['status']}")
                lines.append(f"- **Priority:** {esc['priority']}")
                lines.append(f"- **Created:** {esc['created_at']}")
                lines.append("")

        # Compliance
        if "compliance" in data:
            lines.append("## Compliance Status")
            lines.append("")
            for framework, framework_data in data["compliance"]["frameworks"].items():
                lines.append(f"### {framework.upper()}")
                coverage = framework_data["coverage"]
                lines.append(f"- **Total Controls:** {coverage['total_controls']}")
                lines.append(f"- **Compliance:** {coverage['overall_compliance']:.1f}%")
                lines.append(f"- **Gaps:** {len(framework_data['gaps'])}")
                lines.append("")

        return "\n".join(lines)

    def _format_html(self, data: Dict[str, Any]) -> str:
        """Format as HTML."""
        html = ["<!DOCTYPE html>", "<html>", "<head>"]
        html.append("<title>Governance Audit Export</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 40px; }")
        html.append("h1 { color: #333; }")
        html.append("table { border-collapse: collapse; width: 100%; margin: 20px 0; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #4CAF50; color: white; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        # Header
        html.append("<h1>Governance Audit Export</h1>")
        html.append(f"<p><strong>Export ID:</strong> {data['export_metadata']['export_id']}</p>")
        html.append(f"<p><strong>Generated:</strong> {data['export_metadata']['generated_at']}</p>")

        # Statistics
        if "statistics" in data:
            html.append("<h2>Summary Statistics</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Count</th></tr>")
            stats = data["statistics"]
            html.append(f"<tr><td>Risk Assessments</td><td>{stats.get('total_risks', 0)}</td></tr>")
            html.append(f"<tr><td>Escalations</td><td>{stats.get('total_escalations', 0)}</td></tr>")
            html.append(f"<tr><td>Overrides</td><td>{stats.get('total_overrides', 0)}</td></tr>")
            html.append(f"<tr><td>Evidence Artifacts</td><td>{stats.get('total_evidence', 0)}</td></tr>")
            html.append("</table>")

        html.append("</body>")
        html.append("</html>")
        return "\n".join(html)

    def get_export(self, export_id: str) -> Optional[ExportPackage]:
        """Get an export package by ID."""
        return self._exports.get(export_id)

    def list_exports(
        self,
        requester: Optional[str] = None,
        limit: int = 100
    ) -> List[ExportPackage]:
        """List export packages with optional filtering."""
        exports = list(self._exports.values())

        if requester:
            exports = [e for e in exports if e.request.requester == requester]

        # Sort by generation time (newest first)
        exports.sort(key=lambda e: e.generated_at, reverse=True)

        return exports[:limit]

    def get_export_statistics(self) -> Dict[str, Any]:
        """Get overall export statistics."""
        total_exports = len(self._exports)
        total_size = sum(e.size_bytes for e in self._exports.values())
        total_records = sum(e.record_count for e in self._exports.values())

        format_breakdown = {}
        for export in self._exports.values():
            fmt = export.format.value
            format_breakdown[fmt] = format_breakdown.get(fmt, 0) + 1

        return {
            "total_exports": total_exports,
            "total_size_bytes": total_size,
            "total_records_exported": total_records,
            "format_breakdown": format_breakdown,
            "average_export_size_bytes": total_size // total_exports if total_exports > 0 else 0,
        }

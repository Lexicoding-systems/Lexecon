"""
EU AI Act Compliance Infrastructure

Automated compliance documentation, record-keeping, and evidence generation
for EU Artificial Intelligence Act enforcement.

Target: August 2026 high-risk AI system deadline
"""

from .article_11_technical_docs import TechnicalDocumentationGenerator
from .article_12_records import RecordKeepingSystem
from .article_14_oversight import HumanOversightEvidence

__all__ = [
    "TechnicalDocumentationGenerator",
    "RecordKeepingSystem",
    "HumanOversightEvidence",
]

#!/usr/bin/env python3
"""Coverage Analysis Script

Analyzes test coverage and identifies uncovered lines,
prioritized by modules closest to 100% coverage.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_coverage() -> str:
    """Run pytest with coverage and return the report."""
    print("🔍 Running coverage analysis...")
    result = subprocess.run(
        ["python3", "-m", "pytest", "--cov=src/lexecon", "--cov-report=term-missing", "--tb=no", "-q"],
        check=False, capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.stdout + result.stderr


def parse_coverage_report(report: str) -> List[Dict]:
    """Parse coverage report and extract module information."""
    modules = []

    # Pattern: src/lexecon/path/file.py    STMTS  MISS  COVER  MISSING
    pattern = r"(src/lexecon/[\w/]+\.py)\s+(\d+)\s+(\d+)\s+(\d+)%(?:\s+(.+))?"

    for line in report.split("\n"):
        match = re.match(pattern, line)
        if match:
            filepath, stmts, miss, cover, missing = match.groups()

            # Skip __init__.py files and files with 0 statements
            if "__init__" in filepath or stmts == "0":
                continue

            modules.append({
                "path": filepath,
                "statements": int(stmts),
                "missing": int(miss),
                "coverage": int(cover),
                "missing_lines": missing.strip() if missing else "",
            })

    return modules


def get_file_lines(filepath: str, line_ranges: str) -> List[Tuple[int, str]]:
    """Get the actual code for uncovered lines."""
    if not line_ranges:
        return []

    try:
        with open(filepath) as f:
            lines = f.readlines()

        uncovered = []
        # Parse ranges like "23-25, 30, 45-50"
        for part in line_ranges.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                for i in range(start, min(end + 1, start + 5)):  # Limit to 5 lines per range
                    if i <= len(lines):
                        uncovered.append((i, lines[i - 1].rstrip()))
            else:
                try:
                    line_num = int(part)
                    if line_num <= len(lines):
                        uncovered.append((line_num, lines[line_num - 1].rstrip()))
                except ValueError:
                    continue

        return uncovered[:10]  # Limit to 10 lines per file
    except Exception:
        return []


def categorize_modules(modules: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize modules by coverage percentage."""
    categories = {
        "quick_wins": [],      # 95-99%
        "near_complete": [],   # 90-94%
        "good": [],            # 80-89%
        "needs_work": [],      # 50-79%
        "critical": [],        # 0-49%
    }

    for module in modules:
        cov = module["coverage"]
        if cov >= 95:
            categories["quick_wins"].append(module)
        elif cov >= 90:
            categories["near_complete"].append(module)
        elif cov >= 80:
            categories["good"].append(module)
        elif cov >= 50:
            categories["needs_work"].append(module)
        else:
            categories["critical"].append(module)

    return categories


def print_analysis(categories: Dict[str, List[Dict]]):
    """Print formatted coverage analysis."""
    print("\n" + "=" * 80)
    print("📊 COVERAGE ANALYSIS - PRIORITIZED BY IMPACT")
    print("=" * 80)

    # Quick Wins
    if categories["quick_wins"]:
        print(f"\n🎯 QUICK WINS (95-99% coverage) - {len(categories['quick_wins'])} modules")
        print("-" * 80)
        for module in sorted(categories["quick_wins"], key=lambda x: x["missing"]):
            print(f"\n📄 {module['path']}")
            print(f"   Coverage: {module['coverage']}% ({module['missing']} lines to 100%)")
            print(f"   Missing lines: {module['missing_lines']}")

            # Show actual code
            uncovered = get_file_lines(module["path"], module["missing_lines"])
            if uncovered:
                print("   Uncovered code:")
                for line_num, code in uncovered[:3]:  # Show first 3 lines
                    print(f"      {line_num:4d}: {code}")
                if len(uncovered) > 3:
                    print(f"      ... and {len(uncovered) - 3} more lines")

    # Near Complete
    if categories["near_complete"]:
        print(f"\n✨ NEAR COMPLETE (90-94% coverage) - {len(categories['near_complete'])} modules")
        print("-" * 80)
        for module in sorted(categories["near_complete"], key=lambda x: x["missing"])[:5]:
            print(f"  • {module['path']:50s} {module['coverage']:3d}% ({module['missing']:3d} lines)")

    # Good
    if categories["good"]:
        print(f"\n✅ GOOD COVERAGE (80-89%) - {len(categories['good'])} modules")
        for module in sorted(categories["good"], key=lambda x: x["missing"])[:5]:
            print(f"  • {module['path']:50s} {module['coverage']:3d}% ({module['missing']:3d} lines)")

    # Needs Work
    if categories["needs_work"]:
        print(f"\n⚠️  NEEDS WORK (50-79%) - {len(categories['needs_work'])} modules")
        for module in sorted(categories["needs_work"], key=lambda x: x["coverage"], reverse=True)[:5]:
            print(f"  • {module['path']:50s} {module['coverage']:3d}% ({module['missing']:3d} lines)")

    # Critical
    if categories["critical"]:
        print(f"\n🚨 CRITICAL (0-49%) - {len(categories['critical'])} modules")
        for module in sorted(categories["critical"], key=lambda x: x["coverage"], reverse=True)[:5]:
            print(f"  • {module['path']:50s} {module['coverage']:3d}% ({module['missing']:3d} lines)")

    # Summary
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    total_modules = sum(len(cats) for cats in categories.values())
    quick_wins_lines = sum(m["missing"] for m in categories["quick_wins"])
    near_complete_lines = sum(m["missing"] for m in categories["near_complete"])

    print(f"Total modules analyzed: {total_modules}")
    print("\nQuick wins available:")
    print(f"  • {len(categories['quick_wins'])} modules need only {quick_wins_lines} lines total")
    print(f"  • {len(categories['near_complete'])} modules need {near_complete_lines} lines total")
    print(f"\nTotal impact: {quick_wins_lines + near_complete_lines} lines to cover {len(categories['quick_wins']) + len(categories['near_complete'])} modules")

    print("\n💡 RECOMMENDATION:")
    print(f"   Start with the {len(categories['quick_wins'])} quick wins above!")
    print("   This adds minimal tests for maximum coverage improvement.\n")


def main():
    """Run coverage analysis."""
    report = run_coverage()
    modules = parse_coverage_report(report)

    if not modules:
        print("❌ No coverage data found. Make sure tests are running correctly.")
        sys.exit(1)

    categories = categorize_modules(modules)
    print_analysis(categories)

    # Calculate overall coverage
    total_stmts = sum(m["statements"] for m in modules)
    total_missing = sum(m["missing"] for m in modules)
    overall_coverage = ((total_stmts - total_missing) / total_stmts * 100) if total_stmts > 0 else 0

    print(f"Overall Coverage: {overall_coverage:.1f}%")
    print(f"Lines to 100%: {total_missing}")


if __name__ == "__main__":
    main()

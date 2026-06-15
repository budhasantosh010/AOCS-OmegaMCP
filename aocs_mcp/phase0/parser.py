"""3.1 Parser — clean and structure raw input."""

import re


def parse(problem: str, domain: str | None = None) -> str:
    """Clean and structure the raw problem input.

    Extracts explicit request, implied constraints, and missing context.
    """
    lines = [line.strip() for line in problem.strip().split("\n")]
    lines = [line for line in lines if line]

    # Build a structured representation
    domain_label = domain or "auto-infer from problem"

    structured = [
        f"## Parsed Problem (domain: {domain_label})",
        f"",
        f"### Raw Input",
        f"{problem.strip()}",
        f"",
        f"### Structured Breakdown",
    ]

    # Extract code references (file paths, line numbers)
    code_refs = re.findall(r"[\w./\\-]+\.[a-zA-Z]+:\d+", problem)
    if code_refs:
        structured.append(f"- Code references: {', '.join(code_refs)}")

    # Extract error messages / stack traces
    errors = re.findall(r"(?:Error|Exception|Traceback|FAILED|failed:)\s*[^\n]+", problem)
    if errors:
        structured.append(f"- Error signatures: {len(errors)} found")
        for e in errors[:3]:
            structured.append(f"  - {e.strip()[:120]}")

    # Extract quoted terms (likely key concepts)
    quoted = re.findall(r'"([^"]+)"', problem)
    if quoted:
        structured.append(f"- Key terms: {', '.join(quoted[:5])}")

    # Count lines for size estimation
    structured.append(f"- Input size: {len(lines)} lines, {len(problem)} characters")
    structured.append(f"- Domain: {domain_label}")

    return "\n".join(structured)

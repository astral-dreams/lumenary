from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import IdeaRecord, now_local_iso


BANNED_PUBLIC_TITLE_WORDS = {
    "architecture",
    "authorization",
    "claimant",
    "compound",
    "convergence",
    "custody",
    "epistemic",
    "grammar",
    "inferential",
    "interface",
    "ledger",
    "phenomenology",
    "policy",
    "residue",
    "rubric",
    "scaffold",
    "topology",
}

BANNED_PUBLIC_PHRASES = {
    "this finding",
    "plain english",
    "the cleaner version is",
    "the payoff is",
}

EM_DASH = chr(0x2014)


@dataclass
class WritingIssue:
    code: str
    message: str
    severity: str
    title: str
    idea_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "idea_id": self.idea_id,
            "message": self.message,
            "severity": self.severity,
            "title": self.title,
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return records


def _word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", value))


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", value.strip()) if item.strip()]


def _plain(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _has_banned_title_word(value: str) -> str:
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", value)}
    for word in sorted(BANNED_PUBLIC_TITLE_WORDS):
        if word in words:
            return word
    return ""


def _distillations(root: Path) -> dict[str, dict[str, Any]]:
    by_idea: dict[str, dict[str, Any]] = {}
    for record in _read_jsonl(root / "publication" / "distillations.jsonl"):
        idea_id = str(record.get("ideaId") or "")
        if idea_id:
            by_idea[idea_id] = record
    return by_idea


def _idea_id(idea: IdeaRecord | dict[str, Any]) -> str:
    if isinstance(idea, IdeaRecord):
        return idea.identity()
    return str(idea.get("idea_id") or "")


def _idea_title(idea: IdeaRecord | dict[str, Any]) -> str:
    return idea.title if isinstance(idea, IdeaRecord) else str(idea.get("title") or "")


def _record_text_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    fields = [
        ("publicTitle", _plain(record.get("publicTitle") or record.get("insight") or record.get("title"))),
        ("insight", _plain(record.get("insight"))),
        ("plainSummary", _plain(record.get("plainSummary"))),
        ("atAGlance", _plain(record.get("atAGlance"))),
    ]
    for index, point in enumerate(record.get("keyPoints") or []):
        fields.append((f"keyPoints[{index}]", _plain(point)))
    return fields


def validate_idea_public_copy(
    root: Path,
    idea: IdeaRecord | dict[str, Any],
    *,
    require_distillation: bool = True,
) -> list[WritingIssue]:
    issues: list[WritingIssue] = []
    idea_id = _idea_id(idea)
    title = _idea_title(idea)
    distillation = _distillations(root).get(idea_id)

    if require_distillation and not distillation:
        return [
            WritingIssue(
                code="missing_distillation",
                idea_id=idea_id,
                message="No reader-facing distillation exists for this idea.",
                severity="block",
                title=title,
            )
        ]

    public_title = _plain((distillation or {}).get("publicTitle") or (distillation or {}).get("insight") or title)
    if _word_count(public_title) > 10:
        issues.append(
            WritingIssue(
                code="public_title_too_long",
                idea_id=idea_id,
                message=f"Public title exceeds 10 words: {public_title}",
                severity="block",
                title=title,
            )
        )
    banned_word = _has_banned_title_word(public_title)
    if banned_word:
        issues.append(
            WritingIssue(
                code="public_title_jargon",
                idea_id=idea_id,
                message=f"Public title contains banned research jargon: {banned_word}",
                severity="block",
                title=title,
            )
        )

    if distillation:
        at_a_glance = _plain(distillation.get("atAGlance"))
        sentence_count = len(_sentences(at_a_glance))
        if sentence_count < 3 or sentence_count > 4:
            issues.append(
                WritingIssue(
                    code="at_a_glance_sentence_count",
                    idea_id=idea_id,
                    message=f"At a Glance must be 3 to 4 sentences; found {sentence_count}.",
                    severity="block",
                    title=title,
                )
            )
        key_points = [str(item).strip() for item in distillation.get("keyPoints") or [] if str(item).strip()]
        if len(key_points) != 3:
            issues.append(
                WritingIssue(
                    code="key_point_count",
                    idea_id=idea_id,
                    message=f"Finding pages need exactly 3 key points; found {len(key_points)}.",
                    severity="block",
                    title=title,
                )
            )
        for field, value in _record_text_fields(distillation):
            lower = value.lower()
            if EM_DASH in value or "&mdash;" in lower or "&#8212;" in lower:
                issues.append(
                    WritingIssue(
                        code="em_dash",
                        idea_id=idea_id,
                        message=f"{field} contains an em dash.",
                        severity="block",
                        title=title,
                    )
                )
            for phrase in sorted(BANNED_PUBLIC_PHRASES):
                if phrase in lower:
                    issues.append(
                        WritingIssue(
                            code="banned_phrase",
                            idea_id=idea_id,
                            message=f"{field} contains banned phrase: {phrase}.",
                            severity="block",
                            title=title,
                        )
                    )

    if isinstance(idea, IdeaRecord):
        teaching = idea.teaching_candidate
        practice = idea.practice_candidate
        teaching_body = teaching.body if teaching else ""
        practice_text = " ".join(
            [
                practice.purpose if practice else "",
                practice.non_fit if practice else "",
                practice.weakens_if if practice else "",
            ]
        )
    else:
        teaching = idea.get("teaching_candidate") if isinstance(idea.get("teaching_candidate"), dict) else {}
        practice = idea.get("practice_candidate") if isinstance(idea.get("practice_candidate"), dict) else {}
        teaching_body = str(teaching.get("body") or "")
        practice_text = " ".join(str(practice.get(key) or "") for key in ["purpose", "non_fit", "weakens_if"])

    for field, value in [("teaching_candidate.body", teaching_body), ("practice_candidate", practice_text)]:
        lower = value.lower()
        if EM_DASH in value:
            issues.append(
                WritingIssue(
                    code="candidate_em_dash",
                    idea_id=idea_id,
                    message=f"{field} contains an em dash.",
                    severity="warn",
                    title=title,
                )
            )
        for phrase in ["the hand works", "the fruit belongs", "the cleaner version is", "the payoff is"]:
            if phrase in lower:
                issues.append(
                    WritingIssue(
                        code="candidate_style_warning",
                        idea_id=idea_id,
                        message=f"{field} contains weak teaching phrasing: {phrase}.",
                        severity="warn",
                        title=title,
                    )
                )

    return issues


def validate_public_writing(
    root: Path,
    ideas: list[IdeaRecord] | list[dict[str, Any]],
    *,
    require_distillation: bool = True,
) -> list[WritingIssue]:
    return [
        issue
        for idea in ideas
        for issue in validate_idea_public_copy(root, idea, require_distillation=require_distillation)
    ]


def write_writing_gate_event(root: Path, issues: list[WritingIssue], *, execution_id: str) -> None:
    event = {
        "at": now_local_iso(),
        "blockers": sum(1 for issue in issues if issue.severity == "block"),
        "execution_id": execution_id,
        "issues": [issue.to_dict() for issue in issues],
        "warnings": sum(1 for issue in issues if issue.severity == "warn"),
    }
    path = root / "runs" / "writing-gate-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")


def _recent_ideas(root: Path, limit: int) -> list[dict[str, Any]]:
    records = _read_jsonl(root / "hypotheses" / "ideas.jsonl")
    return sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)[:limit]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate reader-facing Lumenary writing quality.")
    parser.add_argument("--recent", type=int, default=10, help="Validate the N most recent ideas.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if blockers are found.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    issues = validate_public_writing(root, _recent_ideas(root, args.recent), require_distillation=True)
    for issue in issues:
        print(json.dumps(issue.to_dict(), ensure_ascii=True, sort_keys=True))
    if args.strict and any(issue.severity == "block" for issue in issues):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

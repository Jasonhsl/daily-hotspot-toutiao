#!/usr/bin/env python3
"""Build a Toutiao-style daily hotspot publishing pack from JSON input."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_RISK_TERMS = {
    "high": [
        "内幕",
        "爆雷",
        "稳赚",
        "神药",
        "自杀",
        "血腥",
        "恐怖袭击",
        "暴力",
        "偷拍视频",
        "人肉",
    ],
    "medium": [
        "翻车",
        "实锤",
        "封杀",
        "崩了",
        "炸了",
        "怒斥",
        "网暴",
        "造假",
    ],
}


def load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of topic objects.")
    return [item for item in data if isinstance(item, dict)]


def risk_for_text(text: str, extra_terms: list[str]) -> tuple[str, list[str]]:
    hits: list[str] = []
    level = "low"
    for term in DEFAULT_RISK_TERMS["medium"]:
        if term in text:
            hits.append(term)
            level = "medium"
    for term in DEFAULT_RISK_TERMS["high"] + extra_terms:
        if term in text:
            hits.append(term)
            level = "high"
    return level, sorted(set(hits))


def sanitize_title(title: str) -> str:
    # Preserve meaning; contextual editorial review handles flagged wording.
    clean = title.strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def build_markdown(items: list[dict[str, Any]], run_date: str, extra_terms: list[str]) -> str:
    lines = [
        f"# 今日热点发布包 - {run_date}",
        "",
        "## 发布建议",
        f"- 推荐发布数量: {min(len(items), 10)}",
        "- 风险较低主题: 优先选择有官方来源、事实清楚、配图安全的条目",
        "- 建议避开的主题: 高风险、事实不清、涉及隐私或强情绪对立的条目",
        "",
    ]

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        raw_title = str(item.get("title", "")).strip() or f"未命名热点 {index}"
        title = sanitize_title(raw_title)
        summary = str(item.get("summary", "")).strip()
        body = str(item.get("body", "")).strip() or summary
        image = str(item.get("image", "")).strip() or "需要补充: 选择官方图、新闻配图或生成中性插图"
        platforms = as_list(item.get("platforms"))
        sources = as_list(item.get("sources"))
        risk_notes = as_list(item.get("risk_notes"))
        risk_level, hits = risk_for_text(" ".join([raw_title, summary, body]), extra_terms)
        if hits:
            risk_notes.append("命中高风险/敏感表达: " + ", ".join(hits))

        normalized.append(
            {
                "title": title,
                "platforms": platforms,
                "heat": item.get("heat", ""),
                "summary": summary,
                "body": body,
                "image": image,
                "sources": sources,
                "risk_level": risk_level,
                "risk_notes": risk_notes,
            }
        )

        lines.extend(
            [
                f"## {index}. {title}",
                f"- 平台来源: {', '.join(platforms) if platforms else '待补充'}",
                f"- 热度依据: {item.get('heat', '待补充')}",
                f"- 配图: {image}",
                f"- 风险等级: {risk_level}",
                f"- 风险提示: {'; '.join(risk_notes) if risk_notes else '暂无明显风险'}",
                "- 正文:",
                "",
                body or "待补充正文",
                "",
                "- 来源:",
            ]
        )
        if sources:
            lines.extend([f"  - {source}" for source in sources])
        else:
            lines.append("  - 待补充")
        lines.append("")

    return "\n".join(lines), normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--extra-risk-terms", type=Path)
    args = parser.parse_args()

    extra_terms: list[str] = []
    if args.extra_risk_terms and args.extra_risk_terms.exists():
        extra_terms = [
            line.strip()
            for line in args.extra_risk_terms.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    items = load_json(args.input)
    markdown, normalized = build_markdown(items, args.date, extra_terms)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.out_dir / f"toutiao-hotspot-pack-{args.date}.md"
    json_path = args.out_dir / f"toutiao-hotspot-pack-{args.date}.json"
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()

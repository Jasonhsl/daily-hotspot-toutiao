"""Create a single-topic DOCX and audit; never imply editorial approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

REVIEW_KEYS = ("single_question", "reader_benefit", "evidence", "original_analysis",
               "fact_comment_separation", "freshness", "no_filler",
               "title_delivery", "images", "compliance")

def build(data, out):
    run_date = date.fromisoformat(data["run_date"]).isoformat()
    title = data["title"].strip()
    if not 2 <= len(title) <= 30:
        raise ValueError("Title must contain 2-30 characters.")
    if not data["lead"].strip() or data["lead"].strip() == title:
        raise ValueError("A non-repeated lead is required.")
    if not data["sections"]:
        raise ValueError("Sections are required.")
    names = [s["image"] for s in data["sections"] if s.get("image")]
    sources = {i["filename"]: i for i in data["image_sources"]}
    if len(sources) != len(data["image_sources"]) or len(names) != len(set(names)):
        raise ValueError("Duplicate image names or placements.")
    if not names or set(names) != set(sources):
        raise ValueError("Every supplied image must have exactly one placement.")
    for name in names:
        if Path(name).name != name or "/" in name or "\\" in name or ":" in name:
            raise ValueError("Image filename must be a basename.")
        if not Path(sources[name]["source"]).is_file():
            raise ValueError("Missing local image: " + name)
    paragraphs = [data["lead"]]
    for section in data["sections"]:
        if not section["heading"].strip() or not section["paragraphs"]:
            raise ValueError("Each section needs a heading and paragraphs.")
        if section["heading"].strip() == title or section["heading"].lstrip().startswith("#"):
            raise ValueError("No repeated total title or Markdown hash headings.")
        paragraphs.extend([section["heading"], *section["paragraphs"]])
    if any(not isinstance(p, str) or not p.strip() for p in paragraphs):
        raise ValueError("Empty paragraphs are not allowed.")
    if any(re.search(r"https?://", p) for p in paragraphs):
        raise ValueError("Raw source URLs belong in the audit.")
    out = Path(out).resolve()
    doc_path = out / ("toutiao-deep-post-" + run_date + ".docx")
    audit_path = out / ("toutiao-deep-audit-" + run_date + ".json")
    image_dir = out / ("images-" + run_date)
    if any(p.exists() for p in (doc_path, audit_path, image_dir)):
        raise FileExistsError("Run outputs exist; use a revision directory.")
    doc = Document()
    doc.core_properties.title = title
    doc.core_properties.author = ""
    page = doc.sections[0]
    page.top_margin = page.bottom_margin = Inches(.72)
    page.left_margin = page.right_margin = Inches(.92)
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal.font.size = Pt(11)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    def add(text, heading=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.keep_with_next = heading
        r = p.add_run(text)
        r.bold = heading
        r.font.size = Pt(14 if heading else 11)
    add(data["lead"])
    for section in data["sections"]:
        add(section["heading"], True)
        for paragraph in section["paragraphs"]:
            add(paragraph)
        if section.get("image"):
            doc.add_picture(sources[section["image"]]["source"], width=Inches(5))
    # Decode and embed all images before creating output files.
    out.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir()
    images = []
    for i, name in enumerate(names, 1):
        target = image_dir / (str(i).zfill(2) + "-" + name)
        shutil.copy2(sources[name]["source"], target)
        images.append({**sources[name], "order": i, "local_path": str(target)})
    doc.save(doc_path)
    audit = {
        "run_date": run_date, "timezone": "Asia/Shanghai",
        "topic": {"title": title},
        "editorial": data.get("editorial", {}),
        "sources": data.get("sources", []),
        "fact_checks": data.get("fact_checks", []),
        "analysis_outline": data.get("analysis_outline", []),
        "risk_notes": data.get("risk_notes", []), "images": images,
        "article_characters": len("".join("".join(paragraphs).split())),
        "docx_path": str(doc_path),
        "docx_sha256": hashlib.sha256(doc_path.read_bytes()).hexdigest(),
        "quality_checks": {
            k: {"status": "pending", "evidence": ""} for k in REVIEW_KEYS
        },
        "render_check": {"status": "pending", "evidence": ""},
        "platform_preview": {"status": "pending", "evidence": ""},
        "publishing": {"status": "prepared", "first_publish": False}
    }
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"docx": str(doc_path), "images": str(image_dir), "audit": str(audit_path)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    print(json.dumps(build(data, args.out_dir), ensure_ascii=False))

if __name__ == "__main__":
    main()

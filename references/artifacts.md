# Artifact Contract

Use python scripts/build_article.py --input ABSOLUTE_JSON --out-dir ABSOLUTE_OUTPUTS (requires python-docx).

Input uses the existing deep-topic structure: run_date (YYYY-MM-DD), title, lead, sections [{heading, paragraphs: [text], image: optional filename}], image_sources [{source: absolute local path, filename, purpose, rights}], sources [{name,url,published_at,used_for}], fact_checks, analysis_outline, risk_notes, and editorial.

editorial contains audience, central_question, thesis, trend_observations, topic_candidates, five title_candidates (title, scores, reasons), selected_title_reason and reviews. Required reviews are listed in editorial.md. Record genuine evidence and observations; generation does not verify their truth.

Place each image once, in article order. Titles live in DOCX metadata/platform field, not body. Section headings are bold without Markdown hashes. Output: DOCX, ordered images and audit JSON, with final DOCX SHA-256. Existing outputs cannot be overwritten; use a revision directory.

Render using the available documents workflow and inspect EVERY page. Record page count, rendering path, actual observations and DOCX hash in the audit. Rebuilding invalidates prior rendering/preview passes. The builder leaves these checks pending and never hard-codes editorial passes.

Before publication verify all required editorial reviews, five evaluated titles, real render pass, final hash, source dates and image rights/purpose. Missing checks must be completed; generated does not mean publish-ready. Record platform ID, observed timestamp and status after submission. Deliver absolute DOCX/images/audit links. Keep audit notes and raw URLs out of public copy.


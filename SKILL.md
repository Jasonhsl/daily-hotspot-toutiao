---
name: daily-hotspot-toutiao
description: Research current Chinese trends, develop one evidence-backed original article with reader-focused titles, create an illustrated DOCX and audit record, and publish to Toutiao through document import when authorized.
---

# Daily Hotspot Toutiao

## Scope and Defaults

Produce ONE useful original article per scheduled run, not a multi-topic roundup. Default audience: ordinary readers navigating technology and digital life; secondary focus: practical consumer and public services. A trend is a lead, not proof of reader value. Skip publication when evidence or analysis is insufficient.

These files are the maintained editorial and publishing rules. The scheduled task should invoke them instead of duplicating them. A newer explicit user instruction takes precedence over these defaults.

## Workflow

1. Resolve the actual current date in Asia/Shanghai. Check recent audits and the shared publishing ledger; resume unfinished work rather than generating or publishing duplicates. Never silently relabel yesterday's article as today's.
2. Collect live trend signals from multiple accessible Chinese platforms. Save URLs, capture times and observed signals. Cross-check central facts using primary/credible sources; syndicated copies count as one evidence chain. Do not invent rankings when hot lists are unavailable.
3. Read [editorial.md](references/editorial.md). Compare candidate topics on reader relevance, timeliness, evidence, information gain and repetition. Choose one low-risk central question and defensible thesis. Skip unverified incidents, tragedy exploitation and subjects requiring professional/news qualifications.
4. Write the article, then evaluate five distinct titles. Match the final title and opening to the body. Suggested 1800-3000 characters is a guide, not a quota. After two unsuccessful substantive revisions, save the audit and skip publication.
5. Create original local images that explain the argument. Usually 3-5 images; use fewer when additional images add no information and record why. Record rights, purpose and placement. Do not present generated scenes as documentary photographs.
6. Read [artifacts.md](references/artifacts.md). Use scripts/build_article.py with structured JSON to generate embedded-image DOCX, ordered images and separate audit JSON. Use the available documents workflow to render and inspect every page. The body begins with the lead, never a duplicate total title.
7. Record actual review observations; pending is not a pass. If authorized, read [publishing.md](references/publishing.md), import DOCX, verify the preview and submit. Existing authorization persists within its scope; do not ask again merely because the platform button says confirmation.
8. Return absolute DOCX, images and audit links plus observed publishing status. Distinguish under review from publicly published. Report actionable failures.

## Authorization and Account Preferences

Default to preparing files only. Establish the current user's explicit publishing authorization and target account before submission. A standing authorization may cover one quality-checked daily article including the final click; record its scope locally. Never inherit another user's consent. Authorization does not extend to other accounts/platforms, first-publish exclusivity, or overriding a later pause/manual-only request.

Use a location only when specified by the current user. Keep Toutiao first-publish unchecked unless explicitly authorized. Select truthful AI disclosure when AI substantially contributes. If declarations are mutually exclusive, select 引用AI and record why both requested declarations cannot be selected. Preserve existing monetization settings; do not opt into other programs. Schedule, timezone, location and authorization are local configuration, not shared account defaults.

## Quality and Feedback

Read [compliance.md](references/compliance.md) for contextual review. The legacy prepare_toutiao_pack.py is only for explicitly requested old digest conversion; it is not the daily workflow. Keyword hits are review hints, never proof of violation or compliance.

Once a week, when analytics are accessible, compare similar articles using available impressions, reads, reading depth and comments. Record observation time, sample size, metric definitions and missing metrics. Never invent retention data or equate reads/impressions with platform-defined CTR without checking. Treat small samples as tentative evidence. Do not republish near-identical articles to test headlines.

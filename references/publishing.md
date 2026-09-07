# Authorized Toutiao Publishing

## Shared Ledger and Recovery

Use outputs/publishing-ledger.sqlite3 in the task workspace for this account across all dates. Default account key: toutiao-primary. Verify the visible account; an unexpected account change needs clarification. Do not create one ledger per run.

scripts/publish_ledger.py records one daily run per account and a normalized body fingerprint independent of title. Use the same article JSON used for DOCX. It does not control the browser or prove platform state.

Commands (resolve script/data paths absolutely):
- python scripts/publish_ledger.py --db outputs/publishing-ledger.sqlite3 --account toutiao-primary reserve --article work/article.json
- python scripts/publish_ledger.py --db outputs/publishing-ledger.sqlite3 --account toutiao-primary list
- python scripts/publish_ledger.py --db outputs/publishing-ledger.sqlite3 --account toutiao-primary mark --id ID --status preview_verified --evidence "Verified title, body, images, cover and declarations"

created:true returns a new reservation ID. created:false requires checking that record and the platform rather than starting another submission. reserved may resume the same draft. preview_verified requires fresh platform verification. submitting, submitted_review, published and unknown MUST NOT trigger another final click.

Immediately before the final click, transition preview_verified to submitting. Only the worker whose transition succeeds may click. SQLite serializes reservations/transitions. A crash leaves submitting; reconcile via works management and platform ID. If uncertain, mark unknown. Only after positive evidence that submission did not occur may submitting/unknown transition to preview_verified using --confirmed-not-submitted and a detailed evidence note. Absence from one list page or a slow refresh is insufficient.

Store visible draft/article ID through --platform-id as soon as available. Match ID plus title/time, not title alone. Check historic audits and works management for posts predating the ledger. Never reuse a reservation for changed content, clear a daily reservation to force another article, or republish rejected content automatically.

If the user explicitly requests an additional article that day, keep the same account and database and reserve with a stable --edition key such as manual-extra-1 plus --authorization containing the exact request. This is a per-request exception, not a change to the daily limit. Reuse that edition on retries. Body fingerprint uniqueness still applies across editions and dates. Never invent an extra request or an account key to evade the daily reservation.

## Import and Submit

1. Use currently available supported browser tools and documented APIs. Reuse the signed-in creation page. Discover current UI; do not hard-code historic tab IDs or toolbar indices. Preserve user tabs.
2. Check account, today's prior submissions, all editorial reviews and rendered DOCX; reserve the final article.
3. Locate document import, usually the rightmost toolbar icon, using current UI evidence. Arm the supported file chooser before the upload click. Import local DOCX and wait for actual completion. Embedded images need no separate uploads.
4. Fill the dedicated title. Remove a repeated total title from the body only if import adds one; preserve section headings. Compare lead, ending, sections and placements to the artifact. Editor DOM image nodes can duplicate: verify unique images and rendered preview, loading and cover crop.
5. Set a location only when specified by the current user; keep 头条首发 unchecked unless explicitly authorized. Choose 引用AI for substantial AI involvement; add 个人观点，仅供参考 only if the UI supports multiple declarations. If mutually exclusive, use AI disclosure and note it. Preserve unrelated monetization/syndication settings.
6. Click 预览并发布. Verify preview title, full structure, beginning/ending, images and layout, including iframe content using supported APIs. Record preview_verified with evidence.
7. Verify that the current user's authorization covers final submission. If it does, do not ask again solely because of the button label. Otherwise stop at the prepared draft and request authorization. Transition to submitting, click 确认发布 ONCE, then inspect works management for the same ID. Record submitted_review for 审核中; published only for 已发布. Update ledger and audit. Record platform rejection as rejected, without automatic resubmission.

Retry ordinary non-submission UI failures at most twice using fresh state. Reconcile ambiguous submissions, never blindly retry them. Stop on expired login, CAPTCHA/security challenge, failed or missing import, explicit platform rejection or actual tool restriction, with the precise observed reason. Do not invent an approval requirement from a button label or bypass controls.

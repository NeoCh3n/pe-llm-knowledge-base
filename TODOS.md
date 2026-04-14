# TODOS

## Design

### [ ] Precedent card UI spec (Phase 1)
**What:** Define what a precedent card looks like when it appears in the Analysis chat response. Right now results are plain text — the CEO plan specifies that precedent cards are canonical product objects.
**Why:** Without a UI spec, the precedent retrieval endpoint will ship with no visual design contract. The card IS the trust signal — it must show deal identity, similarity basis, decision/outcome status, and source citations.
**Pros:** Locks in the design before the structured precedent endpoint is built. Avoids retrofitting a card design onto existing markup.
**Cons:** Requires coordination between the card schema (backend) and the card component (frontend).
**Context:** Card fields to specify: deal name, similarity score (or confidence band), decision status badge (passed/rejected/pending), outcome status, 2–3 relevant excerpts with page/doc citations, "View deal docs" link. Should reuse the category color system from DocumentCard (left-border accent).
**Depends on:** Structured `/precedents` endpoint — not yet implemented.

### [ ] Create DESIGN.md via /design-consultation (pre-Phase 2)
**What:** Run `/design-consultation` to produce a formal DESIGN.md covering color tokens, typography scale, spacing, and component vocabulary.
**Why:** The design system is currently inferred from Tailwind class patterns in the codebase. Any new developer will introduce drift. Phase 2 adds significant new UI (canonical deal model, outcome labels, structured retrieval). Without a design contract, those screens will diverge.
**Pros:** Prevents visual fragmentation. Makes onboarding faster. Enables consistent implementation across contributors.
**Cons:** Takes ~20 min with Claude Code. Low cost.
**Context:** Working token set to document: primary bg = gray-900 (sidebar), content bg = gray-50 / white (cards), accent = blue-600, text hierarchy = gray-900 / gray-600 / gray-500. Font: Inter (body), JetBrains Mono (numeric fields).
**Depends on:** Nothing — can be done at any time before Phase 2 scope work begins.

# TODOS

## Design

### [ ] Remove icon-in-circle patterns (AI Slop fix)
**What:** Remove `bg-blue-100 rounded-full` icon circles from MessageBubble.tsx (line 11) and any other locations. Replace with clean icon-only pattern or category-appropriate styling.
**Why:** AI Slop pattern #3 — icon circles are generic SaaS template markers that reduce brand distinctiveness.
**Pros:** Cleaner visual hierarchy, aligns with AI Slop Prevention guidelines.
**Cons:** Minor visual change, may affect user recognition briefly.
**Context:** Found in MessageBubble assistant avatar. The category badge system is the primary identity signal — icons don't need decorative containers.
**Depends on:** Nothing — can be done independently.

### [ ] Replace Unicode block characters in Analysis empty state
**What:** Replace `▣` and `▤` Unicode block characters in AnalysisPage.tsx (lines 125-126) with lucide-react icons (`BrainCircuit` for investment analysis, `FileSearch` for document search).
**Why:** AI Slop pattern #7 — Unicode/emoji as design elements. Also fails accessibility (screen readers may not announce these correctly).
**Pros:** Consistent icon system, better accessibility, professional appearance.
**Cons:** None — straightforward replacement.
**Context:** Size should be 40–48px with `text-gray-300` color. Keep the same positioning in empty state.
**Depends on:** Nothing — can be done independently.

### [ ] Specify PrecedentCard citation click behavior
**What:** Define what happens when user clicks "View deal docs →" in PrecedentCard. Options: open in new tab, modal overlay, navigate to Documents page with auto-filter.
**Why:** Currently a dead link — breaks the trust loop. Users need to verify precedents against source documents.
**Pros:** Completes the citation trust loop; critical for PE use case.
**Cons:** Requires routing decision and potentially new URL params for document filtering.
**Context:** Recommendation: navigate to Documents page with `?deal_id=xxx` auto-filter. Keeps user in app context, maintains navigation state.
**Depends on:** Decision on document filtering/deep-linking approach.

### [ ] Implement mobile responsive notice
**What:** Add responsive notice for viewports below 1024px. Design: full-screen overlay or banner with text "PE Memory OS is optimized for desktop use (1024px+)."
**Why:** Desktop-only strategy is intentional but not communicated. Tablet users currently see broken layout.
**Pros:** Sets clear expectations; prevents frustration; documents the intentional limitation.
**Cons:** Blocks mobile users entirely (by design).
**Context:** Should be dismissible so users can proceed if needed, but clearly warns about suboptimal experience.
**Depends on:** Nothing — can be implemented with CSS breakpoint detection.
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

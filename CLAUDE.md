
# gstack × Antigravity — Skill Manifest

This project uses **gstack** methodology. When the user invokes a `/skill-name` command,
read the full SKILL.md from the path listed below, then execute its workflow exactly as
described. Do NOT summarize or shortcut the skill — follow the interactive steps.

## Skill Registry

| Slash command | SKILL.md path | When to invoke |
|---|---|---|
| `/office-hours` | `~/.claude/skills/office-hours/SKILL.md` | New product idea, "is this worth building", brainstorming, design decisions before code |
| `/plan-eng-review` | `~/.claude/skills/plan-eng-review/SKILL.md` | Architecture review, "review the plan", engineering review, lock in execution |
| `/plan-ceo-review` | `~/.claude/skills/plan-ceo-review/SKILL.md` | Strategy review, "think bigger", "expand scope", ambition check |
| `/plan-design-review` | `~/.claude/skills/plan-design-review/SKILL.md` | Review UI/UX plan before implementation, design critique |
| `/design-consultation` | `~/.claude/skills/design-consultation/SKILL.md` | Create DESIGN.md, design system, brand guidelines from scratch |
| `/design-review` | `~/.claude/skills/design-review/SKILL.md` | Live site visual audit, design polish pass |
| `/codex` | `~/.claude/skills/codex/SKILL.md` | Second opinion code review, adversarial challenge mode |
| `/review` | `~/.claude/skills/review/SKILL.md` | Pre-landing PR review, "check my diff", code review |
| `/investigate` | `~/.claude/skills/investigate/SKILL.md` | Bugs, errors, "why is this broken", 500 errors |
| `/ship` | `~/.claude/skills/ship/SKILL.md` | Ship, deploy, push, create PR |
| `/qa` | `~/.claude/skills/qa/SKILL.md` | QA, test the site, find bugs |
| `/retro` | `~/.claude/skills/retro/SKILL.md` | Weekly retro |
| `/checkpoint` | `~/.claude/skills/checkpoint/SKILL.md` | Save progress, resume, checkpoint |
| `/health` | `~/.claude/skills/health/SKILL.md` | Code quality, health check |
| `/document-release` | `~/.claude/skills/document-release/SKILL.md` | Update docs after shipping |
| `/devex-review` | `~/.claude/skills/devex-review/SKILL.md` | Developer experience review |
| `/plan-devex-review` | `~/.claude/skills/plan-devex-review/SKILL.md` | DX plan review |
| `/learn` | `~/.claude/skills/learn/SKILL.md` | Learn a new concept or codebase |
| `/design-html` | `~/.claude/skills/design-html/SKILL.md` | Generate HTML design components |

## Routing Rules (Auto-invoke)

When the user's request matches a skill trigger, **read the SKILL.md first** then execute.
Do NOT answer directly without reading the skill.

- Product ideas / "is this worth building" / brainstorming → `/office-hours`
- Bugs / errors / "why is this broken" → `/investigate`
- Ship / deploy / PR → `/ship`
- QA / test the site → `/qa`
- Code review / "check my diff" → `/review`
- Update docs after shipping → `/document-release`
- Weekly retro → `/retro`
- Design system / brand / DESIGN.md → `/design-consultation`
- Visual audit / design polish → `/design-review`
- Architecture review / engineering review → `/plan-eng-review`
- Strategy / scope / "think bigger" → `/plan-ceo-review`
- UI/UX plan review before implementation → `/plan-design-review`
- DX / developer experience → `/plan-devex-review`
- Save progress / checkpoint → `/checkpoint`
- Code quality / health → `/health`
- New concept / learning → `/learn`
- Second opinion / Codex → `/codex`

## gstack Project State

- **Plan path:** `~/.gstack/projects/NeoCh3n-pe-llm-knowledge-base/`
- **CEO plan:** `~/.gstack/projects/NeoCh3n-pe-llm-knowledge-base/ceo-plans/2026-04-10-pe-evidence-retrieval-wedge.md`
- **Design doc:** `~/.gstack/projects/NeoCh3n-pe-llm-knowledge-base/chaoyanchen-main-design-20260410-143901.md`
- **Eng review:** DONE_WITH_CONCERNS (2026-04-14) — 10 findings open, parser page# fix shipped
- **Design review:** DONE — 9/10
- **CEO review:** Pending

## How to Execute a Skill in Antigravity

1. Read the SKILL.md at the path listed above using `view_file`
2. Follow the workflow steps inside it exactly (it has Preamble → Steps → Output format)
3. Update the CEO plan's GSTACK REVIEW REPORT table after completing a review skill
4. Store any generated plan/design docs in `~/.gstack/projects/NeoCh3n-pe-llm-knowledge-base/`

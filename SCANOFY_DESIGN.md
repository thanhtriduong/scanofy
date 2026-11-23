# Scanofy Design System — v0.1

> Product direction: **Calm Intelligence**. Scanofy is a document-centered knowledge and learning workspace, not a generic SaaS dashboard.
> Status: initial specification; verify against actual frontend framework, accessibility requirements, and user testing.

## Product principles
1. **Content first.** The PDF or learning task is the focal point. UI chrome must be visually secondary.
2. **Source-grounded interactions.** Every concept, explanation, or quiz item derived from a document should offer a navigable source reference when available.
3. **Progressive disclosure.** Show tools contextually; avoid permanently exposing all AI actions at once.
4. **One vocabulary.** Reuse the same names, icon meanings, statuses, components and spacing across views.
5. **Stable workspace.** Keep navigation stable when switching Read, Knowledge, and Practice modes; preserve scroll and selection when practical.
6. **Accessible by default.** Keyboard operation, visible focus, sufficient contrast and reduced-motion support are required.

## Visual language
- Inspiration: Notion/Readwise content focus; Linear's compact precision; Heptabase-style knowledge exploration **only where useful**.
- Light mode is the initial default; dark mode may be implemented using identical semantic tokens.
- Avoid heavy gradients, glassmorphism, generic purple AI cards, decorative glows, and excessive shadows.
- Prefer borders, whitespace, hierarchy, and subtle state colors.
- Brand color is reserved for selected, active, or primary actions; not every element.

## Foundation tokens (light)
| Semantic token | Hex | Usage |
| --- | --- | --- |
| `--background` | `#FFFFFF` | primary canvas |
| `--foreground` | `#18181B` | primary text |
| `--surface` | `#F8FAFC` | secondary surface |
| `--muted-foreground` | `#71717A` | metadata, supporting text (check contrast at small sizes) |
| `--border` | `#E4E4E7` | separators, outlines |
| `--primary` | `#2563EB` | key actions, focus/highlight |
| `--primary-foreground` | `#FFFFFF` | text on primary |
| `--success` | `#16A34A` | completed, verified |
| `--warning` | `#D97706` | caution and nonblocking issues |
| `--destructive` | `#DC2626` | errors, destructive actions |

Implement via semantic CSS custom properties and align to the frontend component library's token contract rather than hardcoding hex values across pages.

### Typography
- UI: Inter or equivalent humanist sans-serif with Vietnamese glyph support.
- Body: 14px / 20px; supporting text 12px / 16px; document reading text 16px / 26px where reflowed text is rendered.
- Page title: 24px / 32px, semibold; section title: 18px / 26px, semibold; card title: 14px / 20px, medium.
- Minimize font-weight variations. Use sentence case, not uppercase for every heading.

### Spacing, radius, sizing
- Base spacing scale: 4, 8, 12, 16, 24, 32px; use semantic aliases for repeated layout gaps.
- Control radii 6px; cards 8px; modals and popovers 12px.
- Default control height 36px; compact 32px; primary large 40px.
- Navigation sidebar 248px initially; collapsible to icon rail.
- Context panel approximately 320–400px; resizable within sensible min/max.
- Icons: Lucide, 16–18px; stroke weight consistent.
- Focus indicator: visible 2px ring, not color-only.
- Motion: 120–200ms for simple transitions, respect prefers-reduced-motion.

## App shell
- Global navigation: Library, Knowledge, Learning; minimal account/settings access.
- Document workspace header: document name, breadcrumb, save/parse status, contextual actions.
- Primary document modes: **Read**, **Knowledge**, **Practice**. Keep them in a stable switcher.
- Left panel: document outline and navigation (not another bulky dashboard).
- Center: current task (PDF viewer, graph/outline, quiz).
- Right panel: context-sensitive details and actions; hide/collapse if not needed.
- When viewport narrows, move right panel to a drawer; do not shrink the PDF into an unusable column.

## Component inventory
### Shared primitives
`AppShell`, `AppSidebar`, `WorkspaceHeader`, `ModeSwitcher`, `ContextPanel`, `StatusBadge`, `EmptyState`, `ErrorState`, `Skeleton`, `ConfirmDialog`, `Toast`, `SearchCommand`.

### Document components
- `DocumentViewer`: original PDF, keyboard-accessible navigation, zoom and page control.
- `DocumentOutline`: heading hierarchy, active section, jump to PDF.
- `DocumentBlockOverlay`: position using the *validated* coordinate system of stored bbox, correct PDF rotation/CropBox and viewport transforms; do not assume all outputs use 0..1.
- `SelectionToolbar`: Translate, Explain, Ask, Create question, View source; rendered on selection, not always visible.
- `SourceReference`: document title, page, block reference, clear link to open/highlight origin.
- `DocumentProcessingStatus`: queued / processing / completed / failed, progress if measurable and retry where possible.

### Knowledge components
- `KnowledgeOutline`: default structured hierarchy; clearer than a graph for many documents.
- `KnowledgeNode`: common shape and typography, types distinguished with labels/icons, not color alone.
- `KnowledgeCanvas`: optional graph exploration with zoom, fit, and focus selected node.
- `KnowledgeDetailPanel`: concept summary, sources, related concepts, learning actions.
- Maintain links `knowledge_node -> source_block -> parse_run -> PDF page`.

### Learning components
- `LearningAction`: reusable action surface for Explain, Translate, Quiz, Flashcards.
- `TranslationPanel`: original/translation pair with source highlight and language selector.
- `QuestionCard`: prompt, answer choices, submit, feedback, explanation and source.
- `PracticeProgress`: compact progress indicator; avoid gamification that distracts from learning.
- `AIComposer`, `AIMessage`, `AnswerCitation`: shared chat UI with source traceability.

## Interaction states
Every interactive component needs default, hover, focus-visible, active/selected, disabled, loading, error, and empty states as applicable. Use skeletons for load transitions; never leave unexplained blank panels. Show recoverable actions for parse failures. Label AI-generated content as such when it could be mistaken for original text.

## Data-to-UI contract
- Use an internal normalized Scanofy document schema, not raw MinerU fields in components.
- Required block fields where available: `id`, `parse_run_id`, `page_index`, `type`, `content`, `bbox`, `coordinate_system`, `source_engine`, `source_version`.
- Store original PDF and parsed output references for reproducibility.
- Block overlay is baseline. Fine-grained selection uses PDF.js text layer where suitable; for image-only scans use separate OCR geometry/alignment if needed.
- Missing geometry must not create fake highlights. Fall back to page-level or block-level reference.

## Layout templates
### Library
Top bar + search/filter + document list/grid. Emphasize filename, parsed status, updated time, and continue learning. Avoid giant KPI cards.

### Reader
Outline sidebar / PDF center / context tools right. Selection toolbar appears near selected content. Source navigation keeps PDF synchronized.

### Knowledge
Outline or graph center / concept details right / stable document breadcrumbs. Default to outline when content is hierarchical; graph is a secondary exploration mode.

### Practice
Question content center / compact progress and optional source panel. Do not show editing/graph controls while answering.

## Implementation guidelines for coding agents
1. Inspect existing components and token names before building a new one.
2. Reuse shadcn/ui primitives if they are already installed; use semantic token CSS variables. Official theming: https://ui.shadcn.com/docs/theming
3. Use resizable panels only when they add value; preserve keyboard and narrow-screen behavior.
4. For React Flow graphs, map node and edge themes to Scanofy semantic tokens. Official theming: https://reactflow.dev/learn/customization/theming
5. Never add hardcoded colors, random radius values, decorative gradients, or conflicting icon libraries without an explicit design decision.
6. Prefer small coherent components and shared patterns over one giant page component.
7. Implement meaningful loading, error, empty, success and disabled states.
8. Test with a long title, Vietnamese content, multi-page PDF, scanned PDF, empty extraction and failed parse.
9. Verify keyboard access, focus, contrast, touch target sizing and reduced motion.
10. Before introducing any new pattern, compare it with the shared component inventory and extend the existing primitive if possible.

## Design review checklist
- Is the content or learning task visually primary?
- Are color, typography, spacing, radius and icons tokenized?
- Are active, hover, focus, disabled, loading and error states consistent?
- Does the action point to a meaningful source block/page where supported?
- Does the UI handle absent bbox without misleading highlights?
- Can users navigate by keyboard and on narrow viewports?
- Is a new component genuinely necessary, or can an existing pattern be reused?

## Deferred decisions
- Final brand identity, logo and dark theme palette.
- Exact responsive breakpoints based on product analytics.
- Whether the frontend already uses React/Tailwind/shadcn; adapt this design specification to the current stack without forcing a migration.

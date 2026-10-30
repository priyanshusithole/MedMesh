# MediTrace — Frontend Theme & UI Design Specification

> **Product:** MediTrace — Smart Medication Intelligence  
> **Purpose:** Help a patient or authorised healthcare professional organise prescriptions belonging to the same person, extract medicine details, identify repeated or potentially overlapping medicines, and review the patient's medication history.  
> **Design direction:** Modern clinical intelligence — calm, trustworthy, precise, accessible, and easy to scan.

---

## 1. Product identity

### Product name
**MediTrace**

### Tagline
**Every Prescription. One Clear Medication History.**

### Short product description
MediTrace brings a person's prescriptions together in one workspace. It helps users review extracted medicine information, compare medicines across prescriptions, locate repeated or potentially overlapping entries, and maintain a chronological medication history.

### Brand personality
- **Trustworthy:** restrained colours, clear labels, and visible provenance for extracted information.
- **Clinical:** structured data tables, precise terminology, and consistent status indicators.
- **Approachable:** plain-language explanations and uncluttered layouts.
- **Intelligent, not overconfident:** show confidence and uncertainty; never present an uncertain OCR or medicine match as a confirmed fact.

### Core design principles
1. **Patient-first:** all prescriptions and medicine records are grouped under the correct patient profile.
2. **Traceable results:** every extracted medicine should link back to its source prescription and, where possible, the relevant page or image region.
3. **Distinguish a match from a duplicate:** same active ingredient, exact same product, and possible therapeutic overlap are different concepts and must have different labels.
4. **Human verification:** uncertain extraction and medicine matching must be easy to review and correct.
5. **No hidden clinical decisions:** the UI organises information; it must not imply that a medicine should be started, stopped, substituted, or changed.
6. **Accessible by default:** colour is never the only way to communicate a status.

---

## 2. Visual direction

### Overall appearance
Use a light, spacious SaaS dashboard with:
- A fixed or collapsible left sidebar on desktop.
- A slim top bar for search, notifications, and account controls.
- A soft cool-grey page background.
- White content cards with subtle borders and restrained shadows.
- Deep navy for primary navigation and important headings.
- Teal for primary actions and positive/neutral clinical highlights.
- Amber and red only for attention states that genuinely require review.

Avoid a playful, heavily saturated, or overly futuristic look. The product should feel appropriate for a clinical setting without looking like an old hospital-management application.

### Visual hierarchy
1. Page title and patient context.
2. Primary action for the current task.
3. Key metrics or review status.
4. Main working area (table, upload area, timeline, or comparison view).
5. Supporting details and activity history.

### Density
- Default to **comfortable density**: enough row spacing to scan medicine names and their attributes.
- Offer a compact table mode only if the project later needs to display very large medicine lists.
- Do not squeeze critical fields such as strength, dosage form, frequency, or source prescription into tiny text.

---

## 3. Colour system

Use the following palette consistently. Keep the colour values centralised as design tokens rather than hard-coding colours in individual components.

### 3.1 Primary brand palette

| Token | HEX | Intended use |
|---|---|---|
| `brand-900` | `#17324D` | Main brand navy; sidebar, primary headings, high-emphasis text |
| `brand-800` | `#1E4563` | Hover/active navy surfaces, secondary headings on dark backgrounds |
| `brand-700` | `#245C83` | Links, selected navigation accents, information icons |
| `brand-600` | `#0D9488` | Main teal action colour, active controls, key highlights |
| `brand-700-teal` | `#0F766E` | Darker teal for text or icons on pale teal surfaces |
| `brand-100` | `#D7F0EC` | Soft teal selected state or informational surface |
| `brand-50` | `#EAF7F5` | Very light teal background |

**Primary action:** `#0D9488` with white text.  
**Primary navigation background:** `#17324D` with white or pale-blue-grey text.

### 3.2 Neutral palette

| Token | HEX | Intended use |
|---|---|---|
| `neutral-950` | `#17212B` | Highest-emphasis body text |
| `neutral-900` | `#263746` | Main text and headings |
| `neutral-700` | `#475569` | Secondary text |
| `neutral-600` | `#64748B` | Descriptions, metadata |
| `neutral-500` | `#718096` | Placeholders and low-emphasis metadata; check contrast before use |
| `neutral-300` | `#CBD5E1` | Borders, dividers, disabled outlines |
| `neutral-200` | `#E2E8F0` | Card borders, table separators |
| `neutral-100` | `#F1F5F9` | Subtle surfaces and hover backgrounds |
| `neutral-50` | `#F5F8FA` | Main application background |
| `white` | `#FFFFFF` | Cards, modals, input backgrounds |

### 3.3 Semantic status palette

Status colours must always be paired with text and/or an icon. Do not rely on colour alone.

| Status | Foreground | Background | Border | Suggested label |
|---|---|---|---|---|
| Success / verified | `#166534` | `#EAF7EE` | `#B7E4C7` | Verified |
| Information | `#245C83` | `#EAF3FA` | `#C7DDEC` | Information |
| Review / uncertain | `#92400E` | `#FFF4DE` | `#F5D79A` | Needs review |
| Warning / possible duplicate | `#9A6418` | `#FFF4DE` | `#F5D79A` | Possible duplicate |
| Critical / potential issue | `#B42318` | `#FCEBEC` | `#F3C1C1` | Requires attention |
| Neutral / not assessed | `#475569` | `#F1F5F9` | `#CBD5E1` | Not assessed |
| Disabled | `#94A3B8` | `#F1F5F9` | `#E2E8F0` | Unavailable |

**Important terminology rule:** reserve **“confirmed match”** for records that meet the application's explicitly defined matching criteria and have been verified as appropriate. Use **“possible match”** when the system has detected similarity but confidence or clinical equivalence has not been established. Use **“potential duplicate”** as a review flag, not as a prescribing instruction.

### 3.4 Chart colours

Use a small, repeatable set for charts:
- Navy: `#245C83`
- Teal: `#0D9488`
- Sky: `#60A5FA`
- Amber: `#F59E0B`
- Rose: `#E87979`
- Slate: `#94A3B8`

Charts should include labels, legends, and tooltips. Avoid red/green-only comparisons.

### 3.5 Colour usage proportions

A practical starting point for most screens:
- 65–70% neutral backgrounds and surfaces.
- 15–20% navy for structure and typography.
- 8–12% teal for primary interactions and key highlights.
- 3–5% semantic colours for statuses and alerts.

Do not use teal, amber, or red as large decorative background blocks across the entire application.

---

## 4. Typography

### Font family
**Inter** is the recommended UI font. It is highly legible for dashboards, tables, and form labels.

Fallback stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif;
```

### Type scale

| Style | Size | Weight | Line height | Use |
|---|---:|---:|---:|---|
| Display | 32 px | 700 | 1.2 | Landing page / welcome heading only |
| H1 | 28 px | 700 | 1.25 | Main page heading |
| H2 | 22 px | 650–700 | 1.3 | Section heading |
| H3 | 18 px | 600 | 1.35 | Card or panel heading |
| Body large | 16 px | 400–500 | 1.5 | Introductory or important body text |
| Body | 14 px | 400 | 1.5 | Default UI text |
| Label | 13 px | 600 | 1.4 | Form labels, table headings |
| Caption | 12 px | 400–500 | 1.45 | Timestamps and metadata |

Use sentence case for headings and buttons. Avoid all-caps labels except for a very small eyebrow label.

---

## 5. Layout, grid, and spacing

### Desktop application shell
- Sidebar width: **248 px** expanded; **72 px** collapsed.
- Top bar height: **68 px**.
- Main content maximum width: **1440 px** (allow wider tables when needed).
- Main content padding: **32 px** on large screens; **24 px** on medium screens.
- Standard card radius: **12 px**.
- Standard input/button radius: **8 px**.
- Card border: `1px solid #E2E8F0`.
- Shadow: subtle, e.g. `0 2px 8px rgba(23, 50, 77, 0.05)`.

### Spacing scale
Use a 4 px base scale.

| Token | Value | Typical use |
|---|---:|---|
| `space-1` | 4 px | Icon-to-label gap |
| `space-2` | 8 px | Compact control spacing |
| `space-3` | 12 px | Input internal spacing |
| `space-4` | 16 px | Standard component gap |
| `space-5` | 20 px | Small card padding |
| `space-6` | 24 px | Standard card padding |
| `space-8` | 32 px | Section spacing |
| `space-10` | 40 px | Large section separation |
| `space-12` | 48 px | Page-level separation |

### Responsive breakpoints
| Breakpoint | Width | Layout behaviour |
|---|---:|---|
| Mobile | `< 640 px` | Sidebar becomes a drawer; cards stack; tables become cards or horizontally scroll |
| Tablet | `640–1023 px` | Collapsible sidebar; two-column cards where space permits |
| Desktop | `1024–1279 px` | Full application shell; compact sidebar if needed |
| Large desktop | `>= 1280 px` | Full sidebar and wider content area |

On mobile, prioritise upload, patient search, and medicine review. Avoid forcing users to interact with a wide desktop-style comparison table without a mobile alternative.

---

## 6. Application information architecture

### Primary sidebar navigation

1. **Dashboard** — overview and recent activity.
2. **Patients** — search and open patient profiles.
3. **Upload prescription** — add a prescription to a selected patient.
4. **Medicine analysis** — review extracted medicines and match results.
5. **Prescription comparison** — compare selected prescriptions side by side.
6. **Medication timeline** — chronological view of recorded medicines.
7. **Reports** — exportable summaries and review records.
8. **Settings** — profile, access, preferences, and system configuration.

### Sidebar design
- Background: `#17324D`.
- Default text: `#D5E2EA`.
- Default icon: `#B9CBD7`.
- Hover background: `#1E4563`.
- Active background: `#245C83`.
- Active indicator: 3 px teal bar (`#0D9488`) on the left.
- Active text and icon: `#FFFFFF`.
- Use a clear icon and text label for each destination.
- On collapsed mode, show tooltips and accessible labels.

### Top bar
Include:
- Breadcrumbs or current section name.
- Global patient search (where appropriate).
- Notifications / review queue indicator.
- Help link.
- User profile menu.

Do not show sensitive patient details in notifications or browser-visible snippets unnecessarily.

---

## 7. Page-by-page UI specification

## 7.1 Sign-in page

**Purpose:** provide secure access to the application.

### Layout
- Split layout on desktop: brand/intro panel on the left, sign-in form on the right.
- Single-column form on mobile.
- Background: `#F5F8FA`; white sign-in card.
- Keep the brand panel understated, with a simple line illustration or abstract medical-data motif.

### Elements
- MediTrace logo and tagline.
- Email or username field.
- Password field with show/hide control.
- Remember-me option only if permitted by the authentication policy.
- Sign-in button.
- Forgot-password link.
- Optional organisation sign-in / SSO entry if implemented.

### Interaction states
- Default, focused, invalid, submitting, disabled, and success/error feedback.
- Never reveal whether an account exists in a password-reset response if that would expose account information.

## 7.2 Dashboard

**Purpose:** provide a quick overview and guide the user to the next useful task.

### Header
- Heading: **Dashboard**.
- Supporting copy: “Review prescription activity and medication records.”
- Patient selector/search when the dashboard is scoped to a patient.
- Primary CTA: **Upload prescription**.

### Summary cards
Recommended cards:
1. Prescriptions uploaded.
2. Medicine entries extracted.
3. Possible repeated medicine entries to review.
4. Items awaiting verification.

Each card should show:
- Label.
- Large value.
- Small explanation or date range.
- Optional icon in a pale tinted square.

Do not use fixed example values in production. The numbers in mock-ups should be clearly marked as sample data.

### Main dashboard sections
- **Recent prescriptions:** file name, patient, date on prescription, upload date, processing state, and action.
- **Review queue:** uncertain medicine extractions, possible matches, and records awaiting human verification.
- **Recent activity:** who uploaded or reviewed an item and when, subject to the product's audit and privacy model.
- **Quick actions:** upload prescription, open a patient, compare prescriptions.

### Empty state
When no data exists, show a short explanation and a prominent **Upload first prescription** action. Do not show empty charts with misleading zero trends.

## 7.3 Patients page

**Purpose:** locate the correct person and keep records separated.

### Patient list/table fields
- Patient identifier (prefer an internal ID or masked identifier where appropriate).
- Display name (only for authorised users).
- Date of birth or age only if needed and permitted.
- Number of prescriptions.
- Last record activity.
- Review status.
- Actions: open profile, view history.

### Search and filtering
- Search by permitted patient identifiers.
- Filters: recently updated, has items to review, has prescriptions, archived (if supported).
- Add a patient flow should collect only necessary information.

### Patient profile header
- Patient display name and unique internal identifier.
- Relevant demographics only where necessary.
- Last updated date.
- Actions: upload prescription, compare prescriptions, export summary (role-controlled).

## 7.4 Prescription upload page

**Purpose:** add one or more prescription files to the correct patient record.

### Upload card
- Large drag-and-drop target.
- Button: **Browse files**.
- Supported file formats: PDF, JPG, JPEG, PNG (adjust to actual backend capability).
- Maximum file size and page count shown clearly from the implemented system limits.
- Multi-file upload support if available.
- Patient selection or a clear patient context indicator before upload.

### Upload flow
1. Select the patient.
2. Add prescription file(s).
3. Preview each file.
4. Add optional source details (prescriber, facility, prescription date) where appropriate.
5. Confirm upload.
6. Show processing progress.
7. Display extraction results and confidence/review status.

### File list states
- Waiting to upload.
- Uploading.
- Uploaded.
- Processing.
- Processed.
- Failed — with a clear retry action and reason where safe to display.

### Preview layout
- Document preview on the left (desktop).
- Extracted prescription metadata on the right.
- Page navigation for multi-page PDFs.
- Zoom and rotate controls where supported.
- Highlight the source region associated with a selected extracted item if the extraction service provides coordinates.

## 7.5 Medicine identification / extraction review

**Purpose:** let users inspect what the system read from a prescription.

### Recommended layout
Two-panel desktop layout:
- **Left:** prescription image/PDF preview.
- **Right:** extracted medicine list and editable details.

### Medicine record fields
- Extracted medicine name (raw OCR text).
- Normalised medicine name (if resolved).
- Brand name (when identified).
- Active ingredient(s) (when reliably identified).
- Strength/concentration.
- Dosage form (tablet, capsule, syrup, injection, etc.).
- Dose instruction (as written; preserve original wording).
- Route (if extracted).
- Frequency (as written).
- Duration (as written).
- Start/end date (only when explicitly available or appropriately derived and clearly labelled).
- Source prescription and page number.
- Extraction confidence / review state.

### Review interaction
- Allow corrections to extracted text without losing the original OCR value.
- Show which values were machine-extracted and which were manually edited.
- Require confirmation before saving corrections.
- Keep an audit record according to the application's privacy and governance requirements.
- Clearly show missing or unreadable values as **Not detected** rather than guessing.

## 7.6 Prescription comparison page

**Purpose:** compare medicines found in two or more prescriptions from the same patient.

### Header controls
- Patient identity/context.
- Prescription selector (multi-select).
- Date range filter.
- Compare button.
- Clear comparison action.

### Comparison table columns
Recommended columns:
1. Medicine / active ingredient.
2. Brand (if present).
3. Strength.
4. Dosage form.
5. Instructions as written.
6. Prescription date/source.
7. Match classification.
8. Review state.

### Match classifications
Use explicit, explainable labels:
- **Exact text match:** same extracted medicine text after the defined normalisation rules.
- **Same active ingredient:** active ingredient appears to match; strength/form may differ.
- **Possible match:** partial or uncertain similarity; requires verification.
- **Potential overlap:** system flags a possible therapeutic or ingredient overlap for qualified review.
- **No match found:** no matching record detected within the selected prescriptions.

Do not collapse these into one generic “duplicate” label. A medicine with the same active ingredient but a different strength, dosage form, release mechanism, or route is not automatically interchangeable.

### Row interaction
Selecting a row should open a detail panel showing:
- Each occurrence and its source prescription.
- The extracted values side by side.
- Match explanation (which fields matched and which differed).
- Confidence score only if the score is calibrated and meaningful; explain it in plain language.
- Verification controls for authorised users.

### Possible duplicate alert
Use amber for a review prompt, not a red emergency banner unless a qualified, validated rule specifically warrants it.

Example text:
> “These entries may contain the same active ingredient. Review the strength, form, instructions, and prescription dates before drawing a conclusion.”

## 7.7 Medication history / timeline

**Purpose:** show when medicine entries appeared across a patient's prescriptions.

### Timeline structure
- Vertical timeline grouped by month or year.
- Each event shows prescription date, source, medicine entries, and review state.
- Filters for medicine, active ingredient, date range, and source.
- Distinguish prescription date from upload date.
- Show changes in strength/form/instructions as differences, not as implied treatment changes unless the source supports that interpretation.

### Timeline item
- Date.
- Prescription or source document.
- Medicine name and strength.
- Original instructions as written.
- Link to open the source prescription.
- Verification status.

## 7.8 Reports page

**Purpose:** create a traceable summary for authorised review.

### Report options
- Patient medication record summary.
- Prescription comparison summary.
- Unverified extraction report.
- Potential duplicate / overlap review list.

### Report content
- Report generation date/time.
- Patient identifier and scope of records included.
- Prescriptions included (with dates and source labels).
- Medicine entries and their source references.
- Match classification and verification status.
- Limitations and items not detected.
- Reviewer identity where the product's governance model requires it.

### Export controls
- PDF / CSV only if supported by the application.
- Confirm export scope before generating.
- Make it clear when a report contains unverified machine-extracted information.

## 7.9 Settings page

Suggested sections:
- User profile.
- Organisation / clinic details (if relevant).
- Roles and permissions (admin only).
- Notification preferences.
- Language and regional formatting.
- Data retention and privacy information.
- Audit log (role-controlled).

---

## 8. Reusable component design

### Buttons

| Type | Background | Text | Border | Use |
|---|---|---|---|---|
| Primary | `#0D9488` | `#FFFFFF` | `#0D9488` | Main action, e.g. Upload prescription |
| Primary hover | `#0F766E` | `#FFFFFF` | `#0F766E` | Hover state |
| Secondary | `#FFFFFF` | `#17324D` | `#CBD5E1` | Supporting action |
| Secondary hover | `#F1F5F9` | `#17324D` | `#94A3B8` | Hover state |
| Tertiary | Transparent | `#245C83` | Transparent | Low-emphasis action or link |
| Danger | `#B42318` | `#FFFFFF` | `#B42318` | Destructive action, with confirmation |
| Disabled | `#E2E8F0` | `#94A3B8` | `#E2E8F0` | Unavailable action |

Button guidance:
- Standard height: 40 px; large primary action: 44–48 px.
- Include a visible focus ring.
- Use verbs that describe the action: “Upload prescription”, “Save changes”, “Review match”.
- Show loading state and prevent accidental double submission.

### Inputs and forms
- Height: 42–44 px.
- Background: `#FFFFFF`.
- Border: `#CBD5E1`.
- Text: `#263746`.
- Placeholder: `#718096` (check contrast and do not use as the only label).
- Focus border: `#0D9488` with a visible outer focus ring.
- Error border: `#B42318` plus an explanatory message.
- Always provide a persistent label; do not rely only on placeholder text.

### Cards
- Background: `#FFFFFF`.
- Border: `1px solid #E2E8F0`.
- Radius: 12 px.
- Padding: 20–24 px.
- Shadow: optional and very subtle.
- Avoid putting every small item in its own card; use dividers and whitespace where a table or list is clearer.

### Tables
- Header background: `#F1F5F9`.
- Header text: `#475569`.
- Body text: `#263746`.
- Row divider: `#E2E8F0`.
- Hover row: `#F5F8FA`.
- Selected row: `#EAF7F5` with a visible selection indicator.
- Recommended row height: 56–64 px for medicine data.
- Use sticky headers for long tables when useful.
- On smaller screens, provide a card view or intentional horizontal scrolling with clear affordance.

### Status badges
- Pill radius: 999 px.
- Font: 12 px, weight 600.
- Padding: 4 px 9 px.
- Include a short text label and optional icon.
- Do not use a badge as the only place to explain a clinical concern.

### Tabs
- Selected tab text: `#17324D`.
- Selected underline: `#0D9488` (2–3 px).
- Unselected text: `#64748B`.
- Include keyboard navigation and a clear focus state.

### Modals and drawers
- Modal width: 480–640 px for standard tasks; wider for complex comparisons.
- Overlay: `rgba(23, 50, 77, 0.45)`.
- Surface: `#FFFFFF`.
- Radius: 14 px.
- Keep destructive actions visually separate from the primary confirmation action.
- On mobile, prefer a full-height drawer or full-screen flow for complex forms.

### Toasts and alerts
- Success: `#EAF7EE` / `#166534`.
- Information: `#EAF3FA` / `#245C83`.
- Warning: `#FFF4DE` / `#92400E`.
- Error: `#FCEBEC` / `#B42318`.
- Include concise text and a close control where appropriate. Important errors must remain visible until addressed; do not rely only on a short-lived toast.

### Icons
Use **Lucide React** for a consistent outline icon style.
Suggested icons:
- Dashboard: `LayoutDashboard`
- Patients: `Users`
- Upload: `UploadCloud`
- Prescription: `FileText`
- Medicine: `Pill`
- Compare: `GitCompareArrows` or `ArrowLeftRight`
- Timeline: `History`
- Reports: `ChartNoAxesCombined` or `FileBarChart`
- Settings: `Settings`
- Review: `ClipboardCheck`
- Warning: `AlertTriangle`
- Search: `Search`
- Notifications: `Bell`
- User: `CircleUserRound`

Use 18–20 px icons for navigation and 16–18 px icons for inline actions. Pair unfamiliar icons with text labels.

---

## 9. Interaction and state design

Every interactive component should have defined states. At minimum, design for:
- Default.
- Hover.
- Focus-visible (keyboard focus).
- Active / selected.
- Disabled.
- Loading.
- Success.
- Empty.
- Error.
- Permission denied (where relevant).

### Prescription processing states
1. Not uploaded.
2. Upload queued.
3. Uploading.
4. Uploaded.
5. Processing / extracting.
6. Extraction complete — review required.
7. Verified / reviewed.
8. Processing failed — retry or manual entry.

### Medicine matching states
- Not assessed.
- Exact text match.
- Same active ingredient — attributes differ or need checking.
- Possible match — uncertain.
- Potential overlap — requires qualified review.
- Reviewed and confirmed.
- Reviewed and dismissed.

Store the machine result and the human review result separately. A user's decision should not overwrite or erase the original model output.

### Confirmation patterns
Ask for confirmation before:
- Deleting a prescription or medicine record.
- Removing a patient profile.
- Overwriting corrected extraction data.
- Exporting sensitive patient information, where a confirmation is appropriate.

### Search patterns
- Debounce search input.
- Provide a clear button.
- Preserve the entered search term when returning from a detail view.
- Provide “No results” and “Search error” states.
- Do not expose patient search results to users without the required access.

---

## 10. Accessibility and clinical usability

Target **WCAG 2.2 AA** as the accessibility baseline where practical.

- Ensure text and interactive controls have sufficient contrast.
- Do not communicate verified/review/critical status by colour alone; use text and icons.
- Provide visible keyboard focus states.
- Make all controls keyboard accessible.
- Use semantic headings, labels, buttons, tables, and landmarks.
- Associate form errors with their inputs.
- Give icon-only buttons accessible names and tooltips.
- Respect reduced-motion preferences.
- Do not use small text for medicine strength, dosage, or important warnings.
- Avoid relying on hover to reveal essential information.
- Use plain language for uncertainty and review instructions.

### Suggested focus ring

```css
:focus-visible {
  outline: 3px solid rgba(13, 148, 136, 0.35);
  outline-offset: 2px;
}
```

---

## 11. Privacy, security, and safety considerations for the UI

This is a medical-data application. The visual design and interaction flow should reinforce careful handling of sensitive records.

- Show patient details only to authorised users.
- Use role-based controls for viewing, editing, reviewing, and exporting records.
- Do not include patient names or medicine details in unnecessary toast notifications, URLs, or browser page titles.
- Display a clear patient context before uploading or editing a prescription to reduce wrong-patient errors.
- Consider an explicit patient confirmation step before attaching a file to a record.
- Clearly mark extracted content that has not been verified.
- Keep source prescription references available for every medicine entry.
- Preserve original prescription files and original OCR text according to the product's retention policy.
- Keep a review history where auditability is required.
- Do not present similarity detection as a diagnosis, interaction checker, or treatment recommendation unless those capabilities have been separately validated and appropriately governed.
- Do not instruct patients to stop, start, or change a medicine based only on an automated match alert. Route potentially significant findings to an appropriately qualified healthcare professional.
- Use secure transport, protected storage, and appropriate access controls in the backend; frontend styling alone does not make medical data secure.

The applicable privacy, health-data, and medical-device requirements depend on the product's intended use, deployment location, and users. Confirm those requirements with qualified legal, security, and clinical stakeholders before production use.

---

## 12. Recommended frontend technology stack

A suitable implementation stack (adapt to the existing project):

| Need | Suggested technology |
|---|---|
| UI framework | React |
| Language | TypeScript |
| Build tool | Vite or the project's existing framework |
| Styling | Tailwind CSS, with CSS variables for theme tokens |
| Components | Reusable project components; optionally shadcn/ui as a base |
| Icons | Lucide React |
| Charts | Recharts (only where trends add value) |
| Tables | TanStack Table for sorting, filtering, and pagination |
| Forms | React Hook Form + Zod (if suitable for the project) |
| Routing | React Router or framework-native routing |
| Animation | Framer Motion, used sparingly |
| PDF preview | A maintained PDF viewer compatible with the project |
| API state | TanStack Query or the existing API/data layer |

Do not add every library by default. Use the project's current dependencies where possible and keep the bundle lean.

---

## 13. Suggested frontend folder structure

```text
src/
├── app/
│   ├── App.tsx
│   ├── routes.tsx
│   └── providers.tsx
├── assets/
│   ├── logo/
│   └── illustrations/
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Topbar.tsx
│   │   └── PageHeader.tsx
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── EmptyState.tsx
│   │   └── DataTable.tsx
│   ├── medicines/
│   │   ├── MedicineDetails.tsx
│   │   ├── MedicineMatchBadge.tsx
│   │   ├── MedicineComparisonTable.tsx
│   │   └── MedicineReviewPanel.tsx
│   └── prescriptions/
│       ├── PrescriptionUploader.tsx
│       ├── PrescriptionPreview.tsx
│       └── PrescriptionStatus.tsx
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── patients/
│   ├── prescriptions/
│   ├── medicine-analysis/
│   ├── comparison/
│   ├── timeline/
│   ├── reports/
│   └── settings/
├── hooks/
├── lib/
├── services/
├── styles/
│   ├── globals.css
│   └── theme.css
├── types/
└── main.tsx
```

This is a suggested structure, not a requirement. Keep existing project conventions if the application is already set up.

---

## 14. CSS theme variables

Add these tokens to a global theme file (for example, `src/styles/theme.css`).

```css
:root {
  /* Brand */
  --color-brand-900: #17324D;
  --color-brand-800: #1E4563;
  --color-brand-700: #245C83;
  --color-brand-600: #0D9488;
  --color-brand-teal-dark: #0F766E;
  --color-brand-100: #D7F0EC;
  --color-brand-50: #EAF7F5;

  /* Neutral */
  --color-text-strong: #17212B;
  --color-text: #263746;
  --color-text-secondary: #475569;
  --color-text-muted: #64748B;
  --color-border-strong: #CBD5E1;
  --color-border: #E2E8F0;
  --color-surface-subtle: #F1F5F9;
  --color-background: #F5F8FA;
  --color-surface: #FFFFFF;

  /* Semantic */
  --color-success-text: #166534;
  --color-success-bg: #EAF7EE;
  --color-success-border: #B7E4C7;
  --color-info-text: #245C83;
  --color-info-bg: #EAF3FA;
  --color-info-border: #C7DDEC;
  --color-warning-text: #92400E;
  --color-warning-bg: #FFF4DE;
  --color-warning-border: #F5D79A;
  --color-danger-text: #B42318;
  --color-danger-bg: #FCEBEC;
  --color-danger-border: #F3C1C1;

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 68px;
  --content-max-width: 1440px;
  --radius-control: 8px;
  --radius-card: 12px;
  --radius-modal: 14px;

  /* Elevation */
  --shadow-card: 0 2px 8px rgba(23, 50, 77, 0.05);
  --shadow-popover: 0 8px 24px rgba(23, 50, 77, 0.12);

  /* Typography */
  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system,
    BlinkMacSystemFont, "Segoe UI", sans-serif;
}

html {
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-background);
}

body {
  margin: 0;
  min-width: 320px;
  background: var(--color-background);
}

:focus-visible {
  outline: 3px solid rgba(13, 148, 136, 0.35);
  outline-offset: 2px;
}

::selection {
  color: #17324D;
  background: #D7F0EC;
}
```

---

## 15. Optional Tailwind theme mapping

If the project uses Tailwind CSS, map the CSS variables into its theme rather than maintaining duplicate colour values. The exact configuration format depends on the installed Tailwind version.

Example conceptual mapping:

```js
// tailwind.config.js — example for a Tailwind setup using theme extensions
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          900: "#17324D",
          800: "#1E4563",
          700: "#245C83",
          600: "#0D9488",
          tealDark: "#0F766E",
          100: "#D7F0EC",
          50: "#EAF7F5",
        },
        clinical: {
          background: "#F5F8FA",
          surface: "#FFFFFF",
          text: "#263746",
          muted: "#64748B",
          border: "#E2E8F0",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
      },
      boxShadow: {
        card: "0 2px 8px rgba(23, 50, 77, 0.05)",
      },
    },
  },
  plugins: [],
};
```

Check your installed Tailwind version before copying this configuration. Newer versions may use a CSS-first configuration approach.

---

## 16. Example page composition

A typical desktop dashboard can follow this structure:

```text
┌──────────────────────┬─────────────────────────────────────────────────────┐
│ MediTrace            │ Breadcrumb / Patient Search / Help / Profile        │
│                      ├─────────────────────────────────────────────────────┤
│ Dashboard            │ Dashboard                         [Upload prescription]
│ Patients             │ Review prescription activity and medication records │
│ Upload prescription  │                                                     │
│ Medicine analysis    │ ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌───────┐ │
│ Compare prescriptions│ │ Prescriptions│ │ Medicines │ │ Possible  │ │Needs  │ │
│ Medication timeline │ │ uploaded   │ │ extracted  │ │ matches   │ │review │ │
│ Reports              │ └────────────┘ └────────────┘ └───────────┘ └───────┘ │
│ Settings             │                                                     │
│                      │ ┌──────────────────────────┐ ┌────────────────────┐ │
│                      │ │ Recent prescriptions     │ │ Review queue       │ │
│                      │ │                          │ │                    │ │
│                      │ └──────────────────────────┘ └────────────────────┘ │
│                      │                                                     │
│                      │ ┌─────────────────────────────────────────────────┐ │
│                      │ │ Recent activity / medication overview           │ │
│                      │ └─────────────────────────────────────────────────┘ │
└──────────────────────┴─────────────────────────────────────────────────────┘
```

On the medicine comparison page, prioritise the comparison table and source traceability rather than dashboard-style metric cards.

---

## 17. Recommended microcopy

Use consistent, plain-language labels throughout the application.

| Situation | Preferred wording |
|---|---|
| File action | Upload prescription |
| OCR in progress | Reading prescription… |
| Extraction completed | Medicine details extracted |
| Low-confidence extraction | Some details need review |
| Similar medicine records | Possible match |
| Same ingredient identified | Same active ingredient detected |
| Potential duplicate | Potential duplicate — review required |
| No matching record | No match found in selected prescriptions |
| Missing field | Not detected |
| User correction | Manually verified |
| Source link | View source prescription |
| Failed processing | We couldn't process this file. Try again or enter the details manually. |

Avoid definitive clinical statements such as “unsafe combination” unless a validated clinical decision-support function supports that exact conclusion and the appropriate governance is in place.

---

## 18. Logo and branding guidance

### Logo concept
Use a simple symbol combining:
- A rounded medical cross or shield outline.
- A small pill/capsule or two linked record lines.
- The wordmark **MediTrace**.

Keep the symbol simple enough to work at 24 px in the sidebar. Avoid detailed illustrations or symbols that imply emergency care or clinical certification.

### Logo colours
- Main logo: `#17324D`.
- Accent detail: `#0D9488`.
- Reverse logo on dark background: `#FFFFFF` with teal accent `#0D9488`.

### Favicon
Use the simplified symbol only, ideally on a white or navy rounded-square background.

---

## 19. Suggested implementation order

Build the project in this order so the design system is stable before the complex screens are implemented.

1. **Theme foundation:** colours, typography, spacing, layout shell, buttons, inputs, cards, badges.
2. **App navigation:** sidebar, top bar, breadcrumbs, responsive drawer.
3. **Patient context:** patient list, patient profile header, patient selector.
4. **Prescription upload:** drag-and-drop, file queue, preview, processing states.
5. **Medicine extraction review:** source preview, extracted fields, corrections, verification.
6. **Medicine comparison:** multi-prescription selector, comparison table, match explanations.
7. **Medication timeline:** chronological record view and filters.
8. **Reports and settings:** summaries, export controls, permissions, preferences.
9. **Polish:** accessibility, responsive testing, empty/error/loading states, and usability testing.

### Minimum viable frontend
For an effective first demo, implement these flows end to end:
- Select or create a patient.
- Upload two or more prescriptions for that patient.
- Display extracted medicine entries with their source prescription.
- Compare entries across prescriptions.
- Flag possible matches separately from confirmed matches.
- Let an authorised reviewer verify or correct the result.

---

## 20. Frontend acceptance checklist

### Branding and layout
- [ ] MediTrace wordmark and tagline are consistent.
- [ ] All screens use the shared colour and typography tokens.
- [ ] Sidebar and top bar work at desktop, tablet, and mobile widths.
- [ ] Main content has consistent spacing and alignment.

### Prescription workflow
- [ ] Upload makes the patient context explicit.
- [ ] Supported file types and size limits are visible.
- [ ] Upload, processing, success, and error states are designed.
- [ ] A user can open the source prescription from an extracted medicine entry.

### Medicine analysis
- [ ] Raw extracted text is distinguishable from normalised medicine data.
- [ ] Missing details display as “Not detected”, not guessed values.
- [ ] Strength, form, route, and instructions remain visible during comparison.
- [ ] Exact match, same ingredient, possible match, and potential overlap are distinct states.
- [ ] Match explanations identify which fields match and which differ.
- [ ] Human verification is recorded separately from the automated result.

### Accessibility and privacy
- [ ] Keyboard focus is visible.
- [ ] Status is conveyed through text/icons as well as colour.
- [ ] Form labels and error messages are accessible.
- [ ] Sensitive patient data is only shown in the correct authorised context.
- [ ] Export and destructive actions have appropriate safeguards.

### Data integrity and clinical safety
- [ ] The interface does not silently discard original prescription data or OCR output.
- [ ] Every extracted medicine can be traced to its source document.
- [ ] The UI does not recommend medication changes based solely on similarity detection.
- [ ] Unverified results are clearly labelled as unverified.

---

## 21. Final design recommendation

Use **MediTrace — Modern Clinical Intelligence** as the frontend theme:

- **Primary navy:** `#17324D`
- **Primary teal:** `#0D9488`
- **Application background:** `#F5F8FA`
- **Card surface:** `#FFFFFF`
- **Primary text:** `#263746`
- **Warning:** `#FFF4DE` / `#92400E`
- **Critical:** `#FCEBEC` / `#B42318`

The most important screen is the **Prescription Comparison** page. Make it the centrepiece of the project: show medicines side by side, preserve their strength and dosage-form differences, provide direct links to the original prescriptions, and explain why the system considers two entries similar. This will make the frontend communicate the actual value of the project rather than looking like a generic hospital dashboard.

> **Implementation note:** This document defines the frontend theme and recommended interaction patterns. It does not define a clinically validated medicine-matching algorithm. Matching rules, confidence thresholds, drug terminology sources, privacy controls, and clinical review processes must be designed and validated separately before real patient use.

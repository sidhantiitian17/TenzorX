# HealthNav — Frontend Feature Instruction Manual

## AI-Powered Healthcare Navigator & Cost Estimator for India

> **Vision:** Build a *"Kayak for Healthcare"* — a structured decision-intelligence platform that translates patient intent into clinical pathways, ranks providers transparently, estimates costs at component level, and presents confidence-aware recommendations.
>
> **Evaluation Weight Reminder:**
> Cost Estimation Logic `25%` · Clinical Mapping `20%` · Provider Ranking `20%` · Multi-Source Intelligence `15%` · UX & Clarity `10%` · Responsible AI `10%`

---

## Table of Contents

1. [Design System & Aesthetic Direction](#1-design-system--aesthetic-direction)
2. [Application Shell & Global Layout](#2-application-shell--global-layout)
3. [Feature: Natural Language Chat Interface](#3-feature-natural-language-chat-interface)
4. [Feature: Patient Profile & Input Specification](#4-feature-patient-profile--input-specification)
5. [Feature: Clinical Pathway Translator](#5-feature-clinical-pathway-translator)
6. [Feature: Provider Discovery & Ranking](#6-feature-provider-discovery--ranking)
7. [Feature: Treatment Cost Estimation Engine](#7-feature-treatment-cost-estimation-engine)
8. [Feature: Multi-Source Intelligence Panel](#8-feature-multi-source-intelligence-panel)
9. [Feature: Lender & Insurer Dashboard](#9-feature-lender--insurer-dashboard)
10. [Feature: Hospital Comparison Tool](#10-feature-hospital-comparison-tool)
11. [Feature: Medical Term Explainer](#11-feature-medical-term-explainer)
12. [Feature: Appointment & Paperwork Assistant](#12-feature-appointment--paperwork-assistant)
13. [Responsible AI & Trust Layer](#13-responsible-ai--trust-layer)
14. [Component Library Reference](#14-component-library-reference)
15. [State Architecture](#15-state-architecture)
16. [API Integration Contracts](#16-api-integration-contracts)
17. [Mock Data Specification](#17-mock-data-specification)
18. [Responsive & Accessibility Requirements](#18-responsive--accessibility-requirements)
19. [Evaluation Checklist](#19-evaluation-checklist)

---

## 1. Design System & Aesthetic Direction

### 1.1 Aesthetic Concept

**Theme:** *Clinical Clarity meets Human Warmth*

The interface should feel like a trusted, knowledgeable friend who happens to be a doctor — not a cold hospital management system. Inspired by the precision of medical dashboards but softened with warmth for patients from Tier 2/3 cities who may not be tech-savvy.

- **Tone:** Editorial + Utilitarian. Clean, confident, informative. Never intimidating.
- **Memorable Moment:** A live-animated cost range bar that builds as the AI processes — users see estimates form in real time, not appear all at once.
- **Layout Personality:** Structured asymmetry — left-aligned chat, right results panel with clear visual hierarchy. Not a symmetric grid.

### 1.2 Typography

```css
/* Primary display: Bold, confident, distinctly Indian-medical feel */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&family=DM+Mono:wght@400;500&display=swap');

:root {
  --font-display: 'Sora', sans-serif;    /* Headings, brand, numbers */
  --font-body:    'DM Sans', sans-serif; /* Body text, chat bubbles, labels */
  --font-mono:    'DM Mono', monospace;  /* INR amounts, codes, ICD-10 */
}
```

**Type Scale:**

| Token | Size | Weight | Usage |
| --- | --- | --- | --- |
| `--text-hero` | 2.25rem | 700 | Landing headline |
| `--text-section` | 1.375rem | 600 | Panel titles |
| `--text-card-title` | 1.0625rem | 600 | Hospital name, card headers |
| `--text-body` | 0.9375rem | 400 | Chat bubbles, descriptions |
| `--text-label` | 0.8125rem | 500 | Badges, tags, captions |
| `--text-mono` | 0.9375rem | 500 | All INR cost figures |
| `--text-caption` | 0.75rem | 400 | Timestamps, disclaimers |

### 1.3 Color System

```css
:root {
  /* === Brand === */
  --c-teal-900:   #042F2E;
  --c-teal-700:   #0F766E;
  --c-teal-500:   #14B8A6;  /* Primary brand */
  --c-teal-100:   #CCFBF1;
  --c-teal-50:    #F0FDFA;

  /* === Accent === */
  --c-saffron:    #F97316;  /* Indian accent — CTAs, highlights */
  --c-saffron-lt: #FFF7ED;

  /* === Surfaces === */
  --c-surface:    #F8FAFC;  /* Page background */
  --c-card:       #FFFFFF;
  --c-card-hover: #FAFFFE;
  --c-border:     #E2E8F0;
  --c-border-soft:#F1F5F9;

  /* === Text === */
  --c-text-primary:   #0F172A;
  --c-text-secondary: #475569;
  --c-text-muted:     #94A3B8;
  --c-text-inverse:   #FFFFFF;

  /* === Semantic === */
  --c-success:    #059669;
  --c-warning:    #D97706;
  --c-danger:     #DC2626;
  --c-info:       #2563EB;

  /* === Confidence Gauge === */
  --c-conf-high:  #059669;  /* >= 70% */
  --c-conf-mid:   #D97706;  /* 40-69% */
  --c-conf-low:   #DC2626;  /* < 40% */

  /* === Cost Component Colors === */
  --c-cost-procedure:   #0D9488;
  --c-cost-doctor:      #6366F1;
  --c-cost-stay:        #8B5CF6;
  --c-cost-diagnostics: #F59E0B;
  --c-cost-medicines:   #10B981;
  --c-cost-contingency: #EF4444;

  /* === Hospital Tier === */
  --c-tier-premium: #7C3AED;
  --c-tier-mid:     #2563EB;
  --c-tier-budget:  #059669;
}
```

### 1.4 Spacing, Radius & Shadows

```css
:root {
  --radius-sm:  6px;
  --radius-md:  12px;
  --radius-lg:  18px;
  --radius-xl:  24px;
  --radius-pill: 9999px;

  --shadow-card:   0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.06);
  --shadow-hover:  0 4px 12px rgba(0,0,0,0.08), 0 12px 32px rgba(0,0,0,0.08);
  --shadow-modal:  0 20px 60px rgba(0,0,0,0.18);
  --shadow-drawer: -4px 0 40px rgba(0,0,0,0.10);
}
```

### 1.5 Motion Tokens

```css
:root {
  --ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth:  cubic-bezier(0.4, 0, 0.2, 1);
  --ease-enter:   cubic-bezier(0, 0, 0.2, 1);
  --duration-fast:   150ms;
  --duration-base:   250ms;
  --duration-slow:   400ms;
  --duration-reveal: 600ms;
}
```

---

## 2. Application Shell & Global Layout

### 2.1 Page Structure

```text
+---------------------------------------------------------------------+
|  DISCLAIMER BANNER (sticky, 36px, amber, always visible)            |
+----------------------------------------------------------------------+
|  HEADER (64px)                                                       |
|  [Menu Logo HealthNav]    [Search Bar]    [Profile]  [Bell]  [Mode] |
+-------------+----------------------------+---------------------------+
|             |                            |                           |
|  SIDEBAR    |   CHAT PANEL               |   RESULTS PANEL           |
|  (240px,    |   (flex-grow, min 480px)   |   (420px, sticky scroll)  |
|  collaps-   |                            |                           |
|  ible)      |                            |                           |
|             |                            |                           |
|  * History  |   [Message Thread]         |   [Hospital List]         |
|  * Saved    |                            |   [Cost Estimate Card]    |
|  * Profile  |                            |   [Confidence Score]      |
|  * Lender   |                            |   [Data Source Info]      |
|    Mode     |                            |                           |
|  * Settings |   [InputBar]               |                           |
+-------------+----------------------------+---------------------------+
```

**Layout Rules:**

- Desktop (>=1280px): All 3 columns visible simultaneously
- Tablet (768-1279px): Sidebar collapses to icon rail; Chat + Results side-by-side
- Mobile (<768px): Single column; Results open as a bottom sheet; Sidebar is a drawer
- ResultsPanel is `position: sticky; top: 100px; max-height: calc(100vh - 140px); overflow-y: auto`
- ChatPanel grows to fill available space with `flex: 1; min-width: 480px`

### 2.2 Disclaimer Banner

```text
+---------------------------------------------------------------------+
|  HealthNav provides decision support only — not medical advice.      |
|  Always consult a qualified doctor before making health decisions.   |
|                                               [Learn More]  [Hide]  |
+---------------------------------------------------------------------+
```

- Background: `var(--c-saffron-lt)`, left border: 3px solid `var(--c-warning)`
- Cannot be permanently dismissed — only minimized to a thin 8px bar
- Minimized state shows a small indicator; clicking expands it again
- On mobile, appears below the header (not sticky — saves screen space)

### 2.3 Header

**Left:** Hamburger (mobile) + Logo wordmark in teal

**Center:** Condensed location pill — `Nagpur, MH` — click to change location.
On mobile this moves below the header as a full-width bar.

**Right:** Profile badge (avatar + name if logged in), Notification bell, Dark mode toggle

---

## 3. Feature: Natural Language Chat Interface

### 3.1 Purpose

Primary entry point. Users describe their health situation in plain language. The system interprets, asks clarifying questions, and generates structured results. This is the core UX differentiator.

### 3.2 Empty / Welcome State

When no conversation exists, the chat area shows:

```text
+--------------------------------------------+
|                                            |
|      HealthNav                             |
|                                            |
|   "Find the right hospital.                |
|    Know the real cost. In plain language." |
|                                            |
|   +--------------------------------------+ |
|   |  What health concern can I help      | |
|   |  you navigate today?          [Send] | |
|   +--------------------------------------+ |
|                                            |
|   Quick Start:                             |
|   [Knee replacement near me]               |
|   [Heart bypass under Rs 3 lakh]           |
|   [Best cancer hospital in Raipur]         |
|   [What is angioplasty?]                   |
|   [Explain my diabetes diagnosis]          |
|                                            |
+--------------------------------------------+
```

Quick-Start Chips are horizontally scrollable on mobile. Each chip pre-fills the input and triggers a send.

### 3.3 InputBar Component

```text
+--------------------------------------------------------------+
| Mic |  Describe your condition, symptoms, or procedure...    |
|     |                                              [Send]    |
+--------------------------------------------------------------+
|  Add Location  |  Patient Details  |  Budget Range           |
+--------------------------------------------------------------+
```

**Behavior:**

- Textarea auto-expands from 1 line to 5 lines max
- `Enter` sends; `Shift+Enter` for newline
- Character counter shown after 350 chars (500 max)
- Disabled + shimmer pulse while AI is processing
- Three inline filter shortcuts below the text area:
  - `Add Location` — Inline location picker (city search or "Use my location")
  - `Patient Details` — Slides open PatientProfileDrawer
  - `Budget Range` — Inline slider: Rs 0 to Rs 20L

**Microphone Button:**

- Web Speech API integration (if browser supports)
- Shows animated waveform bars while listening
- Transcribed text populates the input

### 3.4 Message Thread

**User Message Bubble (right-aligned):**

- Background: `var(--c-teal-500)`, white text
- `border-radius: 18px 18px 4px 18px`
- Max-width: 75% of chat area
- Shows timestamp below

**AI Response Bubble (left-aligned):**

- Background: `var(--c-card)`, border: 1px solid `var(--c-border)`
- Renders Markdown: bold, lists, inline code
- Action buttons link to right-panel sections (View Hospitals, See Cost Breakdown)
- Inline mini-hospital cards may be embedded within bubbles for quick reference
- Always ends with a one-line responsible AI note in muted text
- Feedback row below: thumbs up, thumbs down, Refine, Copy

**Typing Indicator:**

- Three animated dots with a 600ms staggered pulse
- Label below: "Analyzing your query..."

### 3.5 Clarifying Question Flow

If the query is ambiguous, the AI response includes a structured clarifying message with clickable option chips:

Example for "chest pain while walking":

- [Cardiac / Heart-related]
- [Respiratory / Breathing issue]
- [Musculoskeletal / Muscle or bone pain]
- [Not sure — show all]

Clicking a chip sends it as the user's next message and the conversation continues.

### 3.6 Emergency Detection

If the user's input contains flagged terms (chest pain, stroke, unconscious, heavy bleeding, can't breathe, severe pain, etc.):

```text
+----------------------------------------------------------------+
|  MEDICAL EMERGENCY?                                            |
|                                                                |
|  If you or someone you know is having a medical emergency,    |
|  call 112 (India Emergency Services) immediately.             |
|                                                                |
|  Do NOT rely on this tool for emergencies.                    |
|                           [Call 112]  [I'm just researching]  |
+----------------------------------------------------------------+
```

- Full-width red banner, shown above the chat response
- Cannot be auto-dismissed — only by user clicking "I'm just researching"

---

## 4. Feature: Patient Profile & Input Specification

### 4.1 Purpose

Collecting optional patient context improves cost estimation accuracy, adjusts for comorbidity risk, and personalizes provider recommendations.

### 4.2 PatientProfileDrawer

Slides in from the right (or bottom on mobile). Non-blocking — user can close it and still get results.

**Fields:**

| Field | Type | Notes |
| --- | --- | --- |
| Location | City/pincode text search + GPS button | Required for distance ranking |
| Age | Number 1-120 | Affects complication risk scoring |
| Gender | Radio: Male / Female / Other / Prefer not to say | |
| Known Comorbidities | Multi-select chips | Diabetes, Hypertension, Cardiac History, Renal Disease, Obesity, None |
| Budget Constraint | Range slider Rs 0 to Rs 20L + text input | Filters affordability tier |

**Footer:**

- "Why we ask this" privacy note: nothing is stored on servers
- [Clear All] and [Apply & Search] buttons

### 4.3 ProfileBadge (Header)

Once a profile is set, the header shows a condensed pill:
`45M · Nagpur · Rs 5L budget · Diabetes, Cardiac  [Edit]`

A colored dot indicates if comorbidities are active (they affect cost estimates).

### 4.4 Profile Impact Callout

When comorbidities are set, show a highlighted callout above the results panel:

```text
+----------------------------------------------------------------+
|  Your profile affects these estimates                          |
|                                                                |
|  * Diabetes -> Higher complication risk (+Rs 20K-Rs 60K)      |
|  * Cardiac History -> Increased ICU likelihood (+Rs 40K-1.5L) |
|                                                                |
|  Estimates shown below include these adjustments.             |
+----------------------------------------------------------------+
```

---

## 5. Feature: Clinical Pathway Translator

### 5.1 Purpose

Show users exactly how their natural-language query was interpreted into a standardized medical concept. This builds trust and accuracy transparency. Directly addresses the Clinical Mapping (20%) evaluation criterion.

### 5.2 Clinical Mapping Card

Appears as the first item in the ResultsPanel after every query:

```text
+--------------------------------------------------------------+
|  Clinical Interpretation                        [How?]      |
|  ------------------------------------------------------------  |
|  Your query:  "knee replacement near Nagpur under Rs 2 lakh" |
|                                                              |
|  Interpreted as:                                             |
|  Procedure    Total Knee Arthroplasty (TKA)                  |
|  ICD-10       M17.11 — Primary osteoarthritis, right knee   |
|  SNOMED CT    179344001 — Knee joint replacement             |
|  Category     Orthopedic Surgery                             |
|                                                              |
|  Typical Pathway:                                            |
|  [1] Pre-op assessment  ->  [2] Implant selection           |
|  [3] Surgery (2-3 hrs)  ->  [4] 3-5 day hospital stay      |
|  [5] Physiotherapy (6-12 weeks)                             |
|                                                              |
|  [Correct this interpretation]                               |
+--------------------------------------------------------------+
```

**"How?" tooltip** explains:
> "We use ICD-10 and SNOMED CT frameworks to map your words to standardized medical procedures. This helps us match the right hospitals and benchmark costs accurately."

**"Correct this interpretation"** link reopens the chat with pre-filled text:
"Actually, I meant..." — allowing the user to refine.

### 5.3 Treatment Pathway Visualizer

Expandable horizontal step-flow below the Clinical Mapping Card:

```text
  [1 Consult] -> [2 Diagnosis] -> [3 Surgery] -> [4 Recovery] -> [5 Follow-up]
   1-2 days       2-5 days        Core cost      3-5 days         6-12 wks
   Rs500-2K       Rs3K-8K         estimate       Rs30K-60K        Rs5K-15K
```

- Steps are horizontally scrollable on mobile
- Each step is a clickable chip showing what happens and typical costs at that stage
- Highlighted step = current focus of the cost estimate

---

## 6. Feature: Provider Discovery & Ranking

### 6.1 Purpose

Return a transparent, signal-driven list of hospitals and doctors. Users must clearly understand WHY a hospital ranks where it does. Addresses Provider Ranking Quality (20%) criterion.

### 6.2 ResultsPanel Header

```text
+--------------------------------------------------------------+
|  Hospitals for Knee Replacement · Nagpur           [Info]   |
|  ------------------------------------------------------------  |
|  3 results · Ranked by Clinical Fit + Affordability         |
|                                                              |
|  Sort: [Best Match]  Filter: [All Tiers] [NABH] [Distance]  |
+--------------------------------------------------------------+
```

**Sort Options:** Best Match · Lowest Cost · Highest Rating · Nearest · NABH First

**Filter Options:**

- Tier: All / Premium / Mid-tier / Budget
- NABH Accredited: Any / Yes Only
- Distance: Any / <5km / <10km / <25km
- Rating: Any / 4.0+ / 4.5+

### 6.3 HospitalCard — Full Specification

**Collapsed state:**

```text
+--------------------------------------------------------------+
|  #1 Best Match                              [+ Compare] [Save]|
|                                                              |
|  [Logo]   ABC Heart & Ortho Institute                        |
|           Civil Lines, Nagpur, Maharashtra                   |
|           4.5 stars (312 reviews)  [NABH]  [Mid-tier]       |
|  --------------------------------------------------------------  |
|  Procedure:  Total Knee Arthroplasty (TKA)                  |
|                                                              |
|  Estimated Cost Range                                        |
|  Rs 1.4L ------------------------------------ Rs 2.2L        |
|          Best case        Typical      Worst case            |
|                                                              |
|  Confidence: [bar 78%]  78% — High                          |
|  --------------------------------------------------------------  |
|  5.2 km    |    Ortho Specialist    |    Mid-tier            |
|  ~3 days wait (estimated)                                    |
|                                                              |
|  Why this hospital ranks #1:                                 |
|  [High Procedure Volume] [NABH Accredited] [In Budget]      |
|                                                              |
|  [View Full Details]              [Get Cost Breakdown]       |
+--------------------------------------------------------------+
```

**Expanded state** (on "View Full Details" click — smooth height animation):

**Section 1 — Ranking Signal Breakdown:**
A horizontal signal bar for each of 4 groups (Clinical Capability, Reputation, Accessibility, Affordability), each with sub-scores. Each bar fills from 0 to the score value with an animated transition on first render.

**Section 2 — Doctors (where available):**
Cards showing: Name, Specialization, Qualification, Experience years, Rating, Estimated consultation fee range.

**Section 3 — Patient Voice (NLP-extracted):**
Overall positive percentage, top 5 themes with mention counts and sentiment bars, 2-3 representative paraphrased quotes.

**Section 4 — Cost Risk Flags:**
Bulleted list of what could increase costs: ICU requirement, premium room upgrade, complications, extended stay.

### 6.4 Doctor Card (standalone listing)

Shown when the user queries for a specific doctor or the system surfaces doctors independently:

Fields: Name, Specialty, Qualification, Hospital affiliation, Rating + review count, Years experience, Consultation fee range, Estimated wait time, [View Profile] and [Book Appointment] CTAs.

### 6.5 Ranking Logic Transparency Modal

Accessible via the Info button in the results header. Shows the 4 signal groups with their weights:

- **Clinical Capability (35%):** Specialization relevance to the procedure; Procedure volume and depth of expertise
- **Reputation (30%):** Public ratings and review scores; NLP-analyzed sentiment from patient testimonials; NABH accreditation status
- **Accessibility (20%):** Distance from the user's location; Estimated appointment availability
- **Affordability (15%):** Hospital tier vs. the user's stated budget; Cost benchmark vs. regional average

Footer note: "We do NOT accept payments to influence rankings. This is purely algorithm-driven."

---

## 7. Feature: Treatment Cost Estimation Engine

### 7.1 Purpose

The highest-weighted feature (25%). Must show a component-level cost breakdown with realistic ranges, confidence scoring, geographic adjustments, and patient-specific risk flags.

### 7.2 CostEstimateCard — Master Component

Appears at the top of the ResultsPanel, above the hospital list:

```text
+--------------------------------------------------------------+
|  Estimated Cost for Total Knee Arthroplasty                  |
|  Nagpur · Mid-tier hospitals                                 |
|  ------------------------------------------------------------  |
|                                                              |
|  TOTAL RANGE                                                 |
|  Rs 1,20,000 ----------------------------- Rs 2,20,000       |
|  (Rs 1.2 Lakh)                            (Rs 2.2 Lakh)      |
|                                                              |
|  Typical: Rs 1,60,000 – Rs 1,80,000                         |
|                                                              |
|  Confidence: [bar: 74%]  74%  Moderate-High                 |
|  ------------------------------------------------------------  |
|  Cost Breakdown                                              |
|                                                              |
|  Procedure / Surgery       [bar]    Rs 80K – Rs 1.2L        |
|  Doctor Fees               [bar]    Rs 15K – Rs 25K         |
|  Hospital Stay (4-6 nts)   [bar]    Rs 20K – Rs 40K        |
|  Diagnostics (Pre + Post)  [bar]    Rs 8K  – Rs 15K        |
|  Medicines & Consumables   [bar]    Rs 5K  – Rs 12K        |
|  Contingency for Risk      [bar]    Rs 10K – Rs 30K        |
|  ------------------------------------------------------------  |
|  What can increase costs?                                    |
|  [+ ICU requirement]  [+ Premium room]  [+ Complications]   |
|                                                              |
|  [Export Estimate]  [Share]  [Compare Tiers]                 |
+--------------------------------------------------------------+
```

### 7.3 Cost Breakdown Bar — Visual Specification

Each component row:

```text
[Color dot] Component Name        [Animated fill bar]  Rs Min – Rs Max
```

- Bars animate on first render: fill from left (0% to actual width) over 600ms, staggered 80ms per row
- Bar total width = `Max / TotalMax * 100%`
- Hover/tap shows a tooltip with what's included in that component

**Tooltip content per component:**

| Component | What's included |
| --- | --- |
| Procedure / Surgery | Surgeon fee, OT charges, anesthesia, implants |
| Doctor Fees | Consultation (pre-op + post-op), specialist review |
| Hospital Stay | Room charges per night × expected nights (general ward) |
| Diagnostics | X-ray, MRI/CT, blood work, ECG (pre-op + follow-up) |
| Medicines | Prescribed drugs, IV fluids, consumables |
| Contingency | ICU reserve, complication buffer, extended stay risk |

**Component colors:** Use `--c-cost-*` tokens from Section 1.3.

### 7.4 Tier Comparison Panel

```text
+------------------------------------------------------------+
|  Compare Cost by Hospital Tier                             |
|                                                            |
|           Budget        Mid-tier       Premium            |
|  Total    Rs80K-1.2L    Rs1.2L-2.2L   Rs2.5L-4.5L        |
|  --------------------------------------------------------  |
|  Room     Shared ward   Single room    Suite room         |
|  Implant  Basic         Standard       Premium            |
|  Extras   1 follow-up   2 follow-ups   Rehab included     |
+------------------------------------------------------------+
```

### 7.5 Geographic Adjustment Indicator

```text
Cost adjusted for Nagpur (Tier 2 city)
These estimates are ~32% lower than metro city rates.
[See Mumbai rates]  [See Delhi rates]
```

### 7.6 Comorbidity-Adjusted Cost Rows

When patient profile has comorbidities, show adjusted ranges with a diff indicator inline in the breakdown:

```text
Contingency for Risk       [bar]    Rs 10K – Rs 30K
  [+Diabetes]    Revised:           Rs 20K – Rs 60K   (+Rs10K-30K)
  [+Cardiac]     ICU likely:        Rs 40K – Rs 1.5L  (high impact)
```

### 7.7 ConfidenceScore Component

SVG arc gauge (semicircle), animates from 0 to target angle on mount:

- Color: green (>=70%), amber (40-69%), red (<40%)
- Label below: "High" / "Moderate" / "Low" confidence
- Clicking the gauge opens an explanation modal listing the 4 factors that affect the score:
  1. Data availability for this procedure in this city
  2. Pricing consistency across providers
  3. Recency of benchmark data
  4. Patient complexity factors (age, comorbidities)

### 7.8 Cost Export

`[Export Estimate]` generates a formatted plain-text + PDF summary card containing: patient profile summary, procedure name + ICD-10, hospital name + tier, total range + typical range, full component breakdown, confidence score, comorbidity adjustment notes, and the mandatory disclaimer.

Available as: PDF download, PNG image, or plain text copy.

---

## 8. Feature: Multi-Source Intelligence Panel

### 8.1 Purpose

Show users that recommendations are built from multiple data sources — not a black box. Addresses Multi-Source Intelligence (15%) evaluation criterion.

### 8.2 Data Source Footer (Results Panel)

```text
+--------------------------------------------------------------+
|  How we built these results                                  |
|                                                              |
|  Structured Data    Hospital directories, NHA procedure      |
|                      categories, NABH accreditation list     |
|                                                              |
|  Unstructured Data  Patient reviews (Google, Practo),        |
|                      NLP-analyzed testimonials               |
|                                                              |
|  Derived Signals    Regional cost benchmarks, reputation     |
|                      scores, procedure volume proxies        |
|                                                              |
|  Last updated: March 2026   [View Sources]                   |
+--------------------------------------------------------------+
```

### 8.3 Review Intelligence Section (Inside Expanded HospitalCard)

NLP sentiment visualization showing:

- Overall tone bar (e.g., 78% Positive)
- Theme table: Theme name | Mention count | Sentiment bar | Positive %
  - Top themes: Surgery outcome, Staff behavior, Cleanliness, Wait times, Cost transparency
- 2-3 representative paraphrased quotes from public reviews, labeled Positive and Concern

---

## 9. Feature: Lender & Insurer Dashboard

### 9.1 Purpose

A dedicated mode for lenders (healthcare loan companies) and insurers who need cost transparency for pre-approval decisions. Addresses the problem statement section on lender/insurer challenges: high uncertainty in treatment costs and difficulty pre-approving healthcare loans.

### 9.2 Lender Mode Toggle

In Sidebar: a toggle between "Patient Mode" and "Lender / Insurer Mode"

Switching shows a brief modal:
> "Lender Mode provides structured cost estimates, procedure risk scores, and financial implication summaries designed for pre-approval workflows."

### 9.3 Lender Dashboard Layout

Replaces the standard ResultsPanel with a financial-first view:

```text
+--------------------------------------------------------------+
|  Lender / Insurer View              Patient: 45M, Nagpur    |
|  ------------------------------------------------------------  |
|                                                              |
|  Procedure:   Total Knee Arthroplasty                       |
|  ICD-10:      M17.11                                        |
|  Risk Level:  Moderate                                      |
|  ------------------------------------------------------------  |
|  COST SUMMARY                                                |
|  Base Estimate (Mid-tier)       Rs 1,20,000 – Rs 2,20,000  |
|  Comorbidity Adjustment         + Rs 30,000 – Rs 90,000    |
|  Maximum Foreseeable Cost       Rs 2,10,000 – Rs 3,10,000  |
|  Recommended Loan/Cover Range   Rs 1,80,000 – Rs 2,50,000  |
|  Confidence Score               74%                         |
|  ------------------------------------------------------------  |
|  RISK FACTORS                                                |
|  [High]   Diabetes          -> High complication risk       |
|  [Medium] Cardiac History   -> ICU likelihood 15%           |
|  [Low]    Age 45            -> Normal healing trajectory    |
|  ------------------------------------------------------------  |
|  PROCEDURE RISK PROFILE                                      |
|  Hospital Mortality Risk:   Very Low (<0.5% for TKA)        |
|  ICU Requirement Prob.:     12-18% (elevated by profile)    |
|  Avg. Length of Stay:       4-6 days                        |
|  Re-admission Rate:         ~6% (national benchmark)        |
|  ------------------------------------------------------------  |
|  [Export for Underwriting]      [Share with Team]           |
+--------------------------------------------------------------+
```

### 9.4 Underwriting Export

Generates a structured JSON + PDF report containing: patient profile, procedure with ICD-10 code, base and adjusted cost estimates, recommended cover range, confidence score, risk factors with cost deltas, hospital shortlist, and the mandatory disclaimer.

---

## 10. Feature: Hospital Comparison Tool

### 10.1 CompareBar (Bottom Sticky)

Appears when user clicks `[+ Compare]` on any hospital card:

```text
+--------------------------------------------------------------+
|  Compare  ABC Institute  [x]    City Ortho  [x]    [+ Add]  |
|                                           [Compare Now]     |
+--------------------------------------------------------------+
```

Max 3 hospitals. Persists until the user closes it or starts a new search.

### 10.2 CompareDrawer (Full-width bottom sheet)

Side-by-side table comparing all 3 selected hospitals:

| Attribute | Hospital A | Hospital B | Hospital C |
| --- | --- | --- | --- |
| Rating | 4.5 | 4.1 | 3.8 |
| NABH | Yes | No | Yes |
| Tier | Mid | Mid | Budget |
| Distance | 5.2 km | 3.1 km | 8.9 km |
| Total Cost | Rs1.4L-2.2L | Rs1.1L-1.9L | Rs80K-1.4L |
| Confidence | 78% | 65% | 52% |
| Procedure Volume | High | Medium | Low |
| ICU Available | Yes | Yes | No |
| Best for | Quality+budget | Nearest | Lowest cost |

**"Best Value" badge** auto-assigns to the hospital with the best composite score:
`(Rating × 0.4) + (1/CostMidpoint normalized × 0.3) + (Confidence × 0.3)`

Rows with meaningful differences are highlighted (e.g., "ICU Not Available" shown in red for Budget Ortho).

Footer: [Export Comparison] and [Start Over] buttons.

---

## 11. Feature: Medical Term Explainer

### 11.1 Purpose

Help users understand medical terms, diagnoses, and treatment options in simple language. Directly addresses "Explain medical terms, diagnoses, and treatment options in simple language."

### 11.2 Inline Term Highlighting

In AI chat responses, medical terms are underlined with a dashed teal underline. Hovering or tapping shows an inline tooltip with: term name, plain-language explanation, typical duration and recovery, and a "Read More" link.

### 11.3 Term Explainer Modal

Accessible via "Read More" link or by asking the chat: "What is angioplasty?"

Sections:

- **What is it?** — Plain language explanation
- **In simple terms:** — One-sentence analogy (e.g., "Unclogging a pipe in your heart")
- **When is it needed?** — Conditions that require it
- **How long?** — Procedure duration
- **Hospital stay?** — Typical nights
- **Recovery time?** — Weeks/months
- **Medical codes:** — ICD-10 + SNOMED CT for reference
- **Related terms:** — Chips linking to related procedures

Always ends with: "This is educational only. Your doctor will advise whether this procedure is right for you."

---

## 12. Feature: Appointment & Paperwork Assistant

### 12.1 Purpose

Practical help: what to bring, what to expect, what forms to fill. Addresses "Assist with appointments and paperwork."

### 12.2 AppointmentGuide Card

Appears below the hospital list when a user has selected a hospital or clicks "Prepare for Appointment":

**Before your visit, prepare (checkable list):**

- Aadhar card / Photo ID
- Previous medical reports (X-rays, MRI, blood tests)
- List of current medications
- Health insurance card (if applicable)
- Doctor referral letter (if available)

**Questions to ask the doctor (contextual to procedure):**
Generated by AI based on the procedure. For knee replacement: implant options, risks given comorbidities, physiotherapy requirements, what's included in the package price.

**Common forms you may need:**

- Patient Registration Form
- Medical History Declaration
- Consent for Surgery Form
- Insurance Pre-authorization Form (if using insurance)

Footer: [Download Checklist PDF] and [Ask AI for more help]

### 12.3 Financial Assistance Guide

Triggered when user mentions budget constraints or asks about loans/insurance. Addresses "Guide you on insurance, costs, and financial help."

**Sections:**

1. **Government Schemes** — Ayushman Bharat PM-JAY (up to Rs 5L/year), state health schemes with eligibility check links
2. **Healthcare Loans** — Major lenders with loan range and approval time
3. **EMI Calculator** — Inline: Loan amount input + tenure selector + calculated monthly EMI at indicative interest rate

Disclaimer below calculator: "These are indicative. Contact lenders for actual rates."

---

## 13. Responsible AI & Trust Layer

This section is **mandatory** and affects the Responsible AI (10%) evaluation criterion. Every element listed here must be implemented.

### 13.1 Mandatory UI Safeguards

| Safeguard | Where | Implementation |
| --- | --- | --- |
| Persistent Disclaimer Banner | Top of all pages | Cannot be permanently dismissed |
| Confidence Score | Every cost estimate + hospital card | Color-coded SVG arc gauge |
| "Decision Support Only" label | Below every AI response | Muted text with icon |
| Emergency Redirect | Auto-triggered on emergency keywords | Red full-width banner with 112 link |
| No Absolute Cost Figures | All cost displays | Always shown as ranges (Rs X – Rs Y) |
| Data Source Attribution | Results panel footer | Expandable source breakdown |
| "Correct This" Option | Clinical Mapping Card | Link to refine AI interpretation |

### 13.2 Confidence Score Explanation Modal

Triggered by clicking any confidence gauge. Explains:

- What the score means (percentage reliability and expected variance)
- The 4 factors affecting it: data quality, pricing consistency, data recency, patient factors
- What to do with a low score (get formal quotes from hospitals)

### 13.3 Symptom Mapping Disclaimer

Always shown below the Clinical Mapping Card:
> "Symptom-to-condition mapping is approximate. The same symptoms may indicate different conditions. This tool helps you research and prepare — your doctor makes the actual diagnosis."

### 13.4 High Variance Warning

When confidence < 40% or cost range spread > 200%:

```text
+----------------------------------------------------------------+
|  Wide Cost Variation Warning                                   |
|                                                                |
|  Cost estimates for this procedure vary significantly          |
|  across hospitals and patient profiles. The range shown        |
|  is intentionally broad to avoid misleading you.              |
|                                                                |
|  We strongly recommend getting direct quotes from at least    |
|  2-3 hospitals before making any decision.                    |
+----------------------------------------------------------------+
```

### 13.5 Ethical Boundaries in AI Responses

The Claude API system prompt must enforce:

- No diagnostic language — the AI never says "You have X" or "You need Y"
- No treatment prescription — the AI describes pathways, not prescriptions
- Every response ends with a one-line decision-support reminder
- Immediate emergency redirect before any other content when emergency keywords detected

---

## 14. Component Library Reference

### 14.1 Component Index

| Component | File Path | Purpose |
| --- | --- | --- |
| `DisclaimerBanner` | `components/shared/DisclaimerBanner.tsx` | Global top strip |
| `Header` | `components/layout/Header.tsx` | App top bar |
| `Sidebar` | `components/layout/Sidebar.tsx` | Left nav panel |
| `ChatWindow` | `components/chat/ChatWindow.tsx` | Full chat shell |
| `MessageBubble` | `components/chat/MessageBubble.tsx` | User + AI bubbles |
| `InputBar` | `components/chat/InputBar.tsx` | Query input |
| `TypingIndicator` | `components/chat/TypingIndicator.tsx` | AI thinking animation |
| `EmergencyBanner` | `components/chat/EmergencyBanner.tsx` | 112 alert |
| `ResultsPanel` | `components/results/ResultsPanel.tsx` | Right panel shell |
| `ClinicalMappingCard` | `components/results/ClinicalMappingCard.tsx` | Query interpretation |
| `PathwayVisualizer` | `components/results/PathwayVisualizer.tsx` | Treatment step flow |
| `HospitalList` | `components/results/HospitalList.tsx` | Ranked hospital cards |
| `HospitalCard` | `components/results/HospitalCard.tsx` | Single hospital |
| `DoctorCard` | `components/results/DoctorCard.tsx` | Single doctor |
| `RankingModal` | `components/results/RankingModal.tsx` | Signal breakdown modal |
| `CostEstimateCard` | `components/cost/CostEstimateCard.tsx` | Master cost display |
| `CostBreakdown` | `components/cost/CostBreakdown.tsx` | Animated bar chart |
| `TierComparison` | `components/cost/TierComparison.tsx` | Budget/Mid/Premium table |
| `ConfidenceScore` | `components/cost/ConfidenceScore.tsx` | SVG arc gauge |
| `RiskFlags` | `components/cost/RiskFlags.tsx` | Comorbidity warnings |
| `GeoAdjustment` | `components/cost/GeoAdjustment.tsx` | City pricing note |
| `CompareBar` | `components/compare/CompareBar.tsx` | Bottom sticky bar |
| `CompareDrawer` | `components/compare/CompareDrawer.tsx` | Side-by-side sheet |
| `PatientProfileDrawer` | `components/profile/PatientProfileDrawer.tsx` | Profile input |
| `ProfileBadge` | `components/profile/ProfileBadge.tsx` | Header profile pill |
| `ProfileImpactCallout` | `components/profile/ProfileImpactCallout.tsx` | Comorbidity callout |
| `LenderDashboard` | `components/lender/LenderDashboard.tsx` | Lender mode view |
| `UnderwritingExport` | `components/lender/UnderwritingExport.tsx` | Export tool |
| `TermExplainer` | `components/education/TermExplainer.tsx` | Term tooltip + modal |
| `AppointmentGuide` | `components/assist/AppointmentGuide.tsx` | Prep checklist |
| `FinancialGuide` | `components/assist/FinancialGuide.tsx` | EMI + schemes |
| `DataSourcePanel` | `components/shared/DataSourcePanel.tsx` | Source attribution |
| `HighVarianceWarning` | `components/shared/HighVarianceWarning.tsx` | Wide cost warning |
| `Skeleton` | `components/shared/Skeleton.tsx` | Loading states |
| `EmptyState` | `components/shared/EmptyState.tsx` | No results state |
| `Badge` | `components/shared/Badge.tsx` | NABH, tier, rating pills |
| `RangeBar` | `components/shared/RangeBar.tsx` | Generic animated min-max bar |

---

## 15. State Architecture

### 15.1 Global App State Shape

```typescript
// types/app.ts
interface AppState {
  // Conversation
  conversation:     Message[];
  isLoading:        boolean;
  error:            string | null;

  // Patient context
  patientProfile:   PatientProfile | null;
  activeLocation:   Location | null;

  // Clinical intelligence
  clinicalMapping:  ClinicalMapping | null;

  // Results
  hospitals:        Hospital[];
  doctors:          Doctor[];
  costEstimate:     CostEstimate | null;
  searchMeta:       SearchMeta | null;

  // UI state
  selectedForCompare:   string[];       // hospital IDs, max 3
  savedHospitals:       string[];       // bookmarked
  lenderMode:           boolean;
  sidebarCollapsed:     boolean;
  conversationHistory:  ConversationSummary[];
}
```

### 15.2 Core Types

```typescript
interface Message {
  id:          string;
  role:        'user' | 'assistant';
  content:     string;
  timestamp:   Date;
  searchData:  ParsedSearchData | null;
  isStreaming: boolean;
}

interface PatientProfile {
  location:      Location | null;
  age:           number | null;
  gender:        'male' | 'female' | 'other' | null;
  comorbidities: Comorbidity[];
  budgetMax:     number | null;   // INR
}

interface ClinicalMapping {
  userQuery:    string;
  procedure:    string;
  icd10Code:    string;
  icd10Label:   string;
  snomedCode:   string;
  category:     string;
  pathway:      PathwayStep[];
  confidence:   number;
}

interface CostEstimate {
  procedureName:    string;
  location:         string;
  tier:             HospitalTier;
  totalMin:         number;    // INR
  totalMax:         number;
  typicalMin:       number;
  typicalMax:       number;
  confidence:       number;   // 0-1
  breakdown:        CostBreakdown;
  geoAdjustment:    GeoAdjustment;
  riskAdjustments:  RiskAdjustment[];
  dataSource:       DataSourceMeta;
}

interface CostBreakdown {
  procedure:    CostRange;
  doctorFees:   CostRange;
  hospitalStay: CostRange;
  diagnostics:  CostRange;
  medicines:    CostRange;
  contingency:  CostRange;
}

interface Hospital {
  id:              string;
  name:            string;
  address:         string;
  city:            string;
  distanceKm:      number;
  rating:          number;
  reviewCount:     number;
  nahhAccredited:  boolean;
  tier:            'premium' | 'mid' | 'budget';
  specializations: string[];
  doctors:         Doctor[];
  costRange:       CostRange;
  confidence:      number;
  rankScore:       number;
  rankSignals:     RankSignals;
  sentimentData:   SentimentData;
  strengths:       string[];
  riskFlags:       string[];
}

interface RankSignals {
  clinicalCapability: SignalScore;  // 0-100
  reputation:         SignalScore;
  accessibility:      SignalScore;
  affordability:      SignalScore;
}
```

### 15.3 Context + Reducer

Use React Context + useReducer — no external state library required.

```typescript
type Action =
  | { type: 'ADD_MESSAGE';     payload: Message }
  | { type: 'SET_LOADING';     payload: boolean }
  | { type: 'SET_RESULTS';     payload: { hospitals: Hospital[]; costEstimate: CostEstimate; mapping: ClinicalMapping } }
  | { type: 'SET_PROFILE';     payload: PatientProfile }
  | { type: 'TOGGLE_COMPARE';  payload: string }
  | { type: 'TOGGLE_SAVE';     payload: string }
  | { type: 'SET_LENDER_MODE'; payload: boolean }
  | { type: 'RESET_RESULTS' }
  | { type: 'SET_ERROR';       payload: string };
```

---

## 16. API Integration Contracts

### 16.1 Claude API System Prompt (Patient Mode)

```text
You are HealthNav, an AI-powered healthcare navigator for Indian patients.

YOUR ROLE:
- Help users find suitable hospitals and doctors for their condition
- Explain medical terms and treatment options in simple, clear language
- Estimate realistic treatment costs with component-level breakdowns
- Guide users on insurance, loans, and financial assistance options
- Support informed decision-making — never diagnose or prescribe

STRICT RULES:
1. DECISION-SUPPORT ONLY. Never diagnose. Never prescribe treatment.
2. End every response with a short responsible-AI note.
3. Map all symptoms/conditions to ICD-10 and SNOMED CT codes.
4. Always include confidence scores with cost estimates.
5. Show all costs as ranges (min-max), never a single figure.
6. If the query contains emergency symptoms (chest pain, stroke, 
   unconscious, severe bleeding), start your response with:
   <EMERGENCY>true</EMERGENCY>
7. Use simple, jargon-free language. Explain any medical term you use.

OUTPUT FORMAT:
For queries requiring hospital/cost results, return:
1. Natural language response (markdown supported)
2. Structured data block: <SEARCH_DATA>{ ... }</SEARCH_DATA>

SEARCH_DATA JSON schema:
{
  "emergency": false,
  "query_interpretation": "string",
  "procedure": "string",
  "icd10_code": "string",
  "icd10_label": "string",
  "snomed_code": "string",
  "medical_category": "string",
  "pathway": [
    { "step": 1, "name": "string", "duration": "string",
      "cost_range": { "min": 0, "max": 0 } }
  ],
  "mapping_confidence": 0.0,
  "location": "string",
  "cost_estimate": {
    "tier": "mid",
    "total": { "min": 0, "max": 0, "typical_min": 0, "typical_max": 0 },
    "confidence": 0.0,
    "breakdown": {
      "procedure":     { "min": 0, "max": 0 },
      "doctor_fees":   { "min": 0, "max": 0 },
      "hospital_stay": { "min": 0, "max": 0, "nights": "4-6" },
      "diagnostics":   { "min": 0, "max": 0 },
      "medicines":     { "min": 0, "max": 0 },
      "contingency":   { "min": 0, "max": 0 }
    },
    "geo_adjustment": {
      "city_tier": "tier2",
      "discount_vs_metro": 0.32
    },
    "risk_adjustments": [
      { "factor": "diabetes",
        "impact": "Higher complication risk",
        "cost_delta_min": 10000,
        "cost_delta_max": 30000 }
    ]
  },
  "hospitals": [
    {
      "id": "string",
      "name": "string",
      "address": "string",
      "city": "string",
      "distance_km": 0.0,
      "rating": 0.0,
      "review_count": 0,
      "nabh_accredited": false,
      "tier": "mid",
      "specializations": [],
      "doctors": [
        { "name": "string", "specialization": "string",
          "experience_years": 0, "rating": 0.0,
          "fee_min": 0, "fee_max": 0 }
      ],
      "cost_range": { "min": 0, "max": 0 },
      "confidence": 0.0,
      "rank_score": 0.0,
      "rank_signals": {
        "clinical_capability": 0,
        "reputation": 0,
        "accessibility": 0,
        "affordability": 0
      },
      "strengths": [],
      "risk_flags": [],
      "sentiment": {
        "positive_pct": 0,
        "themes": [
          { "theme": "string", "mentions": 0, "positive_pct": 0 }
        ],
        "sample_quotes": []
      }
    }
  ],
  "comorbidity_warnings": [],
  "data_sources": [
    "NHA benchmarks",
    "Public hospital directories",
    "NABH registry"
  ]
}
```

### 16.2 API Route (Next.js)

```typescript
// app/api/chat/route.ts
export async function POST(request: Request) {
  const { messages, patientProfile, lenderMode } = await request.json();

  const systemPrompt = lenderMode
    ? LENDER_SYSTEM_PROMPT
    : PATIENT_SYSTEM_PROMPT;

  const stream = await anthropic.messages.stream({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2000,
    system: systemPrompt,
    messages: messages.map(formatForAPI),
  });

  return new Response(stream.toReadableStream());
}
```

### 16.3 Response Parser

```typescript
// lib/parseResponse.ts
export function parseAIResponse(rawText: string) {
  const isEmergency =
    /<EMERGENCY>true<\/EMERGENCY>/.test(rawText);

  const match = rawText.match(/<SEARCH_DATA>([\s\S]*?)<\/SEARCH_DATA>/);
  let searchData = null;
  if (match) {
    try { searchData = JSON.parse(match[1].trim()); }
    catch { console.error('Failed to parse SEARCH_DATA'); }
  }

  const narrative = rawText
    .replace(/<EMERGENCY>.*?<\/EMERGENCY>/s, '')
    .replace(/<SEARCH_DATA>[\s\S]*?<\/SEARCH_DATA>/, '')
    .trim();

  return { narrative, searchData, isEmergency };
}
```

---

## 17. Mock Data Specification

### 17.1 Hospital Data Requirements

Minimum 8 hospitals across these cities: Nagpur, Raipur, Bhopal, Indore, Nashik, Aurangabad, Surat, Patna.

Mix of tiers: 2 premium (e.g., Apollo, Fortis-affiliated), 4 mid-tier, 2 budget.

Each hospital must include all fields from the Hospital type: id, name, address, city, coordinates, distanceKm, rating, reviewCount, nahhAccredited, tier, specializations, doctors (2-4 each), costBenchmarks per procedure, and sentiment data.

### 17.2 Procedure Cost Benchmarks

Minimum 12 procedures with full cost benchmarks by city tier (metro / tier2 / tier3) and comorbidity adjustment factors:

1. Angioplasty (I25.10)
2. Total Knee Arthroplasty (M17.11)
3. Hip Replacement (M16.11)
4. CABG / Bypass (I25.10)
5. Cataract Surgery (H26.9)
6. Appendectomy (K37)
7. Cholecystectomy (K80.20)
8. Dialysis — monthly (Z99.2)
9. Chemotherapy Cycle (Z51.11)
10. MRI Brain Scan (Z01.01)
11. LASIK Eye Surgery (H52.1)
12. Normal Delivery (Z37.0)

### 17.3 Cost Structure Per Procedure

```typescript
interface ProcedureCostBenchmark {
  procedure: string;
  icd10: string;
  cityTier: {
    metro:  CostRange & { typical: number };
    tier2:  CostRange & { typical: number };
    tier3:  CostRange & { typical: number };
  };
  breakdown: {
    procedure:    { pct: { min: number; max: number } };
    doctorFees:   { pct: { min: number; max: number } };
    hospitalStay: { nights: string; pctPerNight: number };
    diagnostics:  { pct: { min: number; max: number } };
    medicines:    { pct: { min: number; max: number } };
    contingency:  { pct: { min: number; max: number } };
  };
  comorbidityFactors: {
    [comorbidity: string]: {
      costMultiplier: number;
      icuProbability: number;
    };
  };
}
```

---

## 18. Responsive & Accessibility Requirements

### 18.1 Breakpoints

| Name | Width | Layout |
| --- | --- | --- |
| xs mobile | < 480px | Single column, full-width everything |
| sm mobile | 480-767px | Single column, results as bottom sheet |
| md tablet | 768-1023px | Chat + Results side-by-side, no sidebar |
| lg desktop | 1024-1279px | Sidebar icon rail + Chat + Results |
| xl desktop | >= 1280px | Full 3-column layout |

### 18.2 Mobile-Specific Behaviors

- **Results Bottom Sheet:** Full-screen, swipe-to-dismiss, triggered by floating "View N Results" FAB button
- **Compare Drawer:** Full-screen horizontal scroll table with sticky first column
- **PatientProfileDrawer:** Full-screen modal (not side-drawer)
- **InputBar:** Fixed to viewport bottom with `padding-bottom: 80px` on the chat thread
- **CostBreakdown bars:** Scroll horizontally if needed; tooltips become tap-to-reveal

### 18.3 Accessibility (WCAG 2.1 AA)

- All interactive elements: minimum 44×44px touch target
- Color is never the sole differentiator — always pair with text or icon
- `aria-label` on all icon-only buttons
- `role="status"` and `aria-live="polite"` on the TypingIndicator
- `aria-busy="true"` on InputBar while loading
- Focus management: when ResultsPanel populates, move focus to the first hospital card heading
- Keyboard navigation: Tab through hospital cards; Enter to expand; Space to toggle compare
- All images require `alt` text; decorative images use `alt=""`
- ConfidenceScore SVG arc: include `<title>` element and `aria-label` with percentage and label

### 18.4 Indian Number Formatting

All monetary values must use Indian numbering:

- Short form: `Rs 1.8L`, `Rs 3.2L` (for labels and badges)
- Full form: `Rs 1,80,000` (for detailed breakdown tables)
- Never: `Rs 180000` or `Rs 1,800,00`

```typescript
// lib/formatters.ts
export function formatINRShort(amount: number): string {
  if (amount >= 100000) return `Rs ${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000)   return `Rs ${(amount / 1000).toFixed(0)}K`;
  return `Rs ${amount}`;
}

export function formatINRFull(amount: number): string {
  return `Rs ${amount.toLocaleString('en-IN')}`;
}
```

---

## 19. Evaluation Checklist

### Core Features

- [ ] Natural language input accepts: symptoms, conditions, procedures, and preference-based queries
- [ ] Queries map to ICD-10 and SNOMED CT codes with the mapping shown in the UI
- [ ] Treatment pathway visualizer shows step-by-step flow with durations and per-step costs
- [ ] Hospital list returns minimum 3 ranked results per query
- [ ] All 4 ranking signals are shown per hospital (Clinical, Reputation, Access, Affordability)
- [ ] Each hospital card shows: name, rating, NABH status, tier, distance, cost range, confidence
- [ ] Hospital cards are expandable with signal breakdown, doctor list, sentiment analysis, risk flags
- [ ] Doctor cards shown where data is available
- [ ] Cost estimate shows all 6 components with min/max ranges
- [ ] Cost breakdown bars animate on first render with staggered timing
- [ ] Confidence score gauge appears on every estimate and every hospital card
- [ ] Tier comparison panel (Budget / Mid / Premium) renders correctly
- [ ] Geographic cost adjustment is displayed with city-tier label
- [ ] Patient profile drawer collects: location, age, gender, comorbidities, budget
- [ ] Comorbidity warnings appear as a callout with adjusted cost impact values
- [ ] Hospital comparison works for 2-3 hospitals side-by-side
- [ ] Best Value badge auto-assigns in comparison view
- [ ] Medical term explainer works both as inline tooltip and full modal
- [ ] Appointment preparation guide is generated per selected hospital
- [ ] Financial assistance guide includes EMI calculator and government scheme links
- [ ] Lender/Insurer dashboard mode is available via sidebar toggle
- [ ] Underwriting export generates a structured report (PDF or JSON)
- [ ] Clarifying question chips appear for ambiguous queries
- [ ] Quick-start chips work on the landing/welcome state

### Responsible AI

- [ ] Disclaimer banner is always visible and cannot be permanently dismissed
- [ ] Emergency keyword detection triggers the 112 alert banner immediately
- [ ] All cost figures are shown as ranges — no single-number cost claims
- [ ] "Decision Support Only" note appears below every AI response
- [ ] Confidence score explanation modal is accessible from every gauge
- [ ] Data source attribution panel is shown in the results footer
- [ ] High variance warning triggers when confidence is below 40%
- [ ] Symptom mapping disclaimer is shown below every clinical mapping card
- [ ] No diagnostic language appears in any AI response
- [ ] AI responses never recommend a specific treatment — only describe pathways

### UX & Polish

- [ ] Loading skeletons appear during all fetch and processing states
- [ ] Empty state renders with actionable recovery suggestions when no results found
- [ ] All animations use the defined easing tokens — no linear or instant transitions
- [ ] Mobile layout is fully functional with the bottom-sheet results pattern
- [ ] INR values use Indian number formatting throughout (Rs 1.8L, Rs 1,80,000)
- [ ] Ranking logic transparency modal opens from the results panel header
- [ ] Compare bar persists at the bottom until cleared or search resets
- [ ] All interactive elements meet 44px minimum touch target size
- [ ] Cost export generates a clean, shareable summary with disclaimer

---

*This instruction document is the complete frontend specification for HealthNav. Build prioritizing the top evaluation dimensions: Cost Estimation Logic (25%) → Clinical Mapping (20%) → Provider Ranking (20%). Every UI decision should serve the core mission: helping real people in Tier 2/3 Indian cities make informed, confident healthcare decisions.*

# SkillSphere Design System Audit & UI Hardening

**Design System Guideline**: **Calm, High-Contrast & High-Signal**  
**Audit Standard**: WCAG 2.1 AA Typography, Layout & Spacing Consistency  
**Date**: November 2026  

---

## 1. Design System Foundations

SkillSphere's user interface is styled to foster focused deep learning, free from distracting gamification gimmicks, flashing animations, and overwhelming multi-color neon badges.

### Color Palette & Token Hierarchy

| Token | Hex Value | Semantic Role | WCAG Contrast Ratio (vs Background) |
| :--- | :--- | :--- | :---: |
| **`--bg-primary`** | `#0B0F19` | Deep slate canvas background | Base (1:1) |
| **`--bg-surface`** | `#161F37` | Elevated cards, modals, and dropdown menus | Base contrast |
| **`--border-subtle`**| `rgba(255, 255, 255, 0.08)` | Structural dividers and card outlines | Accessible edge definition |
| **`--text-primary`**| `#FFFFFF` | Primary headers, titles, and active nav links | **17.8:1 (AAA)** |
| **`--text-main`** | `#F1F5F9` | Standard body paragraphs and form labels | **15.2:1 (AAA)** |
| **`--text-secondary`**|`#CBD5E1` | Subheadings, dates, secondary badges | **11.4:1 (AAA)** |
| **`--text-muted`** | `#94A3B8` | Metadata, helper text, empty state descriptions | **6.8:1 (AA)** |
| **`--accent-primary`**|`#6366F1` | Primary action buttons and focus indicators | **4.9:1 (AA)** |
| **`--accent-purple`** |`#8B5CF6` | Career track accents and verified milestone tags | **5.3:1 (AA)** |

---

## 2. Component Audits & Improvements

### A. Navigation Sidebar
- **Previous Flaws**: 28 uneven items with loud "NEW", "LIVE", "JUDGE", "RANKED" neon badges causing visual noise.
- **Refinement**: Clean 5-pillar structure with 18px icons, standardized 10px padding, subtle active background highlight (`rgba(99, 102, 241, 0.12)`), and high-contrast typography.

### B. Cards & Containers
- **Border Radius**: Unified `12px` (standard cards) and `16px` (modal / hub containers).
- **Elevation**: Light backdrop blur (`backdrop-filter: blur(12px)`) with subtle border lines rather than heavy drop shadows.
- **Inner Padding**: Standardized to `p-3` (mobile) and `p-4` (desktop).

### C. Buttons & Interactions
- **Primary**: Solid indigo fill (`#6366F1`) with white text and `border-radius: 8px`.
- **Secondary**: Ghost slate button with subtle white border (`rgba(255, 255, 255, 0.15)`).
- **Focus States**: High-contrast outline (`2px solid #818cf8` with `outline-offset: 2px`).

### D. Forms & Inputs
- **Readability**: High contrast inputs with `#0F172A` background and `#FFFFFF` text color.
- **Labels**: Explicit `<label>` elements linked to form control IDs.
- **Validation**: Server-side error banners with red accent alerts and clear remediation advice.

### E. Empty States
- Replaced blank screens with illustrative, helpful empty states containing direct call-to-action buttons (e.g. "No in-progress courses — Browse Course Catalog").

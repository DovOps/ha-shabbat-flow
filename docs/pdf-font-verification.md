# Print font simplification

MD-FR-025 / MD-NFR-011. Shared print CSS prefers local Arial, then Tahoma and generic sans-serif. Screen typography, charts and schedule output are unchanged. No font binaries or runtime dependencies are added.

A fictional two-page Chrome Save as PDF comparison used identical English/Hebrew text at weights 400, 600, 650 and 700. The system-ui page contained 30 Type 3 font resources; the Arial page contained three embedded Type 0 Arial subsets with FontFile2 TrueType data and no Type 3 fonts. The browser added a shared embedded Times-Roman font for print headers/footers. Rendered output confirmed legible English and Hebrew with the intended direction and emphasis.

This validates font selection and embedding in the tested macOS Chrome environment, not mobile performance. Font availability and PDF generation vary across operating systems and browsers. The fallback cannot guarantee a particular embedded format everywhere. Full-report phone comparison and HA installation remain pending. Chart gradients remain unchanged and may still dominate rendering cost.

Regression verification: 77 Python core tests and 58 JavaScript tests passed; repository hygiene check passed. This is an unreleased source change; the installed integration remains unchanged.

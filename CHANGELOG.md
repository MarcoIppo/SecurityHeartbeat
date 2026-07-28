# Changelog

All notable changes to this project are documented in this file.

## [1.3.5] - 2026-07-28

### Fixed
- Inline `{code}text{code}` patterns now render correctly in markup preview
- Auto-detect available monospace font (Consolas → DejaVu Sans Mono fallback on Linux)
- Removed `\r` characters causing rendering artifacts in Description and AC fields

## [1.3.4] - 2026-07-28

### Fixed
- `{code}` blocks with content on same line as opening/closing tag now handled correctly
- `{quote}` multi-line blocks rendering improved with colored sidebar
- Table columns aligned using monospace font and calculated padding

## [1.3.3] - 2026-07-28

### Added
- Full Jira wiki markup renderer supporting all elements: headings, bold, italic, strikethrough, underline, monospace, colors, links, images, code blocks, noformat, quote blocks, panels, bullet/numbered lists, tables, horizontal rules, emoticons, superscript, subscript, citations

## [1.3.2] - 2026-07-28

### Added
- Markup preview popup (👁 button) for Description and Acceptance Criteria fields
- Renders Jira wiki markup as formatted text showing how it would appear in Jira
- Updated translate (IT→EN) tooltip to clarify it replaces entire field content

## [1.3.1] - 2026-07-28

### Added
- Sprint link icon (🔗) next to sprint dropdown — opens backlog planning page in Jira
- Story Points (SP) field on the Labels row, populated from Jira if set
- `-h` / `--help` CLI switch showing available command-line options

## [1.3.0] - 2026-07-27

### Added
- Connection status indicator: ● (filled) = connected to Jira, ○ (outline) = not connected (cached data)
- Detailed contextual help tooltips (EN/IT) for all UI elements
- Create/Update confirmation popup with story classification (new/modified/unchanged)
- Epic Description read-only visual indicator with help button

## [1.1.0] - 2026-06-16

### Added
- Logging system, UI improvements, new tools, epic search fix

## [1.0.0] - 2026-06-16

### Added
- Initial release: GUI application for Jira User Story batch creation
- Epic/Story management, translation, sprint mapping, batch operations

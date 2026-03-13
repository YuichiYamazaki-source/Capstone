# Discussion Log

Open questions and design decisions raised during development.

## Open

### Web Search result caching
- **Context**: Missing data in CSV (Skills=[], Level, Satisfaction Rate) can be supplemented via Web Search at runtime
- **Options**:
  1. Read-only: Use Web Search results only for the current response, do not update CSV
  2. Write-back: Update CSV with Web Search results to avoid repeated lookups
- **Leaning**: Start with read-only; add caching layer later if needed
- **Status**: Pending

## Resolved

(None yet)

# Paper Rendering Notes

This folder contains the JOSS manuscript source in Pandoc Markdown format.

## Source files

- Manuscript: [paper.md](paper.md)
- Bibliography: [paper.bib](paper.bib)

## Local preview

Generate a local preview when needed:

```bash
pandoc paper/paper.md --citeproc --bibliography=paper/paper.bib -o /tmp/noaa-spec-paper-preview.html
```

The preview HTML is a local convenience artifact and is not tracked as part of the repository.

For reviewer-facing context, use [docs/internal/REVIEWER_GUIDE.md](../docs/internal/REVIEWER_GUIDE.md) alongside the manuscript. No archived release bundle is linked for this revision.

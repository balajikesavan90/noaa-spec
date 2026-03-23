# Paper Rendering Notes

This folder contains the JOSS manuscript source in Pandoc Markdown format.

## Source files

- Manuscript: [paper.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/paper/paper.md)
- Bibliography: [paper.bib](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/paper/paper.bib)

## Local preview

Generate a local preview when needed:

```bash
pandoc paper/paper.md --citeproc --bibliography=paper/paper.bib -o /tmp/noaa-spec-paper-preview.html
```

The preview HTML is a local convenience artifact and is not tracked as part of the repository.

For reviewer-facing context, use [docs/REVIEWER_GUIDE.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/docs/REVIEWER_GUIDE.md) alongside the manuscript. The paper is intentionally software-first; frozen larger-build evidence will be paired to a later submission revision rather than to the active development state.

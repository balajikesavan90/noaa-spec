# Paper Rendering Notes

This folder contains a JOSS manuscript in Pandoc Markdown format.

## Why GitHub preview looks unusual

GitHub does not render this manuscript the same way as JOSS/Pandoc:

- The YAML metadata block in `paper.md` is displayed as visible content.
- Citation syntax like `[@smith2011isd]` is not processed into formatted references.
- Some JOSS/Pandoc manuscript conventions are shown literally in GitHub's Markdown renderer.

This is expected and does not indicate a manuscript error.

## Source files

- Manuscript: [paper.md](paper.md)
- Bibliography: [paper.bib](paper.bib)

## Recommended preview path

Use a Pandoc/JOSS-compatible rendering workflow when reviewing manuscript appearance.

If you are in the repository root:

```bash
pandoc paper/paper.md --citeproc --bibliography=paper/paper.bib -o paper/paper-preview.html
```

If you are in the `paper/` directory:

```bash
pandoc paper.md --citeproc --bibliography=paper.bib -o paper-preview.html
```

Then open `paper-preview.html` in a browser.

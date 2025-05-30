# Resume Generator

A Python tool to convert a Markdown-formatted resume into a styled HTML (and optionally PDF) document.

## Features

- **Markdown to HTML**: Converts a structured Markdown resume into a clean, styled HTML file.
- **PDF Export**: Easily print or save the generated HTML as a PDF from your browser.
- **Customizable Styles**: Supports custom CSS for personalized resume designs.
- **Flexible Sections**: Automatically detects and formats sections like Experience, Education, Skills, and more.

## Usage

```bash
python3 main.py input.md [output.html] [--style custom.css]
```

- `input.md`: Your resume in Markdown format.
- `output.html` (optional): Output HTML file name. Defaults to the same name as input with `.html` extension instead of `.md`.
- `--style` or `-s` (optional): Path to a custom CSS file. Defaults to `style.css`.

### Example

```bash
python3 main.py resume.md
```

This will generate `resume.html` in the same directory.

## How to Convert to PDF

1. Open the generated HTML file in your web browser.
2. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (Mac).
3. Select "Save as PDF" as the printer.

## Markdown Resume Format

See [example.md](example.md) for an example resume.

- Start with your name as a top-level header (`# Name`).
- Add your title/specialization in bold (`**Title** | Specialization`).
- List contact info as plain lines.
- Use `## Section` for each section (e.g., Experience, Education).
- For experience/education, use `### Company | Role` and `_Date_` for entries.
- Use bullet points (`- ...`) for lists.

### Example

```markdown
# John Doe
**Software Engineer** | Web Development
john.doe@email.com | github.com/johndoe

## Experience
### Acme Corp | Senior Developer
_2019 - Present_
- Led a team of 5 engineers
- Improved system performance by 30%

## Skills
**Programming Languages:** Python, JavaScript, Java
**Frameworks:** React, Node.js, Django
**Tools:** Git, Docker, AWS

## Education
**B.Sc. Computer Science** - University of Example
```

## Requirements

- Python 3

## Acknowledgments

Inspired by [MarkdownResume](https://markdownresume.app/)


## License

MIT License

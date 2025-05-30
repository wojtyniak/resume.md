#!/usr/bin/env python3
"""
Resume Generator - Convert Markdown resume to styled HTML/PDF
Usage: python resume_generator.py input.md [output.html]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ResumeParser:
    def __init__(self):
        self.sections_list = []  # Changed from dict to list
        self.header_info = {}

    def _determine_section_type(self, content_lines: List[str]) -> str:
        """Determines the type of a section based on its content lines."""
        if not content_lines:
            return "paragraph"

        # Check for Timeline (e.g., Experience, Education with detailed entries)
        # Looks for "### Company | Role" and optionally "_Date_"
        # For a timeline, we expect at least one line to start with "### "
        if any(line.strip().startswith("### ") for line in content_lines):
            return "timeline"

        # Check for Aligned List (e.g., Technical Expertise)
        # Looks for "**Category:** Skills"
        aligned_list_pattern = r"^\*\*(.+?):\*\*\s*(.*)$"
        if any(re.match(aligned_list_pattern, line.strip()) for line in content_lines):
            return "aligned_list"

        # Check for Bullet List (e.g., Notable Achievements, simple lists under custom sections)
        # Considers it a bullet list if a significant portion of non-empty lines are bullet points.
        bullet_lines = 0
        non_empty_lines = 0
        for line_content in content_lines:
            line = line_content.strip()
            if line:
                non_empty_lines += 1
                if line.startswith("- "):
                    bullet_lines += 1

        if non_empty_lines > 0 and (bullet_lines / non_empty_lines) >= 0.5:
            # If more than half of the non-empty lines start with a bullet
            return "bullet_list"

        # Default to Paragraph (e.g., Summary, Languages, or any other text block)
        return "paragraph"

    def parse_markdown(self, content: str) -> Dict:
        """Parse markdown content and extract resume sections with their types"""
        lines = content.strip().split("\n")
        current_section_title = None
        current_content_lines = []
        self.header_info = {}  # Reset for multiple calls if any
        self.sections_list = []  # Reset for multiple calls

        for line_text in lines:
            original_line_stripped = line_text.strip()  # For conditions
            # Keep original line_text for content, but strip for logic

            if not original_line_stripped:  # Empty line
                if current_content_lines and current_content_lines[-1] != "":
                    current_content_lines.append(
                        ""
                    )  # Preserve empty lines within section content
                continue

            # 1. Name (must be the first major header element)
            if original_line_stripped.startswith("# ") and not self.header_info.get(
                "name"
            ):
                if (
                    current_section_title
                ):  # Finalize previous section if # Name appears unexpectedly
                    section_type = self._determine_section_type(current_content_lines)
                    self.sections_list.append(
                        {
                            "title": current_section_title,
                            "type": section_type,
                            "content": "\n".join(current_content_lines).strip(),
                        }
                    )
                self.header_info["name"] = original_line_stripped[2:].strip()
                current_section_title = None  # Reset section context
                current_content_lines = []  # and content buffer
                continue

            # 2. Title/Specialization (must be after name, before sections)
            title_spec_match = re.match(
                r"^\*\*([^*]+)\*\*(?:\s*\|\s*(.*))?$", original_line_stripped
            )
            if (
                self.header_info.get("name")
                and not self.header_info.get("title")
                and title_spec_match
            ):
                self.header_info["title"] = title_spec_match.group(1).strip()
                if title_spec_match.group(2):
                    self.header_info["specialization"] = title_spec_match.group(
                        2
                    ).strip()
                else:
                    self.header_info.pop(
                        "specialization", None
                    )  # Ensure it's removed if not present
                continue

            # Redundant title parsing block removed here.
            # The regex above handles both '**Title**' and '**Title** | Specialization'.

            # 3. Section Start (##)
            # This must be checked before general contact line parsing.
            if original_line_stripped.startswith("## "):
                if current_section_title:  # Finalize previous section
                    section_type = self._determine_section_type(current_content_lines)
                    self.sections_list.append(
                        {
                            "title": current_section_title,
                            "type": section_type,
                            "content": "\n".join(current_content_lines).strip(),
                        }
                    )
                current_section_title = original_line_stripped[3:].strip()
                current_content_lines = []
                continue

            # 4. Contact Lines (NEW GENERAL LOGIC)
            # These are lines after Name & Title/Spec, but before the first "## section".
            # `current_section_title` should be `None` at this stage if we are in the header.
            # `self.header_info.get("name")` ensures we've at least seen the name.
            # `self.header_info.get("title")` ensures we've seen the title.
            if (
                self.header_info.get("name")
                and self.header_info.get(
                    "title"
                )  # Ensures title is parsed before contacts
                and current_section_title is None
                and original_line_stripped  # Line is not empty
            ):
                if "contact" not in self.header_info:
                    self.header_info["contact"] = []
                self.header_info["contact"].append(original_line_stripped)
                continue

            # 5. Accumulate Section Content
            if current_section_title is not None:  # Content for an active section
                current_content_lines.append(line_text)  # Append the original line_text
            # elif not self.header_info.get("name"):
            # Lines before # Name (if any, and not empty) are currently ignored by this logic.
            # This is generally fine as a resume should start with # Name or be structured.

        if current_section_title and current_content_lines:  # Add the last section
            section_type = self._determine_section_type(current_content_lines)
            self.sections_list.append(
                {
                    "title": current_section_title,
                    "type": section_type,
                    "content": "\n".join(current_content_lines).strip(),
                }
            )

        return {"header": self.header_info, "sections": self.sections_list}


class HTMLGenerator:
    def __init__(self):
        self.css = """
        @media print {
            body {
                margin: 0;
            }
            .no-print {
                display: none;
            }
        }
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.5;
            color: #333;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 0.5in;
            font-size: 11pt;
        }
        h1 {
            font-size: 24pt;
            margin: 0 0 5px 0;
            color: #1a1a1a;
        }
        .subtitle {
            font-size: 12pt;
            color: #666;
            margin-bottom: 10px;
        }
        .contact-info {
            font-size: 10pt;
            margin-bottom: 15px;
            color: #555;
        }
        .contact-info a {
            color: #0066cc;
            text-decoration: none;
        }
        h2 {
            font-size: 14pt;
            color: #1a1a1a;
            border-bottom: 2px solid #333;
            padding-bottom: 3px;
            margin: 20px 0 10px 0;
        }
        h3 {
            font-size: 12pt;
            margin: 15px 0 5px 0;
            color: #1a1a1a;
        }
        .job-title {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 8px;
        }
        .company-name {
            font-weight: bold;
        }
        .dates {
            font-style: italic;
            color: #666;
            font-size: 10pt;
        }
        ul {
            margin: 5px 0 10px 0;
            padding-left: 20px;
        }
        li {
            margin-bottom: 4px;
            text-align: justify;
        }
        .tech-skills {
            margin-bottom: 5px;
        }
        .tech-skills strong {
            display: inline-block;
            width: 140px;
        }
        .education-item {
            margin-bottom: 5px;
        }
        .no-print {
            margin-top: 20px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }
        """

    def process_links(self, text: str) -> str:
        """Convert markdown links to HTML"""
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        return re.sub(pattern, r'<a href="\2">\1</a>', text)

    def process_bold(self, text: str) -> str:
        """Convert markdown bold to HTML"""
        return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    def process_italic(self, text: str) -> str:
        """Convert markdown italic to HTML"""
        return re.sub(r"_([^_]+)_", r"<em>\1</em>", text)

    def process_text(self, text: str) -> str:
        """Process markdown formatting"""
        text = self.process_links(text)
        text = self.process_bold(text)
        text = self.process_italic(text)
        return text

    def parse_experience_entry(self, entry: str) -> Dict:
        """Parse a single experience entry"""
        lines = [line.strip() for line in entry.strip().split("\n") if line.strip()]
        if not lines:
            return {}
        header_line = lines[0]
        date_line = lines[1] if len(lines) > 1 and lines[1].startswith("_") else ""
        if " | " in header_line:
            parts = header_line.split(" | ", 1)
            company = parts[0].replace("###", "").strip()
            role = parts[1].strip()
        else:
            company = header_line.replace("###", "").strip()
            role = ""
        date = date_line.replace("_", "").strip() if date_line else ""
        bullets = []
        for line in lines[2:] if date_line else lines[1:]:
            if line.startswith("- "):
                bullets.append(line[2:].strip())
        return {"company": company, "role": role, "date": date, "bullets": bullets}

    def parse_technical_expertise(self, content: str) -> List[Tuple[str, str]]:
        """Parse technical expertise section with a standard regex."""
        skills = []
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()  # Ensure line is stripped before regex
            match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
            if match:
                category = match.group(1).strip()
                skill_list = match.group(2).strip()
                skills.append((category, skill_list))
        return skills

    def parse_education(self, content: str) -> List[Dict]:
        """Parse education section"""
        education = []
        lines = content.strip().split("\n")
        for line in lines:
            if "**" in line and "-" in line:
                parts = line.split(" - ", 1)
                degree = parts[0].replace("**", "").strip()
                school_info = parts[1].strip() if len(parts) > 1 else ""
                education.append({"degree": degree, "school": school_info})
        return education

    def generate_header(self, header_info: Dict) -> str:
        html = ""
        if "name" in header_info:
            html += f"<h1>{header_info['name']}</h1>"
        if "title" in header_info and "specialization" in header_info:
            html += f'<div class="subtitle"><strong>{self.process_text(header_info["title"])}</strong> | {self.process_text(header_info["specialization"])}</div>'
        elif "title" in header_info:
            html += f'<div class="subtitle"><strong>{self.process_text(header_info["title"])}</strong></div>'
        if "contact" in header_info:
            contact_lines = []
            for line in header_info["contact"]:
                contact_lines.append(self.process_text(line))
            html += f'<div class="contact-info">{" | ".join(contact_lines)}</div>'
        return html

    def generate_generic_paragraph_section(self, title: str, content: str) -> str:
        """Generates an HTML section with a title and a paragraph."""
        # Ensure content is not empty or just whitespace before adding p tags
        processed_content = self.process_text(content)
        if not processed_content.strip():
            return f"<h2>{title}</h2>"  # Return title only if content is empty
        return f"""
        <h2>{title}</h2>
        <p style="margin: 5px 0; text-align: justify;">{processed_content}</p>
        """

    def generate_generic_bullet_list_section(self, title: str, content: str) -> str:
        """Generates an HTML section with a title and a bullet list."""
        html_content = f"<h2>{title}</h2><ul>"
        lines = content.strip().split("\n")
        for line in lines:
            processed_line = self.process_text(line.lstrip("- ").strip())
            if processed_line:
                html_content += f"<li>{processed_line}</li>"
        html_content += "</ul>"
        return html_content

    def generate_experience(self, title: str, content: str) -> str:
        html = f"<h2>{title}</h2>"
        entries = content.split("###")
        entries = [entry.strip() for entry in entries if entry.strip()]
        for entry in entries:
            job_data = self.parse_experience_entry(entry)
            if not job_data:
                continue
            html += '<div class="job-title">'
            html += f'<span><span class="company-name">{self.process_text(job_data["company"])}</span>'
            if job_data["role"]:
                html += f" | {self.process_text(job_data['role'])}"
            html += "</span>"
            if job_data["date"]:
                html += (
                    f'<span class="dates">{self.process_text(job_data["date"])}</span>'
                )
            html += "</div>"
            if job_data["bullets"]:
                html += "<ul>"
                for bullet in job_data["bullets"]:
                    html += f"<li>{self.process_text(bullet)}</li>"
                html += "</ul>"
        return html

    def generate_technical_expertise(self, title: str, content: str) -> str:
        skills = self.parse_technical_expertise(content)
        html = f"<h2>{title}</h2>"
        for category, skill_list in skills:
            html += f'<div class="tech-skills"><strong>{self.process_text(category)}:</strong> {self.process_text(skill_list)}</div>'
        return html

    def generate_education(self, title: str, content: str) -> str:
        education_items = self.parse_education(content)
        html = f"<h2>{title}</h2>"
        for item in education_items:
            html += '<div class="education-item">'
            html += f"<strong>{self.process_text(item['degree'])}</strong>"
            if item["school"]:
                html += f" - {self.process_text(item['school'])}"
            html += "</div>"
        return html

    def generate_html(self, parsed_data: Dict) -> str:
        header_info = parsed_data["header"]
        sections = parsed_data["sections"]  # This is now a list of dicts
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{header_info.get("name", "Resume")}</title>
    <style>{self.css}</style>
</head>
<body>
"""
        html += self.generate_header(header_info)

        # Map section types to generator methods
        # The generator methods will now take (title, content)
        section_type_renderers = {
            "timeline": self.generate_experience,  # Re-using generate_experience for timeline
            "aligned_list": self.generate_technical_expertise,  # Re-using for aligned lists
            "bullet_list": self.generate_generic_bullet_list_section,
            "paragraph": self.generate_generic_paragraph_section,
            # Education might need its own type if its structure is distinct enough from generic timeline
            # For now, if education is also "### Degree...\n_Date_...", it could be 'timeline'
            # If education is "**Degree** - School", it could be 'aligned_list' or 'paragraph'
            # Let's assume for now education can be a timeline type if structured like experience.
            # Or a bullet_list or paragraph depending on content.
            # The _determine_section_type needs to be robust.
        }

        # Special handling for 'Education' if its structure isn't strictly timeline or aligned_list based on current parsers
        # The `parse_education` method expects a certain format.
        # If we make `generate_education` take (title, content), it can be used for type 'education' if we add that type.

        # For now, let's adjust generate_experience to be more generic for timelines.
        # And generate_technical_expertise for aligned lists.
        # The _determine_section_type will be key.

        for section_data in sections:
            section_title = section_data["title"]
            section_type = section_data["type"]
            section_content = section_data["content"]

            if section_title == "Education" and self.parse_education(
                section_content
            ):  # Specific handler for Education
                html += self.generate_education(section_title, section_content)
            elif section_type in section_type_renderers:
                html += section_type_renderers[section_type](
                    section_title, section_content
                )
            else:
                # Fallback for unknown types, treat as paragraph
                print(
                    f"Warning: Unknown section type '{section_type}' for title '{section_title}'. Treating as paragraph.",
                    file=sys.stderr,
                )
                html += self.generate_generic_paragraph_section(
                    section_title, section_content
                )

        html += '<div class="no-print"><strong>📄 To save as PDF:</strong> Press Ctrl+P (or Cmd+P on Mac) and select "Save as PDF"</div>'
        html += "</body></html>"
        return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML resume from Markdown")
    parser.add_argument("input_file", help="Input markdown file")
    parser.add_argument("output_file", nargs="?", help="Output HTML file (optional)")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)

    # Determine output file
    if args.output_file:
        output_path = Path(args.output_file)
    else:
        output_path = input_path.with_suffix(".html")

    try:
        # Read markdown content
        with open(input_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Parse markdown
        resume_parser = ResumeParser()
        parsed_data = resume_parser.parse_markdown(markdown_content)

        # Generate HTML
        html_generator = HTMLGenerator()
        html_content = html_generator.generate_html(parsed_data)

        # Write HTML output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Resume generated successfully: {output_path}")
        print(f"To convert to PDF, open the HTML file in a browser and print to PDF")

    except Exception as e:
        print(f"Error generating resume: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

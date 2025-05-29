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
        self.sections = {}
        self.header_info = {}

    def parse_markdown(self, content: str) -> Dict:
        """Parse markdown content and extract resume sections"""
        lines = content.strip().split("\n")
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()

            if not line:  # Skip empty lines
                if current_content and current_content[-1] != "":
                    current_content.append("")
                continue

            if line.startswith("# "):  # Header (name)
                self.header_info["name"] = line[2:].strip()
                continue

            # Try: **Title** | Specialization (specialization can be empty or non-existent)
            title_spec_match = re.match(r"^\*\*([^*]+)\*\*(?:\s*\|\s*(.*))?$", line)
            if title_spec_match:
                self.header_info["title"] = title_spec_match.group(1).strip()
                if title_spec_match.group(
                    2
                ):  # If specialization part was matched and is not None
                    self.header_info["specialization"] = title_spec_match.group(
                        2
                    ).strip()
                continue

            # Fallback for lines that are just bold (e.g. **Title Only**), no pipe involved.
            # This should come AFTER the more specific title|spec match.
            # This regex ensures the entire line is just bold content.
            # title_only_match = re.match(r"^\*\*([^*]+(?:\s*\|\s*[^*]+)*)\*\*$", line)
            # Simpler: if it's fully bold and wasn't title|spec, it's a title.
            if (
                line.startswith("**")
                and line.endswith("**")
                and "title" not in self.header_info
            ):
                # And it wasn't already captured by the more specific regex above
                # This check is a bit weak, relies on title not being set yet
                # A better way is to ensure the previous regex did not match, or make this one more specific.
                # For now, let's ensure it doesn't overwrite a title from title_spec_match
                temp_title = line[2:-2].strip()
                if (
                    "|" not in temp_title
                ):  # if it's simple like **My Title**, not **A | B** (already handled)
                    self.header_info["title"] = temp_title
                    continue

            # Contact info
            if any(
                pattern in line.lower()
                for pattern in ["ca |", "redwood city", "+1 (", "@", "linkedin"]
            ):
                if "contact" not in self.header_info:
                    self.header_info["contact"] = []
                self.header_info["contact"].append(line)
                continue

            # Section headers
            if line.startswith("## "):
                if current_section and current_content:
                    self.sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
                continue

            if current_section:  # Add content to current section
                current_content.append(line)

        if current_section and current_content:  # Add the last section
            self.sections[current_section] = "\n".join(current_content).strip()

        return {"header": self.header_info, "sections": self.sections}


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
        return f"""
        <h2>{title}</h2>
        <p style=\"margin: 5px 0; text-align: justify;\">{self.process_text(content)}</p>
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

    def generate_experience(self, content: str) -> str:
        html = "<h2>Experience</h2>"
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

    def generate_technical_expertise(self, content: str) -> str:
        skills = self.parse_technical_expertise(content)
        html = "<h2>Technical Expertise</h2>"
        for category, skill_list in skills:
            html += f'<div class="tech-skills"><strong>{self.process_text(category)}:</strong> {self.process_text(skill_list)}</div>'
        return html

    def generate_education(self, content: str) -> str:
        education_items = self.parse_education(content)
        html = "<h2>Education</h2>"
        for item in education_items:
            html += '<div class="education-item">'
            html += f"<strong>{self.process_text(item['degree'])}</strong>"
            if item["school"]:
                html += f" - {self.process_text(item['school'])}"
            html += "</div>"
        return html

    def generate_html(self, parsed_data: Dict) -> str:
        header_info = parsed_data["header"]
        sections = parsed_data["sections"]
        html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{header_info.get("name", "Resume")}</title>
    <style>{self.css}</style>
</head>
<body>
"""
        html += self.generate_header(header_info)
        section_renderers = {
            "Summary": lambda content: self.generate_generic_paragraph_section(
                "Summary", content
            ),
            "Experience": self.generate_experience,
            "Technical Expertise": self.generate_technical_expertise,
            "Notable Achievements": lambda content: self.generate_generic_bullet_list_section(
                "Notable Achievements", content
            ),
            "Education": self.generate_education,
            "Languages": lambda content: self.generate_generic_paragraph_section(
                "Languages", content
            ),
        }
        for section_name, generator in section_renderers.items():
            if section_name in sections:
                html += generator(sections[section_name])
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

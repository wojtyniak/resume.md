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
        self.sections_list = []
        self.header_info = {}

    def _determine_section_type(self, content_lines: List[str]) -> str:
        """Determines the type of a section based on its content lines."""
        actual_content_lines = [line.strip() for line in content_lines if line.strip()]

        if not actual_content_lines:
            return "paragraph"

        # 1. Timeline (### Company | Role)
        if any(line.startswith("### ") for line in actual_content_lines):
            return "timeline"

        # 2. Aligned List (**Category:** Details)
        aligned_list_pattern = r"^\*\*(.+?):\*\*\s*(.*)$"
        aligned_matches = 0
        for line in actual_content_lines:
            if re.match(aligned_list_pattern, line):
                aligned_matches += 1
        if aligned_matches > 0 and (aligned_matches / len(actual_content_lines)) >= 0.5:
            return "aligned_list"

        # 3. Description List (**Term** - Description)
        description_list_pattern = r"^\*\*(.+?)\*\*\s*-\s*(.*)$"
        description_matches = 0
        for line in actual_content_lines:
            if re.match(description_list_pattern, line):
                description_matches += 1
        if (
            description_matches > 0
            and (description_matches / len(actual_content_lines)) >= 0.5
        ):
            return "description_list"

        # 4. Bullet List (- Item)
        bullet_lines = 0
        for line in actual_content_lines:
            if line.startswith("- "):
                bullet_lines += 1

        if bullet_lines > 0 and (bullet_lines / len(actual_content_lines)) >= 0.5:
            return "bullet_list"

        return "paragraph"

    def parse_markdown(self, content: str) -> Dict:
        """Parse markdown content and extract resume sections with their types"""
        lines = content.strip().split("\n")
        current_section_title = None
        current_content_lines = []
        self.header_info = {}
        self.sections_list = []

        for line_text in lines:
            original_line_stripped = line_text.strip()

            if not original_line_stripped:
                if current_content_lines and current_content_lines[-1] != "":
                    current_content_lines.append("")
                continue

            # 1. Name (must be the first major header element)
            if original_line_stripped.startswith("# ") and not self.header_info.get(
                "name"
            ):
                if current_section_title:
                    section_type = self._determine_section_type(current_content_lines)
                    self.sections_list.append(
                        {
                            "title": current_section_title,
                            "type": section_type,
                            "content": "\n".join(current_content_lines).strip(),
                        }
                    )
                self.header_info["name"] = original_line_stripped[2:].strip()
                current_section_title = None
                current_content_lines = []
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
                    self.header_info.pop("specialization", None)
                continue

            # 3. Section Start (##)
            if original_line_stripped.startswith("## "):
                if current_section_title:
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

            # 4. Contact Lines
            if (
                self.header_info.get("name")
                and self.header_info.get("title")
                and current_section_title is None
                and original_line_stripped
            ):
                if "contact" not in self.header_info:
                    self.header_info["contact"] = []
                self.header_info["contact"].append(original_line_stripped)
                continue

            # 5. Accumulate Section Content
            if current_section_title is not None:
                current_content_lines.append(line_text)

        if current_section_title and current_content_lines:
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
    def __init__(self, css_file_path="style.css"):
        self.css_file_path = css_file_path

    def _process_text_segment(self, segment: str) -> str:
        """Processes a non-URL text segment for bold and italic."""
        segment = self.process_bold(segment)
        segment = self.process_italic(segment)
        return segment

    def process_links_and_text(self, text: str) -> str:
        """
        Processes markdown links and other text formatting.
        Ensures that URLs are not affected by bold/italic processing.
        Processes bold/italic on link text and surrounding text.
        """
        output_parts = []
        last_end = 0
        # Regex to find Markdown links: [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        for match in re.finditer(link_pattern, text):
            start, end = match.span()

            # Process text before the link
            if start > last_end:
                output_parts.append(self._process_text_segment(text[last_end:start]))

            link_text_md = match.group(1)
            url = match.group(2)

            processed_link_text = self._process_text_segment(link_text_md)

            output_parts.append(f'<a href="{url}">{processed_link_text}</a>')

            last_end = end

        if last_end < len(text):
            output_parts.append(self._process_text_segment(text[last_end:]))

        return "".join(output_parts)

    def process_bold(self, text: str) -> str:
        """Convert markdown bold to HTML"""
        return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    def process_italic(self, text: str) -> str:
        """Convert markdown italic to HTML"""
        return re.sub(r"_([^_]+)_", r"<em>\1</em>", text)

    def process_text(self, text: str) -> str:
        """Process all markdown formatting (links, bold, italic) safely."""
        return self.process_links_and_text(text)

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

    def generate_header(self, header_info: Dict) -> str:
        html = '<div class="header-section">'
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
        html += "</div>"
        return html

    def generate_generic_paragraph_section(self, title: str, content: str) -> str:
        """Generates an HTML section with a title and a paragraph."""
        processed_content = self.process_text(content)
        if not processed_content.strip():
            return f"<h2>{title}</h2>"
        return f"""
        <h2>{title}</h2>
        <p class=\"paragraph-content\">{processed_content}</p>
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
            html += '<div class="list-item-container-flex">'
            html += f'<span><span class="item-name">{self.process_text(job_data["company"])}</span>'
            if job_data["role"]:
                html += f" | {self.process_text(job_data['role'])}"
            html += "</span>"
            if job_data["date"]:
                html += f'<span class="item-meta">{self.process_text(job_data["date"])}</span>'
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
            processed_category = self.process_text(category)
            processed_skill_list = self.process_text(skill_list)
            html += f'<div class="aligned-list-item"><strong>{processed_category}:</strong> {processed_skill_list}</div>'
        return html

    def generate_description_list_section(self, title: str, content: str) -> str:
        """Generates an HTML section for a description list (e.g., **Term** - Definition)."""
        html = f"<h2>{title}</h2>"
        lines = content.strip().split("\n")
        item_pattern = r"^\*\*(.+?)\*\*\s*-\s*(.*)$"
        for line_content in lines:
            line = line_content.strip()
            match = re.match(item_pattern, line)
            if match:
                term = self.process_text(match.group(1).strip())
                description = self.process_text(match.group(2).strip())

                html += '<div class="simple-list-item">'
                html += f'<strong class="item-name">{term}</strong>'
                if (
                    description
                ):
                    html += f" - {description}"
                html += "</div>"
        return html

    def generate_html(self, parsed_data: Dict) -> str:
        header_info = parsed_data["header"]
        sections = parsed_data["sections"]

        css_content = ""
        css_link_tag = f'<link rel="stylesheet" href="{self.css_file_path}">\n'
        try:
            with open(self.css_file_path, "r", encoding="utf-8") as css_file:
                css_content = css_file.read()
        except Exception as e:
            print(
                f"Warning: Could not read CSS file '{self.css_file_path}': {e}",
                file=sys.stderr,
            )
            css_content = ""
            css_link_tag = ""

        html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{header_info.get("name", "Resume")}</title>
    {css_link_tag}<style>\n{css_content}\n</style>
</head>
<body>
"""
        html += self.generate_header(header_info)
        html += '<div class="content-wrapper">'

        section_type_renderers = {
            "timeline": self.generate_experience,
            "aligned_list": self.generate_technical_expertise,
            "bullet_list": self.generate_generic_bullet_list_section,
            "paragraph": self.generate_generic_paragraph_section,
            "description_list": self.generate_description_list_section,
        }

        for section_data in sections:
            section_title = section_data["title"]
            section_type = section_data["type"]
            section_content = section_data["content"]

            if section_type in section_type_renderers:
                html += section_type_renderers[section_type](
                    section_title, section_content
                )
            else:
                print(
                    f"Warning: Unknown section type '{section_type}' for title '{section_title}'. Treating as paragraph.",
                    file=sys.stderr,
                )
                html += self.generate_generic_paragraph_section(
                    section_title, section_content
                )

        html += "</div>"
        html += '<div class="no-print"><strong>📄 To save as PDF:</strong> Press Ctrl+P (or Cmd+P on Mac) and select "Save as PDF"</div>'
        html += "</body></html>"
        return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML resume from Markdown")
    parser.add_argument("input_file", help="Input markdown file")
    parser.add_argument("output_file", nargs="?", help="Output HTML file (optional)")
    parser.add_argument(
        "--style",
        "-s",
        default="style.css",
        help="Path to custom CSS file (default: style.css)",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)

    if args.output_file:
        output_path = Path(args.output_file)
    else:
        output_path = input_path.with_suffix(".html")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        resume_parser = ResumeParser()
        parsed_data = resume_parser.parse_markdown(markdown_content)

        html_generator = HTMLGenerator(css_file_path=args.style)
        html_content = html_generator.generate_html(parsed_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Resume generated successfully: {output_path}")
        print("To convert to PDF, open the HTML file in a browser and print to PDF")

    except Exception as e:
        print(f"Error generating resume: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

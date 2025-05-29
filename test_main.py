import unittest

from main import HTMLGenerator, ResumeParser


class TestResumeParser(unittest.TestCase):
    def setUp(self):
        self.parser = ResumeParser()

    def test_parse_header_and_sections(self):
        markdown_content = """# John Doe
**Software Engineer** | AI Specialist
Location | 123-456-7890 | john.doe@email.com

## Summary
This is a summary.

## Experience
### Company A | Role A
_Date A_
- Bullet A1
- Bullet A2

## Skills
- Skill 1
- Skill 2
"""
        parsed_data = self.parser.parse_markdown(markdown_content)

        self.assertEqual(parsed_data["header"]["name"], "John Doe")
        self.assertEqual(parsed_data["header"]["title"], "Software Engineer")
        self.assertEqual(parsed_data["header"]["specialization"], "AI Specialist")
        self.assertIn(
            "Location | 123-456-7890 | john.doe@email.com",
            parsed_data["header"]["contact"],
        )

        self.assertIn("Summary", parsed_data["sections"])
        self.assertEqual(parsed_data["sections"]["Summary"], "This is a summary.")

        self.assertIn("Experience", parsed_data["sections"])
        self.assertIn("### Company A | Role A", parsed_data["sections"]["Experience"])

        self.assertIn("Skills", parsed_data["sections"])
        self.assertEqual(parsed_data["sections"]["Skills"], "- Skill 1\n- Skill 2")

    def test_empty_input(self):
        parsed_data = self.parser.parse_markdown("")
        self.assertEqual(parsed_data["header"], {})
        self.assertEqual(parsed_data["sections"], {})

    def test_no_specialization(self):
        markdown_content = """# Jane Doe
**Product Manager**
jane.doe@email.com
"""
        parsed_data = self.parser.parse_markdown(markdown_content)
        self.assertEqual(parsed_data["header"]["name"], "Jane Doe")
        self.assertEqual(parsed_data["header"]["title"], "Product Manager")
        self.assertNotIn("specialization", parsed_data["header"])
        self.assertIn("jane.doe@email.com", parsed_data["header"]["contact"])


class TestHTMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HTMLGenerator()

    def test_process_text(self):
        text = "**Bold** _Italic_ [Link](http://example.com)"
        expected = '<strong>Bold</strong> <em>Italic</em> <a href="http://example.com">Link</a>'
        self.assertEqual(self.generator.process_text(text), expected)

    def test_process_links(self):
        text = "[Example Link](http://example.com)"
        expected = '<a href="http://example.com">Example Link</a>'
        self.assertEqual(self.generator.process_links(text), expected)

    def test_process_bold(self):
        text = "**Bold Text**"
        expected = "<strong>Bold Text</strong>"
        self.assertEqual(self.generator.process_bold(text), expected)

    def test_process_italic(self):
        text = "_Italic Text_"
        expected = "<em>Italic Text</em>"
        self.assertEqual(self.generator.process_italic(text), expected)

    def test_parse_experience_entry(self):
        entry = """Company X | Senior Developer
_Jan 2020 - Dec 2022_
- Developed new features.
- Mentored junior developers.
"""
        expected = {
            "company": "Company X",
            "role": "Senior Developer",
            "date": "Jan 2020 - Dec 2022",
            "bullets": ["Developed new features.", "Mentored junior developers."],
        }
        self.assertEqual(self.generator.parse_experience_entry(entry), expected)

    def test_parse_technical_expertise(self):
        content = """**Languages:** Python, Go
**Databases:** SQL, NoSQL"""
        expected = [("Languages", "Python, Go"), ("Databases", "SQL, NoSQL")]
        self.assertEqual(self.generator.parse_technical_expertise(content), expected)

    def test_parse_education(self):
        content = """**M.S. Computer Science** - University A (2020)
**B.S. Software Engineering** - University B (2018)"""
        expected = [
            {"degree": "M.S. Computer Science", "school": "University A (2020)"},
            {"degree": "B.S. Software Engineering", "school": "University B (2018)"},
        ]
        self.assertEqual(self.generator.parse_education(content), expected)

    def test_generate_header(self):
        header_info = {
            "name": "Alice Wonderland",
            "title": "**Chief Storyteller**",
            "specialization": "_Dream Weaver_",
            "contact": ["alice@example.com", "[LinkedIn](http://linkedin.com/alice)"],
        }
        html = self.generator.generate_header(header_info)
        self.assertIn("<h1>Alice Wonderland</h1>", html)
        self.assertIn("<strong>Chief Storyteller</strong>", html)
        self.assertIn("<em>Dream Weaver</em>", html)
        self.assertIn("alice@example.com", html)
        self.assertIn('<a href="http://linkedin.com/alice">LinkedIn</a>', html)

    def test_generate_generic_paragraph_section(self):
        html = self.generator.generate_generic_paragraph_section(
            "Test Section", "This is _italic_ text."
        )
        self.assertIn("<h2>Test Section</h2>", html)
        self.assertIn(
            '<p style="margin: 5px 0; text-align: justify;">This is <em>italic</em> text.</p>',
            html,
        )

    def test_generate_generic_bullet_list_section(self):
        content = (
            "- Item 1 **bold**\n- Item 2\n  - Sub Item (should be treated as full line)"
        )
        html = self.generator.generate_generic_bullet_list_section(
            "Bullet Section", content
        )
        self.assertIn("<h2>Bullet Section</h2>", html)
        self.assertIn("<li>Item 1 <strong>bold</strong></li>", html)
        self.assertIn("<li>Item 2</li>", html)
        self.assertIn("<li>Sub Item (should be treated as full line)</li>", html)

    def test_generate_experience(self):
        content = """### Alpha Inc. | Lead Engineer
_2022 - Present_
- Feature **one**.
- Feature _two_.
"""
        html = self.generator.generate_experience(content)
        self.assertIn("<h2>Experience</h2>", html)
        self.assertIn('<span class="company-name">Alpha Inc.</span>', html)
        self.assertIn("Lead Engineer", html)
        self.assertIn('<span class="dates">2022 - Present</span>', html)
        self.assertIn("<li>Feature <strong>one</strong>.</li>", html)
        self.assertIn("<li>Feature <em>two</em>.</li>", html)

    def test_generate_technical_expertise(self):
        content = "**Core:** _Go_, Python\n**Tools:** Docker, **Kubernetes**"
        html = self.generator.generate_technical_expertise(content)
        self.assertIn("<h2>Technical Expertise</h2>", html)
        self.assertIn(
            '<div class="tech-skills"><strong>Core:</strong> <em>Go</em>, Python</div>',
            html,
        )
        self.assertIn(
            '<div class="tech-skills"><strong>Tools:</strong> Docker, <strong>Kubernetes</strong></div>',
            html,
        )

    def test_generate_education(self):
        content = "**PhD** - _Wonderland Uni_\n**MSc** - Another Place"
        html = self.generator.generate_education(content)
        self.assertIn("<h2>Education</h2>", html)
        self.assertIn("<strong>PhD</strong> - <em>Wonderland Uni</em>", html)
        self.assertIn("<strong>MSc</strong> - Another Place", html)

    def test_generate_html_integration(self):
        parsed_data = {
            "header": {
                "name": "Test User",
                "title": "Tester",
                "contact": ["test@example.com"],
            },
            "sections": {
                "Summary": "This is a _summary_.",
                "Notable Achievements": "- Achieved **goal 1**\n- Achieved goal 2",
                "Languages": "English, TestLang",
            },
        }
        html = self.generator.generate_html(parsed_data)
        self.assertIn("<title>Test User</title>", html)
        self.assertIn("<h1>Test User</h1>", html)
        self.assertIn(
            '<div class="subtitle"><strong>Tester</strong></div>', html
        )  # Title only
        self.assertIn("test@example.com", html)
        # Summary (generic paragraph)
        self.assertIn("<h2>Summary</h2>", html)
        self.assertIn(
            '<p style="margin: 5px 0; text-align: justify;">This is a <em>summary</em>.</p>',
            html,
        )
        # Notable Achievements (generic bullet list)
        self.assertIn("<h2>Notable Achievements</h2>", html)
        self.assertIn("<li>Achieved <strong>goal 1</strong></li>", html)
        self.assertIn("<li>Achieved goal 2</li>", html)
        # Languages (generic paragraph)
        self.assertIn("<h2>Languages</h2>", html)
        self.assertIn(
            '<p style="margin: 5px 0; text-align: justify;">English, TestLang</p>', html
        )
        # Check for the PDF instruction div
        self.assertIn('<div class="no-print"><strong>📄 To save as PDF:</strong>', html)


if __name__ == "__main__":
    unittest.main()

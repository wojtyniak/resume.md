import unittest

from main import HTMLGenerator, ResumeParser


class TestResumeParser(unittest.TestCase):
    def setUp(self):
        self.parser = ResumeParser()

    def test_parse_header_and_typed_sections(self):
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
**Category1:** Skill 1, Skill 2
**Category2:** Skill 3

## Projects
- Project X
- Project Y

## Education
**BS CS** - University Z
_2000-2004_
Some notes.
"""
        parsed_data = self.parser.parse_markdown(markdown_content)

        self.assertEqual(parsed_data["header"]["name"], "John Doe")
        self.assertEqual(parsed_data["header"]["title"], "Software Engineer")
        self.assertEqual(parsed_data["header"]["specialization"], "AI Specialist")
        self.assertIn(
            "Location | 123-456-7890 | john.doe@email.com",
            parsed_data["header"]["contact"],
        )

        self.assertTrue(any(s["title"] == "Summary" for s in parsed_data["sections"]))
        summary_section = next(
            s for s in parsed_data["sections"] if s["title"] == "Summary"
        )
        self.assertEqual(summary_section["type"], "paragraph")
        self.assertEqual(summary_section["content"], "This is a summary.")

        self.assertTrue(
            any(s["title"] == "Experience" for s in parsed_data["sections"])
        )
        experience_section = next(
            s for s in parsed_data["sections"] if s["title"] == "Experience"
        )
        self.assertEqual(experience_section["type"], "timeline")
        self.assertIn("### Company A | Role A", experience_section["content"])
        self.assertIn("- Bullet A1", experience_section["content"])

        self.assertTrue(any(s["title"] == "Skills" for s in parsed_data["sections"]))
        skills_section = next(
            s for s in parsed_data["sections"] if s["title"] == "Skills"
        )
        self.assertEqual(skills_section["type"], "aligned_list")
        self.assertEqual(
            skills_section["content"],
            "**Category1:** Skill 1, Skill 2\n**Category2:** Skill 3",
        )

        self.assertTrue(any(s["title"] == "Projects" for s in parsed_data["sections"]))
        projects_section = next(
            s for s in parsed_data["sections"] if s["title"] == "Projects"
        )
        self.assertEqual(projects_section["type"], "bullet_list")
        self.assertEqual(projects_section["content"], "- Project X\n- Project Y")

        self.assertTrue(any(s["title"] == "Education" for s in parsed_data["sections"]))
        education_section = next(
            s for s in parsed_data["sections"] if s["title"] == "Education"
        )
        self.assertEqual(education_section["type"], "paragraph")
        self.assertIn("**BS CS** - University Z", education_section["content"])
        self.assertIn("_2000-2004_", education_section["content"])
        self.assertIn("Some notes.", education_section["content"])

    def test_empty_input(self):
        parsed_data = self.parser.parse_markdown("")
        self.assertEqual(parsed_data["header"], {})
        self.assertEqual(parsed_data["sections"], [])

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

    def test_section_type_determination(self):
        timeline_content = "### Job 1 | Dev\n_Date_\n- Did stuff"
        self.assertEqual(
            self.parser._determine_section_type(timeline_content.split("\n")),
            "timeline",
        )

        aligned_content_majority = "**Tech:** Go, Python\n**Tools:** Docker, K8s"
        self.assertEqual(
            self.parser._determine_section_type(aligned_content_majority.split("\n")),
            "aligned_list",
        )
        aligned_content_minority = (
            "**Tech:** Go, Python\nJust a normal line\nAnother normal line"
        )
        self.assertEqual(
            self.parser._determine_section_type(aligned_content_minority.split("\n")),
            "paragraph",
        )
        aligned_content_single_good = "**Tech:** Go, Python"
        self.assertEqual(
            self.parser._determine_section_type(
                aligned_content_single_good.split("\n")
            ),
            "aligned_list",
        )

        desc_list_clear = "**Degree 1** - School A\n**Degree 2** - School B"
        self.assertEqual(
            self.parser._determine_section_type(desc_list_clear.split("\n")),
            "description_list",
        )
        desc_list_mixed_majority = "**Degree 1** - School A\nSome other note\n**Degree 2** - School B\n**Degree 3** - School C"
        self.assertEqual(
            self.parser._determine_section_type(desc_list_mixed_majority.split("\n")),
            "description_list",
        )
        desc_list_mixed_minority = (
            "**Degree 1** - School A\nSome other note\nAnother note also"
        )
        self.assertEqual(
            self.parser._determine_section_type(desc_list_mixed_minority.split("\n")),
            "paragraph",
        )
        desc_list_single_good = "**Degree 1** - School A"
        self.assertEqual(
            self.parser._determine_section_type(desc_list_single_good.split("\n")),
            "description_list",
        )

        bullet_content = "- Item 1\n- Item 2\n  - Sub Item"
        self.assertEqual(
            self.parser._determine_section_type(bullet_content.split("\n")),
            "bullet_list",
        )
        bullet_content_mixed = (
            "Some intro text\n- Item 1\n- Item 2"
        )
        self.assertEqual(
            self.parser._determine_section_type(bullet_content_mixed.split("\n")),
            "bullet_list",
        )

        single_line_paragraph = "Just one line of text."
        self.assertEqual(
            self.parser._determine_section_type([single_line_paragraph]), "paragraph"
        )

        self.assertEqual(
            self.parser._determine_section_type([]), "paragraph"
        )

        wojtek_summary = "Technical leader with 12+ years..."
        self.assertEqual(
            self.parser._determine_section_type(wojtek_summary.split("\n")), "paragraph"
        )

        wojtek_experience_first_entry = "### Knowbase One | CTO & Co-Founder\n_January 2025 - Present_\n- Designed multi-modal AI platform"
        self.assertEqual(
            self.parser._determine_section_type(
                wojtek_experience_first_entry.split("\n")
            ),
            "timeline",
        )

        wojtek_tech_expertise = "**AI/ML Systems:** Agentic architectures, RAG, Vector databases, Multi-modal AI, LLM tool design\n**Languages:** Go (Expert), Python (Expert), Clojure"
        self.assertEqual(
            self.parser._determine_section_type(wojtek_tech_expertise.split("\n")),
            "aligned_list",
        )

        wojtek_achievements = '- Automated critical processes: certificate management (saving 2 FTE) and infrastructure remediation (<5 min response)\n- Speaker: ["Building Reliable Security Services"](https://www.youtube.com/watch?v=yaZSTVXrhMA&t=3s) - SRECon'
        self.assertEqual(
            self.parser._determine_section_type(wojtek_achievements.split("\n")),
            "bullet_list",
        )

        wojtek_education = "**M.S. Internet Engineering** - Wrocław University of Technology, Poland (2011-2013)\n**B.S. Computer Science** - Wrocław University of Technology, Poland (2007-2011)"
        self.assertEqual(
            self.parser._determine_section_type(wojtek_education.split("\n")),
            "description_list",
        )

    def test_vimes_header_parsing(self):
        markdown_content = """# Samuel Vimes
**His Grace, The Duke of Ankh, Commander of the Ankh-Morpork City Watch**
Ankh-Morpork, The Discworld | Often Found at The Sign of the Genuinely Surprised Man (Duty Calls) | [Cable Street Particulars](https://wiki.lspace.org/Cable_Street_Particulars)

## Summary
This is a summary.
"""
        parsed_data = self.parser.parse_markdown(markdown_content)
        self.assertEqual(parsed_data["header"]["name"], "Samuel Vimes")
        self.assertEqual(
            parsed_data["header"]["title"],
            "His Grace, The Duke of Ankh, Commander of the Ankh-Morpork City Watch",
        )
        self.assertNotIn(
            "specialization", parsed_data["header"]
        )
        self.assertIn("contact", parsed_data["header"])
        self.assertEqual(len(parsed_data["header"]["contact"]), 1)
        self.assertEqual(
            parsed_data["header"]["contact"][0],
            "Ankh-Morpork, The Discworld | Often Found at The Sign of the Genuinely Surprised Man (Duty Calls) | [Cable Street Particulars](https://wiki.lspace.org/Cable_Street_Particulars)",
        )
        self.assertTrue(any(s["title"] == "Summary" for s in parsed_data["sections"]))


class TestHTMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HTMLGenerator()
        self.maxDiff = None

    def test_process_text(self):
        text = "**Bold** _Italic_ [Link](http://example.com)"
        expected = '<strong>Bold</strong> <em>Italic</em> <a href="http://example.com">Link</a>'
        self.assertEqual(self.generator.process_text(text), expected)

    def test_process_text_with_complex_links(self):
        """Test processing of links with markdown in text and special chars in URL."""
        text1 = "[Link to section](http://example.com/foo_bar/doc_v1.html)"
        expected1 = (
            '<a href="http://example.com/foo_bar/doc_v1.html">Link to section</a>'
        )
        self.assertEqual(self.generator.process_text(text1), expected1)

        text2 = "[Link with **bold** and _italic_ text](http://example.com/page)"
        expected2 = '<a href="http://example.com/page">Link with <strong>bold</strong> and <em>italic</em> text</a>'
        self.assertEqual(self.generator.process_text(text2), expected2)

        text3 = "[**Important** _document_ here](http://example.com/archive/important_doc_version_2.pdf)"
        expected3 = '<a href="http://example.com/archive/important_doc_version_2.pdf"><strong>Important</strong> <em>document</em> here</a>'
        self.assertEqual(self.generator.process_text(text3), expected3)
    
        text4 = "Please see: [**Detail _A_**](http://example.com/details_a) and also [Detail B](http://example.com/details_b)."
        expected4 = 'Please see: <a href="http://example.com/details_a"><strong>Detail <em>A</em></strong></a> and also <a href="http://example.com/details_b">Detail B</a>.'
        self.assertEqual(self.generator.process_text(text4), expected4)

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
            """<p class="paragraph-content">This is <em>italic</em> text.</p>""",
            html,
        )
        html_empty = self.generator.generate_generic_paragraph_section(
            "Empty Section", "  "
        )
        self.assertIn("<h2>Empty Section</h2>", html_empty)
        self.assertNotIn("<p>", html_empty)

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

    def test_generate_experience_timeline_type(
        self,
    ):
        content = """### Alpha Inc. | Lead Engineer
_2022 - Present_
- Feature **one**.
- Feature _two_."""
        html = self.generator.generate_experience(
            "Past Work", content
        )
        self.assertIn("<h2>Past Work</h2>", html)
        self.assertIn('<span class="item-name">Alpha Inc.</span>', html)
        self.assertIn("Lead Engineer", html)
        self.assertIn('<span class="item-meta">2022 - Present</span>', html)
        self.assertIn("<li>Feature <strong>one</strong>.</li>", html)
        self.assertIn("<li>Feature <em>two</em>.</li>", html)

    def test_generate_technical_expertise_aligned_list_type(
        self,
    ):  
        content = "**Core:** _Go_, Python\n**Tools:** Docker, **Kubernetes**"
        html = self.generator.generate_technical_expertise(
            "Tech Stack", content
        )
        self.assertIn("<h2>Tech Stack</h2>", html)
        self.assertIn(
            """<div class="aligned-list-item"><strong>Core:</strong> <em>Go</em>, Python</div>""",
            html,
        )
        self.assertIn(
            """<div class="aligned-list-item"><strong>Tools:</strong> Docker, <strong>Kubernetes</strong></div>""",
            html,
        )

    def test_generate_description_list_section(self):
        content = """**Term One** - Its _description_ here.
**Term Two** - Another description, [link](http://example.com).
Not a description list item.
**Term Three** - Final one."""
        html = self.generator.generate_description_list_section("Descriptions", content)
        self.assertIn("<h2>Descriptions</h2>", html)
        self.assertIn(
            '<div class="simple-list-item"><strong class="item-name">Term One</strong> - Its <em>description</em> here.</div>',
            html,
        )
        self.assertIn(
            '<div class="simple-list-item"><strong class="item-name">Term Two</strong> - Another description, <a href="http://example.com">link</a>.</div>',
            html,
        )
        self.assertIn(
            '<div class="simple-list-item"><strong class="item-name">Term Three</strong> - Final one.</div>',
            html,
        )
        self.assertNotIn(
            "Not a description list item.", html
        )

    def test_generate_html_integration_with_typed_sections(self):
        parsed_data = {
            "header": {
                "name": "Test User",
                "title": "Tester",
                "contact": ["test@example.com"],
            },
            "sections": [
                {
                    "title": "Overview",
                    "type": "paragraph",
                    "content": "This is a _summary_.",
                },
                {
                    "title": "Achievements",
                    "type": "bullet_list",
                    "content": "- Achieved **goal 1**\n- Achieved goal 2",
                },
                {
                    "title": "Toolset",
                    "type": "aligned_list",
                    "content": "**Software:** Editor, Compiler\n**Hardware:** Mouse, Keyboard",
                },
                {
                    "title": "Work History",
                    "type": "timeline",
                    "content": "### Big Corp | Coder\n_Then - Now_\n- Wrote code.",
                },
                {
                    "title": "Qualifications",
                    "type": "description_list",
                    "content": "**Degree Alpha** - School One\n**Certificate Beta** - School Two\nThis line will be ignored.",
                },
            ],
        }
        html = self.generator.generate_html(parsed_data)
        self.assertIn("<title>Test User</title>", html)
        self.assertIn("<h1>Test User</h1>", html)
        self.assertIn("""<div class="subtitle"><strong>Tester</strong></div>""", html)
        self.assertIn("test@example.com", html)
        self.assertIn(
            '<link rel="stylesheet" href="style.css">', html
        )

        self.assertIn("<h2>Overview</h2>", html)
        self.assertIn(
            """<p class="paragraph-content">This is a <em>summary</em>.</p>""",
            html,
        )
        self.assertIn("<h2>Achievements</h2>", html)
        self.assertIn("<li>Achieved <strong>goal 1</strong></li>", html)
        self.assertIn("<li>Achieved goal 2</li>", html)

        self.assertIn("<h2>Toolset</h2>", html)
        self.assertIn(
            """<div class="aligned-list-item"><strong>Software:</strong> Editor, Compiler</div>""",
            html,
        )
        self.assertIn(
            """<div class="aligned-list-item"><strong>Hardware:</strong> Mouse, Keyboard</div>""",
            html,
        )

        self.assertIn("<h2>Work History</h2>", html)
        self.assertIn('<span class="item-name">Big Corp</span>', html)
        self.assertIn("<li>Wrote code.</li>", html)

        self.assertIn("<h2>Qualifications</h2>", html)
        self.assertIn(
            '<div class="simple-list-item"><strong class="item-name">Degree Alpha</strong> - School One</div>',
            html,
        )
        self.assertIn(
            '<div class="simple-list-item"><strong class="item-name">Certificate Beta</strong> - School Two</div>',
            html,
        )
        self.assertNotIn(
            "This line will be ignored.", html
        )

        self.assertIn('<div class="no-print"><strong>📄 To save as PDF:</strong>', html)


if __name__ == "__main__":
    unittest.main()

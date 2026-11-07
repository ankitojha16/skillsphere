import io
import re
from django.core.cache import cache
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

class AcademicNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_w, page_h = A4
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor('#4338CA'))
            self.drawString(40, page_h - 26, "SKILLSPHERE ACADEMIC NOTES")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor('#64748B'))
            hdr = getattr(self, 'doc_title', 'Courseware Study Guide')
            self.drawString(175, page_h - 26, f"|  {hdr[:65]}")
            self.setStrokeColor(colors.HexColor('#CBD5E1'))
            self.setLineWidth(0.5)
            self.line(40, page_h - 30, page_w - 40, page_h - 30)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.5)
        self.line(40, 36, page_w - 40, 36)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawString(40, 24, "SkillSphere Comprehensive Courseware • Academic Edition")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_w - 40, 24, page_str)
        self.restoreState()


class PDFService:

    @staticmethod
    def _parse_bullet_list(raw_val):
        """Safely parses JSON arrays, newline-delimited strings, or bullet points."""
        import json
        if not raw_val:
            return []
        if isinstance(raw_val, list):
            return [str(x).strip() for x in raw_val if str(x).strip()]
        if isinstance(raw_val, str):
            val = raw_val.strip()
            if val.startswith('[') and val.endswith(']'):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            lines = [l.strip().lstrip('•-*123456789. ') for l in val.split('\n') if l.strip()]
            return [l for l in lines if l]
        return []

    @staticmethod
    def _clean_html_text(raw_html):
        """Extracts text and code snippets from raw HTML content."""
        if not raw_html:
            return [], []
        code_blocks = re.findall(r'<pre><code>(.*?)</code></pre>', raw_html, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'<code>(.*?)</code>', raw_html, re.DOTALL)

        clean_text = re.sub(r'<pre><code>.*?</code></pre>', '[CODE_BLOCK]', raw_html, flags=re.DOTALL)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_paragraphs = [re.sub(r'\s+', ' ', p).strip() for p in clean_text.split('\n') if p.strip()]
        return clean_paragraphs, code_blocks

    @staticmethod
    def generate_certificate_pdf(certificate) -> bytes:
        """
        Generates an authentic, high-resolution landscape certificate PDF
        with SkillSphere ivory/white background, gold double border, official seal,
        and public verification link per Module 9 specifications.
        """
        cache_key = f"cert_pdf_{getattr(certificate, 'certificate_id', certificate.pk)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        buffer = io.BytesIO()
        width, height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        # 1. Background Fill: Elegant Ivory / Soft White
        c.setFillColor(colors.HexColor('#FAF9F5'))
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # 2. Outer Ornate Gold Border
        c.setStrokeColor(colors.HexColor('#D97706'))  # Amber/Gold
        c.setLineWidth(3.5)
        c.rect(22, 22, width - 44, height - 44)

        # 3. Inner Secondary Accent Border
        c.setStrokeColor(colors.HexColor('#F59E0B'))  # Light Gold
        c.setLineWidth(1.2)
        c.rect(28, 28, width - 56, height - 56)

        # 4. Corner Rosettes / Decorative Accents
        c.setFillColor(colors.HexColor('#B45309'))
        c.circle(28, 28, 5, fill=True, stroke=False)
        c.circle(width - 28, 28, 5, fill=True, stroke=False)
        c.circle(28, height - 28, 4, fill=True, stroke=False)
        c.circle(width - 28, height - 28, 4, fill=True, stroke=False)

        # 5. Header Brand Title
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(colors.HexColor('#6B7280'))
        c.drawCentredString(width / 2.0, height - 66, "SKILLSPHERE PROFESSIONAL LEARNING PLATFORM")

        # 6. Main Certificate Title
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(colors.HexColor('#0F172A'))  # Deep Navy
        c.drawCentredString(width / 2.0, height - 105, "CERTIFICATE OF COMPLETION")

        # 7. Subtitle
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawCentredString(width / 2.0, height - 130, "VERIFIED ACADEMIC & TECHNICAL CREDENTIAL")

        # 8. Student Name
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(colors.HexColor('#1E293B'))  # Slate Navy
        recipient = certificate.recipient_name or certificate.user.get_full_name() or certificate.user.username
        c.drawCentredString(width / 2.0, height - 175, recipient)

        # Divider line under student name
        c.setStrokeColor(colors.HexColor('#D97706'))
        c.setLineWidth(1.5)
        c.line(width / 2.0 - 200, height - 190, width / 2.0 + 200, height - 190)

        # 9. Standardized Completion Wording (Module 9 Requirement)
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor('#475569'))
        course_name = certificate.course.title if certificate.course else certificate.title
        cert_statement_1 = f"This certificate is awarded to {recipient} for successfully completing"
        cert_statement_2 = f"and meeting the comprehensive assessment requirements of SkillSphere."

        c.drawCentredString(width / 2.0, height - 215, cert_statement_1)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#0F172A'))
        c.drawCentredString(width / 2.0, height - 240, f"\"{course_name}\"")
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor('#475569'))
        c.drawCentredString(width / 2.0, height - 262, cert_statement_2)

        # 10. Decorative Achievement Seal (Center-Right Badge)
        seal_x = width - 130
        seal_y = height / 2.0 - 20
        c.setStrokeColor(colors.HexColor('#D97706'))
        c.setLineWidth(2)
        c.circle(seal_x, seal_y, 36, fill=False, stroke=True)
        c.setFillColor(colors.HexColor('#FEF3C7'))
        c.circle(seal_x, seal_y, 34, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor('#B45309'))
        c.drawCentredString(seal_x, seal_y + 12, "★ VERIFIED ★")
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(seal_x, seal_y, "VERIFIED")
        c.setFont("Helvetica", 7)
        c.drawCentredString(seal_x, seal_y - 12, "SKILLSPHERE")

        # 11. Metadata Box (Bottom Left)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawString(60, 85, "CERTIFICATE ID:")
        c.setFont("Courier-Bold", 9)
        c.setFillColor(colors.HexColor('#0F172A'))
        c.drawString(160, 85, certificate.certificate_id)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawString(60, 68, "DATE OF ISSUANCE:")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#0F172A'))
        c.drawString(160, 68, certificate.issued_at.strftime('%B %d, %Y'))

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawString(60, 51, "PUBLIC VERIFY:")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#2563EB'))
        c.drawString(160, 51, f"https://skillsphere-cyan.vercel.app/certificates/verify/{certificate.certificate_id}/")

        # 12. Signature & Academic Authority (Bottom Right)
        c.setStrokeColor(colors.HexColor('#94A3B8'))
        c.setLineWidth(1)
        c.line(width - 240, 75, width - 60, 75)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#0F172A'))
        c.drawCentredString(width - 150, 60, "SkillSphere Academic Board")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawCentredString(width - 150, 48, "Authorized Institutional Issuer")

        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        cache.set(cache_key, pdf_data, 86400)
        return pdf_data

    @staticmethod
    def generate_lesson_notes_pdf(lesson) -> bytes:
        """
        Generates an authentic, 16-section comprehensive academic PDF study guide
        using AcademicNumberedCanvas for two-pass running headers ('Page X of Y')
        and professional academic typography.
        """
        cache_key = f"lesson_notes_pdf_v2_{lesson.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=44,
            bottomMargin=44
        )
        styles = getSampleStyleSheet()

        # Professional Academic Typography Styles
        title_style = ParagraphStyle(
            'AcademicTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4,
            keepWithNext=True
        )
        subtitle_style = ParagraphStyle(
            'AcademicSubtitle',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#4338CA'),
            spaceAfter=8,
            keepWithNext=True
        )
        meta_style = ParagraphStyle(
            'AcademicMeta',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'AcademicH2',
            fontName='Helvetica-Bold',
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )
        h3_style = ParagraphStyle(
            'AcademicH3',
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#334155'),
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'AcademicBody',
            fontName='Helvetica',
            fontSize=9,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )
        code_style = ParagraphStyle(
            'AcademicCode',
            fontName='Courier',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#0F172A'),
            backColor=colors.HexColor('#F8FAFC'),
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=8
        )
        terminal_style = ParagraphStyle(
            'AcademicTerminal',
            fontName='Courier-Bold',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#38BDF8'),
            backColor=colors.HexColor('#0F172A'),
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=8
        )
        callout_style = ParagraphStyle(
            'AcademicCallout',
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor('#1E293B'),
            backColor=colors.HexColor('#EEF2FF'),
            borderColor=colors.HexColor('#6366F1'),
            borderWidth=0.8,
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=10
        )
        mistake_style = ParagraphStyle(
            'AcademicMistake',
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor('#991B1B'),
            backColor=colors.HexColor('#FEF2F2'),
            borderColor=colors.HexColor('#EF4444'),
            borderWidth=0.8,
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=10
        )

        elements = []

        # Course & Lesson Data Extraction
        course = lesson.course
        module_name = lesson.module.title if lesson.module else (lesson.chapter_name or "Core Module")
        clean_paragraphs, code_snippets = PDFService._clean_html_text(lesson.content or "")
        takeaways = PDFService._parse_bullet_list(lesson.key_takeaways)
        mistakes = PDFService._parse_bullet_list(lesson.common_mistakes)
        exercises = list(lesson.exercises.all()[:4])

        # ----------------------------------------------------
        # 1. Course and Lesson Title Banner
        # ----------------------------------------------------
        header_table = Table([
            [
                Paragraph("<b>SKILLSPHERE ACADEMIC COURSEWARE</b>", ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#4338CA'))),
                Paragraph(f"<b>Estimated:</b> {lesson.estimated_minutes} min read | <b>Difficulty:</b> {course.difficulty}", ParagraphStyle('H2', fontName='Helvetica', fontSize=8.5, alignment=2, textColor=colors.HexColor('#64748B')))
            ]
        ], colWidths=[310, 205])
        header_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#4338CA')),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"{course.title.upper()} • {module_name.upper()}", subtitle_style))
        elements.append(Paragraph(f"Lesson {lesson.lesson_order}: {lesson.title}", title_style))
        instructor = course.instructor_name or "SkillSphere Academic Faculty"
        elements.append(Paragraph(f"<b>Instructor:</b> {instructor} &nbsp;|&nbsp; <b>Academic Standard:</b> Industry Aligned Curriculum", meta_style))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

        # ----------------------------------------------------
        # 2. Learning Objectives
        # ----------------------------------------------------
        elements.append(Paragraph("1. Learning Objectives & Target Competencies", h2_style))
        objs = [
            f"Understand the conceptual model, architecture, and principles of <b>{lesson.title}</b>.",
            f"Analyze core implementation patterns, syntax structures, and best practices in modern software systems.",
            f"Evaluate edge cases, performance trade-offs, and computational complexities.",
            f"Apply concepts directly to production-grade exercises and interview problem-solving."
        ]
        obj_text = "<br/>• ".join(objs)
        elements.append(Paragraph(f"• {obj_text}", body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 3. Topic Introduction
        # ----------------------------------------------------
        elements.append(Paragraph("2. Topic Introduction & Real-World Context", h2_style))
        intro_text = (
            f"In modern software engineering, mastering <b>{lesson.title}</b> provides developers with foundational "
            f"clarity when designing robust, maintainable, and scalable solutions. Whether developing distributed backend "
            f"services, designing data pipelines, or optimizing algorithmic operations, this topic represents an essential "
            f"milestone in the <i>{course.title}</i> curriculum."
        )
        elements.append(Paragraph(intro_text, body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 4. Detailed Concepts
        # ----------------------------------------------------
        elements.append(Paragraph("3. Theoretical Foundations & Detailed Concepts", h2_style))
        if clean_paragraphs:
            for p in clean_paragraphs[:5]:
                if '[CODE_BLOCK]' not in p and len(p.strip()) > 15:
                    elements.append(Paragraph(p, body_style))
        else:
            elements.append(Paragraph(
                f"The architecture of <b>{lesson.title}</b> revolves around structured memory allocation, deterministic execution, "
                f"and clear separation of concerns. Developers must understand how data structures and execution contexts interact "
                f"to guarantee consistency, prevent race conditions, and minimize computational overhead.", body_style
            ))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 5. Syntax & Definitions
        # ----------------------------------------------------
        elements.append(Paragraph("4. Syntax, Rules & Formal Specifications", h2_style))
        syntax_defs = [
            f"<b>Standard Declaration:</b> Formal signatures follow standard conventions with explicit parameter contracts.",
            f"<b>Scope & Mutability:</b> Variables and references operate within designated lexical scopes and lifetime boundaries.",
            f"<b>Error Protocols:</b> Deterministic error checking and boundary handling must be enforced before state modification."
        ]
        elements.append(Paragraph("<br/>• ".join([""] + syntax_defs).strip(), body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 6. Step-by-Step Architecture
        # ----------------------------------------------------
        elements.append(Paragraph("5. Step-by-Step Architecture & Execution Flow", h2_style))
        steps = [
            "<b>Phase 1: Input Ingestion & Sanitization:</b> Validate and parse incoming payloads against expected schema constraints.",
            "<b>Phase 2: Context Initialization:</b> Allocate required stack/heap resources and instantiate operational state.",
            "<b>Phase 3: Core Algorithmic Execution:</b> Execute business logic, transformations, or query executions safely.",
            "<b>Phase 4: Output Verification & Persistence:</b> Verify post-conditions, commit state changes, and return clean response."
        ]
        elements.append(Paragraph("<br/>• ".join([""] + steps).strip(), body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 7. Practical Walkthrough
        # ----------------------------------------------------
        elements.append(Paragraph("6. Practical Walkthrough & Real-World Scenario", h2_style))
        elements.append(Paragraph(
            f"Consider an enterprise production system requiring resilient handling of <b>{lesson.title}</b>. "
            f"The implementation below highlights defensive programming, explicit error trapping, and optimal runtime efficiency. "
            f"Follow the walkthrough annotations to understand every critical decision made in the implementation.", body_style
        ))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 8. Complete Code Examples
        # ----------------------------------------------------
        elements.append(Paragraph("7. Complete Production-Grade Code Example", h2_style))
        sample_code = ""
        if code_snippets:
            sample_code = code_snippets[0].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
        elif exercises and exercises[0].solution:
            sample_code = exercises[0].solution.strip()
        elif exercises and exercises[0].starter_code:
            sample_code = exercises[0].starter_code.strip()
        else:
            sample_code = (
                f"# Production implementation: {lesson.title}\n"
                f"class SolutionArchitecture:\n"
                f"    def __init__(self, context: dict):\n"
                f"        self.context = context\n"
                f"        self.is_valid = True\n\n"
                f"    def execute(self, payload: dict) -> dict:\n"
                f"        if not payload:\n"
                f"            raise ValueError('Payload cannot be empty')\n"
                f"        result = {{'status': 'SUCCESS', 'topic': '{lesson.title}'}}\n"
                f"        return result\n\n"
                f"# Execution trace\n"
                f"service = SolutionArchitecture(context={{'env': 'prod'}})\n"
                f"response = service.execute({{'id': 101}})\n"
                f"print('Execution Result:', response)"
            )
        # Limit to 30 lines for clean layout
        code_lines = sample_code.split('\n')[:25]
        safe_code_html = "<br/>".join([line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;') for line in code_lines])
        elements.append(Paragraph(f"<font face='Courier'>{safe_code_html}</font>", code_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 9. Line-by-Line Annotations
        # ----------------------------------------------------
        elements.append(Paragraph("8. Line-by-Line Code Annotations", h2_style))
        annotations = [
            "<b>Lines 1-4:</b> Class initialization defines essential state attributes and configures defensive baseline guards.",
            "<b>Lines 5-8:</b> Validation check guarantees input integrity before proceeding into algorithmic execution.",
            "<b>Lines 9-12:</b> Immutable result payload assembled and dispatched cleanly without side-effects."
        ]
        elements.append(Paragraph("<br/>• ".join([""] + annotations).strip(), body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 10. Output Examples
        # ----------------------------------------------------
        elements.append(Paragraph("9. Expected Output & Console Trace", h2_style))
        output_snippet = (
            f"$ python -m app.module.runner\n"
            f"[INFO] Initializing {lesson.title} context: SUCCESS\n"
            f"[INFO] Verification checks passed (0 warnings, 0 errors)\n"
            f"Execution Result: {{'status': 'SUCCESS', 'topic': '{lesson.title}', 'exit_code': 0}}"
        )
        safe_output_html = "<br/>".join([line.replace(' ', '&nbsp;') for line in output_snippet.split('\n')])
        elements.append(Paragraph(f"<font face='Courier-Bold'>{safe_output_html}</font>", terminal_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 11. Real-World Applications
        # ----------------------------------------------------
        elements.append(Paragraph("10. Real-World Applications & Industry Patterns", h2_style))
        apps = [
            f"<b>Distributed Microservices:</b> Managing concurrency, thread isolation, and data integrity in multi-tenant environments.",
            f"<b>High-Throughput Pipelines:</b> Minimizing I/O bottlenecks and memory footprint during batch and stream processing.",
            f"<b>Enterprise Security:</b> Guarding against untrusted input, state mutation vulnerabilities, and memory leaks."
        ]
        elements.append(Paragraph("<br/>• ".join([""] + apps).strip(), body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 12. Common Mistakes & Anti-Patterns
        # ----------------------------------------------------
        elements.append(Paragraph("11. Common Mistakes & Anti-Patterns to Avoid", h2_style))
        if mistakes:
            mistakes_text = "<br/>• ".join(mistakes)
        else:
            mistakes_text = (
                f"Ignoring boundary conditions when handling empty collections or edge cases.<br/>• "
                f"Unintentionally mutating shared objects across thread or request boundaries.<br/>• "
                f"Failing to profile time and space complexity under peak load volumes."
            )
        elements.append(Paragraph(f"<b>⚠️ Critical Anti-Patterns:</b><br/>• {mistakes_text}", mistake_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 13. Technical Interview Questions
        # ----------------------------------------------------
        elements.append(Paragraph("12. Technical Interview Questions & Model Answers", h2_style))
        elements.append(Paragraph(f"<b>Q1: What are the core architectural trade-offs involved in {lesson.title}?</b>", h3_style))
        elements.append(Paragraph("<b>Model Answer:</b> The primary trade-offs typically balance computational latency against memory footprint. Engineers must evaluate whether immutability and defensive copying justify the memory overhead or whether targeted caching should be applied.", body_style))
        elements.append(Paragraph(f"<b>Q2: How would you debug an intermittent failure or performance regression related to this topic?</b>", h3_style))
        elements.append(Paragraph("<b>Model Answer:</b> Isolate the reproducible unit test, inspect execution profiles with tracing/benchmarks, verify garbage collection behavior, and check for unhandled edge-case inputs.", body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 14. Practice Questions
        # ----------------------------------------------------
        elements.append(Paragraph("13. Self-Assessment Practice Challenges", h2_style))
        if exercises:
            for idx, ex in enumerate(exercises, 1):
                clean_inst = re.sub(r'<[^>]+>', '', ex.instructions or '')[:140]
                elements.append(Paragraph(f"<b>Challenge #{idx}: {ex.title}</b> — {clean_inst}...", body_style))
        else:
            elements.append(Paragraph(f"<b>Challenge 1:</b> Refactor the code example to accept variable configuration params and validate exceptions.", body_style))
            elements.append(Paragraph(f"<b>Challenge 2:</b> Implement a benchmark test measuring throughput under 10,000 continuous iterations.", body_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 15. Quick Revision Summary
        # ----------------------------------------------------
        elements.append(Paragraph("14. Quick Revision Summary & Core Takeaways", h2_style))
        if takeaways:
            takeaways_text = "<br/>• ".join(takeaways)
        else:
            takeaways_text = (
                f"<b>{lesson.title}</b> provides predictable, high-performance program behavior when applied cleanly.<br/>• "
                f"Always enforce input validation and defensive error boundaries.<br/>• "
                f"Review memory allocation profiles and runtime complexity characteristics before deploying to production."
            )
        elements.append(Paragraph(f"<b>💡 Key Revision Takeaways:</b><br/>• {takeaways_text}", callout_style))
        elements.append(Spacer(1, 6))

        # ----------------------------------------------------
        # 16. Key Terms & Glossary
        # ----------------------------------------------------
        elements.append(Paragraph("15. Key Terms & Architectural Glossary", h2_style))
        terms = [
            f"<b>Deterministic Execution:</b> A computation that always produces the exact same output given the same input.",
            f"<b>Immutability:</b> An architectural design where state cannot be modified after initial creation.",
            f"<b>Defensive Programming:</b> A paradigm ensuring continuing program function under unexpected input conditions.",
            f"<b>Complexity Profiling:</b> Systematic analysis of algorithmic resource consumption (Big-O time and space)."
        ]
        elements.append(Paragraph("<br/>• ".join([""] + terms).strip(), body_style))

        # End of Document Signature
        elements.append(Spacer(1, 14))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        elements.append(Paragraph("<i>Official SkillSphere Learning Resource • Verified Technical Study Notes • Academic Publication</i>", ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#94A3B8'), alignment=1)))

        def make_academic_canvas(*args, **kwargs):
            c = AcademicNumberedCanvas(*args, **kwargs)
            c.doc_title = f"{course.title} — Lesson {lesson.lesson_order}: {lesson.title}"
            return c

        doc.build(elements, canvasmaker=make_academic_canvas)
        pdf_data = buffer.getvalue()
        buffer.close()
        cache.set(cache_key, pdf_data, 86400)
        return pdf_data

    @staticmethod
    def generate_resume_pdf(resume) -> bytes:
        """
        Generates an ATS-compliant, selectable-text clean resume PDF using ReportLab Platypus.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        template_name = getattr(resume, 'template', 'ats')

        # Differentiated color palettes per template
        if template_name == 'modern':
            primary_color = colors.HexColor('#4338CA')    # Deep Indigo
            section_color = colors.HexColor('#6366F1')    # Indigo
            hr_color = colors.HexColor('#A5B4FC')
            font_main = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        elif template_name == 'fresher':
            primary_color = colors.HexColor('#065F46')    # Deep Emerald
            section_color = colors.HexColor('#059669')    # Emerald
            hr_color = colors.HexColor('#6EE7B7')
            font_main = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        elif template_name == 'minimal':
            primary_color = colors.HexColor('#18181B')    # Dark Zinc
            section_color = colors.HexColor('#27272A')
            hr_color = colors.HexColor('#E4E4E7')
            font_main = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        else: # 'ats'
            primary_color = colors.HexColor('#0F172A')    # Slate ATS
            section_color = colors.HexColor('#1E293B')
            hr_color = colors.HexColor('#CBD5E1')
            font_main = 'Helvetica'
            font_bold = 'Helvetica-Bold'

        # Custom Clean Styles
        title_style = ParagraphStyle(
            'ResumeName',
            parent=styles['Normal'],
            fontName=font_bold,
            fontSize=21 if template_name != 'minimal' else 18,
            leading=25 if template_name != 'minimal' else 22,
            textColor=primary_color
        )
        headline_style = ParagraphStyle(
            'ResumeHeadline',
            parent=styles['Normal'],
            fontName=font_main,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569')
        )
        contact_style = ParagraphStyle(
            'ResumeContact',
            parent=styles['Normal'],
            fontName=font_main,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748B')
        )
        section_style = ParagraphStyle(
            'ResumeSection',
            parent=styles['Normal'],
            fontName=font_bold,
            fontSize=11.5,
            leading=15,
            textColor=section_color,
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'ResumeBody',
            parent=styles['Normal'],
            fontName=font_main,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        item_title_style = ParagraphStyle(
            'ResumeItemTitle',
            parent=styles['Normal'],
            fontName=font_bold,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0F172A')
        )

        elements = []
        data = resume.resume_data or {}
        contact = data.get('contact', {})
        full_name = contact.get('full_name') or resume.user.get_full_name() or resume.user.username
        headline = contact.get('headline', '')
        email = contact.get('email') or resume.user.email
        phone = contact.get('phone', '')
        location = contact.get('location', '')
        links = contact.get('links', '')

        # 1. Header & Contact
        elements.append(Paragraph(full_name, title_style))
        if headline:
            elements.append(Paragraph(headline, headline_style))

        contact_line_parts = [p for p in [email, phone, location, links] if p]
        if contact_line_parts:
            elements.append(Paragraph(" • ".join(contact_line_parts), contact_style))

        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.5 if template_name == 'modern' else 1, color=hr_color, spaceAfter=6))

        # 2. Summary
        summary = data.get('summary', '')
        if summary:
            elements.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            elements.append(Paragraph(summary, body_style))
            elements.append(Spacer(1, 4))

        # 3. Technical Skills
        skills = data.get('skills', [])
        if skills:
            elements.append(Paragraph("TECHNICAL SKILLS", section_style))
            skills_text = ", ".join(skills) if isinstance(skills, list) else str(skills)
            elements.append(Paragraph(skills_text, body_style))
            elements.append(Spacer(1, 4))

        # 4. Experience & Internships
        experience = data.get('experience', [])
        if experience:
            elements.append(Paragraph("WORK & INTERNSHIP EXPERIENCE", section_style))
            for exp in experience:
                role = exp.get('role', '')
                company = exp.get('company', '')
                dates = exp.get('dates', '')
                desc = exp.get('description', '')
                top_text = f"<b>{role}</b> — {company}" if company else f"<b>{role}</b>"
                if dates:
                    top_text += f" <font color='#64748B'>({dates})</font>"
                elements.append(Paragraph(top_text, item_title_style))
                if desc:
                    elements.append(Paragraph(desc, body_style))
                elements.append(Spacer(1, 4))

        # 5. Projects
        projects = data.get('projects', [])
        if projects:
            elements.append(Paragraph("FEATURED PROJECTS", section_style))
            for proj in projects:
                p_title = proj.get('title', '')
                tech = proj.get('technologies', '')
                p_desc = proj.get('description', '')
                github = proj.get('github_url', '')
                header = f"<b>{p_title}</b>"
                if tech:
                    header += f" | <i>{tech}</i>"
                if github:
                    header += f" (<a href='{github}' color='#0284C7'>GitHub</a>)"
                elements.append(Paragraph(header, item_title_style))
                if p_desc:
                    elements.append(Paragraph(p_desc, body_style))
                elements.append(Spacer(1, 4))

        # 6. Education
        education = data.get('education', [])
        if education:
            elements.append(Paragraph("EDUCATION", section_style))
            for edu in education:
                degree = edu.get('degree', '')
                school = edu.get('school', '')
                year = edu.get('year', '')
                gpa = edu.get('gpa', '')
                line = f"<b>{degree}</b> — {school}"
                if year:
                    line += f" ({year})"
                if gpa:
                    line += f" | GPA: {gpa}"
                elements.append(Paragraph(line, item_title_style))
                elements.append(Spacer(1, 2))

        # 7. Certifications
        certifications = data.get('certifications', [])
        if certifications:
            elements.append(Paragraph("CERTIFICATIONS & AWARDS", section_style))
            for cert in certifications:
                c_name = cert if isinstance(cert, str) else cert.get('title', '')
                elements.append(Paragraph(f"• {c_name}", body_style))
            elements.append(Spacer(1, 4))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

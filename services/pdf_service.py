import io
import os
import re
import math
import textwrap
from django.conf import settings
from django.core.cache import cache
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm


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

    _cert_fonts_registered = False

    @classmethod
    def _register_certificate_fonts(cls):
        if cls._cert_fonts_registered:
            return
        font_dir = os.path.join(settings.BASE_DIR, "static", "fonts")
        font_map = {
            "Playfair": "PlayfairDisplay-Bold.ttf",
            "Montserrat-Bold": "Montserrat-Bold.ttf",
            "Montserrat-SemiBold": "Montserrat-SemiBold.ttf",
            "Lato": "Lato-Regular.ttf",
        }
        for font_name, filename in font_map.items():
            font_path = os.path.join(font_dir, filename)
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception:
                    pass
        cls._cert_fonts_registered = True

    @classmethod
    def _get_font(cls, preferred, fallback="Helvetica"):
        cls._register_certificate_fonts()
        try:
            pdfmetrics.getFont(preferred)
            return preferred
        except KeyError:
            return fallback

    @staticmethod
    def generate_certificate_pdf(certificate) -> bytes:
        """
        Generates an authentic, high-resolution landscape A4 vector certificate PDF
        implementing the approved SkillSphere premium light-blue academic design:
        - Main background: Very light blue (#EAF4FF)
        - Inner certificate surface: White (#FFFFFF)
        - Primary blue: Royal blue (#2457A7)
        - Secondary blue: Soft blue (#6D9FE8)
        - Dark navy text: Deep navy (#142B4D)
        - Body text: Slate (#425466)
        - Muted text: Grey blue (#64748B)
        - Border: Light blue (#B9D4F2)
        - Watermark: Pale ice blue (#DCEBFA)
        - Gold accent: Soft gold (#C7A45A)
        """
        cache_key = f"cert_pdf_spec_v5_{getattr(certificate, 'certificate_id', certificate.pk)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        PDFService._register_certificate_fonts()

        buffer = io.BytesIO()
        width, height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4), pageCompression=1)

        COLORS = {
            "background": colors.HexColor("#EAF4FF"),
            "white": colors.HexColor("#FFFFFF"),
            "primary": colors.HexColor("#2457A7"),
            "secondary": colors.HexColor("#6D9FE8"),
            "navy": colors.HexColor("#142B4D"),
            "body": colors.HexColor("#425466"),
            "muted": colors.HexColor("#64748B"),
            "border": colors.HexColor("#B9D4F2"),
            "watermark": colors.HexColor("#DCEBFA"),
            "gold": colors.HexColor("#C7A45A"),
        }

        # 1. Main Background: #EAF4FF
        c.setFillColor(COLORS["background"])
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # 2. White Certificate Surface (Inner surface)
        c.setFillColor(COLORS["white"])
        c.roundRect(
            19 * mm, 19 * mm,
            width - 38 * mm,
            height - 38 * mm,
            5,
            fill=True,
            stroke=False
        )

        # 3. Watermark behind text
        c.saveState()
        center_x = width / 2.0
        center_y = height / 2.0 - 5 * mm

        # Concentric subtle circles
        c.setStrokeColor(colors.HexColor("#E2EFFC"))
        c.setLineWidth(1)
        c.circle(center_x, center_y, 50 * mm, stroke=True, fill=False)
        c.circle(center_x, center_y, 45 * mm, stroke=True, fill=False)

        # Watermark disk
        c.setFillColor(COLORS["watermark"])
        c.circle(center_x, center_y, 42 * mm, stroke=False, fill=True)

        c.setFillColor(COLORS["white"])
        c.circle(center_x, center_y, 33 * mm, stroke=False, fill=True)

        # Stylized S in center
        playfair_font = PDFService._get_font("Playfair", "Times-Bold")
        c.setFillColor(COLORS["watermark"])
        c.setFont(playfair_font, 92)
        c.drawCentredString(center_x, center_y - 30, "S")
        c.restoreState()

        # 4. Borders
        # Outer Border (light blue #B9D4F2)
        c.setStrokeColor(COLORS["border"])
        c.setLineWidth(2.0)
        c.roundRect(
            12 * mm, 12 * mm,
            width - 24 * mm,
            height - 24 * mm,
            8,
            stroke=True,
            fill=False
        )

        # Inner Border (soft blue #6D9FE8)
        c.setStrokeColor(COLORS["secondary"])
        c.setLineWidth(0.8)
        c.roundRect(
            17 * mm, 17 * mm,
            width - 34 * mm,
            height - 34 * mm,
            5,
            stroke=True,
            fill=False
        )

        # Elegant Corner Ornaments (strictly inside the inner border)
        c.saveState()
        c.setStrokeColor(COLORS["secondary"])
        c.setLineWidth(0.8)
        bracket_len = 6 * mm
        offset = 2.5 * mm

        for (bx, by, dx, dy) in [
            (17 * mm + offset, 17 * mm + offset, 1, 1),
            (width - 17 * mm - offset, 17 * mm + offset, -1, 1),
            (17 * mm + offset, height - 17 * mm - offset, 1, -1),
            (width - 17 * mm - offset, height - 17 * mm - offset, -1, -1),
        ]:
            c.line(bx, by, bx + dx * bracket_len, by)
            c.line(bx, by, bx, by + dy * bracket_len)
            c.setFillColor(COLORS["gold"])
            c.circle(bx, by, 1.3, fill=True, stroke=False)
        c.restoreState()

        # Helper for dividers with gold diamonds
        def draw_divider(y_pos, length_mm):
            half = (length_mm * mm) / 2.0
            cx = width / 2.0
            c.saveState()
            c.setStrokeColor(COLORS["border"])
            c.setLineWidth(0.8)
            c.line(cx - half, y_pos, cx + half, y_pos)

            # Gold center diamond
            c.setFillColor(COLORS["gold"])
            p = c.beginPath()
            p.moveTo(cx, y_pos + 2.5)
            p.lineTo(cx + 3.0, y_pos)
            p.lineTo(cx, y_pos - 2.5)
            p.lineTo(cx - 3.0, y_pos)
            p.close()
            c.drawPath(p, fill=True, stroke=False)
            c.restoreState()

        # Fonts
        montserrat_bold = PDFService._get_font("Montserrat-Bold", "Helvetica-Bold")
        montserrat_semibold = PDFService._get_font("Montserrat-SemiBold", montserrat_bold)
        lato_font = PDFService._get_font("Lato", "Helvetica")

        # 5. SkillSphere Branding
        c.setFont(montserrat_bold, 23)
        c.setFillColor(COLORS["primary"])
        c.drawCentredString(width / 2.0, height - 38 * mm, "SkillSphere")

        c.setFont(lato_font, 8)
        c.setFillColor(COLORS["muted"])
        c.drawCentredString(width / 2.0, height - 44.5 * mm, "LEARN SKILLS. BUILD PROJECTS. TRACK YOUR GROWTH.")

        # Top Divider
        draw_divider(height - 50 * mm, 90)

        # 6. Heading: CERTIFICATE OF COMPLETION
        c.setFont(playfair_font, 27)
        c.setFillColor(COLORS["primary"])
        c.drawCentredString(width / 2.0, height - 64 * mm, "CERTIFICATE OF COMPLETION")

        # 7. Introductory text
        c.setFont(lato_font, 11)
        c.setFillColor(COLORS["body"])
        c.drawCentredString(width / 2.0, height - 77 * mm, "This certificate is proudly presented to")

        # 8. Recipient Name (Playfair Bold 31 pt, dynamic auto-scaling/wrapping)
        recipient = (certificate.recipient_name or certificate.user.get_full_name() or certificate.user.username).strip()
        name_len = len(recipient)
        if name_len <= 26:
            c.setFont(playfair_font, 31)
            c.setFillColor(COLORS["navy"])
            c.drawCentredString(width / 2.0, height - 92 * mm, recipient)
        elif name_len <= 40:
            c.setFont(playfair_font, 24)
            c.setFillColor(COLORS["navy"])
            c.drawCentredString(width / 2.0, height - 92 * mm, recipient)
        elif name_len <= 54:
            c.setFont(playfair_font, 19)
            c.setFillColor(COLORS["navy"])
            c.drawCentredString(width / 2.0, height - 92 * mm, recipient)
        else:
            name_lines = textwrap.wrap(recipient, width=42)
            c.setFont(playfair_font, 18)
            c.setFillColor(COLORS["navy"])
            c.drawCentredString(width / 2.0, height - 90 * mm, name_lines[0])
            if len(name_lines) > 1:
                c.drawCentredString(width / 2.0, height - 96 * mm, name_lines[1])

        # 9. Completion statement
        c.setFont(lato_font, 10)
        c.setFillColor(COLORS["body"])
        c.drawCentredString(width / 2.0, height - 105 * mm, "for successfully completing")

        # 10. Course Title (Montserrat SemiBold 19 pt, dynamic auto-scaling/wrapping)
        course_title = (certificate.course.title if certificate.course else certificate.title).strip()
        c_len = len(course_title)
        if c_len <= 38:
            c.setFont(montserrat_semibold, 19)
            c.setFillColor(COLORS["primary"])
            c.drawCentredString(width / 2.0, height - 118 * mm, course_title)
        elif c_len <= 58:
            c.setFont(montserrat_semibold, 16)
            c.setFillColor(COLORS["primary"])
            c.drawCentredString(width / 2.0, height - 118 * mm, course_title)
        else:
            lines = textwrap.wrap(course_title, width=52)
            c.setFont(montserrat_semibold, 14)
            c.setFillColor(COLORS["primary"])
            c.drawCentredString(width / 2.0, height - 116 * mm, lines[0])
            if len(lines) > 1:
                c.drawCentredString(width / 2.0, height - 122 * mm, lines[1])

        # 11. Description
        c.setFont(lato_font, 9.5)
        c.setFillColor(COLORS["body"])
        c.drawCentredString(
            width / 2.0,
            height - 132 * mm,
            "Demonstrating dedication to learning, skill development and professional growth."
        )

        # Bottom Divider
        draw_divider(height - 141 * mm, 170)

        # 12. Bottom Left: Date & Certificate ID
        completion_date = certificate.issued_at.strftime('%B %d, %Y')
        cert_id = certificate.certificate_id
        c.setFont(lato_font, 8)
        c.setFillColor(COLORS["muted"])
        c.drawString(28 * mm, 36 * mm, f"Completion Date: {completion_date}")
        c.drawString(28 * mm, 30 * mm, f"Certificate ID: {cert_id}")

        # 13. Bottom Center: QR Code
        verify_url = f"https://skillsphere-cyan.vercel.app/certificates/verify/{certificate.certificate_id}/"
        qr_size = 25 * mm
        qr_x = (width - qr_size) / 2.0
        qr_y = 25 * mm

        qr_widget = QrCodeWidget(verify_url)
        qr_widget.barFillColor = COLORS["navy"]
        bounds = qr_widget.getBounds()
        qw = bounds[2] - bounds[0]
        qh = bounds[3] - bounds[1]

        # White quiet zone
        c.saveState()
        c.setFillColor(COLORS["white"])
        c.rect(qr_x - 1.5 * mm, qr_y - 1.5 * mm, qr_size + 3 * mm, qr_size + 3 * mm, fill=True, stroke=False)

        d = Drawing(qr_size, qr_size, transform=[qr_size / qw, 0, 0, qr_size / qh, 0, 0])
        d.add(qr_widget)
        renderPDF.draw(d, c, qr_x, qr_y)
        c.restoreState()

        c.setFont(lato_font, 7)
        c.setFillColor(COLORS["muted"])
        c.drawCentredString(width / 2.0, 21 * mm, "SCAN TO VERIFY")

        # 14. Bottom Right: Authorized Signature Area
        sig_line_start = width - 85 * mm
        sig_line_end = width - 30 * mm
        sig_line_y = 36 * mm

        c.saveState()
        c.setStrokeColor(COLORS["border"])
        c.setLineWidth(1)
        c.line(sig_line_start, sig_line_y, sig_line_end, sig_line_y)

        # Elegant stylized signature path
        c.setStrokeColor(COLORS["navy"])
        c.setLineWidth(1.2)
        sig_center_x = (sig_line_start + sig_line_end) / 2.0
        p = c.beginPath()
        p.moveTo(sig_center_x - 22, sig_line_y + 8)
        p.curveTo(sig_center_x - 12, sig_line_y + 17, sig_center_x + 4, sig_line_y + 4, sig_center_x + 18, sig_line_y + 13)
        p.curveTo(sig_center_x + 2, sig_line_y + 3, sig_center_x - 14, sig_line_y + 15, sig_center_x + 24, sig_line_y + 8)
        c.drawPath(p, fill=False, stroke=True)
        c.restoreState()

        c.setFont(lato_font, 8)
        c.setFillColor(COLORS["muted"])
        c.drawCentredString((sig_line_start + sig_line_end) / 2.0, 30 * mm, "Authorized Signature")

        c.showPage()
        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        cache.set(cache_key, pdf_data, 86400)
        return pdf_data


    @staticmethod
    def generate_lesson_notes_pdf(lesson) -> bytes:
        """
        Generates an authentic, multi-page comprehensive academic PDF study guide (5 to 12 pages)
        using AcademicNumberedCanvas for two-pass running headers ('Page X of Y')
        and publication-grade academic typography.
        """
        cache_key = f"lesson_notes_pdf_v3_{lesson.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        from services.academic_notes_content import SPECIALIZED_ACADEMIC_LESSONS

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
            fontSize=17,
            leading=21,
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
            spaceAfter=6,
            keepWithNext=True
        )
        meta_style = ParagraphStyle(
            'AcademicMeta',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=10
        )
        h2_style = ParagraphStyle(
            'AcademicH2',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14.5,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True
        )
        h3_style = ParagraphStyle(
            'AcademicH3',
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12.5,
            textColor=colors.HexColor('#334155'),
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'AcademicBody',
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=5
        )
        code_style = ParagraphStyle(
            'AcademicCode',
            fontName='Courier',
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor('#0F172A'),
            backColor=colors.HexColor('#F8FAFC'),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6
        )
        terminal_style = ParagraphStyle(
            'AcademicTerminal',
            fontName='Courier-Bold',
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor('#38BDF8'),
            backColor=colors.HexColor('#0F172A'),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6
        )
        callout_style = ParagraphStyle(
            'AcademicCallout',
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#1E293B'),
            backColor=colors.HexColor('#EEF2FF'),
            borderColor=colors.HexColor('#6366F1'),
            borderWidth=0.8,
            borderPadding=6,
            spaceBefore=5,
            spaceAfter=8
        )
        mistake_style = ParagraphStyle(
            'AcademicMistake',
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#991B1B'),
            backColor=colors.HexColor('#FEF2F2'),
            borderColor=colors.HexColor('#EF4444'),
            borderWidth=0.8,
            borderPadding=6,
            spaceBefore=5,
            spaceAfter=8
        )
        th_style = ParagraphStyle(
            'TH',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor('#FFFFFF')
        )
        td_style = ParagraphStyle(
            'TD',
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        td_code = ParagraphStyle(
            'TDCode',
            fontName='Courier',
            fontSize=7,
            leading=9.5,
            textColor=colors.HexColor('#0F172A')
        )

        elements = []
        course = lesson.course
        module_name = lesson.module.title if lesson.module else (lesson.chapter_name or "Core Module")
        normalized_title = lesson.title.lower()

        # Check for specialized curriculum data
        spec_data = None
        if 'control-flow' in normalized_title or 'if-else' in normalized_title or 'control flow' in normalized_title:
            spec_data = SPECIALIZED_ACADEMIC_LESSONS.get('control-flow-if-else-loops')

        if spec_data:
            data = spec_data
            # Banner
            banner_data = [
                [
                    Paragraph('<b>SKILLSPHERE ACADEMIC COURSEWARE</b>', ParagraphStyle('BH1', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#4338CA'))),
                    Paragraph(f'<b>Estimated:</b> {data["estimated_minutes"]} min read | <b>Difficulty:</b> {data["difficulty"]}', ParagraphStyle('BH2', fontName='Helvetica', fontSize=8, alignment=2, textColor=colors.HexColor('#64748B')))
                ]
            ]
            t_banner = Table(banner_data, colWidths=[310, 205])
            t_banner.setStyle(TableStyle([
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#4338CA')),
            ]))
            elements.append(t_banner)
            elements.append(Spacer(1, 8))

            elements.append(Paragraph(f'{course.title.upper()} • {module_name.upper()}', subtitle_style))
            elements.append(Paragraph(f'Lesson {lesson.lesson_order}: {lesson.title}', title_style))
            instructor = course.instructor_name or data["instructor"]
            elements.append(Paragraph(f'<b>Instructor:</b> {instructor} &nbsp;|&nbsp; <b>Academic Standard:</b> {data["academic_standard"]}', meta_style))
            elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

            # 1. Executive Summary & Competency Matrix
            elements.append(Paragraph('1. Curriculum Overview & Competency Matrix', h2_style))
            elements.append(Paragraph(data['executive_summary'], body_style))
            elements.append(Spacer(1, 4))

            c_table_rows = []
            for idx, row in enumerate(data['competency_matrix']):
                if idx == 0:
                    c_table_rows.append([Paragraph(f'<b>{c}</b>', th_style) for c in row])
                else:
                    c_table_rows.append([
                        Paragraph(f'<b>{row[0]}</b>', td_style),
                        Paragraph(row[1], td_style),
                        Paragraph(row[2], td_style),
                        Paragraph(row[3], td_style)
                    ])
            t_comp = Table(c_table_rows, colWidths=[120, 100, 115, 180])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_comp)
            elements.append(Spacer(1, 8))

            # 2. Learning Objectives
            elements.append(Paragraph('2. Learning Objectives & Pedagogical Target Competencies', h2_style))
            objs_text = '<br/>• '.join([''] + data['learning_objectives']).strip()
            elements.append(Paragraph(objs_text, body_style))
            elements.append(Spacer(1, 6))

            # 3. Theoretical Foundations
            elements.append(Paragraph('3. Theoretical Foundations & Execution Models', h2_style))
            for tf in data['theoretical_foundations']:
                elements.append(Paragraph(tf, body_style))
                elements.append(Spacer(1, 3))
            elements.append(Spacer(1, 6))

            # 4. Syntax & Specifications
            elements.append(Paragraph('4. Formal Syntax & Construct Specifications', h2_style))
            s_table_rows = []
            for idx, row in enumerate(data['syntax_specifications']):
                if idx == 0:
                    s_table_rows.append([Paragraph(f'<b>{c}</b>', th_style) for c in row])
                else:
                    s_table_rows.append([
                        Paragraph(f'<b>{row[0]}</b>', td_style),
                        Paragraph(row[1].replace('\n', '<br/>').replace(' ', '&nbsp;'), td_code),
                        Paragraph(row[2], td_style),
                        Paragraph(row[3], td_style)
                    ])
            t_syntax = Table(s_table_rows, colWidths=[80, 140, 175, 120])
            t_syntax.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_syntax)
            elements.append(Spacer(1, 8))

            # 5. Boolean Logic Truth Matrix
            elements.append(Paragraph('5. Boolean Logic Truth Matrix & Short-Circuit Evaluation', h2_style))
            tt = data['truth_tables']
            tt_rows = [[Paragraph(f'<b>{h}</b>', th_style) for h in tt['headers']]]
            for r in tt['rows']:
                tt_rows.append([
                    Paragraph(r[0], td_style),
                    Paragraph(r[1], td_style),
                    Paragraph(f'<b>{r[2]}</b>', td_style),
                    Paragraph(f'<b>{r[3]}</b>', td_style),
                    Paragraph(f'<b>{r[4]}</b>', td_style)
                ])
            t_tt = Table(tt_rows, colWidths=[130, 130, 85, 85, 85])
            t_tt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_tt)
            elements.append(Spacer(1, 6))

            sc_rows = [[Paragraph(f'<b>{c}</b>', th_style) for c in tt['short_circuit_rules'][0]]]
            for r in tt['short_circuit_rules'][1:]:
                sc_rows.append([
                    Paragraph(f'<b>{r[0]}</b>', td_code),
                    Paragraph(r[1], td_style),
                    Paragraph(r[2], td_style),
                    Paragraph(r[3], td_style)
                ])
            t_sc = Table(sc_rows, colWidths=[80, 160, 120, 155])
            t_sc.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_sc)
            elements.append(Spacer(1, 8))

            # 6. Flowcharts
            elements.append(Paragraph('6. Execution Flow Architecture & Control Diagrams', h2_style))
            for fc in data['execution_flowcharts']:
                elements.append(Paragraph(f'<b>{fc["title"]}</b>', h3_style))
                fc_clean = fc['diagram'].replace(' ', '&nbsp;').replace('\n', '<br/>')
                elements.append(Paragraph(f'<font face="Courier">{fc_clean}</font>', code_style))
                elements.append(Spacer(1, 4))
            elements.append(Spacer(1, 6))

            # 7. Code Examples
            elements.append(Paragraph('7. Production Implementations, Annotations & Console Traces', h2_style))
            for ce in data['code_examples']:
                elements.append(Paragraph(f'<b>{ce["title"]}</b>', h3_style))
                elements.append(Paragraph(ce['description'], body_style))
                code_clean = ce['code'].replace(' ', '&nbsp;').replace('\n', '<br/>')
                elements.append(Paragraph(f'<font face="Courier">{code_clean}</font>', code_style))

                ann_rows = [[Paragraph(f'<b>{c}</b>', th_style) for c in ce['annotations'][0]]]
                for an in ce['annotations'][1:]:
                    ann_rows.append([
                        Paragraph(f'<b>{an[0]}</b>', td_style),
                        Paragraph(an[1], td_code),
                        Paragraph(an[2], td_style),
                        Paragraph(an[3], td_style)
                    ])
                t_ann = Table(ann_rows, colWidths=[70, 135, 145, 165])
                t_ann.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_ann)
                elements.append(Spacer(1, 4))

                out_clean = ce['console_output'].replace(' ', '&nbsp;').replace('\n', '<br/>')
                elements.append(Paragraph(f'<font face="Courier-Bold">{out_clean}</font>', terminal_style))
                elements.append(Spacer(1, 8))

            # 8. Architectural Comparisons
            elements.append(Paragraph('8. Architectural Comparisons & Decision Matrices', h2_style))
            for comp in data['comparisons']:
                elements.append(Paragraph(f'<b>{comp["title"]}</b>', h3_style))
                comp_rows = [[Paragraph(f'<b>{h}</b>', th_style) for h in comp['headers']]]
                for cr in comp['rows']:
                    comp_rows.append([Paragraph(f'<b>{cr[0]}</b>', td_style)] + [Paragraph(c, td_style) for c in cr[1:]])
                t_cmp = Table(comp_rows, colWidths=[95, 95, 95, 80, 150])
                t_cmp.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_cmp)
                elements.append(Spacer(1, 8))

            # 9. Common Pitfalls
            elements.append(Paragraph('9. Common Pitfalls, Anti-Patterns & Defensive Debugging', h2_style))
            for pitfall in data['common_pitfalls']:
                elements.append(Paragraph(f'<b>⚠️ {pitfall[0]}</b>', h3_style))
                elements.append(Paragraph(pitfall[1], body_style))
                bad_code = pitfall[2].replace(' ', '&nbsp;').replace('\n', '<br/>')
                good_code = pitfall[3].replace(' ', '&nbsp;').replace('\n', '<br/>')
                elements.append(Paragraph(f'<b>Broken Anti-Pattern:</b><br/><font face="Courier">{bad_code}</font>', mistake_style))
                elements.append(Paragraph(f'<b>Idiomatic Resolution:</b><br/><font face="Courier">{good_code}</font>', callout_style))
                elements.append(Spacer(1, 4))

            # 10. Technical Interview Masterclass
            elements.append(Paragraph('10. Technical Interview Questions & Model Answers', h2_style))
            for iqa in data['interview_qa']:
                elements.append(Paragraph(f'<b>{iqa["q"]}</b>', h3_style))
                elements.append(Paragraph(f'<i>Interviewer Evaluation Criteria:</i> {iqa["eval_criteria"]}', meta_style))
                elements.append(Paragraph(f'<b>Model Answer:</b><br/>{iqa["answer"]}', body_style))
                elements.append(Spacer(1, 6))

            # 11. Practice Challenges
            elements.append(Paragraph('11. Graded Practice Challenges & Problem Sets', h2_style))
            for pc in data['practice_challenges']:
                elements.append(Paragraph(f'<b>{pc["level"]}: {pc["title"]}</b>', h3_style))
                elements.append(Paragraph(pc['description'], body_style))
                sc_clean = pc['starter_code'].replace(' ', '&nbsp;').replace('\n', '<br/>')
                elements.append(Paragraph(f'<font face="Courier">{sc_clean}</font>', code_style))
                elements.append(Spacer(1, 4))

            # 12. Quick Revision Cheat Sheet
            elements.append(Paragraph('12. Quick Revision Summary & Architectural Cheat Sheet', h2_style))
            cs_rows = [[Paragraph(f'<b>{c}</b>', th_style) for c in data['cheat_sheet'][0]]]
            for csr in data['cheat_sheet'][1:]:
                cs_rows.append([
                    Paragraph(f'<b>{csr[0]}</b>', td_style),
                    Paragraph(csr[1], td_code),
                    Paragraph(csr[2], td_style),
                    Paragraph(csr[3], td_style)
                ])
            t_cs = Table(cs_rows, colWidths=[70, 120, 160, 165])
            t_cs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_cs)
            elements.append(Spacer(1, 8))

            # 13. References
            elements.append(Paragraph('13. Academic Bibliography & Formal References', h2_style))
            for ref in data['references']:
                elements.append(Paragraph(f'• <b>{ref[0]}:</b> <i>{ref[1]}</i> — {ref[2]}', body_style))

        else:
            # Domain-Aware Comprehensive Generator for All Other Lessons (5 to 8 Pages)
            clean_paragraphs, code_snippets = PDFService._clean_html_text(lesson.content or "")
            takeaways = PDFService._parse_bullet_list(lesson.key_takeaways)
            mistakes = PDFService._parse_bullet_list(lesson.common_mistakes)
            exercises = list(lesson.exercises.all()[:4])

            # Header Banner
            banner_data = [
                [
                    Paragraph('<b>SKILLSPHERE ACADEMIC COURSEWARE</b>', ParagraphStyle('BH1', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#4338CA'))),
                    Paragraph(f'<b>Estimated:</b> {lesson.estimated_minutes} min read | <b>Difficulty:</b> {course.difficulty}', ParagraphStyle('BH2', fontName='Helvetica', fontSize=8, alignment=2, textColor=colors.HexColor('#64748B')))
                ]
            ]
            t_banner = Table(banner_data, colWidths=[310, 205])
            t_banner.setStyle(TableStyle([
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#4338CA')),
            ]))
            elements.append(t_banner)
            elements.append(Spacer(1, 8))

            elements.append(Paragraph(f'{course.title.upper()} • {module_name.upper()}', subtitle_style))
            elements.append(Paragraph(f'Lesson {lesson.lesson_order}: {lesson.title}', title_style))
            instructor = course.instructor_name or "SkillSphere Academic Faculty"
            elements.append(Paragraph(f'<b>Instructor:</b> {instructor} &nbsp;|&nbsp; <b>Academic Standard:</b> Industry Aligned Curriculum', meta_style))
            elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

            # 1. Executive Summary & Competency Matrix
            elements.append(Paragraph('1. Curriculum Overview & Competency Matrix', h2_style))
            elements.append(Paragraph(
                f"This academic study guide provides in-depth technical analysis of <b>{lesson.title}</b> within the "
                f"<b>{course.title}</b> curriculum. It synthesizes core theoretical foundations, runtime characteristics, "
                f"production design patterns, and defensive implementation standards necessary for enterprise engineering.",
                body_style
            ))
            elements.append(Spacer(1, 4))

            c_matrix = [
                [Paragraph('<b>Competency Domain</b>', th_style), Paragraph('<b>Cognitive Level</b>', th_style), Paragraph('<b>Prerequisite Knowledge</b>', th_style), Paragraph('<b>Mastery Target</b>', th_style)],
                [Paragraph(f'<b>{lesson.title} Core Architecture</b>', td_style), Paragraph('Understanding & Analysis', td_style), Paragraph('Foundation Concepts', td_style), Paragraph('Master internal mechanics and execution semantics.', td_style)],
                [Paragraph('Production Implementation', td_style), Paragraph('Application & Synthesis', td_style), Paragraph('Syntax & Data Structures', td_style), Paragraph('Write deterministic, defensively guarded code.', td_style)],
                [Paragraph('Error Handling & Optimization', td_style), Paragraph('Evaluation', td_style), Paragraph('Runtime Profiling', td_style), Paragraph('Identify edge cases, mitigate pitfalls, and ensure scalability.', td_style)],
                [Paragraph('System Design Integration', td_style), Paragraph('Creation', td_style), Paragraph('API & Module Design', td_style), Paragraph('Integrate cleanly into enterprise-scale architectures.', td_style)]
            ]
            t_comp = Table(c_matrix, colWidths=[120, 100, 115, 180])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_comp)
            elements.append(Spacer(1, 8))

            # 2. Learning Objectives
            elements.append(Paragraph('2. Learning Objectives & Pedagogical Target Competencies', h2_style))
            objs = [
                f"Deconstruct the architecture, memory model, and operational semantics of <b>{lesson.title}</b>.",
                f"Apply idiomatic syntax patterns, type safety constraints, and interface contracts to production systems.",
                f"Evaluate algorithmic complexity, memory allocation trade-offs, and latency implications under peak workloads.",
                f"Diagnose anti-patterns, boundary edge cases, and concurrency risks associated with this domain.",
                f"Synthesize comprehensive unit, integration, and property-based test suites to guarantee correctness."
            ]
            elements.append(Paragraph('<br/>• '.join([''] + objs).strip(), body_style))
            elements.append(Spacer(1, 6))

            # 3. Theoretical Foundations
            elements.append(Paragraph('3. Theoretical Foundations & Detailed Concepts', h2_style))
            if clean_paragraphs:
                for p in clean_paragraphs:
                    if '[CODE_BLOCK]' not in p and len(p.strip()) > 15:
                        elements.append(Paragraph(p, body_style))
            else:
                elements.append(Paragraph(
                    f"The architectural design of <b>{lesson.title}</b> is grounded in structured program decomposition, "
                    f"deterministic state transformation, and explicit invariant enforcement. In production environments, "
                    f"understanding the underlying execution lifecycle enables engineers to avoid resource contention, "
                    f"optimize throughput, and build maintainable software components.",
                    body_style
                ))
            elements.append(Spacer(1, 6))

            # 4. Formal Syntax & Specifications Table
            elements.append(Paragraph('4. Formal Syntax & Structural Specifications', h2_style))
            spec_rows = [
                [Paragraph('<b>Construct / Component</b>', th_style), Paragraph('<b>Signature / Pattern</b>', th_style), Paragraph('<b>Operational Semantics</b>', th_style), Paragraph('<b>Complexity Profile</b>', th_style)],
                [Paragraph('Primary Interface', td_style), Paragraph(f'def execute_{lesson.id}(*args, **kwargs) -> Any', td_code), Paragraph('Defines the entry point and execution contract.', td_style), Paragraph('O(1) dispatch overhead', td_style)],
                [Paragraph('State Encapsulation', td_style), Paragraph('class StateContext: ...', td_code), Paragraph('Isolates mutable state within scoped boundaries.', td_style), Paragraph('O(1) memory allocation', td_style)],
                [Paragraph('Defensive Validation', td_style), Paragraph('assert payload is not None', td_code), Paragraph('Guarantees pre-conditions before mutating state.', td_style), Paragraph('O(k) schema validation', td_style)],
                [Paragraph('Terminal Execution', td_style), Paragraph('return ResultPayload(...)', td_code), Paragraph('Emits immutable response payload cleanly.', td_style), Paragraph('O(1) clean exit', td_style)]
            ]
            t_spec = Table(spec_rows, colWidths=[100, 140, 165, 110])
            t_spec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_spec)
            elements.append(Spacer(1, 8))

            # 5. Execution Flow Architecture & Control Diagrams
            elements.append(Paragraph('5. Execution Flow Architecture & Control Diagrams', h2_style))
            flow_ascii = (
                f"   [Input Payload Ingestion] ──► [Pre-Condition Validation] ──► [Context Initialization]\n"
                f"                                                                        │\n"
                f"   [Clean State Output] ◄── [Post-Condition Invariant Check] ◄── [Core Algorithmic Engine]\n"
                f"                                                                        │\n"
                f"                                                           (On Error: Defensive Rollback)"
            )
            flow_clean = flow_ascii.replace(' ', '&nbsp;').replace('\n', '<br/>')
            elements.append(Paragraph(f'<font face="Courier">{flow_clean}</font>', code_style))
            elements.append(Spacer(1, 6))

            # 6. Production Implementations
            elements.append(Paragraph('6. Production Implementation, Annotations & Console Traces', h2_style))
            sample_code = ""
            if code_snippets:
                sample_code = code_snippets[0].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
            elif exercises and exercises[0].solution:
                sample_code = exercises[0].solution.strip()
            elif exercises and exercises[0].starter_code:
                sample_code = exercises[0].starter_code.strip()
            else:
                sample_code = (
                    f"from typing import Dict, Any, Optional\n"
                    f"\n"
                    f"class {lesson.title.replace(' ', '').replace(':', '').replace('-', '')}Engine:\n"
                    f"    \"\"\"\n"
                    f"    Production reference implementation for {lesson.title}.\n"
                    f"    \"\"\"\n"
                    f"    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:\n"
                    f"        self.config = config or {{'mode': 'strict', 'timeout': 30}}\n"
                    f"        self._initialized = True\n"
                    f"\n"
                    f"    def execute_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:\n"
                    f"        if not payload or not isinstance(payload, dict):\n"
                    f"            raise ValueError('Invalid payload specification')\n"
                    f"\n"
                    f"        # Execute core domain operations with invariant enforcement\n"
                    f"        processed_data = {{k: v for k, v in payload.items() if v is not None}}\n"
                    f"        return {{'status': 'SUCCESS', 'data': processed_data, 'topic': '{lesson.title}'}}\n"
                    f"\n"
                    f"# Verification Execution\n"
                    f"engine = {lesson.title.replace(' ', '').replace(':', '').replace('-', '')}Engine()\n"
                    f"response = engine.execute_transaction({{'id': 'TX-901', 'metric': 42.0}})\n"
                    f"print('Transaction Result:', response)"
                )
            code_lines = sample_code.split('\n')
            safe_code_html = "<br/>".join([line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;') for line in code_lines])
            elements.append(Paragraph(f"<font face='Courier'>{safe_code_html}</font>", code_style))

            ann_rows = [
                [Paragraph('<b>Line Range</b>', th_style), Paragraph('<b>Construct / Pattern</b>', th_style), Paragraph('<b>Technical Rationale</b>', th_style), Paragraph('<b>Operational Behavior</b>', th_style)],
                [Paragraph('Lines 1-5', td_style), Paragraph('Class & Signature Definition', td_code), Paragraph('Defines explicit contracts and configuration options.', td_style), Paragraph('Instantiates state safely in heap memory.', td_style)],
                [Paragraph('Lines 6-10', td_style), Paragraph('Defensive Input Guards', td_code), Paragraph('Ensures invalid payloads fail fast before resource usage.', td_style), Paragraph('Raises ValueError on malformed inputs.', td_style)],
                [Paragraph('Lines 11-15', td_style), Paragraph('Transformation & Dispatch', td_code), Paragraph('Applies pure business transformation cleanly.', td_style), Paragraph('Emits immutable response payload.', td_style)]
            ]
            t_ann = Table(ann_rows, colWidths=[70, 135, 145, 165])
            t_ann.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_ann)
            elements.append(Spacer(1, 4))

            output_snippet = (
                f"$ python -m runtime.executor\n"
                f"[INFO] Initializing {lesson.title} context: SUCCESS\n"
                f"[INFO] Verification checks passed (0 warnings, 0 errors)\n"
                f"Transaction Result: {{'status': 'SUCCESS', 'data': {{'id': 'TX-901', 'metric': 42.0}}, 'topic': '{lesson.title}'}}"
            )
            safe_output_html = "<br/>".join([line.replace(' ', '&nbsp;') for line in output_snippet.split('\n')])
            elements.append(Paragraph(f"<font face='Courier-Bold'>{safe_output_html}</font>", terminal_style))
            elements.append(Spacer(1, 8))

            # Implementation 2: Defensive Edge-Case Trapping & Optimization
            elements.append(Paragraph(f'<b>Implementation 2: Defensive Edge-Case Validation & Memory Bounds</b>', h3_style))
            code_2 = (
                f"# Defensive Edge-Case Validation & Memory Isolation\n"
                f"def validate_and_transform_batch(records: list) -> list:\n"
                f"    \"\"\"\n"
                f"    Transforms record sequence with strict type checking and bounded memory allocation.\n"
                f"    \"\"\"\n"
                f"    if not records:\n"
                f"        return []\n"
                f"    validated = []\n"
                f"    for idx, item in enumerate(records, start=1):\n"
                f"        if item is None:\n"
                f"            continue  # Defensive skip\n"
                f"        validated.append({{'index': idx, 'value': item, 'valid': True}})\n"
                f"    return validated\n\n"
                f"# Verification Trace\n"
                f"batch_result = validate_and_transform_batch(['alpha', None, 'gamma'])\n"
                f"print('Batch Transformation:', batch_result)"
            )
            code_2_html = "<br/>".join([line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;') for line in code_2.split('\n')])
            elements.append(Paragraph(f"<font face='Courier'>{code_2_html}</font>", code_style))
            elements.append(Spacer(1, 6))

            # 7. Architectural Comparisons
            elements.append(Paragraph('7. Architectural Comparisons & Trade-Off Matrix', h2_style))
            cmp_rows = [
                [Paragraph('<b>Approach / Strategy</b>', th_style), Paragraph('<b>Throughput</b>', th_style), Paragraph('<b>Memory Overhead</b>', th_style), Paragraph('<b>Maintainability</b>', th_style), Paragraph('<b>Optimal Scenario</b>', th_style)],
                [Paragraph('Standard Implementation', td_style), Paragraph('High (O(1) to O(N))', td_style), Paragraph('Minimal (O(1))', td_style), Paragraph('High (clean idioms)', td_style), Paragraph('Production baseline workflows.', td_style)],
                [Paragraph('Defensive Cached Pattern', td_style), Paragraph('Very High (sub-ms)', td_style), Paragraph('Moderate (cache pool)', td_style), Paragraph('Moderate (invalidation)', td_style), Paragraph('Read-heavy enterprise APIs.', td_style)],
                [Paragraph('Async / Event-Driven', td_style), Paragraph('Ultra High (concurrent)', td_style), Paragraph('Low per connection', td_style), Paragraph('High (structured concurrency)', td_style), Paragraph('I/O-bound microservices.', td_style)],
                [Paragraph('Streaming / Generator', td_style), Paragraph('High (pipelined)', td_style), Paragraph('Strictly O(1) memory', td_style), Paragraph('High (iterator protocol)', td_style), Paragraph('Large datasets & continuous feeds.', td_style)]
            ]
            t_cmp = Table(cmp_rows, colWidths=[100, 95, 95, 95, 130])
            t_cmp.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_cmp)
            elements.append(Spacer(1, 8))

            # 8. Common Pitfalls
            elements.append(Paragraph('8. Common Pitfalls, Anti-Patterns & Defensive Debugging', h2_style))
            if mistakes:
                for idx, m in enumerate(mistakes, 1):
                    elements.append(Paragraph(f'<b>⚠️ Pitfall {idx}:</b> {m}', mistake_style))
            else:
                elements.append(Paragraph(
                    "<b>⚠️ Pitfall 1: Unvalidated Input Mutation:</b> Modifying shared input objects in-place leads to unintended side-effects across asynchronous execution contexts.<br/>"
                    "<b>Idiomatic Resolution:</b> Treat input payloads as strictly immutable or create defensive shallow/deep copies prior to transformation.",
                    mistake_style
                ))
                elements.append(Paragraph(
                    "<b>⚠️ Pitfall 2: Silent Exception Swallowing:</b> Catching broad exceptions (`except Exception: pass`) conceals runtime failures, database deadlocks, and syntax bugs.<br/>"
                    "<b>Idiomatic Resolution:</b> Catch specific exceptions explicitly and record structured telemetry logs before gracefully degrading.",
                    callout_style
                ))
            elements.append(Paragraph(
                "<b>⚠️ Pitfall 3: Inadequate Boundary Invariant Checks:</b> Failing to validate edge boundaries (empty inputs, zero values, overflow limits) causes unhandled exceptions in production.<br/>"
                "<b>Idiomatic Resolution:</b> Establish explicit preconditions at function entry points.",
                mistake_style
            ))
            elements.append(Spacer(1, 6))

            # 9. Technical Interview Questions
            elements.append(Paragraph('9. Technical Interview Questions & Model Answers', h2_style))
            elements.append(Paragraph(f"<b>Q1: What are the primary computational and memory trade-offs in {lesson.title}?</b>", h3_style))
            elements.append(Paragraph(f"<i>Interviewer Evaluation Criteria:</i> Evaluates depth of runtime mechanics, cache efficiency, and Big-O asymptotic limits.", meta_style))
            elements.append(Paragraph(f"<b>Model Answer:</b> In production systems, <b>{lesson.title}</b> balances CPU cycle utilization against RAM consumption. Implementations must optimize locality of reference, avoid unnecessary object allocations on heap memory, and ensure predictable latency without GC pauses.", body_style))
            elements.append(Spacer(1, 4))

            elements.append(Paragraph(f"<b>Q2: How would you debug an intermittent production regression associated with this component?</b>", h3_style))
            elements.append(Paragraph(f"<i>Interviewer Evaluation Criteria:</i> Assesses systematic observability, distributed tracing, and root-cause analysis methodology.", meta_style))
            elements.append(Paragraph(f"<b>Model Answer:</b> Isolate the reproducible failure in a sandbox harness with deterministic fixtures. Enable structured telemetry, inspect thread/connection pool starvation, verify database lock contention, and validate invariant boundary tests.", body_style))
            elements.append(Spacer(1, 4))

            elements.append(Paragraph(f"<b>Q3: What concurrency risks or thread-safety considerations apply to {lesson.title}?</b>", h3_style))
            elements.append(Paragraph(f"<i>Interviewer Evaluation Criteria:</i> Tests understanding of state mutation, atomic operations, and lock contention.", meta_style))
            elements.append(Paragraph(f"<b>Model Answer:</b> Concurrency issues arise when multiple threads mutate shared references without synchronization. In Python, while the GIL protects CPython internal data structures, application-level race conditions must be resolved with mutex locks, thread-local storage, or immutable data structures.", body_style))
            elements.append(Spacer(1, 4))

            elements.append(Paragraph(f"<b>Q4: How does this architectural component behave under horizontal scaling across multiple instances?</b>", h3_style))
            elements.append(Paragraph(f"<i>Interviewer Evaluation Criteria:</i> Evaluates distributed systems design, shared vs local state, and cache coherence.", meta_style))
            elements.append(Paragraph(f"<b>Model Answer:</b> Under multi-instance deployments (such as serverless workers or container clusters), local in-memory state is isolated per instance. Shared coordinates, rate-limits, and token buckets must be backed by distributed Redis stores with atomic transactions.", body_style))
            elements.append(Spacer(1, 6))

            # 10. Self-Assessment Practice Challenges
            elements.append(Paragraph('10. Graded Practice Challenges & Problem Sets', h2_style))
            if exercises:
                for idx, ex in enumerate(exercises, 1):
                    clean_inst = re.sub(r'<[^>]+>', '', ex.instructions or '')
                    elements.append(Paragraph(f'<b>Challenge #{idx}: {ex.title}</b>', h3_style))
                    elements.append(Paragraph(clean_inst, body_style))
                    if ex.starter_code:
                        clean_sc = ex.starter_code.strip().replace(' ', '&nbsp;').replace('\n', '<br/>')
                        elements.append(Paragraph(f'<font face="Courier">{clean_sc}</font>', code_style))
                    elements.append(Spacer(1, 4))
            else:
                elements.append(Paragraph(f'<b>Challenge 1 (Foundational):</b> Implement a clean validation wrapper for {lesson.title} enforcing strict parameter contracts and boundary checks.', body_style))
                elements.append(Paragraph(f'<b>Challenge 2 (Intermediate):</b> Implement an idempotent handler verifying that duplicate inputs produce deterministic outcomes without side-effects.', body_style))
                elements.append(Paragraph(f'<b>Challenge 3 (Advanced):</b> Benchmark throughput under 50,000 continuous iterations, measuring p95 and p99 latency distributions.', body_style))
            elements.append(Spacer(1, 6))

            # 11. Quick Revision Summary & Cheat Sheet
            elements.append(Paragraph('11. Quick Revision Summary & Architectural Cheat Sheet', h2_style))
            cs_gen_rows = [
                [Paragraph('<b>Construct / Component</b>', th_style), Paragraph('<b>Syntax Pattern</b>', th_style), Paragraph('<b>Core Rule</b>', th_style), Paragraph('<b>Idiomatic Practice</b>', th_style)],
                [Paragraph('Entrypoint', td_style), Paragraph('def handle(ctx: dict)', td_code), Paragraph('Must declare explicit typed arguments.', td_style), Paragraph('Validate pre-conditions first.', td_style)],
                [Paragraph('State Scope', td_style), Paragraph('with lock: ...', td_code), Paragraph('Synchronize mutable shared state.', td_style), Paragraph('Prefer immutable objects.', td_style)],
                [Paragraph('Error Protocol', td_style), Paragraph('except SpecificError as e:', td_code), Paragraph('Catch narrow exceptions only.', td_style), Paragraph('Log structured diagnostics.', td_style)],
                [Paragraph('Response Envelope', td_style), Paragraph('return {"status": "ok"}', td_code), Paragraph('Maintain consistent payload contracts.', td_style), Paragraph('Include telemetry metadata.', td_style)]
            ]
            t_cs_gen = Table(cs_gen_rows, colWidths=[80, 130, 150, 155])
            t_cs_gen.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_cs_gen)
            elements.append(Spacer(1, 8))

            if takeaways:
                takeaways_text = '<br/>• '.join([''] + takeaways).strip()
            else:
                takeaways_text = (
                    f"Mastery of <b>{lesson.title}</b> guarantees reliable, maintainable software architecture.<br/>• "
                    f"Always enforce defensive input boundaries and pre-condition invariants.<br/>• "
                    f"Review runtime profiles and space-time complexity bounds prior to production rollout."
                )
            elements.append(Paragraph(f'<b>💡 Key Revision Takeaways:</b><br/>{takeaways_text}', callout_style))
            elements.append(Spacer(1, 6))

            # 12. References
            elements.append(Paragraph('12. Academic Bibliography & Formal References', h2_style))
            elements.append(Paragraph(f'• <b>Official Documentation:</b> Industry Reference Standard for {course.title}.', body_style))
            elements.append(Paragraph(f'• <b>Knuth, D. E.:</b> <i>The Art of Computer Programming</i>, Addison-Wesley, Core System Foundations.', body_style))
            elements.append(Paragraph(f'• <b>IEEE Software Engineering Standards:</b> Architectural Patterns & Code Quality Guidelines.', body_style))
            elements.append(Paragraph(f'• <b>Gamma, Helm, Johnson, Vlissides:</b> <i>Design Patterns: Elements of Reusable Object-Oriented Software</i>.', body_style))

        # End of Document Signature
        elements.append(Spacer(1, 12))
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

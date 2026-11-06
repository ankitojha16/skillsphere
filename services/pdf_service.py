import io
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

class PDFService:

    @staticmethod
    def generate_certificate_pdf(certificate) -> bytes:
        """
        Generates an authentic, high-resolution landscape certificate PDF
        with SkillSphere ivory/white background, gold double border, official seal,
        and public verification link per Module 9 specifications.
        """
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
        c.drawCentredString(seal_x, seal_y + 12, "★ OFFICIAL ★")
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
        return pdf_data

    @staticmethod
    def generate_lesson_notes_pdf(lesson) -> bytes:
        """
        Generates professionally formatted, downloadable lesson study notes PDF
        including SkillSphere header, chapter metadata, key concepts, code blocks,
        key takeaways, and common mistakes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'LessonTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'LessonSubTitle',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#4F46E5'),
            spaceAfter=12
        )
        meta_style = ParagraphStyle(
            'LessonMeta',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=14,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'LessonBody',
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )
        code_style = ParagraphStyle(
            'CodeBlock',
            fontName='Courier',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#0F172A'),
            backColor=colors.HexColor('#F1F5F9'),
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=10
        )
        box_style = ParagraphStyle(
            'CalloutBox',
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1E293B'),
            backColor=colors.HexColor('#EFF6FF'),
            borderColor=colors.HexColor('#3B82F6'),
            borderWidth=1,
            borderPadding=10,
            spaceBefore=8,
            spaceAfter=12
        )

        elements = []

        # 1. Header Banner
        header_table = Table([
            [
                Paragraph("<b>SKILLSPHERE COURSEWARE</b>", ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#4F46E5'))),
                Paragraph(f"<b>Estimated:</b> {lesson.estimated_minutes} min read", ParagraphStyle('H2', fontName='Helvetica', fontSize=9, alignment=2, textColor=colors.HexColor('#64748B')))
            ]
        ], colWidths=[350, 160])
        header_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#4F46E5')),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 14))

        # 2. Titles
        module_name = lesson.module.title if lesson.module else lesson.chapter_name
        elements.append(Paragraph(f"{lesson.course.title.upper()} • {module_name.upper()}", subtitle_style))
        elements.append(Paragraph(f"Lesson {lesson.lesson_order}: {lesson.title}", title_style))
        elements.append(Paragraph(f"Instructor: {lesson.course.instructor_name} | Difficulty: {lesson.course.difficulty}", meta_style))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=14))

        # 3. Main Body Content
        raw_text = lesson.content or ""
        code_blocks = re.findall(r'<pre><code>(.*?)</code></pre>', raw_text, re.DOTALL)
        clean_text = re.sub(r'<pre><code>.*?</code></pre>', '[CODE_BLOCK]', raw_text, flags=re.DOTALL)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_paragraphs = [p.strip() for p in clean_text.split('\n') if p.strip()]

        code_idx = 0
        for p in clean_paragraphs:
            if '[CODE_BLOCK]' in p and code_idx < len(code_blocks):
                code_text = code_blocks[code_idx].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
                elements.append(Paragraph(f"<font face='Courier'>{code_text.replace(chr(10), '<br/>')}</font>", code_style))
                code_idx += 1
            else:
                p_clean = p.replace('[CODE_BLOCK]', '')
                if p_clean:
                    elements.append(Paragraph(p_clean, body_style))

        # 4. Key Takeaways Callout
        if lesson.key_takeaways:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("<b>💡 Key Takeaways & Summary:</b>", h2_style))
            takeaways_html = lesson.key_takeaways.replace('\n', '<br/>• ')
            elements.append(Paragraph(f"• {takeaways_html}", box_style))

        # 5. Common Mistakes Callout
        if lesson.common_mistakes:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("<b>⚠️ Common Pitfalls & Mistakes to Avoid:</b>", h2_style))
            mistakes_html = lesson.common_mistakes.replace('\n', '<br/>• ')
            mistake_box_style = ParagraphStyle(
                'MistakeBox',
                parent=box_style,
                backColor=colors.HexColor('#FEF2F2'),
                borderColor=colors.HexColor('#EF4444'),
                textColor=colors.HexColor('#991B1B')
            )
            elements.append(Paragraph(f"• {mistakes_html}", mistake_box_style))

        # 6. Footer metadata
        elements.append(Spacer(1, 18))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=8))
        elements.append(Paragraph("<i>Official SkillSphere Learning Resource • For personal student study and revision.</i>", ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#94A3B8'), alignment=1)))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
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

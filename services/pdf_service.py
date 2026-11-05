import io
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
        with SkillSphere official border, badge, and verification reference.
        """
        buffer = io.BytesIO()
        width, height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        # Background Fill
        c.setFillColor(colors.HexColor('#0B1020'))
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # Outer Golden/Cyan Border
        c.setStrokeColor(colors.HexColor('#8B5CF6'))
        c.setLineWidth(3)
        c.rect(20, 20, width - 40, height - 40)

        # Inner Accent Border
        c.setStrokeColor(colors.HexColor('#06B6D4'))
        c.setLineWidth(1)
        c.rect(28, 28, width - 56, height - 56)

        # Decorative Corner Accents
        c.setFillColor(colors.HexColor('#22C55E'))
        c.circle(28, 28, 4, fill=True, stroke=False)
        c.circle(width - 28, 28, 4, fill=True, stroke=False)
        c.circle(28, height - 28, 4, fill=True, stroke=False)
        c.circle(width - 28, height - 28, 4, fill=True, stroke=False)

        # Header Title
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#06B6D4'))
        c.drawCentredString(width / 2.0, height - 70, "SKILLSPHERE PROFESSIONAL LEARNING PLATFORM")

        c.setFont("Helvetica-Bold", 30)
        c.setFillColor(colors.HexColor('#F8FAFC'))
        c.drawCentredString(width / 2.0, height - 110, "CERTIFICATE OF COMPLETION")

        # Subtitle
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawCentredString(width / 2.0, height - 135, "This is proudly presented to verify that")

        # Recipient Name
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(colors.HexColor('#38BDF8'))
        recipient = certificate.recipient_name or certificate.user.get_full_name() or certificate.user.username
        c.drawCentredString(width / 2.0, height - 180, recipient)

        # Divider line
        c.setStrokeColor(colors.HexColor('#8B5CF6'))
        c.setLineWidth(1.5)
        c.line(width / 2.0 - 180, height - 195, width / 2.0 + 180, height - 195)

        # Course / Achievement Text
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawCentredString(width / 2.0, height - 225, "has successfully mastered the coursework and completed all practical requirements for")

        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.HexColor('#F8FAFC'))
        c.drawCentredString(width / 2.0, height - 255, certificate.title)

        # Criteria text
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.HexColor('#64748B'))
        c.drawCentredString(width / 2.0, height - 280, certificate.criteria_met)

        # Verification & Signature Box
        # Left: Verification metadata
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawString(60, 90, "CERTIFICATE ID:")
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor('#22C55E'))
        c.drawString(160, 90, certificate.certificate_id)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawString(60, 72, "ISSUE DATE:")
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor('#F8FAFC'))
        c.drawString(160, 72, certificate.issued_at.strftime('%B %d, %Y'))

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawString(60, 54, "VERIFY ONLINE:")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#06B6D4'))
        c.drawString(160, 54, f"/verify/{certificate.certificate_id}/")

        # Right: Official Seal / Signing
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#F8FAFC'))
        c.drawCentredString(width - 150, 95, "SkillSphere Academic Board")
        c.setStrokeColor(colors.HexColor('#64748B'))
        c.setLineWidth(1)
        c.line(width - 230, 85, width - 70, 85)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawCentredString(width - 150, 72, "Verified Credential • Autonomous Evaluation")

        c.save()
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
        
        # Custom Clean Styles
        title_style = ParagraphStyle(
            'ResumeName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A')
        )
        headline_style = ParagraphStyle(
            'ResumeHeadline',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569')
        )
        contact_style = ParagraphStyle(
            'ResumeContact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748B')
        )
        section_style = ParagraphStyle(
            'ResumeSection',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'ResumeBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        item_title_style = ParagraphStyle(
            'ResumeItemTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
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
        
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

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

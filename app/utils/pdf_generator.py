import base64
import io
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_candidate_pdf(firstname: str, lastname: str, candidate_data: Dict[str, Any], talent_info: Dict[str, Any]) -> str:
    """
    Génère un joli PDF récapitulatif pour un candidat et le retourne en base64 pour Flatchr.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#2C3E50"),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitleStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=(0, 0, 4, 0),
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 6
    normal_style.textColor = colors.HexColor("#34495E")
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=normal_style,
        leftIndent=15,
        firstLineIndent=0,
        spaceAfter=4
    )

    item_title_style = ParagraphStyle(
        'ItemTitle',
        parent=normal_style,
        fontName='Helvetica-Bold',
        spaceAfter=2,
        textColor=colors.HexColor("#2C3E50")
    )
    
    item_desc_style = ParagraphStyle(
        'ItemDesc',
        parent=normal_style,
        leftIndent=10,
        spaceAfter=8,
        textColor=colors.HexColor("#5D6D7E")
    )

    story = []
    
    # Title
    story.append(Paragraph(f"Profil : {firstname} {lastname}", title_style))
    
    # LinkedIn / Score
    score = candidate_data.get("match_score")
    score_text = f"Score Sourcing Jemmo : {score}/100" if score is not None else "Évaluation Jemmo en cours"
    if talent_info.get("linkedin_url"):
         score_text += f" | LinkedIn disponible"
    story.append(Paragraph(score_text, subtitle_style))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#BDC3C7"), spaceBefore=10, spaceAfter=20))

    # Justification (Pros / Cons)
    justification = candidate_data.get("justification") or {}
    if justification:
        pros = justification.get("pros") or []
        if pros:
            story.append(Paragraph("Points Forts", section_title_style))
            for pro in pros:
                title_text = f"<b>{pro.get('title') or ''}</b> : {pro.get('description') or ''}"
                story.append(Paragraph(f"• {title_text}", bullet_style))
            story.append(Spacer(1, 10))
            
        cons = justification.get("cons") or []
        if cons:
            story.append(Paragraph("Points d'Attention", section_title_style))
            for con in cons:
                title_text = f"<b>{con.get('title') or ''}</b> : {con.get('description') or ''}"
                story.append(Paragraph(f"• {title_text}", bullet_style))
            story.append(Spacer(1, 10))

    # Competences
    skills = talent_info.get("skills") or []
    if skills:
        story.append(Paragraph("Compétences Clés", section_title_style))
        skills_text = ", ".join(skills)
        story.append(Paragraph(skills_text, normal_style))
        story.append(Spacer(1, 10))

    # Remuneration
    compensation = talent_info.get("compensation")
    if compensation:
        story.append(Paragraph("Rémunération Attendue", section_title_style))
        story.append(Paragraph(str(compensation), normal_style))
        story.append(Spacer(1, 10))
        
    # Experiences
    experiences = talent_info.get("experiences") or []
    if experiences:
        story.append(Paragraph("Expériences Professionnelles", section_title_style))
        for exp in experiences:
            title = exp.get("title") or ""
            company = exp.get("company") or ""
            start = exp.get("start_date") or ""
            end = exp.get("end_date") or ("Présent" if exp.get("is_current") else "")
            desc = exp.get("description") or ""
            
            date_str = f" ({start} - {end})" if start or end else ""
            header_text = f"{title} chez {company}{date_str}"
            
            story.append(Paragraph(header_text, item_title_style))
            if desc:
                # Handle basic newlines gracefully
                desc_formatted = desc.replace('\n', '<br />')
                story.append(Paragraph(desc_formatted, item_desc_style))
        story.append(Spacer(1, 10))

    # Educations
    educations = talent_info.get("educations") or []
    if educations:
        story.append(Paragraph("Formations", section_title_style))
        for edu in educations:
            degree = edu.get("degree") or ""
            school = edu.get("school") or ""
            start = edu.get("start_date") or ""
            end = edu.get("end_date") or ""
            
            degree_text = f"{degree} à " if degree else ""
            date_str = f" ({start} - {end})" if start or end else ""
            header_text = f"{degree_text}{school}{date_str}"
            story.append(Paragraph(header_text, bullet_style))

    # Build PDF
    doc.build(story)
    
    # Get base64 string
    pdf_bytes = buffer.getvalue()
    buffer.close()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return base64_pdf

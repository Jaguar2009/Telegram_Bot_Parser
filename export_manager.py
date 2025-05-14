from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from datetime import datetime

from data_manager import load_sites, load_points, PARSED_DATA_FILE
import json
import os


def create_pdf(filename, title, items):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Heading", fontSize=16, spaceAfter=10, alignment=TA_LEFT, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name="Body", fontSize=11, spaceAfter=6, leading=14))

    elements = [Paragraph(title, styles["Heading"])]
    for item in items:
        elements.append(Paragraph(item, styles["Body"]))
    doc.build(elements)

def export_sites_to_pdf():
    sites = load_sites()
    if not sites:
        return None
    filename = "export_sites.pdf"
    create_pdf(filename, "List of Sites for Parsing", sites)
    return filename

def export_points_to_pdf():
    points = load_points()
    if not points:
        return None
    lines = []
    for p in points:
        rep = "repeating" if p.get("repeat") else "one-time"
        days = "/".join(p.get("days", []))
        lines.append(f"{p.get('time')} — {days} ({rep})")
    filename = "export_points.pdf"
    create_pdf(filename, "Auto-parsing Time Points", lines)
    return filename

def export_results_to_pdf():
    if not os.path.exists(PARSED_DATA_FILE):
        return None
    try:
        with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None
    if not data:
        return None

    lines = [
        f"[{entry['datetime']}] {entry['url']} → {entry['result']}"
        for entry in data
    ]
    filename = "export_results.pdf"
    create_pdf(filename, "Parsing Results", lines)
    return filename

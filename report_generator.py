from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def generate_report_pdf(summary, filename="report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(
        "<b>Social Sentiment Monitor – Sentiment Report</b>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 20))

    # Metadata
    date_str = datetime.now(IST).strftime("%d %B %Y, %I:%M %p IST")
    elements.append(Paragraph(f"<b>Search Query:</b> {summary['query']}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Generated On:</b> {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Summary table
    table_data = [
        ["Metric", "Count"],
        ["Total Tweets", summary["total_tweets"]],
        ["Analyzed Tweets", summary["sentiment_input"]],
        ["Positive", summary["positive"]],
        ["Neutral", summary["neutral"]],
        ["Negative", summary["negative"]],
    ]

    table = Table(table_data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.pink),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 25))

    # Insight
    dominant = max(
        [("Positive", summary["positive"]),
         ("Neutral", summary["neutral"]),
         ("Negative", summary["negative"])],
        key=lambda x: x[1]
    )[0]

    insight_text = (
        f"The dominant public sentiment for <b>{summary['query']}</b> "
        f"is <b>{dominant}</b>. This insight can help brands understand "
        f"current audience perception and guide strategic decisions."
    )

    elements.append(Paragraph("<b>Insight</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(insight_text, styles["Normal"]))

    doc.build(elements)

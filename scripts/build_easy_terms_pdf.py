"""
build_easy_terms_pdf.py - Compiles the 2-page easy-terms architecture PDF.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (page 2)
        if self._pageNumber > 1:
            self.drawString(40, 755, "MarketTide RAGBot — Architecture, Matching Logic & Workflow Specification")
            self.drawRightString(572, 755, "System Architecture Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 38, 572, 38)
        self.drawString(40, 26, "MarketTide Regulatory AI · National Stock Exchange (NSE) Corporate Disclosures")
        self.drawRightString(572, 26, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=44
    )

    PRIMARY = colors.HexColor("#0f172a")    # Slate 900
    SECONDARY = colors.HexColor("#0284c7")  # Cyan / Blue
    TEXT_DARK = colors.HexColor("#1e293b")  # Slate 800
    BG_LIGHT = colors.HexColor("#f8fafc")   # Slate 50
    BORDER_CLR = colors.HexColor("#cbd5e1") # Slate 300

    style_title = ParagraphStyle(
        "DocTitle", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=PRIMARY, spaceAfter=2
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle", fontName="Helvetica", fontSize=9, leading=12, textColor=SECONDARY, spaceAfter=5
    )
    style_h1 = ParagraphStyle(
        "SectionH1", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=PRIMARY, spaceBefore=4, spaceAfter=3, keepWithNext=True
    )
    style_body = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=7.4, leading=10.0, textColor=TEXT_DARK, spaceAfter=2
    )
    style_callout = ParagraphStyle(
        "Callout", fontName="Helvetica", fontSize=7.3, leading=9.6, textColor=TEXT_DARK
    )
    style_th = ParagraphStyle(
        "TableHead", fontName="Helvetica-Bold", fontSize=7.0, leading=9.0, textColor=colors.white
    )
    style_td = ParagraphStyle(
        "TableCell", fontName="Helvetica", fontSize=6.8, leading=8.8, textColor=TEXT_DARK
    )
    style_td_bold = ParagraphStyle(
        "TableCellBold", fontName="Helvetica-Bold", fontSize=6.8, leading=8.8, textColor=PRIMARY
    )

    story = []

    # ==========================================
    # PAGE 1: OVERVIEW, DATA & QUERY PIPELINE
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Architecture & Technical Workflow", style_title))
    story.append(Paragraph("An Accessible, Plain-Terms Guide to How the Query Pipeline, Matching, and UI Work", style_subtitle))

    meta_table = Table([
        [
            Paragraph("<b>Project:</b> MarketTide RAGBot Regulatory Search Engine<br/>"
                      "<b>Core Objective:</b> Zero-Hallucination Corporate Disclosures<br/>"
                      "<b>Exchange Scope:</b> National Stock Exchange of India (NSE)", style_callout),
            Paragraph("<b>Core Engineering Team:</b><br/>"
                      "• <b>Shreyansh Shailesh</b> &nbsp;&nbsp;&nbsp; • <b>Shubh Tanna</b><br/>"
                      "• <b>David Jeremie Anand</b> &nbsp; • <b>Shaurya Gupta</b>", style_callout)
        ]
    ], colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))

    # SECTION 1: WHAT IT DOES
    story.append(Paragraph("1. High-Level Overview: What MarketTide RAGBot Does", style_h1))
    story.append(Paragraph(
        "<b>The Problem:</b> Standard AI models like ChatGPT hallucinate numbers and dates when asked about financial news. In finance, making decisions on hallucinated numbers is dangerous.<br/>"
        "<b>Our Solution:</b> MarketTide RAGBot is a domain-specific, <b>zero-hallucination regulatory search engine</b> for the Indian stock market. It answers questions strictly using verified corporate announcements submitted to the National Stock Exchange of India (NSE). Every answer includes direct clickable links to the <b>official signed PDF documents</b> submitted by company secretaries. If asked an irrelevant question (<i>'are you dumb?'</i>), it refuses to answer rather than guessing.<br/>"
        "<b>Two Frontends:</b> (1) Standalone Chatbot Terminal (<code>RAG-Chatbot</code> branch) built on Streamlit with live step-by-step latency tracking, and (2) Spatial 3D Workstation (<code>shrey</code> branch) built on Three.js with real-time 3D stock trajectory lines.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 2: THE DATA FOUNDATION
    story.append(Paragraph("2. The Data Foundation: What Lives in the Engine", style_h1))
    data_rows = [
        [Paragraph("<b>Data Parameter</b>", style_th), Paragraph("<b>Exact Dataset Specifications & Coverage</b>", style_th)],
        [Paragraph("<b>Primary Source</b>", style_td_bold), Paragraph("Official statutory announcements submitted to the <b>National Stock Exchange of India (NSE)</b>.", style_td)],
        [Paragraph("<b>Time Window</b>", style_td_bold), Paragraph("Active 7-day reporting cycle: <b>November 9 to November 15, 2026</b> (representing an active Q2 earnings week).", style_td)],
        [Paragraph("<b>Scale & Volume</b>", style_td_bold), Paragraph("<b>2,766 verified corporate filings</b> covering <b>1,716 publicly listed Indian equities</b>.", style_td)],
        [Paragraph("<b>Regulatory Framework</b>", style_td_bold), Paragraph("Mandatory filings under <b>SEBI (LODR) Regulations 2015</b>: Reg 30 (Material Events), Reg 33 (Financial Results), Reg 42 (Actions).", style_td)],
        [Paragraph("<b>Filing Categories</b>", style_td_bold), Paragraph("Audited/Unaudited Q2 Results, Board Meeting Outcomes, Buybacks, Rights Issues, Volume Spurt intimations, Demergers, Leadership Changes.", style_td)],
        [Paragraph("<b>Quality Threshold</b>", style_td_bold), Paragraph("Filings filtered by importance score (0-100). Low-value paperwork is eliminated, keeping disclosures with <b>score &ge; 45</b>.", style_td)],
        [Paragraph("<b>Pre-Computed Cache</b>", style_td_bold), Paragraph("Saved in a <b>9.07 MB</b> local binary cache (<code>embeddings.npy</code> 4.2MB, <code>bm25.pkl</code> 1.2MB, <code>metadata.pkl</code> 3.6MB) for instant boot under 2s.", style_td)]
    ]
    data_table = Table(data_rows, colWidths=[120, 412])
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(data_rows)):
        if i % 2 == 0:
            data_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(data_table)
    story.append(Spacer(1, 3))

    # SECTION 3: THE QUERY JOURNEY
    story.append(Paragraph("3. The Query Journey: What Happens When You Type in the Box", style_h1))
    pipe_rows = [
        [
            Paragraph("<b>Station 1: Pre-Check Filter</b>", style_td_bold),
            Paragraph("<b>Station 2: Conglomerate Router</b>", style_td_bold),
            Paragraph("<b>Station 3: Hybrid Search</b>", style_td_bold),
            Paragraph("<b>Station 4: LLM Synthesis</b>", style_td_bold)
        ],
        [
            Paragraph("• <b>Slang Check (0 ms):</b> Questions like <i>'are you dumb?'</i> are blocked immediately.<br/>• <b>Word Boundaries (\\b):</b> Blocks substring collisions (e.g. 'am' matching Dhampur).<br/>• <b>Foreign Interceptor:</b> Directs Apple/Tesla to US exchanges.", style_td),
            Paragraph("• <b>Multi-Hop Resolution:</b> 'Tata Group' expands into <b>TMPV, TATAPOWER, TATASTEEL, and TCS</b> simultaneously, gathering 25 filings in one structured briefing.", style_td),
            Paragraph("• <b>Dense Vectors:</b> 384-dim semantic matching (<code>all-MiniLM-L6-v2</code>).<br/>• <b>Sparse BM25:</b> Exact ticker matching.<br/>• <b>Rank Fusion (RRF):</b> Merges scoreboards to select Top 5.", style_td),
            Paragraph("• <b>Groq Llama-3.3-70B:</b> Streams bulleted summary in &lt; 650 ms.<br/>• <b>Grounding:</b> Cites only retrieved text and provides direct links to the official signed NSE PDF filings.", style_td)
        ]
    ]
    pipe_table = Table(pipe_rows, colWidths=[133, 133, 133, 133])
    pipe_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for c in range(4):
        pipe_rows[0][c].style = style_th
    story.append(pipe_table)

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: MATCHING, UI, APPS & TECH
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Matching Logic, UI & Applications", style_title))
    story.append(Paragraph("Dual Search Engines, Result Presentation Layout, and Complete Software Stack", style_subtitle))
    story.append(Spacer(1, 3))

    # SECTION 4: HOW WE MATCH
    story.append(Paragraph("4. How We Match: The Dual Search Engines & Rank Fusion", style_h1))
    story.append(Paragraph(
        "To find the exact right filing out of 2,766 documents in just <b>68 milliseconds</b>, MarketTide runs two complementary engines in parallel:<br/>"
        "• <b>Search Engine 1: Semantic Vector Search (Dense):</b> Converts the question into a 384-dimensional vector coordinate. Understands <i>meaning and intent</i> (e.g. matching <i>'returning cash to shareholders'</i> to <i>'share buyback'</i> or <i>'dividend'</i>).<br/>"
        "• <b>Search Engine 2: Exact Keyword Search (BM25):</b> Matches <i>exact stock codes and legal numbers</i> (e.g. <code>TMPV</code>, <code>TATAPOWER</code>, <code>Regulation 30</code>).<br/>"
        "• <b>The Matchmaker (Reciprocal Rank Fusion - RRF):</b> Combines the two ranked lists using a mathematical balancing formula: <i>Combined Score = &Sigma; 1 / (60 + Rank)</i>. Filings that score high on both lists rise to the top. The engine selects the <b>Top 5 verified filings</b>.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 5: HOW WE SHOW RESULTS
    story.append(Paragraph("5. How We Show the Results: The 3-Part Output Display", style_h1))
    ui_rows = [
        [Paragraph("<b>UI Component</b>", style_th), Paragraph("<b>What the User Sees on the Screen</b>", style_th)],
        [Paragraph("<b>1. Executive Synthesis Card</b>", style_td_bold), Paragraph("High-level summary generated by <b>Llama-3.3 70B via Groq LPUs</b> in &lt; 650 ms, stating core findings, involved companies, and average importance score.", style_td)],
        [Paragraph("<b>2. Verified Filing Dossiers</b>", style_td_bold), Paragraph("Interactive cards for each supporting document displaying: Stock Ticker Badge, Legal Company Name, Filing Timestamp, Category Tag, Importance Rating (45-100), and a clickable link to the <b>official signed NSE PDF filing</b>.", style_td)],
        [Paragraph("<b>3. Execution Step Timeline</b>", style_td_bold), Paragraph("Shows live millisecond latencies for each pipeline stage: <i>Query Filter (0ms) &rarr; Hybrid Search (68ms) &rarr; Groq LLM Synthesis (510ms)</i>.", style_td)]
    ]
    ui_table = Table(ui_rows, colWidths=[140, 392])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(ui_rows)):
        if i % 2 == 0:
            ui_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(ui_table)
    story.append(Spacer(1, 3))

    # SECTION 6: APPLICATIONS
    story.append(Paragraph("6. Real-World Applications & Use Cases", style_h1))
    app_rows = [
        [
            Paragraph("<b>Application 1: Conglomerate Risk Monitoring</b><br/>Auditing conglomerates like the <b>Tata Group</b> requires checking multiple listed entities. The system searches across Tata Motors (TMPV), Tata Power, Tata Steel, and TCS at once, aggregating 25 filings in one brief.", style_td),
            Paragraph("<b>Application 2: M&A & Buyback Compliance Audits</b><br/>Compliance teams can instantly filter capital actions (SEBI Reg 30/33/42 buybacks, rights issues, demergers) without sorting through routine paperwork, providing direct links to signed exchange filings.", style_td)
        ],
        [
            Paragraph("<b>Application 3: Intraday Volume Spike Clarification</b><br/>When a stock moves unexpectedly, traders need to know if the move is backed by real news. MarketTide surfaces official exchange volume clarification letters (e.g. TTML) to separate fact from speculation.", style_td),
            Paragraph("<b>Application 4: Audit-Ready Financial Research</b><br/>Every single sentence synthesized is anchored to an authentic regulatory filing, giving financial analysts an audit trail with zero legal liability.", style_td)
        ]
    ]
    app_table = Table(app_rows, colWidths=[266, 266])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(app_table)
    story.append(Spacer(1, 3))

    # SECTION 7: SOFTWARE STACK
    story.append(Paragraph("7. Software Technologies Used (Complete Stack)", style_h1))
    tech_rows = [
        [Paragraph("<b>Tool</b>", style_th), Paragraph("<b>Category</b>", style_th), Paragraph("<b>Role in the System & Selection Rationale</b>", style_th)],
        [Paragraph("<b>Python 3.11/3.13</b>", style_td_bold), Paragraph("Language", style_td), Paragraph("Runs the core data pipeline, vector ranking algorithms, and local API server.", style_td)],
        [Paragraph("<b>Streamlit</b>", style_td_bold), Paragraph("Chatbot UI", style_td), Paragraph("Powers the interactive chat terminal (<code>app.py</code>) and live step-by-step latency tracking.", style_td)],
        [Paragraph("<b>Three.js (WebGL)</b>", style_td_bold), Paragraph("3D Graphics", style_td), Paragraph("Renders interactive 3D stock trajectory lines and orbit camera controls on the landing page.", style_td)],
        [Paragraph("<b>Sentence-Transformers</b>", style_td_bold), Paragraph("Vector NLP", style_td), Paragraph("Uses <code>all-MiniLM-L6-v2</code> for fast 384-dimensional semantic similarity matching on CPU.", style_td)],
        [Paragraph("<b>Rank-BM25</b>", style_td_bold), Paragraph("Lexical Search", style_td), Paragraph("Matches exact tickers (<code>TMPV</code>, <code>TATAPOWER</code>) and regulatory phrases.", style_td)],
        [Paragraph("<b>Groq Cloud API</b>", style_td_bold), Paragraph("LLM Inference", style_td), Paragraph("Runs <b>Llama-3.3-70b-versatile</b> on Groq LPUs, streaming answers in &lt; 650 ms.", style_td)],
        [Paragraph("<b>ReportLab</b>", style_td_bold), Paragraph("PDF Engine", style_td), Paragraph("Programmatically compiles formal, publication-ready 2-page documentation.", style_td)]
    ]
    tech_table = Table(tech_rows, colWidths=[105, 80, 347])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(tech_rows)):
        if i % 2 == 0:
            tech_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(tech_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated exact 2-page Easy-Terms PDF: {filename}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "MarketTide_RAGBot_Architecture_Easy_Terms_2Pager.pdf"
    generate_pdf(out)

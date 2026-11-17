"""
build_query_lifecycle_pdf.py - Compiles the 2-page technical guide on query lifecycle,
vector DB, chunking, RRF, and card importance scoring.
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
            self.drawString(40, 755, "MarketTide RAGBot — Backend Query Lifecycle, Retrieval & Scoring Architecture")
            self.drawRightString(572, 755, "Deep-Dive Technical Specification")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 38, 572, 38)
        self.drawString(40, 26, "MarketTide RAG Intelligence Engine · National Stock Exchange (NSE) Regulatory Disclosures")
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
        "DocTitle", fontName="Helvetica-Bold", fontSize=15.5, leading=18.5, textColor=PRIMARY, spaceAfter=2
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle", fontName="Helvetica", fontSize=8.8, leading=11.5, textColor=SECONDARY, spaceAfter=5
    )
    style_h1 = ParagraphStyle(
        "SectionH1", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=PRIMARY, spaceBefore=4, spaceAfter=2.5, keepWithNext=True
    )
    style_body = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=7.3, leading=9.8, textColor=TEXT_DARK, spaceAfter=2
    )
    style_callout = ParagraphStyle(
        "Callout", fontName="Helvetica", fontSize=7.2, leading=9.4, textColor=TEXT_DARK
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
    # PAGE 1: QUERY LIFECYCLE, VECTOR DB, CHUNKING
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Query Lifecycle & Retrieval Architecture", style_title))
    story.append(Paragraph("Technical Guide to Query Processing, Vector Storage, Structured Chunking & RRF Math", style_subtitle))

    meta_table = Table([
        [
            Paragraph("<b>Topic:</b> Backend Query Pipeline, In-Memory Vectors & Chunking<br/>"
                      "<b>Corpus:</b> 2,766 NSE Disclosures across 1,716 Listed Equities<br/>"
                      "<b>Architecture:</b> Hybrid BM25 + Dot-Product Vector RAG with RRF", style_callout),
            Paragraph("<b>Core Engineering Team:</b><br/>"
                      "• <b>Shreyansh Shailesh</b> &nbsp;&nbsp;&nbsp; • <b>Shubh Tanna</b><br/>"
                      "• <b>David Jeremie Anand</b> &nbsp; • <b>Shaurya Gupta</b>", style_callout)
        ]
    ], colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))

    # SECTION 1: QUERY LIFECYCLE
    story.append(Paragraph("1. What Happens in the Backend When a User Enters a Query", style_h1))
    story.append(Paragraph(
        "When a user types a query or corporate ticker into the search dock, the backend executes an automated 7-stage assembly pipeline:<br/>"
        "• <b>1. Pre-Check Gate (0 ms):</b> Sanitizes input and intercepts conversational greetings or insults (<i>'are you dumb?'</i>) before touching the search index. Enforces word boundaries (<code>\\b</code>) to stop substring errors (e.g. 'am' in Dhampur). Identifies foreign non-NSE tickers (Apple, Tesla).<br/>"
        "• <b>2. Conglomerate Router:</b> If a conglomerate family is detected (e.g. <i>'Tata'</i>), expands into all operating subsidiaries: <b>TMPV, TATAPOWER, TATASTEEL, and TCS</b>, pulling 25 filings together.<br/>"
        "• <b>3. Parallel Search:</b> Executes dense semantic vector dot-product and sparse BM25 term frequency in parallel across 2,766 filings.<br/>"
        "• <b>4. Reciprocal Rank Fusion (RRF):</b> Merges both ranked lists using rank reciprocal weighting (<i>k = 60</i>).<br/>"
        "• <b>5. Relevance Scoring:</b> Awards exact ticker matches (+80), company name matches (+40), and headline matches (+25).<br/>"
        "• <b>6. Context Assembly:</b> Compiles top-5 verified disclosures under strict SEBI Regulation 30 context boundaries.<br/>"
        "• <b>7. LLM Synthesis & UI Delivery:</b> Groq Cloud LPU runs <b>Llama-3.3 70B</b> in &lt; 650 ms, streaming the executive briefing and official signed NSE PDF links.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 2: VECTOR DATABASE
    story.append(Paragraph("2. Vector Database: Why an In-Memory Memory-Mapped Vector Store?", style_h1))
    vdb_rows = [
        [Paragraph("<b>Vector Storage Dimension</b>", style_th), Paragraph("<b>Engineering Rationale & Production Performance</b>", style_th)],
        [
            Paragraph("<b>Vector Engine Used</b>", style_td_bold),
            Paragraph("<b>In-memory, memory-mapped NumPy vector store (<code>embeddings.npy</code>)</b> with exact cosine dot-product matrix multiplication (<code>np.dot</code>).", style_td)
        ],
        [
            Paragraph("<b>Why Not Pinecone / ChromaDB?</b>", style_td_bold),
            Paragraph("External cloud vector databases introduce 50–150 ms of network round-trip HTTP overhead per query. Our 2,766-filing embedding matrix is only <b>4.24 MB</b>, enabling instantaneous in-RAM matrix multiplication in just <b>68 milliseconds</b>.", style_td)
        ],
        [
            Paragraph("<b>Memory Footprint & Speed</b>", style_td_bold),
            Paragraph("384-dimensional normalized dense vectors produced by <code>all-MiniLM-L6-v2</code>. Vector search over the entire corpus executes in RAM at &gt; 40,000 document comparisons per second.", style_td)
        ],
        [
            Paragraph("<b>Deterministic Cache Packaging</b>", style_td_bold),
            Paragraph("The entire binary cache (<code>embeddings.npy</code> 4.2MB, <code>bm25.pkl</code> 1.2MB, <code>metadata.pkl</code> 3.6MB) is pre-packaged (9.07 MB total), booting the app in &lt; 2 seconds with zero cloud dependencies.", style_td)
        ]
    ]
    vdb_table = Table(vdb_rows, colWidths=[135, 397])
    vdb_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(vdb_rows)):
        if i % 2 == 0:
            vdb_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(vdb_table)
    story.append(Spacer(1, 3))

    # SECTION 3: CHUNKING STRATEGY
    story.append(Paragraph("3. Chunking Strategy: Semantic Schema-Aware Structured Chunking", style_h1))
    story.append(Paragraph(
        "<b>Why Naive Token Chunking Fails:</b> Arbitrary fixed-character splitting (e.g. every 500 characters) cuts corporate names, dates, and financial metrics in half (e.g. <i>'Consolidated Profit rose 24.'</i> in chunk 1 and <i>'5% to ₹1,420 Crores'</i> in chunk 2), causing severe hallucinations.<br/>"
        "<b>Our Structured Solution:</b> We implement <b>Document-Level Regulatory Chunking</b>. Every filing is preserved as an atomic, self-contained semantic record enriched with structured metadata fields:<br/>"
        "<code>Chunk = Date: {date} {time} | Exchange: NSE | Company: {name} ({ticker}) | Category: {cat} | Tag: {tag} | Headline: {head} | Details: {desc}</code><br/>"
        "This guarantees that every retrieved chunk retains its full factual context, legal company identity, and filing timestamp.",
        style_body
    ))

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: RRF, SCORING LOGIC, CARD SCORES, UI
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Matching Math, Scoring & UI Dossiers", style_title))
    story.append(Paragraph("Reciprocal Rank Fusion, Query Score vs. Card Importance Rating, and Result Layout", style_subtitle))
    story.append(Spacer(1, 3))

    # SECTION 4: RECIPROCAL RANK FUSION (RRF)
    story.append(Paragraph("4. Reciprocal Rank Fusion (RRF): How We Merge Search Rankings", style_h1))
    story.append(Paragraph(
        "Vector search produces cosine similarity scores between [-1.0, 1.0], while BM25 produces unbounded positive scores [0, &infin;). Directly adding raw scores causes mathematical skew. We use <b>Reciprocal Rank Fusion (RRF)</b> to merge candidate lists based on rank position rather than raw score:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>RRF Score(d) = &Sigma; w / (60 + rank_m(d))</b><br/>"
        "The constant <i>k = 60</i> prevents a filing ranked #1 by BM25 from unfairly overshadowing a filing ranked #2 on both BM25 and Vector search. Filings supported by both semantic meaning and exact keyword spelling rise to the Top-5.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 5: SCORING COMPARISON TABLE
    story.append(Paragraph("5. Scoring Breakdown: Query Relevance Score vs. Card Importance Score", style_h1))
    story.append(Paragraph(
        "There are <b>two distinct scores</b> in the system. The internal score ranks results; the card score indicates regulatory impact:",
        style_body
    ))

    score_rows = [
        [
            Paragraph("<b>Internal Query Relevance Score (Ranking)</b>", style_th),
            Paragraph("<b>Card Importance Score (Displayed: e.g. 'Score: 68')</b>", style_th)
        ],
        [
            Paragraph("• <b>Exact Ticker Match:</b> <b>+80 points</b> (e.g. query matches <code>TATAPOWER</code>).<br/>"
                      "• <b>Company Name Match:</b> <b>+40 points</b> (matching tokens in corporate name).<br/>"
                      "• <b>Headline Token Match:</b> <b>+25 points</b>.<br/>"
                      "• <b>Description Body Match:</b> <b>+12 points</b>.<br/>"
                      "• <b>Regulatory Multiplier:</b> <code>Match Points + (Importance Score &times; 0.15)</code>.<br/>"
                      "• <b>Relevance Gate:</b> Filings scoring &lt; 35 are discarded. If none pass, query is rejected.", style_td),
            Paragraph("• <b>Material Financials (65–80+):</b> Board Meeting Financial Outcomes, Audited/Unaudited Q2 results, Press Releases with full earnings, Demergers, Share Buybacks, and Rights Issues.<br/>"
                      "• <b>Corporate Developments (55–64):</b> Investor Concall transcripts, Capital Additions, Executive KMP Appointments, and Joint Venture agreements.<br/>"
                      "• <b>Market Alerts (45–54):</b> Official Exchange volume surge ('Spurt in Volume') clarifications.<br/>"
                      "• <b>Routine Filings (&lt; 45):</b> Compliance receipts; filtered out prior to search.", style_td)
        ]
    ]
    score_table = Table(score_rows, colWidths=[266, 266])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 3))

    # SECTION 6: HOW RESULTS ARE DISPLAYED
    story.append(Paragraph("6. How Results Are Shown on the Screen", style_h1))
    ui_rows = [
        [Paragraph("<b>Result Panel Component</b>", style_th), Paragraph("<b>Display Elements, Telemetry & User Interactions</b>", style_th)],
        [
            Paragraph("<b>1. Executive Synthesis Card</b>", style_td_bold),
            Paragraph("AI brief generated by Groq Llama-3.3 70B in &lt; 650 ms, stating total disclosures located, involved subsidiaries, and average institutional importance rating (e.g. <i>Avg Score: 59/100</i>).", style_td)
        ],
        [
            Paragraph("<b>2. Verified Filing Dossiers</b>", style_td_bold),
            Paragraph("Cards displaying Stock Ticker Badge, Legal Name, Timestamp, Category Tag (Results, Buyback, Spurt in Volume), Importance Score (e.g. <b>Score: 68</b>), and clickable link to the <b>official signed NSE PDF filing</b>.", style_td)
        ],
        [
            Paragraph("<b>3. Step Execution Timeline</b>", style_td_bold),
            Paragraph("Shows live telemetry for each pipeline stage: <i>Pre-Check Gate (0ms) &rarr; In-Memory Vector Search (68ms) &rarr; RRF Ranking (2ms) &rarr; Groq LLM Synthesis (510ms)</i>.", style_td)
        ]
    ]
    ui_table = Table(ui_rows, colWidths=[140, 392])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
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

    # SECTION 7: APPLICATIONS
    story.append(Paragraph("7. Depicted Applications in Institutional Workflows", style_h1))
    app_rows = [
        [
            Paragraph("<b>Multi-Hop Conglomerate Risk Tracking:</b> Resolves complex parent-subsidiary structures across Tata Group, Adani Group, and Reliance Industries into unified board briefings.", style_td),
            Paragraph("<b>M&A & Buyback Compliance Audits:</b> Isolates high-impact capital allocation events (SEBI Reg 30/33/42) with immediate audit links to company secretary signed filings.", style_td)
        ],
        [
            Paragraph("<b>Intraday Volume Spike Clarification:</b> Surfaces statutory 'Spurt in Volume' intimations to distinguish genuine material corporate developments from speculative market rumors.", style_td),
            Paragraph("<b>Zero-Liability Financial Research:</b> Eliminates LLM hallucination liabilities by enforcing strict citation grounding against the 2,766 verified NSE filings.", style_td)
        ]
    ]
    app_table = Table(app_rows, colWidths=[266, 266])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(app_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated exact 2-page Query Lifecycle PDF: {filename}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "MarketTide_RAGBot_Query_Lifecycle_and_Scoring_2Pager.pdf"
    generate_pdf(out)

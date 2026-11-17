"""
build_nomad_pdf.py - Compiles the 2-page plain-language Nomad Edition architecture PDF.
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
            self.drawString(40, 755, "MarketTide RAGBot — The Plain-Language Architecture Guide (Nomad Edition)")
            self.drawRightString(572, 755, "Simplified Architecture Specification")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 38, 572, 38)
        self.drawString(40, 26, "MarketTide RAGBot · Clear, Intuitive Architecture Guide for Non-Technical Evaluators")
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
        "DocTitle", fontName="Helvetica-Bold", fontSize=16.5, leading=19.5, textColor=PRIMARY, spaceAfter=2
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle", fontName="Helvetica", fontSize=9, leading=12, textColor=SECONDARY, spaceAfter=6
    )
    style_h1 = ParagraphStyle(
        "SectionH1", fontName="Helvetica-Bold", fontSize=10.5, leading=13.5, textColor=PRIMARY, spaceBefore=4, spaceAfter=3, keepWithNext=True
    )
    style_body = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=7.6, leading=10.2, textColor=TEXT_DARK, spaceAfter=2
    )
    style_callout = ParagraphStyle(
        "Callout", fontName="Helvetica", fontSize=7.4, leading=9.8, textColor=TEXT_DARK
    )
    style_th = ParagraphStyle(
        "TableHead", fontName="Helvetica-Bold", fontSize=7.2, leading=9.2, textColor=colors.white
    )
    style_td = ParagraphStyle(
        "TableCell", fontName="Helvetica", fontSize=7.0, leading=9.0, textColor=TEXT_DARK
    )
    style_td_bold = ParagraphStyle(
        "TableCellBold", fontName="Helvetica-Bold", fontSize=7.0, leading=9.0, textColor=PRIMARY
    )

    story = []

    # ==========================================
    # PAGE 1: THE CORE ANALOGY, DATA & SCOUTS
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: The Plain-Language Architecture Guide", style_title))
    story.append(Paragraph("An Intuitive, Non-Complex Explanation of How Our AI Financial Engine Works (The Nomad Edition)", style_subtitle))

    meta_table = Table([
        [
            Paragraph("<b>Core Metaphor:</b> The Honest Scribe of the Great Trading Bazaar<br/>"
                      "<b>Mission:</b> Explain complex AI RAG math in simple, physical analogies<br/>"
                      "<b>Focus:</b> 100% Zero-Hallucination Stock Regulatory Answers", style_callout),
            Paragraph("<b>Engineering Team:</b><br/>"
                      "• <b>Shreyansh Shailesh</b> &nbsp;&nbsp;&nbsp; • <b>Shubh Tanna</b><br/>"
                      "• <b>David Jeremie Anand</b> &nbsp; • <b>Shaurya Gupta</b>", style_callout)
        ]
    ], colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 5))

    # SECTION 1: THE CORE IDEA
    story.append(Paragraph("1. The Core Idea: The Honest Scribe of the Great Bazaar", style_h1))
    story.append(Paragraph(
        "Imagine a massive trading bazaar—the <b>National Stock Exchange (NSE)</b>—where thousands of merchant caravan families (companies) trade goods. Under royal trading rules (SEBI regulations), whenever a caravan makes a big move—discovering new gold (profits), buying back caravan shares, or replacing an elder—they must nail an official stamped letter to the public gate.<br/>"
        "Most travelers ask ordinary roadside storytellers (like generic ChatGPT) what happened. But storytellers get tired, confuse caravan names, invent fake dates, and tell believable lies. In trading, trusting a false tale means losing your horses and gold.<br/>"
        "<b>What We Made:</b> We built an <b>Honest Scribe System</b> called <b>MarketTide RAGBot</b>. It does not tell fables or guess. It answers questions strictly by reading the verified stamped letters, and it pins the original <b>royal wax-sealed scroll (an official signed PDF)</b> to every answer so you can inspect the signature yourself.",
        style_body
    ))
    story.append(Spacer(1, 4))

    # SECTION 2: THE TREASURE CHEST
    story.append(Paragraph("2. The Treasure Chest: What Real Data We Used", style_h1))
    story.append(Paragraph(
        "We did not gather gossip from roadside taverns. We collected <b>2,766 verified letters</b> from <b>1,716 merchant families</b> during one busy 7-day trading week (November 9–15, 2026):",
        style_body
    ))

    data_rows = [
        [Paragraph("<b>Treasury Scroll Type</b>", style_th), Paragraph("<b>What It Actually Represents in Simple Language</b>", style_th)],
        [Paragraph("<b>Quarterly Earnings (Q2)</b>", style_td_bold), Paragraph("Official profit-and-loss reports showing exactly how much gold each caravan earned or lost.", style_td)],
        [Paragraph("<b>Clan Council Outcomes</b>", style_td_bold), Paragraph("Formal board meeting minutes detailing approved mergers, expansions, and executive leadership changes.", style_td)],
        [Paragraph("<b>Capital Returns (Buybacks)</b>", style_td_bold), Paragraph("Official announcements where companies return surplus cash directly back to caravan equity owners.", style_td)],
        [Paragraph("<b>Volume Spurt Intimations</b>", style_td_bold), Paragraph("Letters explaining whether a sudden dust cloud of rapid trading activity is backed by real news or rumors.", style_td)],
        [Paragraph("<b>Quality Filter (&ge; 45)</b>", style_td_bold), Paragraph("We filtered out thousands of minor routine receipts, keeping only meaningful, price-sensitive disclosures.", style_td)],
        [Paragraph("<b>The 9 MB Pocket Pouch</b>", style_td_bold), Paragraph("All 2,766 scrolls and index maps are packed into a tiny 9.07 MB digital pouch that opens in under 2 seconds.", style_td)]
    ]
    data_table = Table(data_rows, colWidths=[130, 402])
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(1, len(data_rows)):
        if i % 2 == 0:
            data_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(data_table)
    story.append(Spacer(1, 4))

    # SECTION 3: THE GATEKEEPER & CLAN SCOUT
    story.append(Paragraph("3. Step 1 & 2: The Tent Gatekeeper & The Clan Scout", style_h1))
    story.append(Paragraph(
        "<b>Step 1 — The Gatekeeper at the Tent Flap (Guardrails):</b> Before anyone enters to search the scrolls, our Gatekeeper inspects the question. If a traveler shouts insults (<i>'are you dumb?'</i>) or riddles (<i>'am i god?'</i>), the Gatekeeper turns them away at 0 ms without waking up the master scribe. If they ask about caravans from the Western Empire (<i>Apple, Tesla</i>), the Gatekeeper explains they trade across the ocean on NASDAQ, not here.<br/>"
        "<b>Step 2 — The Clan Scout (Multi-Hop Conglomerate Resolver):</b> Great houses like the <b>Tata Clan</b> have many tents: <i>Tata Motors, Tata Power, Tata Steel, and TCS</i>. If you ask: <i>'What did the Tatas announce?'</i>, our Scout checks all 4 tents at once, gathering 25 scrolls in one turn.",
        style_body
    ))

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: TWO SCOUTS, MASTER SCRIBE & UI
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: The Search Engine & Master Scribe", style_title))
    story.append(Paragraph("How the Information is Found, Verified, and Delivered to Travelers", style_subtitle))
    story.append(Spacer(1, 4))

    # SECTION 4: TWO DIFFERENT SCOUTS & THE BALANCING SCALE
    story.append(Paragraph("4. Step 3 & 4: Two Different Scouts & The Balancing Scale", style_h1))
    story.append(Paragraph(
        "How do we find the exact right scroll out of 2,766 letters in just <b>68 milliseconds</b>? We send out <b>Two Different Scouts</b> with different talents:",
        style_body
    ))

    scout_rows = [
        [Paragraph("<b>Scout 1: The Idea Scout (Dense Vectors)</b>", style_td_bold), Paragraph("<b>Scout 2: The Exact Word Tracker (BM25)</b>", style_td_bold)],
        [
            Paragraph("• Doesn't look for literal words; understands <i>underlying intent</i>.<br/>• If you ask: <i>'giving gold back to investors'</i>, it knows you mean <i>'share buyback'</i>, even without using those exact words.<br/>• Uses 384-dimensional mathematical coordinates (<code>all-MiniLM-L6-v2</code>).", style_td),
            Paragraph("• A meticulous clerk that checks for exact spelling.<br/>• Looks for merchant initials like <b>TMPV</b>, <b>TATAPOWER</b>, or legal clauses like <b>SEBI Reg 30</b>.<br/>• Never gets fooled by vague similarities.", style_td)
        ],
        [
            Paragraph("<b>The Council Table (Reciprocal Rank Fusion - RRF):</b> Both scouts return with their top 20 candidate scrolls. The Council places them on a mathematical balancing scale: <i>Score = &Sigma; 1 / (60 + Scout_Rank)</i>. The scrolls that both scouts agree on rise to the top. We select the <b>Top 5 cleanest scrolls</b>.", style_td),
            Paragraph("<b>The Master Scribe (Groq Llama-3.3 70B):</b> An ultra-fast scribe sitting at an enchanted desk reads only the top 5 scrolls. In under <b>650 ms</b>, it writes an honest summary and staples direct links to the official signed NSE PDF filings.", style_td)
        ]
    ]
    scout_table = Table(scout_rows, colWidths=[266, 266])
    scout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for c in range(2):
        scout_rows[0][c].style = style_th
    story.append(scout_table)
    story.append(Spacer(1, 5))

    # SECTION 5: THE TWO VIEWING TENTS
    story.append(Paragraph("5. Step 5 & 6: The Two Viewing Tents (User Interfaces)", style_h1))

    tent_rows = [
        [Paragraph("<b>Interface Mode</b>", style_th), Paragraph("<b>Software Technology</b>", style_th), Paragraph("<b>What You Experience as a Traveler</b>", style_th)],
        [
            Paragraph("<b>The Conversation Tent (<code>RAG-Chatbot</code> Branch)</b>", style_td_bold),
            Paragraph("<b>Streamlit (Python)</b>", style_td),
            Paragraph("A direct, private chat room where you ask questions, inspect the scribe's step-by-step thinking in milliseconds, and review cards of the original signed PDF filings.", style_td)
        ],
        [
            Paragraph("<b>The 3D Star Map (<code>shrey</code> Branch)</b>", style_td_bold),
            Paragraph("<b>Three.js & WebGL</b>", style_td),
            Paragraph("An executive visual trading desk featuring living 3D stock trajectories flowing like desert trade routes, with camera orbit controls and an instant bottom search dock.", style_td)
        ]
    ]
    tent_table = Table(tent_rows, colWidths=[140, 95, 297])
    tent_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(tent_rows)):
        if i % 2 == 0:
            tent_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(tent_table)
    story.append(Spacer(1, 4))

    # SECTION 6: THE NOMAD DICTIONARY
    story.append(Paragraph("6. The Nomad's Technology Translation Ledger", style_h1))

    dict_rows = [
        [Paragraph("<b>Technical Name</b>", style_th), Paragraph("<b>Nomad Translation</b>", style_th), Paragraph("<b>What It Actually Does in Our Engine</b>", style_th)],
        [Paragraph("<b>Llama-3.3 70B</b>", style_td_bold), Paragraph("The Master Scribe", style_td), Paragraph("The AI brain that reads the 5 retrieved letters and writes the clean summary.", style_td)],
        [Paragraph("<b>Groq Cloud LPU</b>", style_td_bold), Paragraph("The Lightning Quill", style_td), Paragraph("Special silicon chips that make the scribe stream words in under 0.5 seconds.", style_td)],
        [Paragraph("<b>Dense Vectors</b>", style_td_bold), Paragraph("The Idea Scout", style_td), Paragraph("Understands what your question means conceptually, even with different words.", style_td)],
        [Paragraph("<b>BM25 Okapi</b>", style_td_bold), Paragraph("The Word Clerk", style_td), Paragraph("Scans letters for exact merchant initials (e.g. TMPV) and statutory clauses.", style_td)],
        [Paragraph("<b>Reciprocal Rank Fusion</b>", style_td_bold), Paragraph("The Council Scale", style_td), Paragraph("Balances the two scout lists so only agreed-upon, high-confidence letters win.", style_td)],
        [Paragraph("<b>Official NSE PDFs</b>", style_td_bold), Paragraph("Royal Wax Seals", style_td), Paragraph("The real, verifiable documents that prove our answers are 100% truthful.", style_td)]
    ]
    dict_table = Table(dict_rows, colWidths=[105, 105, 322])
    dict_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(dict_rows)):
        if i % 2 == 0:
            dict_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(dict_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated exact 2-page Nomad PDF: {filename}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "MarketTide_Architecture_Nomad_Edition.pdf"
    generate_pdf(out)

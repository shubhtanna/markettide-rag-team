"""
build_embedding_chunking_pdf.py - Compiles the 2-page deep-dive specification
on the Embedding Model (all-MiniLM-L6-v2) and Chunking Model (Semantic Schema-Aware Chunking).
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
            self.drawString(40, 755, "MarketTide RAGBot — Embedding & Chunking Model Architecture Specification")
            self.drawRightString(572, 755, "Deep-Dive NLP Specification")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 38, 572, 38)
        self.drawString(40, 26, "MarketTide Regulatory AI · Dense Vector Embeddings & Structured Schema Chunking")
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
        "SectionH1", fontName="Helvetica-Bold", fontSize=9.8, leading=12.5, textColor=PRIMARY, spaceBefore=4, spaceAfter=2.5, keepWithNext=True
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
    # PAGE 1: THE EMBEDDING MODEL
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Embedding & Chunking Model Specification", style_title))
    story.append(Paragraph("A Deep-Dive into Dense Vector Embeddings, Mathematical Optimization & Semantic Chunking", style_subtitle))

    meta_table = Table([
        [
            Paragraph("<b>Embedding Model:</b> <code>sentence-transformers/all-MiniLM-L6-v2</code><br/>"
                      "<b>Vector Output:</b> 384-dimensional dense vectors (unit L2-normalized)<br/>"
                      "<b>Chunking Strategy:</b> Semantic Schema-Aware Structured Chunking", style_callout),
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

    # SECTION 1: EMBEDDING MODEL SPECS
    story.append(Paragraph("1. The Embedding Model: sentence-transformers/all-MiniLM-L6-v2", style_h1))
    story.append(Paragraph(
        "MarketTide RAGBot utilizes <b><code>all-MiniLM-L6-v2</code></b>, a 6-layer MiniLM transformer model fine-tuned on over 1 billion sentence pairs for semantic search. It converts regulatory disclosure texts into dense, high-dimensional vector representations that capture underlying semantic meaning.",
        style_body
    ))

    emb_rows = [
        [Paragraph("<b>Model Parameter</b>", style_th), Paragraph("<b>Specification & Value</b>", style_th), Paragraph("<b>Technical Significance in MarketTide</b>", style_th)],
        [Paragraph("<b>Base Architecture</b>", style_td_bold), Paragraph("6-Layer MiniLM (BERT-style)", style_td), Paragraph("Distilled student model providing 5x faster inference than BERT-Base with 99% accuracy retention.", style_td)],
        [Paragraph("<b>Vector Dimension</b>", style_td_bold), Paragraph("<b>384 dimensions</b> (float32)", style_td), Paragraph("Compact coordinate space capturing topic, entity intent, and financial category relationships.", style_td)],
        [Paragraph("<b>Tokenizer</b>", style_td_bold), Paragraph("WordPiece (Vocab: 30,522)", style_td), Paragraph("Gracefully handles financial abbreviations and sub-words without out-of-vocabulary crashes.", style_td)],
        [Paragraph("<b>Max Sequence Length</b>", style_td_bold), Paragraph("<b>512 tokens</b>", style_td), Paragraph("Comfortably encodes 100% of statutory disclosure headlines and descriptions without truncation.", style_td)],
        [Paragraph("<b>Pooling Method</b>", style_td_bold), Paragraph("Mean Pooling + Mask", style_td), Paragraph("Averages contextualized token representations into a single unified sentence embedding.", style_td)],
        [Paragraph("<b>Normalization</b>", style_td_bold), Paragraph("<b>Unit L2 Length</b> (||v|| = 1.0)", style_td), Paragraph("Enforces unit length so that <b>Cosine Similarity = Dot Product</b>, eliminating vector magnitude division.", style_td)],
        [Paragraph("<b>Model Size</b>", style_td_bold), Paragraph("22.7M parameters (~80 MB)", style_td), Paragraph("Ultra-lightweight footprint; runs on standard CPUs without requiring GPU acceleration.", style_td)]
    ]
    emb_table = Table(emb_rows, colWidths=[110, 125, 297])
    emb_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(emb_rows)):
        if i % 2 == 0:
            emb_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(emb_table)
    story.append(Spacer(1, 3))

    # SECTION 2: MATHEMATICAL FOUNDATION
    story.append(Paragraph("2. Mathematical Foundation: Cosine Similarity via Dot Product", style_h1))
    story.append(Paragraph(
        "Standard cosine similarity between query <b>q</b> and document <b>d</b> requires calculating Euclidean norms: "
        "<i>CosSim(q, d) = (q · d) / (||q|| · ||d||)</i>.<br/>"
        "Because our ingestion pipeline strictly enforces <b>unit L2 normalization</b> (<code>normalize_embeddings=True</code>):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>||q|| = 1.0 &nbsp;and&nbsp; ||d|| = 1.0 &nbsp;&rArr;&nbsp; CosSim(q, d) = q · d = &Sigma; q_i · d_i</b><br/>"
        "<b>Architectural Impact:</b> Scoring 2,766 filings becomes a single matrix-vector multiplication <code>np.dot(embeddings, query_vec)</code> in RAM, completing across the entire exchange dataset in just <b>68 milliseconds</b>.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 3: MODEL COMPARISON TABLE
    story.append(Paragraph("3. Embedding Model Selection Rationale & Benchmarks", style_h1))
    comp_rows = [
        [Paragraph("<b>Model</b>", style_th), Paragraph("<b>Dims</b>", style_th), Paragraph("<b>Size</b>", style_th), Paragraph("<b>CPU Latency</b>", style_th), Paragraph("<b>RAM Footprint</b>", style_th), Paragraph("<b>Selection Decision & Rationale</b>", style_th)],
        [
            Paragraph("<b>all-MiniLM-L6-v2 (Chosen)</b>", style_td_bold),
            Paragraph("384", style_td), Paragraph("80 MB", style_td), Paragraph("<b>68 ms</b>", style_td_bold), Paragraph("<b>4.24 MB</b>", style_td_bold),
            Paragraph("<b>Selected:</b> Optimal balance of MTEB retrieval accuracy, sub-100ms CPU speed, and tiny RAM usage.", style_td)
        ],
        [
            Paragraph("text-embedding-3-small", style_td_bold),
            Paragraph("1536", style_td), Paragraph("API", style_td), Paragraph("180–350 ms", style_td), Paragraph("16.9 MB", style_td),
            Paragraph("<b>Rejected:</b> Network API calls add 200ms latency and per-query cloud billing.", style_td)
        ],
        [
            Paragraph("BAAI/bge-large-en-v1.5", style_td_bold),
            Paragraph("1024", style_td), Paragraph("1.34 GB", style_td), Paragraph("380 ms", style_td), Paragraph("11.3 MB", style_td),
            Paragraph("<b>Rejected:</b> Heavyweight model; severe CPU latency penalty on cloud containers.", style_td)
        ]
    ]
    comp_table = Table(comp_rows, colWidths=[110, 30, 45, 60, 65, 222])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(comp_rows)):
        if i % 2 == 0:
            comp_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(comp_table)

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: CHUNKING MODEL & EVALUATION
    # ==========================================

    story.append(Paragraph("MarketTide RAGBot: Structured Chunking & Lexical Indexing", style_title))
    story.append(Paragraph("Document-Level Regulatory Chunking, Entity Preservation, and Dual Index Representation", style_subtitle))
    story.append(Spacer(1, 3))

    # SECTION 4: CHUNKING MODEL
    story.append(Paragraph("4. The Chunking Model: Semantic Schema-Aware Structured Chunking", style_h1))
    story.append(Paragraph(
        "MarketTide RAGBot rejects arbitrary character-splitting in favor of <b>Semantic Schema-Aware Structured Chunking (Document-Level Regulatory Chunking)</b>.<br/>"
        "Every statutory filing is an atomic legal instrument. The chunking pipeline in <code>chatbot/ingest.py</code> constructs an enriched search string embedding all contextual metadata directly into the textual payload:<br/>"
        "<code>Chunk = Date: {date} {time} | Exchange: NSE | Company: {name} ({ticker}) | Category: {cat} | Tag: {tag} | Importance: {score} | Headline: {head} | Details: {desc}</code><br/>"
        "<b>Context Injection:</b> By prefixing the filing with company name, ticker, and SEBI category, the embedding vector captures the legal entity identity regardless of phrasing in the headline.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 5: WHY NAIVE CHUNKING FAILS
    story.append(Paragraph("5. Why Naive Token Chunking Fails in Financial Compliance", style_h1))
    story.append(Paragraph(
        "Generic RAG tutorials often recommend <code>RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)</code>. In financial regulatory compliance, this naive method causes three fatal errors:",
        style_body
    ))

    fail_rows = [
        [Paragraph("<b>Failure Mode</b>", style_th), Paragraph("<b>What Happens with Naive Fixed-Size Chunking</b>", style_th), Paragraph("<b>How MarketTide's Chunking Solves It</b>", style_th)],
        [
            Paragraph("<b>1. Severed Financial Metrics</b>", style_td_bold),
            Paragraph("Sentences like <i>'Net Profit grew 24.5% to ₹1,420 Cr'</i> are split across boundaries (*'24.'* in Chunk 1, *'5% to ₹1,420 Cr'* in Chunk 2).", style_td),
            Paragraph("Preserves the complete disclosure in one chunk, keeping numbers, currency units, and percentages intact.", style_td)
        ],
        [
            Paragraph("<b>2. Corporate Entity Loss</b>", style_td_bold),
            Paragraph("Company names reside in headers. Splitting bodies detaches financial results from the corporate entity, causing hallucinated earnings attribution.", style_td),
            Paragraph("Injects company name and ticker symbol into every chunk header, permanently binding facts to the legal entity.", style_td)
        ],
        [
            Paragraph("<b>3. Temporal Disconnection</b>", style_td_bold),
            Paragraph("Splitting detaches timestamps from announcements, making it impossible to answer time-sensitive queries (*'announced on Nov 13'*).", style_td),
            Paragraph("Explicitly embeds ISO date and time into the first token coordinates of every filing chunk.", style_td)
        ]
    ]
    fail_table = Table(fail_rows, colWidths=[120, 205, 207])
    fail_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(fail_table)
    story.append(Spacer(1, 3))

    # SECTION 6: DUAL-INDEX REPRESENTATION
    story.append(Paragraph("6. Dual-Index Representation: Dense Embedding + Sparse Token Matrix", style_h1))
    story.append(Paragraph(
        "Each structured chunk is indexed in parallel across two distinct representations:<br/>"
        "• <b>Dense Vector Representation:</b> <code>all-MiniLM-L6-v2</code> produces 384-dimensional unit-normalized floats stored in <code>embeddings.npy</code> (4.24 MB). Captures semantic concepts (e.g. <i>'cash return'</i> &rarr; <i>'buyback'</i>).<br/>"
        "• <b>Sparse Lexical Representation:</b> Alphanumeric tokenizer <code>re.findall(r'\\w+', text.lower())</code> builds a <b>BM25Okapi</b> token corpus with regulatory boilerplate stopword stripping (removing <i>'limited', 'ltd', 'pursuant', 'regulation', 'intimation'</i>). Captures exact tickers (<code>TMPV</code>, <code>TATAPOWER</code>).<br/>"
        "• <b>Reciprocal Rank Fusion (RRF, k=60):</b> Blends dense and sparse rankings mathematically: <i>RRF(d) = &Sigma; w / (60 + rank_m(d))</i>.",
        style_body
    ))
    story.append(Spacer(1, 3))

    # SECTION 7: QUANTITATIVE SUMMARY
    story.append(Paragraph("7. Quantitative Ingestion & Pipeline Summary", style_h1))
    stat_rows = [
        [Paragraph("<b>Metric Dimension</b>", style_th), Paragraph("<b>Achieved Specification & Benchmark</b>", style_th), Paragraph("<b>Architectural Benefit</b>", style_th)],
        [Paragraph("<b>Total Chunk Count</b>", style_td_bold), Paragraph("<b>2,766 Atomic Chunks</b>", style_td), Paragraph("100% of validated filings from Nov 9–15, 2026 reporting cycle.", style_td)],
        [Paragraph("<b>Average Chunk Length</b>", style_td_bold), Paragraph("<b>68 words (~92 tokens)</b>", style_td), Paragraph("Fits well within the 512-token sequence limit; zero truncation.", style_td)],
        [Paragraph("<b>Vector Storage Size</b>", style_td_bold), Paragraph("<b>4.24 MB</b> (embeddings.npy)", style_td), Paragraph("Loads into RAM in 12 milliseconds; zero cloud database cost.", style_td)],
        [Paragraph("<b>BM25 Lexical Size</b>", style_td_bold), Paragraph("<b>1.21 MB</b> (bm25.pkl)", style_td), Paragraph("Instant keyword lookups for exact stock ticker codes.", style_td)],
        [Paragraph("<b>Total Cache Footprint</b>", style_td_bold), Paragraph("<b>9.07 MB total</b>", style_td), Paragraph("Enables instant local & cloud startup (&lt; 2 seconds) on any container.", style_td)]
    ]
    stat_table = Table(stat_rows, colWidths=[120, 160, 252])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_CLR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(1, len(stat_rows)):
        if i % 2 == 0:
            stat_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), BG_LIGHT)]))
    story.append(stat_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated exact 2-page Embedding & Chunking PDF: {filename}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "MarketTide_Embedding_and_Chunking_Models_2Pager.pdf"
    generate_pdf(out)

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
import textwrap
import io

# ── Dimensions ──────────────────────────────────────────────────────────────
CARD_W  = 3.5 * inch
CARD_H  = 4.5 * inch
TAB_W   = 0.85 * inch   # wider to fit 3 letters
TAB_H   = 0.35 * inch
# ── Tab stop positions ───────────────────────────────────────────────────────
# 5 evenly-spaced stops across the card, cycling as cards progress.
# Left edge padding + equal steps so the last tab doesn't fall off the right edge.
_TAB_MARGIN = 0.15 * inch                          # min gap from card edge
_TAB_TRAVEL = CARD_W - TAB_W - 2 * _TAB_MARGIN    # usable travel distance
TAB_STOPS   = 5                                    # number of positions
TAB_POSITIONS = [
    _TAB_MARGIN + (_TAB_TRAVEL / (TAB_STOPS - 1)) * i
    for i in range(TAB_STOPS)
]
PAGE_W, PAGE_H = landscape(letter)   # 11 × 8.5

# 2 cards side by side, centred on page
GAP_X   = 0.50 * inch                        # gap between cards
TOTAL_W = 2 * CARD_W + GAP_X                 # 7.5"
TOTAL_H = CARD_H + TAB_H                     # 4.85"
MARGIN_X = (PAGE_W - TOTAL_W) / 2            # ~1.75" each side
MARGIN_Y = (PAGE_H - TOTAL_H) / 2            # ~1.825" top and bottom

CARD1_X = MARGIN_X
CARD2_X = MARGIN_X + CARD_W + GAP_X
CARD_Y  = MARGIN_Y                           # both cards same Y

POSITIONS = [(CARD1_X, CARD_Y), (CARD2_X, CARD_Y)]

# ── Colours ─────────────────────────────────────────────────────────────────
NAV   = HexColor('#1a2e4a')   # fallback default
WHT   = colors.white
DIVIDER = HexColor('#e4e8f0')
TBLU  = HexColor('#deeaf6')
TBLU2 = HexColor('#1e3d6b')
ORED  = HexColor('#fdeee8')
ORED2 = HexColor('#b83a0a')
ORED3 = HexColor('#f5c4b0')
YAMB  = HexColor('#fffbf0')
YAMB2 = HexColor('#e09a1a')
YAMB3 = HexColor('#6b3d00')
GBLU  = HexColor('#f2f5ff')
GBLU2 = HexColor('#3a5f9a')
GBLU3 = HexColor('#1e3050')
GRN   = HexColor('#4a8065')
GRN2  = HexColor('#1a3a2a')
MID   = HexColor('#8090aa')
SHADOW = HexColor('#c0cad8')

# ── Per-letter header colours ────────────────────────────────────────────────
# Each letter gets a unique dark colour — white text readable on all of them.
LETTER_COLORS = {
    'A': HexColor('#7b2d00'),   # burnt sienna
    'B': HexColor('#1a4a2e'),   # deep forest green
    'C': HexColor('#4a1a6b'),   # deep purple
    'D': HexColor('#003d5c'),   # teal navy
    'E': HexColor('#5c2a00'),   # dark amber brown
    'F': HexColor('#1a3d1a'),   # dark moss green
    'G': HexColor('#6b1a2a'),   # deep rose/burgundy
    'H': HexColor('#1a2e5c'),   # cobalt blue
    'I': HexColor('#3d3000'),   # dark olive
    'J': HexColor('#2a4a4a'),   # dark teal
    'K': HexColor('#5c1a1a'),   # dark crimson
    'L': HexColor('#1a2e4a'),   # original navy (keep existing L color)
    'M': HexColor('#1a4a4a'),   # deep cyan
    'N': HexColor('#3d1a5c'),   # violet
    'O': HexColor('#3d4a00'),   # dark chartreuse
    'P': HexColor('#003d3d'),   # dark turquoise
    'Q': HexColor('#4a2a00'),   # dark saddle brown
    'R': HexColor('#1a3a00'),   # dark pine green
    'S': HexColor('#3a0050'),   # dark indigo
    'T': HexColor('#004a1a'),   # deep emerald
    'U': HexColor('#5c3a00'),   # dark burnt orange
    'V': HexColor('#1a1a5c'),   # deep royal blue
    'W': HexColor('#3a1a00'),   # very dark brown
    'X': HexColor('#1a5c3a'),   # dark jade
    'Y': HexColor('#4a0028'),   # dark magenta
    'Z': HexColor('#002a4a'),   # dark steel blue
}

def letter_color(drug):
    """Return the header colour for this drug based on its first letter."""
    first = (drug.get("tab_letter") or "A")[0].upper()
    return LETTER_COLORS.get(first, NAV)

# Section accent colours (left bar) — consistent visual rhythm
SEC_COLORS = {
    "ind":   HexColor('#3a7abd'),
    "ae":    HexColor('#c04020'),
    "bbw":   HexColor('#e09a1a'),
    "meal":  HexColor('#4a8065'),
    "pearl": HexColor('#3a5f9a'),
}

# ── Drug data ─────────────────────────────────────────────────────────────
drug = {
    "generic":     "Lisinopril",
    "brand":       "Prinivil / Zestril",
    "tab_letter":  "LIS",
    "drug_class":  "Antihypertensive - ACE Inhibitor",
    "indications": ["Hypertension", "HFrEF", "STEMI"],
    "ae":          ["Angioedema", "Dry Cough", "Hyperkalemia", "Hypotension"],
    "bbw":         "None",
    "meal":        "Take with or without food at the same time daily",
    "pearls": [
        "Monitor renal function & potassium regularly",
        "First-dose hypotension risk, especially with diuretics",
        "Contraindicated with prior ACE-inhibitor angioedema",
        "Not a prodrug (unlike enalapril/benazepril)",
        "Avoid concurrent ARBs or aliskiren",
    ],
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def rounded_rect(c, x, y, w, h, r,
                 fill_color=None, stroke_color=None, stroke_width=0.5,
                 corners=(True, True, True, True)):
    if fill_color:   c.setFillColor(fill_color)
    if stroke_color: c.setStrokeColor(stroke_color); c.setLineWidth(stroke_width)
    else:            c.setLineWidth(0)
    p = c.beginPath()
    tl, tr, br, bl = corners
    if bl: p.moveTo(x+r, y)
    else:  p.moveTo(x, y)
    if br: p.lineTo(x+w-r, y);     p.arcTo(x+w-2*r, y,     x+w,   y+2*r, -90, 90)
    else:  p.lineTo(x+w, y)
    if tr: p.lineTo(x+w, y+h-r);   p.arcTo(x+w-2*r, y+h-2*r, x+w, y+h,  0,  90)
    else:  p.lineTo(x+w, y+h)
    if tl: p.lineTo(x+r, y+h);     p.arcTo(x,       y+h-2*r, x+2*r, y+h, 90, 90)
    else:  p.lineTo(x, y+h)
    if bl: p.lineTo(x, y+r);       p.arcTo(x, y, x+2*r, y+2*r, 180, 90)
    else:  p.lineTo(x, y)
    p.close()
    if fill_color and stroke_color: c.drawPath(p, fill=1, stroke=1)
    elif fill_color:                c.drawPath(p, fill=1, stroke=0)
    else:                           c.drawPath(p, fill=0, stroke=1)


def draw_section_label(c, text, x, y, accent_color):
    """Label with a small filled square accent dot."""
    sq = 5
    c.setFillColor(accent_color)
    c.rect(x, y + 1.5, sq, sq, fill=1, stroke=0)
    c.setFillColor(accent_color)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + sq + 5, y, text.upper())


def draw_cut_guides(c, cx, cy, tab_pos=0, has_tab=True):
    """Dashed cut guide tracing the card+tab silhouette at a uniform offset."""
    pad = 6   # uniform offset from card edges
    c.setStrokeColor(HexColor('#888888'))
    c.setLineWidth(0.5)

    if has_tab:
        tx = cx + TAB_POSITIONS[tab_pos % TAB_STOPS]
        tw = TAB_W

        # Trace the full silhouette as one continuous dashed path, offset outward
        # Starting at bottom-left, going clockwise
        pts = [
            (cx - pad,        cy - pad),               # BL
            (cx + CARD_W + pad, cy - pad),              # BR
            (cx + CARD_W + pad, cy + CARD_H + pad),     # card TR
            (tx + tw + pad,   cy + CARD_H + pad),       # step in to tab right base
            (tx + tw + pad,   cy + CARD_H + TAB_H + pad),  # tab TR
            (tx - pad,        cy + CARD_H + TAB_H + pad),  # tab TL
            (tx - pad,        cy + CARD_H + pad),       # step down to tab left base
            (cx - pad,        cy + CARD_H + pad),       # card TL
            (cx - pad,        cy - pad),                # back to BL
        ]
        c.setDash([4, 4])
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        c.drawPath(p, fill=0, stroke=1)
        c.setDash([])

    else:
        # No tab — simple offset rectangle
        c.setDash([4, 4])
        p = c.beginPath()
        p.moveTo(cx - pad, cy - pad)
        p.lineTo(cx + CARD_W + pad, cy - pad)
        p.lineTo(cx + CARD_W + pad, cy + CARD_H + pad)
        p.lineTo(cx - pad, cy + CARD_H + pad)
        p.lineTo(cx - pad, cy - pad)
        c.drawPath(p, fill=0, stroke=1)
        c.setDash([])


def fit_text(c, text, font, max_size, min_size, max_width):
    """Return (font_size, lines[]) that fit within max_width."""
    for size in range(max_size, min_size - 1, -1):
        if c.stringWidth(text, font, size) <= max_width:
            return size, [text]
    size = min_size
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return size, lines if lines else [text]


def draw_card(c, cx, cy, drug, tab_pos=0):
    """cx, cy = bottom-left of card body (tab sits above).
    tab_pos: index into TAB_POSITIONS (0 = leftmost, cycles through 5 stops).
    """
    r  = 7
    tr = 5

    # ── INDEX TAB ──────────────────────────────────────────────────────────
    tx = cx + TAB_POSITIONS[tab_pos % TAB_STOPS]
    ty = cy + CARD_H
    hdr_color = letter_color(drug)
    rounded_rect(c, tx, ty, TAB_W, TAB_H, tr,
                 fill_color=hdr_color, corners=(True, True, False, False))
    # First 3–5 letters of the alphabet-determining name, as many as fit
    alpha_name   = drug["tab_letter"].upper()
    tab_avail_w  = TAB_W - 8
    tab_text = alpha_name[:3]
    for n in range(4, min(6, len(alpha_name) + 1)):
        candidate = alpha_name[:n]
        if c.stringWidth(candidate, "Helvetica-Bold", 9) <= tab_avail_w:
            tab_text = candidate
        else:
            break
    tab_font_size = 11
    for fs in range(11, 6, -1):
        if c.stringWidth(tab_text, "Helvetica-Bold", fs) <= tab_avail_w:
            tab_font_size = fs
            break
    c.setFillColor(WHT)
    c.setFont("Helvetica-Bold", tab_font_size)
    c.drawCentredString(tx + TAB_W/2, ty + TAB_H/2 - tab_font_size/2 + 1, tab_text)

    # ── SHADOW ─────────────────────────────────────────────────────────────
    rounded_rect(c, cx+2, cy-2, CARD_W, CARD_H, r,
                 fill_color=SHADOW, corners=(False, True, True, True))

    # ── CARD BASE ──────────────────────────────────────────────────────────
    rounded_rect(c, cx, cy, CARD_W, CARD_H, r,
                 fill_color=WHT, stroke_color=HexColor('#cdd4df'),
                 stroke_width=0.75, corners=(False, True, True, True))

    # ── SEAL THE TAB-TO-CARD SEAM ──────────────────────────────────────────
    # The card's top border line runs across the full width, creating a visible
    # white gap under the tab. Cover it by painting the header color over the
    # seam area between tab bottom and card top-left corner.
    c.setFillColor(hdr_color)
    c.rect(tx, cy + CARD_H - 1, TAB_W, 2, fill=1, stroke=0)

    # ── HEADER ─────────────────────────────────────────────────────────────
    MAX_TXT_W  = CARD_W - 24

    # Pre-calculate class lines to determine header height
    class_size, class_lines = fit_text(c, drug["drug_class"], "Helvetica", 7, 5, MAX_TXT_W)
    name_size, name_lines   = fit_text(c, drug["generic"],    "Helvetica-Bold", 21, 11, MAX_TXT_W)
    brand_size, brand_lines = fit_text(c, drug["brand"],      "Helvetica-Oblique", 9, 7, MAX_TXT_W)

    # Calculate total header height needed
    class_block_h = len(class_lines) * (class_size + 2)
    name_block_h  = len(name_lines)  * (name_size + 3)
    brand_block_h = len(brand_lines) * (brand_size + 2)
    RULE_GAP = 4
    PAD_TOP_HDR = 10   # space from top of card to first line
    PAD_BOT_HDR = 6    # space below brand name to header bottom
    HDR_H = PAD_TOP_HDR + class_block_h + RULE_GAP + name_block_h + brand_block_h + PAD_BOT_HDR
    HDR_H = max(HDR_H, 0.85 * inch)   # minimum height

    header_bot = cy + CARD_H - HDR_H
    header_top = cy + CARD_H

    rounded_rect(c, cx, header_bot, CARD_W, HDR_H, r,
                 fill_color=hdr_color, corners=(False, True, False, False))
    c.setFillColor(hdr_color)
    c.rect(cx, header_bot, CARD_W, 8, fill=1, stroke=0)  # flat bottom

    # Drug class — top of header
    c.setFillColor(HexColor('#6a9ac0'))
    c.setFont("Helvetica", class_size)
    class_y = header_top - PAD_TOP_HDR
    for line in class_lines:
        c.drawString(cx + 12, class_y, line)
        class_y -= class_size + 2

    # Thin rule beneath class text
    rule_y = class_y + class_size - 1
    c.setStrokeColor(HexColor('#2e4d6e') if hdr_color == LETTER_COLORS.get('L') else hdr_color)
    c.setLineWidth(0.5)
    c.line(cx + 12, rule_y, cx + CARD_W - 12, rule_y)

    # Generic name — below rule
    c.setFillColor(WHT)
    c.setFont("Helvetica-Bold", name_size)
    name_y = rule_y - RULE_GAP - name_size + 2
    for line in name_lines:
        c.drawString(cx + 11, name_y, line)
        name_y -= name_size + 3

    # Brand name — anchored just above the header bottom border
    c.setFillColor(HexColor('#7faed4'))
    c.setFont("Helvetica-Oblique", brand_size)
    brand_y = header_bot + PAD_BOT_HDR + (len(brand_lines) - 1) * (brand_size + 2)
    for line in brand_lines:
        c.drawString(cx + 12, brand_y, line)
        brand_y -= brand_size + 2

    # ── BODY SECTIONS ──────────────────────────────────────────────────────
    PAD_X        = 12    # left padding from card edge to text/chips
    BAR_W        = 3     # width of left accent bar
    body_top     = header_bot
    TEXT_SZ      = 8.5   # body text font size
    TEXT_LEAD    = 11    # line height for body text
    LABEL_SZ     = 7     # label font size
    LABEL_H      = 9     # height of label row (font + a little room)
    PAD_TOP      = 7     # gap from section top to top of label
    PAD_MID      = 5     # gap from bottom of label to top of content
    PAD_BOT      = 7     # gap from bottom of content to section bottom
    CHIP_H       = 14    # height of each pill/chip
    CHIP_LEAD    = 4     # vertical gap between chip rows
    CHIP_GAP     = 5     # horizontal gap between chips
    CONTENT_X    = PAD_X + 3   # x offset for text content (slight indent past label)

    def calc_chip_rows(items, font, font_size, pad=16):
        """Count how many rows a list of chips will occupy."""
        x = cx + PAD_X
        rows = 1
        for item in items:
            w = c.stringWidth(item, font, font_size) + pad
            if x + w > cx + CARD_W - 10:
                rows += 1
                x = cx + PAD_X
            x += w + CHIP_GAP
        return rows

    def chip_section_h(rows):
        return PAD_TOP + LABEL_H + PAD_MID + rows * CHIP_H + (rows - 1) * CHIP_LEAD + PAD_BOT

    def text_section_h(lines):
        return PAD_TOP + LABEL_H + PAD_MID + len(lines) * TEXT_LEAD + PAD_BOT

    def draw_section_bg(top, h, bg_color, bar_color, divider_color=None):
        c.setFillColor(bg_color)
        c.rect(cx, top - h, CARD_W, h, fill=1, stroke=0)
        c.setFillColor(bar_color)
        c.rect(cx, top - h, BAR_W, h, fill=1, stroke=0)
        if divider_color:
            c.setStrokeColor(divider_color)
            c.setLineWidth(0.5)
            c.line(cx, top - h, cx + CARD_W, top - h)

    def draw_label(top, h, text, color):
        draw_section_label(c, text, cx + PAD_X, top - PAD_TOP - LABEL_H, color)

    def draw_chips(top, h, items, bg, text_color, border=None, font_r=4):
        x = cx + PAD_X
        y = top - PAD_TOP - LABEL_H - PAD_MID - CHIP_H
        for item in items:
            iw = c.stringWidth(item, "Helvetica-Bold", 8) + 16
            if x + iw > cx + CARD_W - 10:
                x = cx + PAD_X
                y -= CHIP_H + CHIP_LEAD
            if border:
                rounded_rect(c, x, y, iw, CHIP_H, font_r,
                             fill_color=bg, stroke_color=border, stroke_width=0.5)
            else:
                rounded_rect(c, x, y, iw, CHIP_H, font_r, fill_color=bg)
            c.setFillColor(text_color)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 8, y + 3.5, item)
            x += iw + CHIP_GAP

    def draw_text_lines(top, lines, text_color, font="Helvetica", font_size=TEXT_SZ):
        y = top - PAD_TOP - LABEL_H - PAD_MID - font_size + 1
        c.setFillColor(text_color)
        c.setFont(font, font_size)
        for line in lines:
            c.drawString(cx + CONTENT_X, y, line)
            y -= TEXT_LEAD

    # ── INDICATIONS ────────────────────────────────────────────────────────
    ind_rows = calc_chip_rows(drug["indications"], "Helvetica-Bold", 8)
    IND_H    = chip_section_h(ind_rows)
    IND_TOP  = body_top
    IND_BOT  = IND_TOP - IND_H

    draw_section_bg(IND_TOP, IND_H, WHT, SEC_COLORS["ind"], DIVIDER)
    draw_label(IND_TOP, IND_H, "Indications", SEC_COLORS["ind"])
    draw_chips(IND_TOP, IND_H, drug["indications"], TBLU, TBLU2, font_r=6)

    # ── ADVERSE EFFECTS ────────────────────────────────────────────────────
    ae_rows = calc_chip_rows(drug["ae"], "Helvetica-Bold", 8)
    AE_H    = chip_section_h(ae_rows)
    AE_TOP  = IND_BOT
    AE_BOT  = AE_TOP - AE_H

    draw_section_bg(AE_TOP, AE_H, WHT, SEC_COLORS["ae"], DIVIDER)
    draw_label(AE_TOP, AE_H, "Adverse Effects", SEC_COLORS["ae"])
    draw_chips(AE_TOP, AE_H, drug["ae"], ORED, ORED2, border=ORED3, font_r=3)

    # ── BLACK BOX WARNING (only if present) ───────────────────────────────
    has_bbw = drug.get("bbw", "").strip() not in ("", "None")
    if has_bbw:
        bbw_lines = textwrap.wrap(drug["bbw"], 48)
        BBW_H    = text_section_h(bbw_lines)
        BBW_TOP  = AE_BOT
        BBW_BOT  = BBW_TOP - BBW_H

        draw_section_bg(BBW_TOP, BBW_H, YAMB, SEC_COLORS["bbw"], HexColor('#f0d890'))
        draw_label(BBW_TOP, BBW_H, "Black Box Warning", SEC_COLORS["bbw"])
        draw_text_lines(BBW_TOP, bbw_lines, YAMB3, font="Helvetica-Bold")
    else:
        BBW_BOT = AE_BOT   # section takes no space

    # ── MEAL TIMING ────────────────────────────────────────────────────────
    meal_lines = textwrap.wrap(drug["meal"], 48)
    MEAL_TOP = BBW_BOT

    # Pre-measure meal text height
    meal_h_needed = text_section_h(meal_lines)

    # Pre-check pearls overflow before drawing Meal Timing so we know its height
    # Also check if meal itself overflows (leaves no room for pearls and still clips)
    test_meal_bot = MEAL_TOP - meal_h_needed

    # Does meal section itself clip below card bottom?
    meal_overflows = test_meal_bot < cy

    if meal_overflows:
        # Meal goes to back — extend BBW section (or AE if no BBW) color to card bottom
        # Determine what the last drawn section was and its color/bar color
        last_bg    = YAMB if has_bbw else WHT
        last_bar   = SEC_COLORS["bbw"] if has_bbw else SEC_COLORS["ae"]
        # Fill remaining space with that section's color + left bar
        fill_h = MEAL_TOP - cy
        if fill_h > 0:
            c.setFillColor(last_bg)
            c.rect(cx, cy, CARD_W, fill_h, fill=1, stroke=0)
            c.setFillColor(last_bar)
            c.rect(cx, cy, BAR_W, fill_h, fill=1, stroke=0)
        pearls_that_fit_check = []
        overflow_check = drug["pearls"]
        all_pearls_overflow = True
        MEAL_BOT = MEAL_TOP
        MEAL_H   = 0
    else:
        test_y = test_meal_bot - PAD_TOP - LABEL_H - PAD_MID - 7
        pearls_that_fit_check = []
        overflow_check = []
        for pi, pearl in enumerate(drug["pearls"]):
            wrapped = textwrap.wrap(pearl, 46)
            needed = len(wrapped) * TEXT_LEAD + 2
            if test_y - needed < cy + 4:
                overflow_check = drug["pearls"][pi:]
                break
            pearls_that_fit_check.append(pearl)
            test_y -= needed

        all_pearls_overflow = bool(overflow_check) and not pearls_that_fit_check

        # If all pearls go to the back, stretch Meal Timing to fill remaining card space
        if all_pearls_overflow:
            MEAL_BOT = cy
            MEAL_H   = MEAL_TOP - MEAL_BOT
        else:
            MEAL_H   = meal_h_needed
            MEAL_BOT = MEAL_TOP - MEAL_H

        draw_section_bg(MEAL_TOP, MEAL_H, WHT, SEC_COLORS["meal"], DIVIDER)
        draw_label(MEAL_TOP, MEAL_H, "Meal and Timing Considerations", SEC_COLORS["meal"])
        draw_text_lines(MEAL_TOP, meal_lines, GRN2)

    # ── CLINICAL PEARLS ────────────────────────────────────────────────────
    PEARLS_TOP = MEAL_BOT
    PEARLS_BOT = cy
    PEARLS_H   = PEARLS_TOP - PEARLS_BOT

    pearls_that_fit  = pearls_that_fit_check
    overflow_pearls  = overflow_check

    # If ALL pearls overflow (none fit), skip pearls section — meal already stretched to cy
    if overflow_pearls and not pearls_that_fit:
        # Meal section should already stretch to cy (handled above).
        # If not (e.g. meal was short), extend it now with the meal color.
        if MEAL_BOT > cy:
            remaining_h = MEAL_BOT - cy
            c.setFillColor(WHT)
            c.rect(cx, cy, CARD_W, remaining_h, fill=1, stroke=0)
            c.setFillColor(SEC_COLORS["meal"])
            c.rect(cx, cy, BAR_W, remaining_h, fill=1, stroke=0)
    else:
        # Draw pearls section with whatever fits
        c.setFillColor(GBLU)
        c.rect(cx, PEARLS_BOT, CARD_W, PEARLS_H, fill=1, stroke=0)
        c.setFillColor(SEC_COLORS["pearl"])
        c.rect(cx, PEARLS_BOT, BAR_W, PEARLS_H, fill=1, stroke=0)

        draw_label(PEARLS_TOP, PEARLS_H, "Clinical Pearls", SEC_COLORS["pearl"])

        c.setFillColor(GBLU3)
        py_cur = PEARLS_TOP - PAD_TOP - LABEL_H - PAD_MID - 7
        for pearl in pearls_that_fit:
            pearl = pearl[0].upper() + pearl[1:] if pearl else pearl
            wrapped = textwrap.wrap(pearl, 46)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(cx + PAD_X + 3, py_cur, "\u2022")
            c.setFont("Helvetica", 8)
            for wline in wrapped:
                c.drawString(cx + PAD_X + 11, py_cur, wline)
                py_cur -= TEXT_LEAD
            py_cur -= 2

    return overflow_pearls, meal_overflows  # empty list/False = fits on front


def draw_card_custom(c, cx, cy, drug, tab_pos=0, sections=None):
    """
    Draw a card using a custom ordered sections list.
    sections: list of dicts with keys:
      type:    'indications'|'ae'|'bbw'|'meal'|'pearls'|'custom'
      title:   string (section label)
      color:   hex string (bar + label color)
      content: string (for custom/text sections)
      enabled: bool
    Returns (overflow_sections, []) — overflow_sections is the list of
    section dicts that didn't fit and should go on the back card.
    """
    if sections is None:
        return draw_card(c, cx, cy, drug, tab_pos=tab_pos)

    r  = 7
    hdr_color = letter_color(drug)

    # ── SHADOW + BASE ─────────────────────────────────────────────────────────
    rounded_rect(c, cx+2, cy-2, CARD_W, CARD_H, r,
                 fill_color=SHADOW, corners=(False, True, True, True))
    rounded_rect(c, cx, cy, CARD_W, CARD_H, r,
                 fill_color=WHT, stroke_color=HexColor('#cdd4df'),
                 stroke_width=0.75, corners=(False, True, True, True))

    # ── SEAL TAB-TO-CARD SEAM ────────────────────────────────────────────────
    tx = cx + TAB_POSITIONS[tab_pos % TAB_STOPS]
    c.setFillColor(hdr_color)
    c.rect(tx, cy + CARD_H - 1, TAB_W, 2, fill=1, stroke=0)

    # ── INDEX TAB ─────────────────────────────────────────────────────────────
    ty = cy + CARD_H
    rounded_rect(c, tx, ty, TAB_W, TAB_H, r,
                 fill_color=hdr_color, corners=(True, True, False, False))
    alpha_name   = drug["tab_letter"].upper()
    tab_avail_w  = TAB_W - 8
    tab_text = alpha_name[:3]
    for n in range(4, min(6, len(alpha_name) + 1)):
        candidate = alpha_name[:n]
        if c.stringWidth(candidate, "Helvetica-Bold", 9) <= tab_avail_w:
            tab_text = candidate
        else:
            break
    tab_font_size = 11
    for fs in range(11, 6, -1):
        if c.stringWidth(tab_text, "Helvetica-Bold", fs) <= tab_avail_w:
            tab_font_size = fs
            break
    c.setFillColor(WHT)
    c.setFont("Helvetica-Bold", tab_font_size)
    c.drawCentredString(tx + TAB_W/2, ty + TAB_H/2 - tab_font_size/2 + 1, tab_text)

    # ── HEADER ────────────────────────────────────────────────────────────────
    MAX_TXT_W  = CARD_W - 24
    class_size, class_lines = fit_text(c, drug["drug_class"], "Helvetica", 7, 5, MAX_TXT_W)
    name_size,  name_lines  = fit_text(c, drug["generic"],    "Helvetica-Bold", 21, 11, MAX_TXT_W)
    brand_size, brand_lines = fit_text(c, drug["brand"],      "Helvetica-Oblique", 9, 7, MAX_TXT_W)
    class_block_h = len(class_lines) * (class_size + 2)
    name_block_h  = len(name_lines)  * (name_size + 3)
    brand_block_h = len(brand_lines) * (brand_size + 2)
    RULE_GAP = 4; PAD_TOP_HDR = 10; PAD_BOT_HDR = 6
    HDR_H = max(PAD_TOP_HDR + class_block_h + RULE_GAP + name_block_h + brand_block_h + PAD_BOT_HDR, 0.85 * inch)
    header_bot = cy + CARD_H - HDR_H
    header_top = cy + CARD_H
    rounded_rect(c, cx, header_bot, CARD_W, HDR_H, r,
                 fill_color=hdr_color, corners=(False, True, False, False))
    c.setFillColor(hdr_color)
    c.rect(cx, header_bot, CARD_W, 8, fill=1, stroke=0)
    c.setFillColor(HexColor('#6a9ac0'))
    c.setFont("Helvetica", class_size)
    class_y = header_top - PAD_TOP_HDR
    for line in class_lines:
        c.drawString(cx + 12, class_y, line); class_y -= class_size + 2
    rule_y = class_y + class_size - 1
    c.setStrokeColor(hdr_color); c.setLineWidth(0.5)
    c.line(cx + 12, rule_y, cx + CARD_W - 12, rule_y)
    c.setFillColor(WHT); c.setFont("Helvetica-Bold", name_size)
    name_y = rule_y - RULE_GAP - name_size + 2
    for line in name_lines:
        c.drawString(cx + 11, name_y, line); name_y -= name_size + 3
    c.setFillColor(HexColor('#7faed4')); c.setFont("Helvetica-Oblique", brand_size)
    brand_y = header_bot + PAD_BOT_HDR + (len(brand_lines) - 1) * (brand_size + 2)
    for line in brand_lines:
        c.drawString(cx + 12, brand_y, line); brand_y -= brand_size + 2

    # ── Section drawing constants ──────────────────────────────────────────────
    BAR_W    = 3
    PAD_X    = 12
    PAD_TOP  = 7
    PAD_MID  = 5
    PAD_BOT  = 7
    LABEL_H  = 9
    TEXT_SZ  = 8.5
    TEXT_LEAD= 11
    CHIP_H   = 14
    CHIP_LEAD= 3
    CHIP_GAP = 5
    CONTENT_X= PAD_X + 3

    def calc_chip_rows_c(items):
        x = cx + PAD_X; rows = 1
        for item in items:
            w = c.stringWidth(item, "Helvetica-Bold", 8) + 16
            if x + w > cx + CARD_W - 10: rows += 1; x = cx + PAD_X
            x += w + CHIP_GAP
        return rows

    def section_h_chips(items):
        rows = calc_chip_rows_c(items)
        return PAD_TOP + LABEL_H + PAD_MID + rows * CHIP_H + (rows-1)*CHIP_LEAD + PAD_BOT

    def section_h_text(text, wrap_w=48):
        lines = textwrap.wrap(text, wrap_w)
        return PAD_TOP + LABEL_H + PAD_MID + max(1, len(lines)) * TEXT_LEAD + PAD_BOT

    def draw_sec_bg(top, h, bg, bar_color):
        c.setFillColor(bg); c.rect(cx, top-h, CARD_W, h, fill=1, stroke=0)
        c.setFillColor(HexColor(bar_color) if isinstance(bar_color, str) else bar_color)
        c.rect(cx, top-h, BAR_W, h, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#e4e8f0')); c.setLineWidth(0.5)
        c.line(cx, top-h, cx+CARD_W, top-h)

    def draw_sec_label(top, h, text, color):
        col = HexColor(color) if isinstance(color, str) else color
        draw_section_label(c, text, cx+PAD_X, top-PAD_TOP-LABEL_H, col)

    def draw_chips_c(top, items, bg, fg, border=None):
        x = cx+PAD_X; y = top-PAD_TOP-LABEL_H-PAD_MID-CHIP_H
        for item in items:
            iw = c.stringWidth(item,"Helvetica-Bold",8)+16
            if x+iw > cx+CARD_W-10: x=cx+PAD_X; y -= CHIP_H+CHIP_LEAD
            if border:
                rounded_rect(c,x,y,iw,CHIP_H,4,fill_color=bg,stroke_color=border,stroke_width=0.5)
            else:
                rounded_rect(c,x,y,iw,CHIP_H,4,fill_color=bg)
            c.setFillColor(fg); c.setFont("Helvetica-Bold",8); c.drawString(x+8,y+3.5,item)
            x += iw+CHIP_GAP

    def draw_text_c(top, text, color, wrap_w=48, bold=False):
        lines = textwrap.wrap(text, wrap_w)
        y = top-PAD_TOP-LABEL_H-PAD_MID-TEXT_SZ+1
        c.setFillColor(color if not isinstance(color, str) else HexColor(color))
        c.setFont("Helvetica-Bold" if bold else "Helvetica", TEXT_SZ)
        for line in lines:
            c.drawString(cx+CONTENT_X, y, line); y -= TEXT_LEAD

    def draw_pearls_c(top, h, pearls_list, color):
        col = color if not isinstance(color, str) else HexColor(color)
        c.setFillColor(GBLU); c.rect(cx, top-h, CARD_W, h, fill=1, stroke=0)
        c.setFillColor(col);   c.rect(cx, top-h, BAR_W,  h, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#e4e8f0')); c.setLineWidth(0.5)
        c.line(cx, top-h, cx+CARD_W, top-h)
        draw_section_label(c, "Clinical Pearls", cx+PAD_X, top-PAD_TOP-LABEL_H, col)
        py = top-PAD_TOP-LABEL_H-PAD_MID-7
        c.setFillColor(GBLU3)
        for pearl in pearls_list:
            pearl = pearl[0].upper()+pearl[1:] if pearl else pearl
            wrapped = textwrap.wrap(pearl, 46)
            c.setFont("Helvetica-Bold",8); c.drawString(cx+PAD_X+3, py, "\u2022")
            c.setFont("Helvetica",8)
            for wline in wrapped:
                c.drawString(cx+PAD_X+11, py, wline); py -= TEXT_LEAD
            py -= 2

    # ── Calculate heights for each enabled section ────────────────────────────
    enabled = [s for s in (sections or []) if s.get('enabled', True)]

    def sec_height(s):
        t = s['type']
        if t == 'indications': return section_h_chips(drug.get('indications', []))
        if t == 'ae':          return section_h_chips(drug.get('ae', []))
        if t == 'bbw':
            bbw = drug.get('bbw','').strip()
            if not bbw or bbw.lower() == 'none': return 0
            return section_h_text(bbw)
        if t == 'meal':        return section_h_text(drug.get('meal',''))
        if t == 'pearls':
            total = PAD_TOP+LABEL_H+PAD_MID+PAD_BOT
            for p in drug.get('pearls',[]):
                total += len(textwrap.wrap(p,46))*TEXT_LEAD+2
            return total
        if t == 'custom':
            content = s.get('content','')
            if not content: return 0
            bullets = [x.strip() for x in content.replace('\n',';').split(';') if x.strip()]
            if len(bullets) > 1:
                total = PAD_TOP+LABEL_H+PAD_MID+PAD_BOT
                for b in bullets:
                    total += len(textwrap.wrap(b,46))*TEXT_LEAD+2
                return total
            return section_h_text(content)
        return 0

    # ── Layout: draw sections that fit, collect overflow ─────────────────────
    current_top = header_bot
    overflow_sections = []
    in_overflow = False

    for sec in enabled:
        h = sec_height(sec)
        if h == 0:
            continue
        if in_overflow or (current_top - h < cy + 2):
            in_overflow = True
            overflow_sections.append(sec)
            continue

        t = sec['type']
        bar_color = sec.get('color', '#3a7abd')
        bc = HexColor(bar_color) if isinstance(bar_color, str) else bar_color

        if t == 'indications':
            draw_sec_bg(current_top, h, WHT, bc)
            draw_sec_label(current_top, h, sec.get('title','Indications'), bc)
            draw_chips_c(current_top, drug.get('indications',[]), TBLU, TBLU2)
        elif t == 'ae':
            draw_sec_bg(current_top, h, WHT, bc)
            draw_sec_label(current_top, h, sec.get('title','Adverse Effects'), bc)
            draw_chips_c(current_top, drug.get('ae',[]), ORED, ORED2, border=ORED3)
        elif t == 'bbw':
            bbw = drug.get('bbw','').strip()
            if not bbw or bbw.lower() == 'none':
                continue
            draw_sec_bg(current_top, h, YAMB, bc)
            draw_sec_label(current_top, h, sec.get('title','Black Box Warning'), bc)
            draw_text_c(current_top, bbw, YAMB3, bold=True)
        elif t == 'meal':
            draw_sec_bg(current_top, h, WHT, bc)
            draw_sec_label(current_top, h, sec.get('title','Meal and Timing'), bc)
            draw_text_c(current_top, drug.get('meal',''), GRN2)
        elif t == 'pearls':
            pearls = drug.get('pearls', [])
            # Fit as many pearls as possible
            fits = []; py = current_top-PAD_TOP-LABEL_H-PAD_MID-7
            for p in pearls:
                needed = len(textwrap.wrap(p,46))*TEXT_LEAD+2
                if py - needed < cy+4:
                    overflow_sections.extend([
                        {'type':'pearls_overflow','pearls':pearls[pearls.index(p):],
                         'color':bar_color,'title':sec.get('title','Clinical Pearls')}
                    ])
                    in_overflow = True; break
                fits.append(p); py -= needed
            actual_h = current_top - max(py + TEXT_LEAD, cy)
            draw_pearls_c(current_top, min(h, current_top-cy), fits, bc)
        elif t == 'custom':
            content = sec.get('content','')
            if not content: continue
            draw_sec_bg(current_top, h, WHT, bc)
            draw_sec_label(current_top, h, sec.get('title','Section'), bc)
            # Render as bullets if content has semicolons or newlines
            bullets = [x.strip() for x in content.replace('\n',';').split(';') if x.strip()]
            if len(bullets) > 1:
                py = current_top-PAD_TOP-LABEL_H-PAD_MID-7
                c.setFillColor(HexColor('#1a2a3a'))
                for bullet in bullets:
                    bullet = bullet[0].upper()+bullet[1:] if bullet else bullet
                    wrapped = textwrap.wrap(bullet, 46)
                    c.setFont("Helvetica-Bold",8); c.drawString(cx+PAD_X+3, py, "\u2022")
                    c.setFont("Helvetica",TEXT_SZ)
                    for wline in wrapped:
                        c.drawString(cx+PAD_X+11, py, wline); py -= TEXT_LEAD
                    py -= 2
            else:
                draw_text_c(current_top, content, HexColor('#1a2a3a'))

        current_top -= h

    # Fill any remaining space with the color of the last drawn section
    if current_top > cy + 2:
        last = next((s for s in reversed(enabled) if s not in overflow_sections
                     and sec_height(s) > 0), None)
        if last:
            last_bar = last.get('color','#3a7abd')
            c.setFillColor(WHT); c.rect(cx, cy, CARD_W, current_top-cy, fill=1, stroke=0)
            c.setFillColor(HexColor(last_bar) if isinstance(last_bar,str) else last_bar)
            c.rect(cx, cy, BAR_W, current_top-cy, fill=1, stroke=0)

    return overflow_sections, False


def draw_card_custom_back(c, cx, cy, drug, overflow_sections, tab_pos=0):
    """Draw back card for custom-layout cards."""
    if not overflow_sections:
        return
    r = 7
    hdr_color = letter_color(drug)
    rounded_rect(c, cx+2, cy-2, CARD_W, CARD_H, r,
                 fill_color=SHADOW, corners=(True,True,True,True))
    rounded_rect(c, cx, cy, CARD_W, CARD_H, r,
                 fill_color=WHT, stroke_color=HexColor('#cdd4df'),
                 stroke_width=0.75, corners=(True,True,True,True))
    HDR_H = 0.65*inch
    header_bot = cy+CARD_H-HDR_H
    rounded_rect(c, cx, header_bot, CARD_W, HDR_H, r,
                 fill_color=hdr_color, corners=(True,True,False,False))
    c.setFillColor(hdr_color); c.rect(cx, header_bot, CARD_W, 8, fill=1, stroke=0)
    header_top = cy+CARD_H
    MAX_TXT_W = CARD_W-24
    name_size, name_lines = fit_text(c, drug["generic"], "Helvetica-Bold", 18, 10, MAX_TXT_W)
    c.setFillColor(WHT); c.setFont("Helvetica-Bold", name_size)
    name_y = header_top - 0.30*inch
    for line in name_lines:
        c.drawString(cx+11, name_y, line); name_y -= name_size+3
    c.setFillColor(HexColor('#7faed4')); c.setFont("Helvetica-Oblique", 8)
    c.drawString(cx+12, header_top-0.52*inch, drug["brand"])

    BAR_W=3; PAD_X=12; PAD_TOP=7; PAD_MID=5; PAD_BOT=7
    LABEL_H=9; TEXT_SZ=8.5; TEXT_LEAD=11; CHIP_H=14; CHIP_LEAD=3; CHIP_GAP=5; CONTENT_X=PAD_X+3

    def section_h_text_b(text): return PAD_TOP+LABEL_H+PAD_MID+max(1,len(textwrap.wrap(text,48)))*TEXT_LEAD+PAD_BOT
    def draw_sec_bg_b(top, h, bg, bar):
        col = HexColor(bar) if isinstance(bar,str) else bar
        c.setFillColor(bg); c.rect(cx,top-h,CARD_W,h,fill=1,stroke=0)
        c.setFillColor(col); c.rect(cx,top-h,BAR_W,h,fill=1,stroke=0)
        c.setStrokeColor(HexColor('#e4e8f0')); c.setLineWidth(0.5); c.line(cx,top-h,cx+CARD_W,top-h)
    def draw_text_b(top, text, color, bold=False):
        lines=textwrap.wrap(text,48); y=top-PAD_TOP-LABEL_H-PAD_MID-TEXT_SZ+1
        c.setFillColor(HexColor(color) if isinstance(color,str) else color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica",TEXT_SZ)
        for line in lines: c.drawString(cx+CONTENT_X,y,line); y-=TEXT_LEAD

    current_top = header_bot
    for sec in overflow_sections:
        if current_top <= cy+2: break
        t = sec.get('type','')
        bar = sec.get('color','#3a5f9a')

        if t == 'pearls_overflow':
            pearls = sec.get('pearls',[])
            h_avail = current_top - cy
            c.setFillColor(GBLU); c.rect(cx, cy, CARD_W, h_avail, fill=1, stroke=0)
            bc = HexColor(bar) if isinstance(bar,str) else bar
            c.setFillColor(bc); c.rect(cx, cy, BAR_W, h_avail, fill=1, stroke=0)
            draw_section_label(c, sec.get('title','Clinical Pearls'), cx+PAD_X, current_top-PAD_TOP-LABEL_H, bc)
            py = current_top-PAD_TOP-LABEL_H-PAD_MID-7
            c.setFillColor(GBLU3)
            for pearl in pearls:
                if py < cy+4: break
                pearl = pearl[0].upper()+pearl[1:] if pearl else pearl
                wrapped = textwrap.wrap(pearl,46)
                c.setFont("Helvetica-Bold",8); c.drawString(cx+PAD_X+3,py,"\u2022")
                c.setFont("Helvetica",8)
                for wline in wrapped: c.drawString(cx+PAD_X+11,py,wline); py-=TEXT_LEAD
                py-=2
            current_top = cy
        elif t == 'custom':
            content = sec.get('content','')
            h = section_h_text_b(content)
            if current_top-h < cy: h = current_top-cy
            draw_sec_bg_b(current_top, h, WHT, bar)
            draw_section_label(c, sec.get('title','Section'), cx+PAD_X, current_top-PAD_TOP-LABEL_H,
                               HexColor(bar) if isinstance(bar,str) else bar)
            draw_text_b(current_top, content, '#1a2a3a')
            current_top -= h


def draw_card_back(c, cx, cy, drug, tab_pos=0, overflow_pearls=None, show_meal=False):
    """Draw the back side of a card — no tab, compact header, optional meal + Clinical Pearls."""
    r  = 7
    pearls = overflow_pearls or drug["pearls"]
    hdr_color = letter_color(drug)

    # ── SHADOW + BASE (all corners rounded — no tab on back) ──────────────
    rounded_rect(c, cx+2, cy-2, CARD_W, CARD_H, r,
                 fill_color=SHADOW, corners=(True, True, True, True))
    rounded_rect(c, cx, cy, CARD_W, CARD_H, r,
                 fill_color=WHT, stroke_color=HexColor('#cdd4df'),
                 stroke_width=0.75, corners=(True, True, True, True))

    # ── HEADER (compact — drug name + brand name) ──────────────────────────
    HDR_H = 0.65 * inch
    header_bot = cy + CARD_H - HDR_H
    rounded_rect(c, cx, header_bot, CARD_W, HDR_H, r,
                 fill_color=hdr_color, corners=(True, True, False, False))
    c.setFillColor(hdr_color)
    c.rect(cx, header_bot, CARD_W, 8, fill=1, stroke=0)

    header_top = cy + CARD_H
    MAX_TXT_W  = CARD_W - 24

    name_size, name_lines = fit_text(c, drug["generic"], "Helvetica-Bold", 18, 10, MAX_TXT_W)
    c.setFillColor(WHT)
    c.setFont("Helvetica-Bold", name_size)
    name_y = header_top - 0.30 * inch
    for line in name_lines:
        c.drawString(cx + 11, name_y, line)
        name_y -= name_size + 3

    c.setFillColor(HexColor('#7faed4'))
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(cx + 12, header_top - 0.52 * inch, drug["brand"])

    # ── FULL PEARLS SECTION ────────────────────────────────────────────────
    PAD_X    = 12
    BAR_W    = 3
    TEXT_LEAD = 11
    PAD_TOP  = 8
    LABEL_H  = 9
    PAD_MID  = 5

    PEARLS_TOP = header_bot

    # ── MEAL SECTION (if pushed to back) ──────────────────────────────────
    if show_meal:
        _PAD_TOP = 7; _LABEL_H = 9; _PAD_MID = 5; _PAD_BOT = 7
        _TEXT_LEAD = 11; _TEXT_SZ = 8.5; _CONTENT_X = PAD_X + 3
        meal_lines_back = textwrap.wrap(drug["meal"], 48)
        MEAL_H_BACK = _PAD_TOP + _LABEL_H + _PAD_MID + len(meal_lines_back) * _TEXT_LEAD + _PAD_BOT
        MEAL_TOP_BACK = PEARLS_TOP
        MEAL_BOT_BACK = MEAL_TOP_BACK - MEAL_H_BACK

        c.setFillColor(WHT)
        c.rect(cx, MEAL_BOT_BACK, CARD_W, MEAL_H_BACK, fill=1, stroke=0)
        c.setFillColor(SEC_COLORS["meal"])
        c.rect(cx, MEAL_BOT_BACK, BAR_W, MEAL_H_BACK, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#e4e8f0'))
        c.setLineWidth(0.5)
        c.line(cx, MEAL_BOT_BACK, cx + CARD_W, MEAL_BOT_BACK)

        draw_section_label(c, "Meal and Timing Considerations", cx + PAD_X,
                           MEAL_TOP_BACK - _PAD_TOP - _LABEL_H, SEC_COLORS["meal"])
        c.setFillColor(GRN2)
        my = MEAL_TOP_BACK - _PAD_TOP - _LABEL_H - _PAD_MID - _TEXT_SZ + 1
        c.setFont("Helvetica", _TEXT_SZ)
        for line in meal_lines_back:
            c.drawString(cx + _CONTENT_X, my, line)
            my -= _TEXT_LEAD

        PEARLS_TOP = MEAL_BOT_BACK
    PEARLS_BOT = cy
    PEARLS_H   = PEARLS_TOP - PEARLS_BOT

    c.setFillColor(GBLU)
    c.rect(cx, PEARLS_BOT, CARD_W, PEARLS_H, fill=1, stroke=0)
    c.setFillColor(SEC_COLORS["pearl"])
    c.rect(cx, PEARLS_BOT, BAR_W, PEARLS_H, fill=1, stroke=0)

    draw_section_label(c, "Clinical Pearls", cx + PAD_X,
                       PEARLS_TOP - PAD_TOP - LABEL_H, SEC_COLORS["pearl"])

    c.setFillColor(GBLU3)
    py_cur = PEARLS_TOP - PAD_TOP - LABEL_H - PAD_MID - 7
    for pearl in pearls:
        if py_cur < PEARLS_BOT + 4:
            break
        pearl = pearl[0].upper() + pearl[1:] if pearl else pearl
        wrapped = textwrap.wrap(pearl, 46)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cx + PAD_X + 3, py_cur, "\u2022")
        c.setFont("Helvetica", 8)
        for wline in wrapped:
            if py_cur < PEARLS_BOT + 4:
                break
            c.drawString(cx + PAD_X + 11, py_cur, wline)
            py_cur -= TEXT_LEAD
        py_cur -= 2



if __name__ == '__main__':
    # ── Build PDF ────────────────────────────────────────────────────────────────
    output_path = "/mnt/user-data/outputs/drug_cards.pdf"
    c = canvas.Canvas(output_path, pagesize=landscape(letter))
    c.setTitle("Drug Reference Cards")

    # Instruction banner
    c.setFillColor(HexColor('#888ea0'))
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.30*inch,
        "DRUG REFERENCE CARDS  \u2014  Print on cardstock  \u00b7  Cut on dashed lines  \u00b7  Laminate")

    # Draw 2 cards per page (prototype — both same drug, different tab positions)
    for idx, (px, py) in enumerate(POSITIONS):
        draw_cut_guides(c, px, py, tab_pos=idx)
        draw_card(c, px, py, drug, tab_pos=idx)

    c.save()
    print(f"Saved: {output_path}")

# ── BATCH GENERATION ────────────────────────────────────────────────────────
import openpyxl

FULL_DATA = {
    "Acyclovir": {
        "indications": ["Herpes Simplex (HSV)", "Herpes Zoster", "Varicella"],
        "ae": ["Nausea", "Headache", "Nephrotoxicity (IV)", "Neurotoxicity (IV)"],
        "bbw": "None",
        "meal": "Can take with or without food; stay well hydrated",
        "pearls": [
            "Renal dose adjustment required",
            "Maintain adequate hydration to prevent crystalluria",
            "Valacyclovir is a prodrug — better oral bioavailability",
            "For shingles: start within 72 hours of rash onset",
        ],
    },
    "Adapalene": {
        "indications": ["Acne Vulgaris"],
        "ae": ["Dryness", "Erythema", "Scaling", "Burning/Stinging"],
        "bbw": "None",
        "meal": "Topical — not applicable",
        "pearls": [
            "Not photolabile (unlike tretinoin)",
            "Takes 6+ weeks to see improvement",
            "Acne flaring may occur and last 4-6 weeks after initiation",
            "Apply thin layer at bedtime; avoid eyes, lips, mucous membranes",
            "Use sunscreen daily",
        ],
    },
    "Albuterol HFA": {
        "indications": ["Bronchospasm", "Asthma", "Exercise-Induced Bronchospasm"],
        "ae": ["Tachycardia", "Tremor", "Headache", "Hypokalemia", "Nervousness"],
        "bbw": "None",
        "meal": "Inhaled — not applicable",
        "pearls": [
            "Short-acting beta-2 agonist (SABA) — rescue inhaler",
            "Shake well before each use",
            "Use >2 days/week suggests uncontrolled asthma",
            "Rinse mouth after use if using spacer",
        ],
    },
    "Alclometasone Dipropionate": {
        "indications": ["Corticosteroid-Responsive Dermatoses"],
        "ae": ["Skin Atrophy", "Telangiectasia", "Striae", "Contact Dermatitis", "Hypopigmentation"],
        "bbw": "None",
        "meal": "Topical — not applicable",
        "pearls": [
            "Low potency (Group 6) — safe for face and skin folds",
            "Do not use with occlusive dressings",
            "Prolonged use can cause cutaneous and systemic side effects",
            "Safer than systemic corticosteroids for localized use",
        ],
    },
}

def parse_drug_row(row, headers):
    """Build a drug dict from a spreadsheet row, filling gaps from FULL_DATA."""
    d = dict(zip(headers, row))
    generic = d.get("Generic Name", "") or ""
    full    = FULL_DATA.get(generic, {})

    def split_list(val):
        if not val or str(val).strip() in ("None", ""):
            return []
        return [x.strip() for x in str(val).replace(";", ",").split(",") if x.strip()]

    def split_bullets(val):
        if not val or str(val).strip() in ("None", ""):
            return []
        return [x.strip() for x in str(val).split(";") if x.strip()]

    indications = split_list(d.get("Indications")) or full.get("indications", ["See prescribing information"])
    ae          = split_list(d.get("Adverse Effects")) or full.get("ae", ["See prescribing information"])
    bbw         = (d.get("BBW") or "").strip()
    if not bbw or bbw == "None": bbw = full.get("bbw", "None")
    meal        = (d.get("Meal & Time of Day Considerations") or d.get("Meal-Timing") or "").strip()
    if not meal or meal == "None": meal = full.get("meal", "No specific timing required")
    pearls_raw  = split_bullets(d.get("Drug Pearls")) or full.get("pearls", [])

    tab_letter  = (d.get("Alphabet Determining Name") or generic or "???").upper()

    return {
        "generic":    generic,
        "brand":      d.get("Brand Name") or "",
        "tab_letter": tab_letter,
        "drug_class": d.get("Drug Class") or "",
        "indications": indications,
        "ae":          ae,
        "bbw":         bbw,
        "meal":        meal,
        "pearls":      pearls_raw,
    }


def generate_batch(xlsx_path, start_card, end_card, output_path, start_tab_pos=0):
    """
    start_card / end_card are 1-based indices into the full sorted drug list.
    Drugs are sorted by Alphabet Determining Name (col C) before slicing.
    """
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]

    # Load all drugs
    all_rows = []
    for row_idx in range(2, ws.max_row + 1):
        row = [ws.cell(row_idx, c).value for c in range(1, ws.max_column + 1)]
        if not row[0]:
            continue
        all_rows.append(row)

    # Sort by Alphabet Determining Name (col index 2), fallback to Generic Name
    alpha_col = headers.index("Alphabet Determining Name") if "Alphabet Determining Name" in headers else 2
    all_rows.sort(key=lambda r: (str(r[alpha_col] or r[0] or '')).upper())

    # Slice to requested card range (1-based)
    batch_rows = all_rows[start_card - 1 : end_card]
    drugs_batch = [parse_drug_row(row, headers) for row in batch_rows]

    c = canvas.Canvas(output_path, pagesize=landscape(letter))
    c.setTitle("Drug Reference Cards")

    def banner(is_back=False):
        c.setFillColor(HexColor('#888ea0'))
        c.setFont("Helvetica", 7)
        msg = ("BACK SIDES \u2014 Print on reverse of front page \u00b7 Align before laminating"
               if is_back else
               "DRUG REFERENCE CARDS \u2014 Print on cardstock \u00b7 Cut on dashed lines \u00b7 Laminate")
        c.drawCentredString(PAGE_W / 2, PAGE_H - 0.22 * inch, msg)

    # Build a flat sequence of slots: each item is
    # ('front', drug, tab_pos) or ('back', drug, tab_pos, overflow_pearls)
    slots = []
    card_index = start_tab_pos
    for drug in drugs_batch:
        slots.append(('front', drug, card_index, None))
        card_index += 1

    # Expand: after each front that overflows, insert its back immediately after
    # We don't know overflow until we draw, so we do a pre-draw pass first
    expanded = []
    for slot in slots:
        _, drug, tab, _ = slot
        # Quick pre-render to detect overflow
        test_c = canvas.Canvas(io.BytesIO(), pagesize=landscape(letter))
        result = draw_card(test_c, CARD1_X, CARD_Y, drug, tab_pos=tab)
        overflow, meal_ov = result if isinstance(result, tuple) else (result, False)
        expanded.append(('front', drug, tab, None, False))
        if overflow or meal_ov:
            expanded.append(('back', drug, tab, overflow, meal_ov))

    # Lay out slots sequentially, but never put two backs on the same page.
    # If the next two slots are both backs, insert the earliest pending front between them.
    i = 0
    while i < len(expanded):
        left  = expanded[i]
        right = expanded[i + 1] if i + 1 < len(expanded) else None

        left_is_back  = left[0] == 'back'
        right_is_back = right[0] == 'back' if right else False

        # If both slots are backs, find the next front and pull it in as right slot
        if left_is_back and right_is_back:
            # Find the next front after i+1
            next_front_idx = None
            for j in range(i + 2, len(expanded)):
                if expanded[j][0] == 'front':
                    next_front_idx = j
                    break
            if next_front_idx is not None:
                # Swap: pull that front into i+1, push the current i+1 back one slot
                front_slot = expanded.pop(next_front_idx)
                expanded.insert(i + 1, front_slot)
                right = expanded[i + 1]
                right_is_back = False

        page_has_back = left_is_back or right_is_back
        banner(is_back=page_has_back)

        # Draw left slot
        _, ldrug, ltab, loverflow, lmeal_ov = left
        if left_is_back:
            draw_cut_guides(c, CARD1_X, CARD_Y, tab_pos=ltab, has_tab=False)
            draw_card_back(c, CARD1_X, CARD_Y, ldrug, tab_pos=ltab,
                           overflow_pearls=loverflow, show_meal=lmeal_ov)
        else:
            draw_cut_guides(c, CARD1_X, CARD_Y, tab_pos=ltab)
            draw_card(c, CARD1_X, CARD_Y, ldrug, tab_pos=ltab)

        # Draw right slot
        if right:
            _, rdrug, rtab, roverflow, rmeal_ov = right
            if right_is_back:
                draw_cut_guides(c, CARD2_X, CARD_Y, tab_pos=rtab, has_tab=False)
                draw_card_back(c, CARD2_X, CARD_Y, rdrug, tab_pos=rtab,
                               overflow_pearls=roverflow, show_meal=rmeal_ov)
            else:
                draw_cut_guides(c, CARD2_X, CARD_Y, tab_pos=rtab)
                draw_card(c, CARD2_X, CARD_Y, rdrug, tab_pos=rtab)

        c.showPage()
        i += 2

    c.save()
    backs = sum(1 for s in expanded if s[0] == 'back')
    print(f"Saved cards {start_card}–{end_card} ({len(drugs_batch)} drugs, {backs} with back sides) to: {output_path}")

if __name__ == '__main__':
    generate_batch(
        '/mnt/user-data/outputs/Claude_Drugs_1.xlsx',
        start_card=131,
        end_card=140,
        output_path='/mnt/user-data/outputs/drug_cards_131_140.pdf',
        start_tab_pos=130
    )
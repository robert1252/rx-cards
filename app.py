"""
Drug Card Creator — Local Web App
Run with: python app.py
Then open: http://localhost:5000
"""

import sys, os, io, base64, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.colors import HexColor
import make_cards as mc

app = Flask(__name__)

# ── Helper: build drug dict from form data ───────────────────────────────────
def form_to_drug(data):
    def split_list(val):
        return [x.strip() for x in val.replace(";", ",").split(",") if x.strip()]
    def split_bullets(val):
        val = val.replace("\r\n", "\n").replace("\r", "\n")
        if "\n" in val:
            return [x.strip() for x in val.split("\n") if x.strip()]
        return [x.strip() for x in val.split(";") if x.strip()]

    # Build drug dict from sections list if present
    sections = data.get("sections", None)
    if sections:
        # Extract standard field content from sections
        def sec_content(stype):
            s = next((s for s in sections if s.get('type') == stype), None)
            return s.get('content', '') if s else ''

        return {
            "generic":    data.get("generic", "").strip(),
            "brand":      data.get("brand", "").strip(),
            "tab_letter": (data.get("alpha_name") or data.get("generic") or "???").strip().upper(),
            "drug_class": data.get("drug_class", "").strip(),
            "indications": split_list(sec_content("indications")),
            "ae":          split_list(sec_content("ae")),
            "bbw":         sec_content("bbw").strip() or "None",
            "meal":        sec_content("meal").strip(),
            "pearls":      split_bullets(sec_content("pearls")),
            "_sections":   sections,  # keep for custom layout
            "_tab_pos":    data.get("tab_pos", None),
        }
    else:
        return {
            "generic":    data.get("generic", "").strip(),
            "brand":      data.get("brand", "").strip(),
            "tab_letter": (data.get("alpha_name") or data.get("generic") or "???").strip().upper(),
            "drug_class": data.get("drug_class", "").strip(),
            "indications": split_list(data.get("indications", "")),
            "ae":          split_list(data.get("ae", "")),
            "bbw":         data.get("bbw", "None").strip() or "None",
            "meal":        data.get("meal", "").strip(),
            "pearls":      split_bullets(data.get("pearls", "")),
            "_sections":   None,
            "_tab_pos":    data.get("tab_pos", None),
        }


# ── Helper: generate PDF from list of drug dicts ─────────────────────────────
def generate_pdf(drugs):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    c.setTitle("Drug Reference Cards")

    PAGE_W, PAGE_H = landscape(letter)

    # Build expanded slot list (front + back if overflow)
    expanded = []
    for i, drug in enumerate(drugs):
        # Determine tab position
        tab_pos_override = drug.get("_tab_pos")
        tab = int(tab_pos_override) if tab_pos_override is not None else i
        sections = drug.get("_sections")

        test_c = canvas.Canvas(io.BytesIO(), pagesize=landscape(letter))
        if sections:
            overflow, meal_ov = mc.draw_card_custom(test_c, mc.CARD1_X, mc.CARD_Y, drug,
                                                     tab_pos=tab, sections=sections)
        else:
            result = mc.draw_card(test_c, mc.CARD1_X, mc.CARD_Y, drug, tab_pos=tab)
            overflow, meal_ov = result if isinstance(result, tuple) else (result, False)

        expanded.append(('front', drug, tab, None, False, sections))
        if overflow or meal_ov:
            expanded.append(('back', drug, tab, overflow, meal_ov, sections))

    # Layout: 2 per page, never two backs on same page
    idx = 0
    while idx < len(expanded):
        left  = expanded[idx]
        right = expanded[idx + 1] if idx + 1 < len(expanded) else None

        left_is_back  = left[0] == 'back'
        right_is_back = right[0] == 'back' if right else False

        if left_is_back and right_is_back:
            for j in range(idx + 2, len(expanded)):
                if expanded[j][0] == 'front':
                    front_slot = expanded.pop(j)
                    expanded.insert(idx + 1, front_slot)
                    right = expanded[idx + 1]
                    right_is_back = False
                    break

        # Banner
        is_back_page = left_is_back or right_is_back
        c.setFillColor(HexColor('#888ea0'))
        c.setFont("Helvetica", 7)
        msg = ("BACK SIDES — Print on reverse · Align before laminating"
               if is_back_page else
               "DRUG REFERENCE CARDS — Print on cardstock · Cut on dashed lines · Laminate")
        c.drawCentredString(PAGE_W / 2, PAGE_H - 0.22 * mc.inch, msg)

        def draw_slot(slot, cx):
            _, drug, tab, overflow, meal_ov, sections = slot
            if slot[0] == 'back':
                mc.draw_cut_guides(c, cx, mc.CARD_Y, tab_pos=tab, has_tab=False)
                if sections:
                    mc.draw_card_custom_back(c, cx, mc.CARD_Y, drug, overflow, tab_pos=tab)
                else:
                    mc.draw_card_back(c, cx, mc.CARD_Y, drug, tab_pos=tab,
                                      overflow_pearls=overflow, show_meal=meal_ov)
            else:
                mc.draw_cut_guides(c, cx, mc.CARD_Y, tab_pos=tab)
                if sections:
                    mc.draw_card_custom(c, cx, mc.CARD_Y, drug, tab_pos=tab, sections=sections)
                else:
                    mc.draw_card(c, cx, mc.CARD_Y, drug, tab_pos=tab)

        draw_slot(left, mc.CARD1_X)
        if right:
            draw_slot(right, mc.CARD2_X)

        c.showPage()
        idx += 2

    c.save()
    buf.seek(0)
    return buf


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Accept JSON list of drug dicts, return PDF."""
    data = request.get_json()
    drugs_raw = data.get("drugs", [])
    if not drugs_raw:
        return jsonify({"error": "No drugs provided"}), 400

    drugs = [form_to_drug(d) for d in drugs_raw]
    pdf_buf = generate_pdf(drugs)

    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="custom_drug_cards.pdf"
    )


@app.route("/preview", methods=["POST"])
def preview():
    """Return base64-encoded PNG preview of the first card."""
    data = request.get_json()
    drug = form_to_drug(data.get("drug", {}))

    # Generate single-card PDF, convert first page to image via ReportLab SVG
    # We'll return a single-page PDF as base64 instead for simplicity
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    c.setTitle("Preview")
    PAGE_W, PAGE_H = landscape(letter)
    mc.draw_cut_guides(c, mc.CARD1_X, mc.CARD_Y, tab_pos=0)
    mc.draw_card(c, mc.CARD1_X, mc.CARD_Y, drug, tab_pos=0)
    c.save()
    buf.seek(0)
    pdf_b64 = base64.b64encode(buf.read()).decode()
    return jsonify({"pdf_b64": pdf_b64})


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════╗")
    print("║  Drug Card Creator — ready!          ║")
    print("║  Open: http://localhost:5000         ║")
    print("╚══════════════════════════════════════╝\n")
    app.run(debug=False, port=5000)

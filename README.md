# Drug Card Creator

A local web application for creating pharmacy reference cards that match
the exact format of the main drug card deck.

## Quickstart — Double Click to Open

**Windows:**
Double-click `launcher.pyw`
> If nothing happens, right-click → Open with → Python

**Mac:**
Double-click `launcher.pyw`
> If blocked, right-click → Open → Open anyway (first time only)

The launcher will:
1. Install any missing dependencies automatically
2. Start the Flask server in the background
3. Open the card creator in your browser
4. Show a small status window — close it to stop the server

---

## Requirements

- Python 3.8+ (must be installed on your system)
- `flask` and `reportlab` — installed automatically on first launch

## Manual Start (if double-click doesn't work)

```
cd card_creator
python app.py
```
Then open: http://localhost:5000

## How to Use

1. **Fill in the form** on the left side panel
2. **Sections tab** — reorder, enable/disable, add custom sections
3. **Layout tab** — choose tab position (1–5) or leave on Auto
4. Click **Generate PDF** to download print-ready cards

## Output

Cards are identical in format to the main drug card deck:
same dimensions, color system, tab positioning, cut guides, and overflow logic.

## Stopping the App

Close the launcher window, or press `Ctrl+C` in the terminal if running manually.


A local web application for creating pharmacy reference cards that match
the exact format of the main drug card deck.

## Requirements

- Python 3.8+
- The following Python packages (install once):
  ```
  pip install flask reportlab
  ```
- `make_cards.py` must be in the parent directory (already in place)

## How to Run

1. Open a terminal
2. Navigate to this folder:
   ```
   cd card_creator
   ```
3. Start the app:
   ```
   python app.py
   ```
4. Open your browser and go to:
   ```
   http://localhost:5000
   ```

## How to Use

1. **Fill in the form** on the left side panel:
   - **Generic Name** — the drug's generic name
   - **Brand Name** — comma-separate multiple brands (e.g. "Prinivil, Zestril")
   - **Alphabet Determining Name** — controls the tab letters and sort order
   - **Drug Class** — shown in small text above the generic name
   - **Indications** — comma-separated (e.g. "Hypertension, HFrEF, CKD")
   - **Adverse Effects** — comma-separated, aim for 4-5 max
   - **Black Box Warning** — full text, or just "None"
   - **Meal & Timing Considerations** — plain paragraph text
   - **Clinical Pearls** — semicolon-separated bullets

2. **Add more cards** using the "+ Add Card" tab button

3. **Watch the live preview** update as you type — it matches the visual
   style of the real cards

4. Click **Generate PDF** to download a print-ready PDF using the exact
   same ReportLab rendering engine as the full drug deck

## Output

The generated PDF is identical in format to the main drug card deck:
- Same card dimensions (3.5" × 4.5" + tab)
- Same color system (tab and header color based on Alphabet Determining Name)
- Same tab positioning system (5 staggered stops)
- Same section layout and typography
- Same overflow logic (long sections move to back card)
- Same cut guide format
- Landscape letter paper, 2 cards per page

## Stopping the App

Press `Ctrl+C` in the terminal to stop the server.

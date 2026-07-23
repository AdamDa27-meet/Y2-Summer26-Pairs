# Pixel & UX Helper — Backend (main.py)

A dual-agent AI design assistant, built on the Anthropic API. Includes:

- **Pixel** — a UI/UX design mentor agent with tools for scheduling, mockup
  generation/editing, tailored design reference docs, and file analysis
- **UX Helper AI** — a focused UX advisor agent
- **Both mode** — sends a message to both agents and shows/combines
  whichever response(s) are most useful

Everything lives in a single file: `main.py`.

---

## 1. Requirements

- Python 3.9 or newer
- An [Anthropic API key](https://console.anthropic.com/)
- (Optional) A Google Cloud OAuth client, if you want Google Calendar sync

---

## 2. Install dependencies

```bash
pip install anthropic python-dotenv pypdf python-docx google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

If a `requirements.txt` is included in this project instead, just run:

```bash
pip install -r requirements.txt
```

---

## 3. Set up your API key

Create a file named `.env` in the same folder as `main.py`:

```
ANTHROPIC_API_KEY=your-key-here
```

Replace `your-key-here` with your actual Anthropic API key. This file is
read automatically on startup — do not commit it to git or share it
publicly.

---

## 4. (Optional) Set up Google Calendar sync

This lets the `schedule` command read your existing busy times and add new
sessions to your Google Calendar. If you skip this, scheduling still works —
it just won't touch your actual calendar.

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create/select a project, then enable the **Google Calendar API**
3. Go to **APIs & Services → Credentials → + Create Credentials → OAuth
   client ID**
4. Application type: **Desktop app**
5. Download the resulting JSON file, rename it to `credentials.json`, and
   place it in the same folder as `main.py`
6. Do **not** commit `credentials.json` to git — see the `.gitignore` note
   below

The first time you use `schedule` → `google`, a browser tab will open asking
you to log in and approve access. After that, a `token.json` file is created
automatically so you won't be asked again.

---

## 5. Running it

```bash
python3 main.py
```

You'll be asked to choose:
- **1** — Pixel (UI design agent)
- **2** — UX Helper AI
- **3** — Both agents at once

You can type `switch` at any time inside either agent to return to this menu
without losing your place.

---

## 6. Commands (inside Pixel)

| Command | What it does |
|---|---|
| `schedule` | Builds a work schedule around your free time / existing calendar |
| `mockup` | Generates an HTML/CSS UI mockup; follow-up messages like "change the button color" edit the same file instead of creating a new one |
| `basics` | Generates a UI design fundamentals reference tailored to your app, audience, and platform; ask follow-up questions about it afterward without regenerating |
| `analyze file` / `summarize file` | Reads a `.txt`, `.md`, `.pdf`, or `.docx` file (or accepts pasted text) and summarizes/analyzes it |
| `summary` | Summarizes the current conversation |
| `reset` | Clears conversation history |
| `switch` | Returns to the agent picker |
| `exit` | Quits |

## Commands (inside UX Helper AI)

| Command | What it does |
|---|---|
| `export` | Saves the full conversation to `UX_Report.txt` |
| `reset` | Clears conversation history |
| `switch` | Returns to the agent picker |
| `exit` | Quits |

---

## 7. Security notes

- **Never commit `credentials.json`, `token.json`, or `.env` to version
  control.** Add these to `.gitignore`:
  ```
  credentials.json
  token.json
  .env
  ```
- If you ever accidentally commit these, regenerate the OAuth client in
  Google Cloud Console and get a fresh API key — treat exposed credentials
  as compromised even if they were never actually pushed to a public repo.

---

## 8. File outputs

Running the app creates these in the same folder:

- `mockups/mockup_N.html` — generated UI mockups
- `ui_design_basics.md` — the generated design reference doc
- `schedule.md` — a running log of generated schedules
- `UX_Report.txt` — exported conversations (from UX Helper AI's `export`)

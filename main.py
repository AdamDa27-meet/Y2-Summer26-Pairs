
import os
import re
import json
import base64
import webbrowser
from datetime import datetime, timedelta
from anthropic import Anthropic
from dotenv import load_dotenv
 
load_dotenv()
 
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
 
BASE_DIR = os.path.dirname(__file__)
MOCKUP_DIR = os.path.join(BASE_DIR, 'mockups')
BASICS_FILE = os.path.join(BASE_DIR, 'ui_design_basics.md')
SCHEDULE_FILE = os.path.join(BASE_DIR, 'schedule.md')
CREDS_FILE = os.path.join(BASE_DIR, 'credentials.json')   # from Google Cloud Console (see README)
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')          # auto-created after first Google login
 
os.makedirs(MOCKUP_DIR, exist_ok=True)
 
MODEL = 'claude-haiku-4-5-20251001'
 

TIMEZONE = 'Asia/Jerusalem'
 
SYSTEM_MESSAGE = """You are Pixel, a senior UI/UX designer and mentor.
 
Your ONLY focus is user interface and user experience design — layout, visual
hierarchy, color, typography, spacing, component choice, accessibility, and
usability flow. You do not write backend logic, databases, or app architecture
unless it directly affects the UI.
 
Keep responses practical and concrete. When giving feedback, point to specific
design principles (contrast, whitespace, affordance, consistency, etc.) rather
than vague opinions. Ask a clarifying question only when you genuinely can't
proceed without it.
"""
 

 # how the code uses oAuth Client to access the google calendar and if it fails it doesnt crash the code
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
 
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.events',
                   'https://www.googleapis.com/auth/calendar.readonly']
 
 
 
def ask_agent():
    which = input("Which Agent would you like to use?")
    if which == 'Agent 1' or '1' in which or 'Agent 1' in which:
        run_chat() # run agent 1
    elif which == 'Agent 2' or '2' in which or 'Agent 2' in which:
        running_chat() # run agent 2
    else:
        print("Please pick an available agent.")


 #checks if the credentials.json exists and uses it to to acceess the google calendar and returns None so an error doesnt appear. Also uses tokens.json if its previously logged in.
def get_calendar_service():
    """Returns an authenticated Google Calendar service, or None if unavailable/not set up."""
    if not GOOGLE_LIBS_AVAILABLE:
        return None
    if not os.path.exists(CREDS_FILE):
        return None
 

    #creates credentials if non existent
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, CALENDAR_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
 
    return build('calendar', 'v3', credentials=creds)
 
 # when accessing the google calendar it finds busy and free times with in the next 28 days and fills them according to the user request.
def fetch_google_busy_times(service, days_ahead=28):
    """Returns a plain-text list of upcoming events so Claude can schedule around them."""
    now = datetime.utcnow().isoformat()
    end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
    events_result = service.events().list(
        calendarId='primary', timeMin=now, timeMax=end,
        singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if not events:
        return "No upcoming events found."
    lines = []
    #creates and finds the time to add the task to the calendar in a formatable way.
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        end_t = e['end'].get('dateTime', e['end'].get('date'))
        lines.append(f"{e.get('summary', '(busy)')}: {start} - {end_t}")
    return "\n".join(lines)
 
 #creates the actual event with the description summary and uses the date as well.
def create_calendar_events(service, sessions):
    """Inserts parsed schedule sessions as events on the user's primary calendar."""
    created = 0
    for s in sessions:
        try:
            event = {
                'summary': s.get('title', 'UI Design Session'),
                'description': s.get('focus', ''),
                'start': {'dateTime': f"{s['date']}T{s['start_time']}:00", 'timeZone': TIMEZONE},
                'end': {'dateTime': f"{s['date']}T{s['end_time']}:00", 'timeZone': TIMEZONE},
            }
            service.events().insert(calendarId='primary', body=event).execute()
            created += 1
        except Exception as e:
            print(f"Could not add session '{s.get('title')}': {e}")
    return created
 
 
def describe_calendar_image(path):
    """Sends a photo/screenshot of an existing calendar to Claude and returns the busy slots it sees."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return ""
    ext = path.lower().rsplit('.', 1)[-1]
    media_type = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                  'webp': 'image/webp'}.get(ext, 'image/jpeg')
    #reads the image file in binary instead of regular text, and ensures that the result is a regular python string. 'rb' is read binary instead of 'r,' read.
    with open(path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
 
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_b64}},
                {'type': 'text', 'text': "List every busy/booked time slot visible in this calendar image "
                                          "as plain text lines (day/date + time range). Just the list, no extra commentary."}
            ]
        }]
    )
    return response.content[0].text
 
 
def extract_json_sessions(text):
    """Pulls the fenced ```json [...] ``` block out of Claude's schedule response, if present."""
    match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL) #searches for specific characters and find the important information and creates empty space to make it readable. #uses re library to search for and replace characters.
    if not match:
        return []
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
 
 
def strip_json_block(text):
    return re.sub(r'```json.*?```', '', text, flags=re.DOTALL).strip()#again, re.sub uses the re library to substitue xyz, with zyx.
 
 
def ask_claude(system, messages, max_tokens=800, temperature=0.7, tools=None):
    kwargs = dict(model=MODEL, max_tokens=max_tokens, temperature=temperature,
                  system=system, messages=messages)
    if tools:
        kwargs['tools'] = tools
    return client.messages.create(**kwargs)
 
 
def cmd_schedule(history):
    """Build a work schedule for the UI project around the user's free time / existing calendar."""
    print("\nLet's build a schedule around your actual free time.")
    project = goal or input("What is the project or app name? (or leave blank): ")
    deadline = input("Any deadline or target date? (or leave blank): ")
 
    calendar_choice = input(
        "Pull busy times from an existing calendar first? "
        "(google / image / no): "
    ).strip().lower()
 
    busy_info = ""
    calendar_service = None
    #user is asked 3 options for the calendar, google calendar, python HTML file, or manual. google uses get_calendar_service() to access the authetnticator client and edit tasks.
    if calendar_choice == 'google':
        calendar_service = get_calendar_service()
        if calendar_service:
            busy_info = fetch_google_busy_times(calendar_service)
            print("Pulled busy times from your Google Calendar.")
        else:
            print("Google Calendar isn't set up yet (see README.md for one-time setup).")
            print("Continuing without it — you can still describe your free time manually.")
    #uses binary to read the image file through describe_calendar_image(img_path) - where image path is the file name of the downloaded image.
    elif calendar_choice == 'image':
        img_path = input("Path to a screenshot/photo of your calendar: ").strip()
        busy_info = describe_calendar_image(img_path)
        if busy_info:
            print("Read your calendar image.")
 
    free_time = input("Describe your free time (e.g. 'Mon/Wed/Fri evenings 7-9pm, Sat afternoon'): ")
 
    today = datetime.now().strftime('%Y-%m-%d')
    prompt = f"""Create a realistic UI-design work schedule.
 
Today's date: {today}
Project: {project}
Deadline: {deadline or 'none given'}
Existing commitments already on the calendar: {busy_info or 'none provided'}
User-stated free time: {free_time}
 
Break the work into UI-design stages (research/moodboard, wireframes, high-fidelity
mockups, review/iterate) and slot them into real upcoming dates within the user's
free time, avoiding the existing commitments listed above. Aim for 2-hour sessions
unless the free-time slot is shorter.
 
First, output a short human-readable markdown table: Session | Date | Time | Focus | Deliverable.
 
Then, output the exact same sessions as a fenced JSON block with this schema:
```json
[{{"date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM", "title": "short title", "focus": "what this session covers"}}]
```
"""
    response = ask_claude(
        system="You are a scheduling assistant specialized in creative/design work. Be concise and realistic.",
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1200,
    )
    plan_text = response.content[0].text
    sessions = extract_json_sessions(plan_text)
 
    with open(SCHEDULE_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## Schedule generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Project: {project}\n\n")
        f.write(plan_text)
 
    print(f"\n{strip_json_block(plan_text)}\n")
    print(f"Saved to {SCHEDULE_FILE}")
 
    if sessions:
        if calendar_service is None:
            calendar_service = get_calendar_service()
        if calendar_service:
            add = input(f"\nAdd these {len(sessions)} sessions to your Google Calendar? (y/N): ")
            if add.lower() == 'y':
                created = create_calendar_events(calendar_service, sessions)
                print(f"Added {created}/{len(sessions)} sessions to Google Calendar.")
        else:
            print("\n(Google Calendar not connected — sessions saved to schedule.md only. "
                  "See README.md if you'd like to enable calendar sync.)")
 
 

 #creates an HTML file that automatically downloads on your computer and is linked in your fies.
def cmd_mockup(user_message=None):
    """Generate a self-contained HTML/CSS file for a described screen, then open it in a browser."""
    if user_message:
        description = user_message
    else:
        description = input("\nDescribe the screen/component you want mocked up: ")
    style_notes = input("Any style direction? (colors, mood, brand — or leave blank): ")
 
    prompt = f"""Generate a single self-contained HTML file (inline <style>, no external
dependencies except optionally Google Fonts) that implements this UI screen as a
static, realistic-looking mockup:
 
Screen: {description}
Style direction: {style_notes or 'use your best judgment, keep it clean and modern'}
 
Requirements:
- Fully valid HTML5 document (doctype, head, body).
- All CSS inline in a <style> tag.
- Use realistic placeholder text/data, not lorem ipsum.
- Responsive enough to look right on a typical laptop screen.
- No JavaScript needed unless essential for showing the layout (e.g. a dropdown state).
- Output ONLY the HTML code, no explanation, no markdown code fences.
"""
    response = ask_claude(
        system="You are an expert front-end UI developer who writes clean, semantic, well-styled HTML/CSS mockups.",
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=3000,
        temperature=0.6,
    )
    code = response.content[0].text.strip()
    code = re.sub(r'^```(?:html)?\n?', '', code)
    code = re.sub(r'\n?```$', '', code)
    #
 
    #only keeps files created that starts with mockup reducing clutter and possible overwriting or overlapping.
    existing = [f for f in os.listdir(MOCKUP_DIR) if f.startswith('mockup_')]
    n = len(existing) + 1
    filename = os.path.join(MOCKUP_DIR, f'mockup_{n}.html')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
 
    print(f"\nSaved mockup to {filename}")
    try:
        webbrowser.open(f'file://{os.path.abspath(filename)}')
        print("Opened it in your browser.")
    except Exception:
        print("Open it manually in a browser to view it.")
 

 #uses similair code to the previous mockup function but reads the current HTML code and alters it in the way asked by the user, instead of making a new mockup each time.
def cmd_edit_mockup(instruction, filepath):
    """Applies a natural-language change to an existing mockup file, in place."""
    with open(filepath, 'r', encoding='utf-8') as f:
        current_code = f.read()

    prompt = f"""Here is the current HTML/CSS mockup:

```html
{current_code}
```

Apply this requested change: {instruction}

Output the FULL updated HTML file (not a diff, not just the changed part) —
keep everything else exactly the same except what the instruction asks to
change. Output ONLY the HTML code, no explanation, no markdown code fences."""

    response = ask_claude(
        system="You are an expert front-end UI developer. Make precise, targeted edits to an "
               "existing HTML/CSS mockup without unnecessarily rewriting unrelated parts.",
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=3000,
        temperature=0.4,
    )
    code = response.content[0].text.strip()
    code = re.sub(r'^```(?:html)?\n?', '', code)
    code = re.sub(r'\n?```$', '', code)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"\nUpdated {filepath}")
    try:
        webbrowser.open(f'file://{os.path.abspath(filepath)}')
        print("Opened the updated version in your browser.")
    except Exception:
        print("Open it manually in a browser to see the changes.")

    return filepath


#generates the file with the basics of UI according to the app, audience, and platform.
def cmd_basics():
    """Create a UI fundamentals reference file, tailored to the user's specific app and audience,
    including a web-researched section on designing for that audience."""
    print("\nLet's tailor this to your actual app.")
    app_desc = input("What does your app do? (one or two sentences): ")
    audience = input("Who is it for? (age range, profession, context of use, etc.): ")
    platform = input("What platform is it for? (iOS, Android, web, desktop...): ")
    #if its not the first time creating a file, it asks to overwrite a file.
    if os.path.exists(BASICS_FILE):
        overwrite = input("\nui_design_basics.md already exists. Regenerate it? (y/N): ")
        if overwrite.lower() != 'y':
            print(f"Keeping existing file at {BASICS_FILE}")
            return
 
    general_prompt = """Write a concise, practical reference covering the fundamentals of
UI design for a beginner building their own app. Cover: visual hierarchy, color
theory basics, typography basics, spacing/layout (grids, whitespace), contrast &
accessibility, consistency & design systems, and common beginner mistakes. Use
markdown headers and short bullet points, not long paragraphs. Keep it under 500 words."""
 
    general_response = ask_claude(
        system="You are a UI/UX educator who writes clear, beginner-friendly reference material.",
        messages=[{'role': 'user', 'content': general_prompt}],
        max_tokens=900,
        temperature=0.5,
    )
    general_content = general_response.content[0].text
 
    print("\nLooking up current design guidance for your specific audience...")
    search_prompt = f"""Search the web for current, specific UI/UX design guidance relevant to this app:
 
App: {app_desc}
Target audience: {audience}
Platform: {platform}
 
Find and summarize practical guidance on: accessibility needs specific to this
audience, interaction patterns this audience already expects, color/typography
considerations, platform-specific conventions (e.g. iOS Human Interface Guidelines,
Material Design) if relevant, and common usability pitfalls for this audience.
Write it as actionable markdown bullet points grouped under short subheadings.
Briefly note the source of any specific claim in parentheses."""
 
    search_response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system="You are a UX researcher. Use web search to find current, specific, practical "
               "UI design guidance. Keep it concise and actionable.",
        messages=[{'role': 'user', 'content': search_prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )
    audience_content = "\n".join(
        block.text for block in search_response.content if getattr(block, 'type', None) == 'text'
    ).strip()
    if not audience_content:
        audience_content = "(Web search returned no usable results — check that your Anthropic account has web search enabled.)"
 
    full_content = f"""# UI Design Basics — tailored for: {app_desc}
 
**Target audience:** {audience}
**Platform:** {platform}
 
{general_content}
 
## Audience & Platform-Specific Considerations
 
{audience_content}
"""
 #adds the information to the document, making a full document and savings it to the file.
    with open(BASICS_FILE, 'w', encoding='utf-8') as f:
        f.write(full_content)
 
    print(f"\n{full_content}\n")
    print(f"Saved to {BASICS_FILE}")
 

# -----------------------------
# Tool Function
# -----------------------------
def export_to_file(content):
    filename = "UX_Report.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    return filename


# -----------------------------
# Chat Function
# -----------------------------
def running_chat():

    print("=== UX Helper AI ===")
    print("Type 'export' to save the conversation.")
    print("Type 'reset' to clear the chat.")
    print("Type 'exit' to quit.\n")

    history = []

    system_message = """
WHO:
You are UX Helper AI, a UX design assistant.

WHAT:
Help users improve the UX of any web or mobile application.

You should:
- Identify the target audience.
- Suggest accessibility improvements.
- Explain how to make the app user-friendly.
- Recommend UX best practices.
- Give constructive feedback on app ideas.

WHAT YOU WILL NOT DO:
- Do not answer unrelated questions.
- Do not invent research or statistics.
- Do not generate code.
- Keep answers focused on UX.

Every response MUST follow this format:

[Summary]:
Repeat the user's request in one sentence.

[Response]:
Provide UX advice.

[Next Step]:
Suggest one concrete action the user can take.
"""

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            history = []
            print("Conversation cleared.")
            continue

        if user_input.lower() == "export":

            conversation = ""

            for message in history:
                conversation += f"{message['role'].upper()}:\n{message['content']}\n\n"

            filename = export_to_file(conversation)

            print(f"Conversation exported to {filename}")
            continue

        history.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            temperature=0.7,
            system=system_message,
            messages=history
        )

        reply = response.content[0].text

        print("\nUX Helper AI:")
        print(reply)

        history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )


def run_chat():
    print("You: Pixel here — your UI design assistant.")
    print("Commands: 'schedule' (plan work around your free time / calendar), 'mockup' (generate an HTML mockup),")
    print("          'basics' (tailored UI design reference), 'summary', 'reset', 'exit'")
    global goal
    goal = input("\nWhat are you designing / what's your goal for this session?: ")
    history = []
 
    system_message = SYSTEM_MESSAGE + f"\n\nThe user's current goal for this session: {goal}"

    lastmockup_path = None  # Track the last mockup file path for potential edits
    while True:
        user_input = input('\n>> ').strip()
 
        if user_input == '':
            print("Please enter a message.")
            continue
 
        low = user_input.lower()
 
        if low == 'exit' or 'quit' in low or 'bye' in low or 'goodbye' in low or 'end' in low:
            print("Exiting. Good luck with the design!")
            break
 
        if low == 'help' or 'commands' in low or 'options' in low:
            print("Available commands: 'schedule', 'mockup', 'basics', 'summary', 'reset', 'exit'")
            continue


        if low == 'reset' or 'reset' in low or 'clear' in low:
            history = []
            print("History cleared.")
            continue
 
        if low == 'schedule' or 'schedule' in low or 'calendar' in low or 'plan' in low:
            cmd_schedule(history)
            continue
 
        if low == 'mockup' or 'mockup' in low or 'html' in low or 'prototype' in low:
            edit_list = ['change', 'edit', 'update', 'modify', 'replace' 'can you', 'make it', 'adjust', 'improve', 'fix']
            edit_detected = any(word in low for word in edit_list)
            if edit_detected and lastmockup_path:
                cmd_edit_mockup(user_input, lastmockup_path)
            else:
                if edit_detected and not lastmockup_path:
                    print("No previous mockup found to edit. Please create a mockup first.")
                lastmockup_path = cmd_mockup(user_input)
            cmd_mockup(history)
            continue
 
        if low == 'basics' or 'basics' in low or 'reference' in low or 'guide' in low:
            cmd_basics()
            continue
 
        if low == 'summary' or 'summary' in low or 'recap' in low or 'review' in low:
            if not history:
                print("No conversation history to summarize.")
                continue
            summary = ask_claude(
                system="Summarize the chat history so far. Keep it short and coherent.",
                messages=history + [{'role': 'user', 'content': "Please summarize the chat history so far."}],
                max_tokens=300,
            )
            print(f"Summary: {summary.content[0].text}")
            continue
 
        history.append({'role': 'user', 'content': user_input})
 
        response = ask_claude(system_message, history, max_tokens=500)
        reply = response.content[0].text
        history.append({'role': 'assistant', 'content': reply})
 
        print(f"\nPixel: {reply}")
 
        usage = response.usage
        total = usage.input_tokens + usage.output_tokens
        print(f"[tokens: {usage.input_tokens} in / {usage.output_tokens} out / {total} total]")
 
 
if __name__ == '__main__':
    ask_agent()
 



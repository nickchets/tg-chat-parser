PROJECT_UPDATE.md: Interactive Telegram-to-Book Exporter
1. Objective
Refactor the existing Telegram Exporter into an interactive CLI tool with a user-friendly interface, enhanced formatting capabilities, and robust session management.
2. New Requirements & User Inputs
2.1. Interactive Setup (Startup Flow)
Auth Check: Before starting, check if a valid session.session exists.
If no: Prompt for Phone Number (+7...) and then the Confirmation Code.
If yes: Display "Authorized as [Username]".
Input: Channel Source: Prompt for CHANNEL_URL or username.
Input: Temporal Scope: Ask for START_DATE in dd.mm.yyyy format. Default to 4 months ago if empty.
Toggle: Image Positioning:
[1] Images Before Text
[2] Images After Text (Default)
Toggle: Hyperlink Handling:
[1] Ignore Links (Plain text)
[2] Active Hyperlinks (Blue/Underlined and Clickable)
2.2. Enhanced Features (GSI Recommended)
Progress Visualization: Use the tqdm or rich library to show a real-time progress bar while fetching messages and downloading media.
Summary Table: After completion, display a summary: Total Posts, Images Downloaded, Links Found.
File Naming: Automatically name the output file based on the channel name and date range (e.g., Methodology_PsychicAlchemy_Jan25_May25.docx).
3. Technical Logic Modifications
3.1. Telegram Client (src/tg_client.py)
Implement interactive_auth() method using Telethon's client.start().
Update fetch_messages to accept the dd.mm.yyyy string and convert it to UTC datetime.
3.2. DOCX Client (src/docx_client.py)
Image Position Toggle: Modify add_post() to respect the image_position flag.
The Hyperlink Hack: python-docx does not support hyperlinks natively in a simple way. You must implement a helper function that accesses the document's XML (using docx.oxml) to create a relationship and an r:id for the URL.
Agent Note: Implement add_hyperlink(paragraph, url, text).
3.3. Main Orchestrator (main.py)
Wrap the logic in an interactive loop using input() or rich.prompt.
Handle KeyboardInterrupt gracefully (save what's already processed).
4. Instructions for Windsurf Agent
Read and Analyze: Scan the current src/ folder to understand the AlbumGrouper and DocxExporter logic.
Implement CLI UI: Use rich library for a beautiful console interface (colors, panels, prompts).
Refactor Auth: Move the logic from auth_telegram.py directly into the startup flow of main.py.
Fix Hyperlinks: This is the priority. Ensure links in the DOCX are actually clickable in Word/Google Docs, not just colored blue.
Clean Up: Remove all dead code related to gdocs_client.py as we are focusing on the High-Quality DOCX/PDF path.
5. Metadata for active links (Python snippet for Agent)
code
Python
# Use this logic to implement real hyperlinks
def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id, )
    new_run = docx.oxml.shared.OxmlElement('w:r')
    rPr = docx.oxml.shared.OxmlElement('w:rPr')
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink
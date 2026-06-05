# 🎙️ GestureGaze_Voice User Manual & Command List

Welcome to the comprehensive command manual for the **GestureGaze_Voice** system. This document outlines every capability, intent, system state, and limitation to help you fully harness the system's voice control and automation features.

---

## 1. System States

The system operates using a localized state machine to ensure security, prevent accidental triggers, and correctly handle ambiguous or dangerous commands.

*   **LISTENING_WAKE_WORD**: The idle default state. The system is securely listening **only** for the wake word (or registration commands). General commands will not execute.
*   **ACTIVE_COMMAND_MODE**: Activated upon a recognized wake word. The system grants a **30-second window** during which any command can be executed. Continuous interactions refresh this timer. If inactive, the system silently relocks.
*   **CONFIRMATION_WAIT**: A specialized 15-second blocking state triggered by dangerous actions (e.g., deleting a file, shutting down). The system suspends regular listening and waits explicitly for a "Yes" or "No".
*   **REGISTRATION_WAITING_FOR_NAME**: The state where the system waits for a new user to speak their name (e.g., "My name is John").
*   **RECORDING_VOICE_SAMPLE**: The system blocks to securely capture static audio samples (3 samples, 5 seconds each) to build a voice printing profile.

---

## 2. Voice Security

GestureGaze_Voice uses advanced speaker authentication via Resemblyzer embeddings. A user's voice print must match with >= `0.65` cosine similarity to be authorized for secure commands.

### Profile Management
*   **Register User**: `"register new user"`, `"register my voice"`. *(System will ask for a name, then guide you to speak a phrase to capture audio)*.
*   **Identify User**: `"who am i"`, `"who is speaking"`, `"what is my name"`, `"identify user"`.
*   **Delete Voice Profile**: `"delete my voice"`, `"remove my voice"`, `"clear my voice"`, `"delete user"`. *(Requires active authentication)*.

### Security Commands
*   **Wake Word**: `"voice mode activate"`, `"voice mode"`, `"more doctor"` *(misheard)*, `"mode activ"`.
*   **Activate Secure Mode**: `"secure voice mode"`. *(Enforces identity verification against the current speaker's voice on every command)*.
*   **Lock System**: `"lock system"`. *(Locks Windows and places the Voice system back to LISTENING_WAKE_WORD)*.
*   **Global Reset**: `"reset system"`. *(A hard override that resets the voice engine back to listening for the wake word, clearing errors or hung loops)*.

---

## 3. System Controls

Direct hardware and operating system integration using `pyautogui` and `screen_brightness_control`.

*   **Increase Volume**: `"volume up"`, `"increase volume"`, `"louder"`, `"make it louder"`
*   **Decrease Volume**: `"volume down"`, `"decrease volume"`, `"quieter"`, `"make it quieter"`
*   **Mute / Unmute**: `"mute"`, `"mute audio"`, `"silence"`, `"shut up"`, `"unmute"`, `"restore volume"`
*   **Increase Brightness (+10%)**: `"brightness up"`, `"increase brightness"`, `"brighter"`, `"make it brighter"`
*   **Decrease Brightness (-10%)**: `"brightness down"`, `"decrease brightness"`, `"dimmer"`, `"dim screen"`
*   **Take Screenshot**: `"take screenshot"`, `"screenshot"`, `"capture screen"`, `"print screenshot"`, `"excrete"` *(misheard)*. *(Saves time-stamped PNG to `Pictures/Screenshots`)*.
*   **Window Control**: `"close window"` *(Alt+F4)*, `"minimize window"` *(Win+Down)*
*   **Task Manager**: `"task manager"`
*   **Shutdown**: `"shutdown"`, `"shut down"`. *(Requires confirmation. Currently configured to log warning only for safety)*.

---

## 4. Media Control

Controls the active media player (Spotify, YouTube, Media Player, etc.).

*   **Play / Pause**: `"play"`, `"play music"`, `"pause"`, `"resume"`, `"stop"`, `"stop music"`
*   **Next Track**: `"next"`, `"next track"`, `"skip"`
*   **Previous Track**: `"previous"`, `"previous track"`, `"back track"`

---

## 5. Application Control

Say **"open"**, **"start"**, or **"launch"** followed by the target application.

**Supported Applications & Aliases**:
*   **Browsers**: Google Chrome (`"chrome"`, `"google"`), Edge
*   **Office**: Word, Excel, PowerPoint, Outlook, OneNote, Teams
*   **System Tools**: Calculator, Notepad, Paint (`"ms paint"`), File Explorer, Task Manager, Control Panel, Command Prompt (`"cmd"`), PowerShell, Settings, Microsoft Store
*   **Dev Tools**: Visual Studio, VS Code (`"code"`, `"visual studio code"`), Android Studio, Terminal, Git Bash, WSL, Python
*   **Media & Web Apps**: Camera, Photos, WhatsApp (`"what's up"`, `"var sab"`), Spotify, My Account
*   **Windows Utilities**: Weather, Calendar, Clock, Snipping Tool, Sound Recorder, Sticky Notes, Phone Link

---

## 6. File System Control

GestureGaze_Voice includes comprehensive file management capabilities mapping human commands to system operations. 

### File Actions
*   **Open File**: `"open file [name]"` OR `"open file [name] inside [folder]"`
*   **Open Folder**: `"open folder [name]"`
*   **Search/Find File**: `"search file [name]"`, `"find file [name]"`, `"search for [name]"`
*   **Create Folder**: `"create folder [name]"`, `"make folder [name]"`, `"new folder [name]"`
*   **Create File**: `"create file [name] in [type]"`, `"make file [name] in [type]"` 
*   **Move File**: `"move file [name] to [folder]"`
*   **Delete File**: `"delete file [name]"`, `"delete file [name] in [type]"` *(Danger Action, triggers confirmation)*.
*   **Open in VS Code**: `"open [name] in vs code"`

### Supported File Type Mapping
When creating or deleting files, provide the "spoken type" to map exactly to the correct extension:
*   `word` → `.docx` (or `.doc`)
*   `excel` → `.xlsx` (or `.xls`)
*   `powerpoint` → `.pptx` (or `.ppt`)
*   `text` → `.txt`
*   `python` → `.py`
*   `image` → `.png` (searches `.jpg`, `.jpeg`, `.gif`)
*   `pdf` → `.pdf`
*   `zip` → `.zip`

---

## 7. Confirmation Commands

When a dangerous action is invoked (e.g., **Lock System**, **Shutdown**, **Delete File**), the system enters the `CONFIRMATION_WAIT` state for 15 seconds.

During this state, the microphone pauses background hearing and awaits explicit input:
*   **Valid YES Responses**: `"yes"`, `"yeah"`, `"yep"`, `"confirm"`, `"do it"`, `"sure"`
*   **Valid NO Responses**: `"no"`, `"cancel"`, `"stop"`, `"don't"`, `"nah"`, `"nope"`

**Confirmation Behaviors**:
*   **Authentication Check**: If Secure Mode is active, the confirmation voice must closely match the logged-in user. Mimics or unauthorized voices will be rejected.
*   **Invalid Responses**: Allowed up to 2 invalid attempts before the operation auto-cancels.
*   **Timeout**: If no response is heard for 15 seconds, the action cancels and the system returns to its idle state.

---

## 8. Limitations

*   **Fuzzy Target Matching**: The system uses string-based fuzzy matching (0.75 accuracy cutoff) to discover folder and file names. Very complex, ultra-technical, or extremely short single-character files might mismatch. 
*   **File Search Scope**: File and folder CRUD commands (Move, search, create, delete, open) primarily target and scan the user's `Desktop` and `OneDrive/Desktop` paths. The system actively skips large or system folders (e.g., `.git`, `node_modules`, `venv`, `AppData`). Searching for deep `C:\Windows\` nested files is not currently supported natively by these commands.
*   **Speech Recognition Nuances**: Operates heavily on recognizing phonetic aliases for common errors (e.g. "excrete" interpreted as "take screenshot" due to API artifacts).
*   **Voice Sample Requirement**: During User Registration, a user **must** say "My name is [Name]" due to limitations in Google's Speech API recognizing single word utterances effectively.

---

## 9. Examples

Here are some real-world flow examples connecting multiple commands.

**Standard Start and Usage:**
> `"Voice mode activate"` → *(System recognizes you, activates 30-sec mode)*
> `"Take screenshot"`
> `"Open file annual report in pdf"`
> `"Volume down"`

**Creating and Managing Files:**
> `"Create folder tax documents"`
> `"Create file notes in word"`
> `"Move file notes to tax documents"`

**Secure Deletion:**
> `"Delete file resume in text"`
> *(System: "Are you sure you want to delete resume.txt?")*
> `"Yes"`
> *(System matches voice print, secures the transaction, and deletes file)*

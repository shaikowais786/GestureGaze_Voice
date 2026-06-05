# 🎙️ GestureGaze_Voice

GestureGaze_Voice is an advanced, AI-powered secure voice control and automation system. It integrates high-fidelity local speech recognition, voice biometrics (speaker authentication), and system automation to allow users to securely control their operating system, manage applications, and perform file system operations entirely through voice commands.

The system uses a localized state machine to ensure execution security, preventing unauthorized access using state-of-the-art speaker embeddings.

---

## 🚀 Key Features

- **Secure Voice Biometrics**: Utilizes speaker-recognition embeddings (via Resemblyzer) with cosine similarity verification (`>= 0.65`) to authenticate voice profiles and verify user identity.
- **Localized Speech-to-Text**: Integrates the Vosk offline speech recognition engine for private, low-latency command parsing.
- **Ambient Noise Calibration**: Automatically adjusts audio capture thresholds dynamically for clear voice processing in variable environments.
- **Robust Command Parser**: Built-in regex and semantic fuzzy-matching parser with phonetic error correction (e.g. handling "sistum" as "system", "excrete" as "screenshot").
- **Operating System Control**: Native execution of system commands (volume adjust, mute, screen brightness, window minimize/close, lock system, task manager, and direct shutdown).
- **Application Launcher**: Start, open, and switch between common applications (Browsers, MS Office, Dev Tools like VS Code/Command Prompt, and Windows utilities).
- **File System Management (CRUD)**: Create, open, search, move, and recycle files/folders directly on the Desktop/OneDrive. Supports Office templates (`.docx`, `.xlsx`, `.pptx`) and developers' file types (`.py`, `.html`, `.txt`, `.pdf`, `.zip`).
- **Robust Confirmation Handling**: Triggers automatic confirmation prompts for critical/dangerous system commands.

---

## 📂 Project Structure

```
GestureGaze_Voice/
├── actions/                         # Action execution modules
│   ├── __init__.py
│   ├── action_manager.py            # Central dispatcher mapping parsed intents to actions
│   ├── app_controller.py            # Application launch logic & paths
│   ├── file_controller.py           # Desktop/OneDrive file CRUD operations
│   └── system_controller.py         # Hardware controls (Volume, Brightness, Windows APIs)
├── models/                          # Speech recognition model directory
│   ├── model/                       # Extracted Vosk model files (Git ignored)
│   └── .gitkeep
├── modules/                         # Core utility & processing modules
│   ├── __init__.py
│   ├── command_parser.py            # Spoken text normalizer and intent matcher
│   ├── speaker_authentication.py    # Embeddings extractor & cosine similarity verifier
│   └── speech_recognition_engine.py  # Local mic-listener and noise calibrator
├── security/                        # Authorization and credential managers
│   ├── __init__.py
│   ├── security_mode.py             # Active command session verification states
│   └── user_manager.py              # User profiles storage (Pickle-based)
├── users/                           # Database folder for user voice templates
│   ├── voice_profiles.pkl           # Pickled speaker embeddings database (Git ignored)
│   └── .gitkeep
├── Voice Commands Manual.md         # Detailed end-user manual and command cheat sheet
├── README.md                        # Project documentation
├── requirements.txt                 # Project environment dependencies
├── main.py                          # Core entry point starting the listening loop
├── controller.py                    # Core system finite state machine (FSM)
├── download_upgrade_model.py        # Utility script to download 1.8GB Vosk model
└── revert_model.py                  # Utility script to revert model to backup
```

---

## 🛠️ System Requirements & Prerequisites

### Prerequisites

1.  **Python 3.8 - 3.11** (recommended: Python 3.10).
2.  **Visual Studio C++ Build Tools** (Required to compile specific speech/embedding dependencies like `dlib` during package installation).
3.  **Active Microphone Input Device**.

### Windows Dependencies

Ensure you have `PyAudio` pre-compiled binaries if installing on Windows fails:

```bash
pip install pipwin
pipwin install pyaudio
```

---

## ⚙️ Setup & Installation

1.  **Clone the Repository**:

    ```bash
    git clone <repository_url>
    cd GestureGaze_Voice
    ```

2.  **Create and Activate Virtual Environment**:

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Required Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Download Vosk Speech Model**:
    The system requires a local Vosk model placed inside `models/model/`.
    - **Lightweight Model (Default)**: Download `vosk-model-small-en-us-0.15` (approx 40MB) from [Vosk Models](https://alphacephei.com/vosk/models).
    - **High-Accuracy Model (Recommended)**: You can upgrade to the large 1.8GB model by running:
      `bash
    python download_upgrade_model.py
    `
      Ensure your final model folder structure looks like this:
    ```
    GestureGaze_Voice/
    └── models/
        └── model/
            ├── conf/
            ├── graph/
            ├── am/
            └── ...
    ```

---

## 🎮 How to Run and Use the System

### Starting the System

Run the main script from your terminal:

```bash
python main.py
```

Upon startup, the system will calibrate for background noise, prompt `System ready. Listening for wake word.`, and enter the `LISTENING_WAKE_WORD` state.

### Core Interaction Workflow

1.  **Wake Word**: Say `"Voice mode activate"` to start an active command session.
2.  **New User Registration**:
    - Say `"Register new user"`.
    - Follow the prompts to state your name: `"My name is <Your Name>"`.
    - Speak the required sentence three times to build your profile database.
3.  **Command Execution**: Run system, media, folder, file, and application launcher commands.
4.  **Inactivity Timeout**: The session auto-locks after 30 seconds of inactivity to preserve security.
5.  **Manual Reset**: Say `"Reset system"` to reset the state machine instantly.

For a full list of commands, voice security options, and detailed system states, see the [Voice Commands Manual](file:///c:/Users/ahmed/.gemini/antigravity/scratch/GestureGaze_Voice/Voice%20Commands%20Manual.md).

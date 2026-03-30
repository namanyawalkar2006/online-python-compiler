import streamlit as st
import subprocess
import tempfile
import os
import sys
import time
import re

# Optional ACE editor
try:
    from streamlit_ace import st_ace
    ACE = True
except:
    ACE = False

# ---------------- CONFIG ----------------
MAX_CODE_LENGTH = 5000
TIMEOUT = 5
BLOCKED = ["os", "sys", "subprocess", "shutil", "open", "eval", "exec"]

st.set_page_config(page_title="VS Code Python IDE", layout="wide")

# ---------------- SESSION ----------------
if "files" not in st.session_state:
    st.session_state.files = {
        "main.py": "# File 1\nprint('Hello 👋')",
        "second.py": "# File 2\nprint('Second file')"
    }
if "active_file" not in st.session_state:
    st.session_state.active_file = "main.py"
if "second_file" not in st.session_state:
    st.session_state.second_file = "second.py"
if "output" not in st.session_state:
    st.session_state.output = ""
if "logs" not in st.session_state:
    st.session_state.logs = ""
if "saved" not in st.session_state:
    st.session_state.saved = True
if "exec_time" not in st.session_state:
    st.session_state.exec_time = 0

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📁 Explorer")

    for file in st.session_state.files:
        if st.button(f"🐍 {file}", use_container_width=True):
            st.session_state.active_file = file

    new_file = st.text_input("New file")
    if st.button("➕ Add File") and new_file:
        st.session_state.files[new_file] = ""

    uploaded = st.file_uploader("Upload .py", type=["py"])
    if uploaded:
        st.session_state.files[uploaded.name] = uploaded.read().decode("utf-8")

    st.markdown("---")

    dark_mode = st.toggle("🌙 Dark Mode", True)
    split = st.toggle("🧩 Split Editor", True)
    font_size = st.slider("Font Size", 12, 24, 14)

    if st.button("💾 Save"):
        st.session_state.saved = True

    if st.button("🧹 Clear Output"):
        st.session_state.output = ""
        st.session_state.logs = ""

# ---------------- THEME ----------------
bg = "#433939" if dark_mode else "#ffffff"
text = "#d4d4d4" if dark_mode else "#111"

st.markdown(f"""
<style>
.stApp {{ background:{bg}; color:{text}; }}
.terminal {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 220px;
    background: black;
    color: #00ff9c;
    padding: 10px;
    font-family: monospace;
    overflow-y: auto;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- STATUS BAR ----------------
status = "● Unsaved" if not st.session_state.saved else "✔ Saved"
st.markdown(f"### 🧠 Python Compiler | {status} | ⏱ {st.session_state.exec_time}s")

# ---------------- SAFETY ----------------
def is_safe(code):
    for w in BLOCKED:
        if re.search(rf"\b{w}\b", code):
            return False, w
    return True, None

# ---------------- RUN ----------------
def run_code(code, user_input):
    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
            f.write(code)
            path = f.name

        result = subprocess.run(
            [sys.executable, path],
            input=user_input,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )

        os.remove(path)

        st.session_state.exec_time = round(time.time() - start, 3)

        out = result.stdout.strip()
        err = result.stderr.strip()

        res = "> python temp.py\n\n"
        if not out and not err:
            res += "No output"
        else:
            if out:
                res += out + "\n"
            if err:
                res += "\n[Error]\n" + err

        return res

    except subprocess.TimeoutExpired:
        return "> python temp.py\n\n[Error]\nTimeout"
    except Exception as e:
        return f"> python temp.py\n\n[Error]\n{str(e)}"

# ---------------- EDITORS ----------------
files = list(st.session_state.files.keys())

if split and len(files) > 1:
    col1, col2 = st.columns(2)

    with col1:
        code1 = st_ace(
            value=st.session_state.files[files[0]],
            language="python",
            theme="monokai" if dark_mode else "github",
            height=300,
            font_size=font_size
        ) if ACE else st.text_area("Editor 1", st.session_state.files[files[0]])

    with col2:
        code2 = st_ace(
            value=st.session_state.files[files[1]],
            language="python",
            theme="monokai" if dark_mode else "github",
            height=300,
            font_size=font_size
        ) if ACE else st.text_area("Editor 2", st.session_state.files[files[1]])

    st.session_state.files[files[0]] = code1
    st.session_state.files[files[1]] = code2

    main_code = code1
else:
    main_code = st_ace(
        value=st.session_state.files[st.session_state.active_file],
        language="python",
        theme="monokai" if dark_mode else "github",
        height=350,
        font_size=font_size
    ) if ACE else st.text_area("Editor", st.session_state.files[st.session_state.active_file])

    st.session_state.files[st.session_state.active_file] = main_code

# ---------------- INPUT ----------------
user_input = st.text_input("Program Input")

# ---------------- RUN ----------------
if st.button("▶ Run"):
    if len(main_code) > MAX_CODE_LENGTH:
        st.warning("Code too long")
    else:
        safe, word = is_safe(main_code)
        if not safe:
            st.error(f"Blocked: {word}")
        else:
            out = run_code(main_code, user_input)
            st.session_state.output = out
            st.session_state.logs += out + "\n"

# ---------------- TERMINAL ----------------
st.markdown(f'<div class="terminal">{st.session_state.output}</div>', unsafe_allow_html=True)
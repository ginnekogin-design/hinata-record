import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path
from openai import OpenAI
import zipfile
import io

st.set_page_config(
    page_title="ひなた記録 Ver.1.6",
    page_icon="☀️",
    layout="centered"
)

DATA_DIR = Path("data")
AUDIO_DIR = DATA_DIR / "audio"
DATA_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / "record_log.csv"

STAFF_LIST = [
    "小久保",
    "大森",
    "岸田",
    "その他"
]

USER_LIST = [
    "長田様",
    "辰江様",
    "岩堀様",
    "その他"
]

DEFAULTS = {
    "staff_name": STAFF_LIST[0],
    "current_start": "",
    "current_end": "",
    "saved_audio_path": "",
    "transcript": "",
    "draft": "",
    "record_state": "idle",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def safe_filename(text):
    text = text or "blank"
    for mark in ["/", "\\", ":", "*", "?", '"', "<", ">", "|", " "]:
        text = text.replace(mark, "_")
    return text


def save_log(row):
    if LOG_FILE.exists():
        df = pd.read_csv(LOG_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")


def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def transcribe_audio(audio_path):
    client = get_openai_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY が設定されていません")

    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            language="ja"
        )
    return result.text


mode = st.sidebar.radio("画面", ["記録入力", "管理者"])


if mode == "管理者":
    st.title("☀️ 管理者画面")

    password = st.text_input("管理者パスワード", type="password")

    if password != "hinata":
        st.warning("パスワードを入力してください")
        st.stop()

    st.success("管理者モード")

    st.subheader("保存済みログ")

    if LOG_FILE.exists():
        df = pd.read_csv(LOG_FILE)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "CSVダウンロード",
            data=csv.encode("utf-8-sig"),
            file_name="hinata_record_log.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("保存済みログはありません")

    st.divider()

    st.subheader("音声ファイル")

    audio_files = list(AUDIO_DIR.glob("*.wav"))

    if audio_files:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for audio_file in audio_files:
                zf.write(audio_file, arcname=audio_file.name)

        st.download_button(
            "音声ファイル一括ZIPダウンロード",
            data=zip_buffer.getvalue(),
            file_name="audio_files.zip",
            mime="application/zip",
            use_container_width=True,
        )

        for file in audio_files:
            st.write(file.name)
    else:
        st.caption("音声ファイルなし")

    st.stop()


st.title("☀️ ひなた記録 Ver.1.6")
st.caption("録音 → 確認 → 文字起こし → 記録")

with st.expander("担当者設定", expanded=False):
    selected_staff = st.selectbox(
        "担当者",
        STAFF_LIST,
        index=STAFF_LIST.index(st.session_state.staff_name)
        if st.session_state.staff_name in STAFF_LIST else 0
    )

    if selected_staff == "その他":
        other_staff = st.text_input("担当者名")
        if other_staff:
            st.session_state.staff_name = other_staff
    else:
        st.session_state.staff_name = selected_staff

st.info(f"担当：{st.session_state.staff_name}")

selected_user = st.selectbox("利用者", USER_LIST)

if selected_user == "その他":
    user_name = st.text_input("利用者名")
else:
    user_name = selected_user

service_type = st.selectbox(
    "種別",
    ["居宅", "同行", "通院介助", "移動支援", "その他"]
)

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ 開始", use_container_width=True):
        st.session_state.current_start = now_text()

with col2:
    if st.button("■ 終了", use_container_width=True):
        st.session_state.current_end = now_text()

st.info(
    f"開始：{st.session_state.current_start or '未入力'}　"
    f"終了：{st.session_state.current_end or '未入力'}"
)

st.divider()

st.subheader("🎙 録音")

if st.session_state.record_state == "idle":
    state_text = "🎙 録音開始"
elif st.session_state.record_state == "recorded":
    state_text = "📝 文字起こし"
else:
    state_text = "処理中"

st.markdown(
    """
    <style>
    div.stButton > button {
        min-height: 70px;
        font-size: 24px;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

col3, col4 = st.columns([3, 1])

with col3:
    main_action = st.button(state_text, use_container_width=True)

with col4:
    retry_action = st.button("🔄 やり直し", use_container_width=True)

if retry_action:
    st.session_state.saved_audio_path = ""
    st.session_state.transcript = ""
    st.session_state.record_state = "idle"
    st.rerun()


if st.session_state.record_state == "idle":
    audio_value = st.audio_input("録音")

    if audio_value is not None:
        st.audio(audio_value)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = (
            f"{timestamp}_"
            f"{safe_filename(st.session_state.staff_name)}_"
            f"{safe_filename(user_name)}.wav"
        )

        audio_path = AUDIO_DIR / filename

        with open(audio_path, "wb") as f:
            f.write(audio_value.getbuffer())

        st.session_state.saved_audio_path = str(audio_path)
        st.session_state.record_state = "recorded"

        st.success("録音完了。内容を確認してください")
        st.rerun()


if st.session_state.saved_audio_path:
    st.caption("録音済み")
    st.audio(st.session_state.saved_audio_path)
    st.info("問題なければ『文字起こし』を押してください")


if main_action and st.session_state.record_state == "recorded":
    try:
        with st.spinner("文字起こし中..."):
            st.session_state.transcript = transcribe_audio(
                st.session_state.saved_audio_path
            )
        st.success("文字起こし完了")
    except Exception as e:
        st.error(f"文字起こし失敗：{e}")

st.divider()

transcript = st.text_area(
    "文字起こし結果",
    value=st.session_state.transcript,
    height=180,
)

memo = st.text_area(
    "補足メモ",
    height=100,
    placeholder="交通費・体調など"
)

if st.button("記録案を作成", type="primary", use_container_width=True):
    body = transcript

    if memo:
        body += f"\\n補足：{memo}"

    st.session_state.draft = f"""【支援記録案】
担当：{st.session_state.staff_name}
利用者：{user_name}
種別：{service_type}
開始：{st.session_state.current_start}
終了：{st.session_state.current_end}

【記録】
{body}
"""

if st.session_state.draft:
    st.text_area(
        "記録案",
        value=st.session_state.draft,
        height=250
    )

    if st.button("保存", use_container_width=True):
        save_log({
            "保存日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "担当": st.session_state.staff_name,
            "利用者": user_name,
            "種別": service_type,
            "開始": st.session_state.current_start,
            "終了": st.session_state.current_end,
            "音声ファイル": st.session_state.saved_audio_path,
            "文字起こし": transcript,
            "補足": memo,
            "記録案": st.session_state.draft,
        })

        st.success("保存しました")

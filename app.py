import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="ひなた記録", page_icon="☀️", layout="centered")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "record_log.csv"

st.title("☀️ ひなた記録")
st.caption("まずは試作版：開始・終了・録音メモの3ボタン")

if "staff_name" not in st.session_state:
    st.session_state.staff_name = ""

if "current_start" not in st.session_state:
    st.session_state.current_start = ""

if "current_end" not in st.session_state:
    st.session_state.current_end = ""

with st.expander("初回設定 / 職員名", expanded=not bool(st.session_state.staff_name)):
    staff_name = st.text_input("職員名", value=st.session_state.staff_name, placeholder="例：大森としえ")
    if st.button("職員名を保存"):
        st.session_state.staff_name = staff_name
        st.success(f"{staff_name} さんで保存しました")

st.divider()

user_name = st.text_input("利用者名", placeholder="例：辰江様")
service_type = st.selectbox("種別", ["同行", "居宅", "通院介助", "研修", "その他"])

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶ 開始", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.current_start = now
        st.success(f"開始：{now}")

with col2:
    if st.button("■ 終了", use_container_width=True):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.current_end = now
        st.success(f"終了：{now}")

with col3:
    if st.button("🎙 録音", use_container_width=True):
        st.info("試作版では録音ボタンのみです。次段階で音声アップロード/文字起こしを追加します。")

st.divider()

st.subheader("報告メモ")
st.caption("今は録音の代わりに、話した内容をここへ入力する試作です。")

memo = st.text_area(
    "報告内容",
    placeholder="例：買い物同行。体調変化なし。交通費260円。",
    height=140
)

if st.button("記録案を作成", type="primary", use_container_width=True):
    start = st.session_state.get("current_start", "")
    end = st.session_state.get("current_end", "")

    draft = f"""【支援記録案】
担当：{st.session_state.staff_name}
利用者：{user_name}
種別：{service_type}
開始：{start}
終了：{end}

内容：
{memo}

記録文：
{user_name}の{service_type}を実施。{memo}
"""
    st.session_state.draft = draft

if "draft" in st.session_state:
    st.text_area("記録案", value=st.session_state.draft, height=220)

    if st.button("保存", use_container_width=True):
        row = {
            "保存日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "担当": st.session_state.staff_name,
            "利用者": user_name,
            "種別": service_type,
            "開始": st.session_state.get("current_start", ""),
            "終了": st.session_state.get("current_end", ""),
            "報告メモ": memo,
            "記録案": st.session_state.draft,
        }

        if LOG_FILE.exists():
            df = pd.read_csv(LOG_FILE)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
        st.success("保存しました")

st.divider()

if LOG_FILE.exists():
    st.subheader("保存済みログ")
    df = pd.read_csv(LOG_FILE)
    st.dataframe(df.tail(10), use_container_width=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "CSVをダウンロード",
        data=csv.encode("utf-8-sig"),
        file_name="hinata_record_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

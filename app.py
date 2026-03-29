"""
app.py - Streamlit UIのみ。ビジネスロジックはここに書かない。

責務：
  1. session_state を AppState として読み込む
  2. UIを描画する
  3. ボタンクリック時は ui/actions.py の関数を呼び出す
  4. 返ってきた AppState を session_state に書き戻す

UIファイルに書いてよいもの：
  - st.* の呼び出し
  - ui/actions.py の関数呼び出し
  - st.session_state への読み書き

UIファイルに書いてはいけないもの：
  - API呼び出し
  - JSONパース
  - ビジネスルールの判定
"""

import streamlit as st

from ui.state import AppState
from ui.actions import on_generate, on_confirm, on_reset

# ------------------------------------------------------------------ #
# Session State 初期化
# ------------------------------------------------------------------ #
if "app_state" not in st.session_state:
    st.session_state.app_state = AppState()

state: AppState = st.session_state.app_state

# ------------------------------------------------------------------ #
# ページ設定
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="躓き → ナレッジオーディット変換ツール",
    layout="centered",
)
st.title("躓き → ナレッジオーディット変換ツール")

# ------------------------------------------------------------------ #
# Section 1: 入力
# ------------------------------------------------------------------ #
st.subheader("① 躓きの核心を入力")
stumbling_point = st.text_area(
    label="躓きの核心",
    value=state.stumbling_point,
    placeholder="例：押した前後の変化量について、フィードバックの基準がない",
    height=100,
)

if st.button("問いを生成する", type="primary"):
    with st.spinner("生成中..."):
        st.session_state.app_state = on_generate(stumbling_point, state)
    st.rerun()

if state.error:
    st.error(state.error)

# ------------------------------------------------------------------ #
# Section 2: 草案（生成後に表示）
# ------------------------------------------------------------------ #
if state.generated is not None:
    st.divider()
    st.subheader("② 問いを確認・編集")

    labels = {
        "cue":     "手がかり（Cue）",
        "gap":     "新人との差（Gap）",
        "anomaly": "異常認識（Anomaly）",
    }
    descriptions = {
        "cue":     "何を見て判断しているか",
        "gap":     "外から観察した経験を活用",
        "anomaly": "失敗状態を起点に逆から引き出す",
    }

    selected: set[str] = set()
    audit_texts: dict[str, str] = {}

    for key, label in labels.items():
        st.markdown(f"**{label}** — *{descriptions[key]}*")
        if st.checkbox("使用する", value=True, key=f"use_{key}"):
            selected.add(key)
        audit_texts[key] = st.text_area(
            label=label,
            value=getattr(state.generated, key),
            key=f"edit_{key}",
            label_visibility="collapsed",
        )

    if st.button("確定する"):
        st.session_state.app_state = on_confirm(audit_texts, selected, state)
        st.rerun()

# ------------------------------------------------------------------ #
# Section 3: 確定した問い（確定後に表示）
# ------------------------------------------------------------------ #
if state.confirmed:
    st.divider()
    st.subheader("③ 確定した問い")

    copy_text = "\n".join(f"・{q}" for q in state.confirmed)
    for q in state.confirmed:
        st.markdown(f"- {q}")

    st.code(copy_text, language=None)
    st.caption("↑ コードブロックの右上アイコンでコピーできます")

    if st.button("リセット", type="secondary"):
        st.session_state.app_state = on_reset()
        st.rerun()

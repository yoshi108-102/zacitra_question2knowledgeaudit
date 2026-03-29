# Implementation Plan：躓き→ナレッジオーディット変換ツール（Streamlit版）

**ベース設計：** `knowledge_audit_converter_design_1.md`  
**システム設計：** `docs/system_design.md`

---

## 概要

「躓きの核心」→3形式の問い生成をStreamlitで実現する。  
**UIとロジックを徹底分割し、`app.py` を読まなくてもビジネスロジックが把握できる構造とする。**

---

## ファイル構成

```
zacitra_question2knowledgeaudit/
├── app.py               # UIレンダリングのみ（ビジネスロジックを書かない）
├── models.py            # データモデル（TypedDict）← ロジック理解の起点
├── converter.py         # Claude API呼び出しと JSON パース（純粋関数）
├── prompt.py            # プロンプト文字列定義
├── actions.py           # ボタン操作ロジック（AppState → AppState の純粋関数）
├── examples.json        # few-shot変換例（参照用）
├── requirements.txt
├── .env
├── .gitignore
└── docs/
```

---

## 実装ステップ

### Step 1：プロジェクト基盤

#### [NEW] `requirements.txt`

```
streamlit>=1.32.0
anthropic>=0.25.0
python-dotenv>=1.0.0
```

#### [NEW] `.gitignore`

```
.env
__pycache__/
*.pyc
.DS_Store
```

---

### Step 2：データモデル定義

#### [NEW] `models.py`

アプリで流通するデータの型を全て定義する。**ロジックを読む際の起点となるファイル。**

```python
from typing import TypedDict

class QuestionSet(TypedDict):
    """Claude APIが返す3形式の問い"""
    cue: str      # 手がかり　　（Cue: 何を見て判断しているか）
    gap: str      # 新人との差　（Gap: 外から観察した経験を活用）
    anomaly: str  # 異常認識　　（Anomaly: 失敗状態を起点に逆から引き出す）


class AppState(TypedDict):
    """アプリ全体の状態。UIはこれを読み書きするだけ"""
    stumbling_point: str           # ユーザーが入力した躓きの核心
    generated: QuestionSet | None  # 生成結果（未生成時はNone）
    confirmed: list[str]           # 確定した問いのリスト
    error: str | None              # エラーメッセージ（正常時はNone）


def initial_state() -> AppState:
    """AppStateの初期値を返す"""
    return AppState(
        stumbling_point="",
        generated=None,
        confirmed=[],
        error=None,
    )
```

---

### Step 3：プロンプト定義

#### [NEW] `prompt.py`

プロンプト文字列のみ。実行コードは含まない。

```python
SYSTEM_PROMPT = """
あなたは丸棒矯正の技能伝承研究をサポートするアシスタントです。
新人の「躓きの核心」を、熟練者が答えやすいナレッジオーディット形式の問いに変換します。

## 出力形式
以下の3形式で問いを生成し、JSONで返してください。

{
  "cue": "手がかりを聞く問い（何を見て判断しているかを引き出す）",
  "gap": "新人との差を聞く問い（外から観察した経験を活用する）",
  "anomaly": "異常認識を聞く問い（失敗状態を起点に逆から引き出す）"
}

## 各形式のガイドライン
- cue（手がかり）:「〜するとき、何を見ていますか？どこに注目しますか？」の形
- gap（新人との差）:「新人が〜できないとしたら、何が見えていないからだと思いますか？」の形
- anomaly（異常認識）:「〜になったとき、最初に気づくのはどんな手がかりですか？」の形

## 注意
- 「基準はありますか？」「どうやって判断しますか？」の形は使わない（熟練者が答えにくいため）
- 問いは丸棒矯正の文脈（視覚による曲がりの検知、プレスによる矯正）に即したものにする
- JSONのみ返す（説明文は不要）
"""

USER_PROMPT_TEMPLATE = "躓きの核心：{stumbling_point}"
```

---

### Step 4：few-shot例

#### [NEW] `examples.json`

設計書の2件をそのまま格納。将来のfew-shot活用・品質評価のための参照用。

```json
[
  {
    "input": "押した前後の変化量について、フィードバックの基準がない",
    "output": {
      "cue": "押した後に棒を見るとき、何を見ていますか？どこに注目しますか？",
      "gap": "新人が押した前後の変化を読めないとしたら、何が見えていないからだと思いますか？",
      "anomaly": "押しすぎたとき、最初に気づくのはどんな手がかりですか？"
    }
  },
  {
    "input": "真ん中を押すときにどこを押すかよくわからない。基準がない",
    "output": {
      "cue": "全体が弓なりになっているとき、どこを最初に見ますか？",
      "gap": "新人が弓なりのときにどこを押すか迷うとしたら、何が見えていないからだと思いますか？",
      "anomaly": "押す場所を間違えたとき、最初に気づくのはどんな変化ですか？"
    }
  }
]
```

---

### Step 5：API呼び出しモジュール

#### [NEW] `converter.py`

Claude APIを呼び出す純粋関数。Streamlitに一切依存しない。

```python
import os
import json
import anthropic
from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from models import QuestionSet

load_dotenv()

def generate_questions(stumbling_point: str) -> QuestionSet:
    """
    躓きの核心テキストを受け取り、3形式の問いを返す純粋関数。

    Args:
        stumbling_point: 躓きの核心（一文、日本語）

    Returns:
        QuestionSet: {"cue": str, "gap": str, "anomaly": str}

    Raises:
        ValueError: APIレスポンスのJSONパースに失敗した場合
        anthropic.APIError: API呼び出し自体が失敗した場合
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(stumbling_point=stumbling_point)
        }]
    )
    raw = message.content[0].text.strip()
    parsed = json.loads(raw)
    return QuestionSet(
        cue=parsed["cue"],
        gap=parsed["gap"],
        anomaly=parsed["anomaly"],
    )
```

---

### Step 6：アクション定義

#### [NEW] `actions.py`

**ボタンクリック時に「何が起きるか」を定義する層。**  
`AppState` を受け取り、更新済みの `AppState` を返す純粋関数群。  
Streamlitに依存しない＝UIを見なくてもロジックが全て読める。

```python
from models import AppState, QuestionSet, initial_state
from converter import generate_questions

def on_generate(stumbling_point: str, state: AppState) -> AppState:
    """
    「問いを生成する」ボタン押下時の処理。

    - 入力が空の場合はエラーをセット
    - API呼び出しが成功したらgeneratedにQuestionSetをセット
    - 失敗したらerrorにメッセージをセット
    """
    if not stumbling_point.strip():
        return {**state, "error": "躓きの核心を入力してください。"}

    try:
        question_set = generate_questions(stumbling_point)
        return {
            **state,
            "stumbling_point": stumbling_point,
            "generated": question_set,
            "confirmed": [],
            "error": None,
        }
    except Exception as e:
        return {**state, "error": f"生成に失敗しました：{e}"}


def on_confirm(
    edited_questions: dict[str, str],
    use_flags: dict[str, bool],
    state: AppState,
) -> AppState:
    """
    「確定する」ボタン押下時の処理。

    Args:
        edited_questions: {"cue": "編集後テキスト", "gap": ..., "anomaly": ...}
        use_flags:        {"cue": True, "gap": False, "anomaly": True}

    - use_flags が True のものだけ confirmed に追加する
    - 何も選択されていない場合はエラーをセット
    """
    confirmed = [
        text
        for key, text in edited_questions.items()
        if use_flags.get(key, False) and text.strip()
    ]
    if not confirmed:
        return {**state, "error": "少なくとも1つの問いを選択してください。"}

    return {**state, "confirmed": confirmed, "error": None}


def on_reset(state: AppState) -> AppState:
    """
    「リセット」ボタン押下時の処理。初期状態に戻す。
    """
    return initial_state()
```

---

### Step 7：Streamlit UI

#### [NEW] `app.py`

**レンダリングのみ。ビジネスロジックは一切書かない。**

```python
import streamlit as st
from models import initial_state, AppState
from actions import on_generate, on_confirm, on_reset

# --- Session State 初期化 ---
if "app_state" not in st.session_state:
    st.session_state.app_state = initial_state()

state: AppState = st.session_state.app_state

# --- タイトル ---
st.title("躓き → ナレッジオーディット変換ツール")

# --- Section 1: 入力 ---
st.subheader("① 躓きの核心を入力")
stumbling_point = st.text_area("躓きの核心", value=state["stumbling_point"])

if st.button("問いを生成する"):
    with st.spinner("生成中..."):
        st.session_state.app_state = on_generate(stumbling_point, state)
    st.rerun()

if state["error"]:
    st.error(state["error"])

# --- Section 2: 草案（生成後に表示）---
if state["generated"] is not None:
    st.subheader("② 問いを確認・編集")
    questions = state["generated"]
    labels = {"cue": "手がかり（Cue）", "gap": "新人との差（Gap）", "anomaly": "異常認識（Anomaly）"}

    use_flags = {}
    edited_questions = {}
    for key, label in labels.items():
        use_flags[key] = st.checkbox(label, value=True, key=f"use_{key}")
        edited_questions[key] = st.text_area(
            label=" ", value=questions[key], key=f"edit_{key}"
        )

    if st.button("確定する"):
        st.session_state.app_state = on_confirm(edited_questions, use_flags, state)
        st.rerun()

# --- Section 3: 確定（確定後に表示）---
if state["confirmed"]:
    st.subheader("③ 確定した問い")
    copy_text = "\n".join(f"・{q}" for q in state["confirmed"])
    st.code(copy_text, language=None)
    if st.button("リセット"):
        st.session_state.app_state = on_reset(state)
        st.rerun()
```

---

## 依存関係の向き

```
app.py
  └→ actions.py
       └→ converter.py
            └→ prompt.py
  └→ models.py
```

`app.py` を削除してもロジック層は完全に成立する。

---

## 検証手順

```bash
cd /Users/yoshi/zacitra_question2knowledgeaudit
pip install -r requirements.txt
# .envにANTHROPIC_API_KEYを設定
streamlit run app.py
```

### テスト入力（設計書サンプル）

| 入力 | 期待：cue |
|---|---|
| 押した前後の変化量について、フィードバックの基準がない | 押した後に棒を見るとき、何を見ていますか？どこに注目しますか？ |
| 真ん中を押すときにどこを押すかよくわからない。基準がない | 全体が弓なりになっているとき、どこを最初に見ますか？ |

---

## v1スコープ外

- ログ保存・CSV出力
- なぜなぜチェーン全体の一括変換
- ACTAカテゴリ自動判定

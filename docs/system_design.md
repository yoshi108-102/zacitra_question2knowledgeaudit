# 躓き→ナレッジオーディット変換ツール システム設計書（Streamlit版）

**プロジェクト：** 丸棒矯正 技能伝承研究  
**バージョン：** v1.0-streamlit  
**ベース設計：** knowledge_audit_converter_design_1.md

---

## 1. 概要

「躓きの核心」を入力すると、熟練者へのインタビュー用の問い（草案）を3形式で自動生成する。  
ブラウザUI上で編集・選択・コピーできる最小構成のStreamlitアプリ。

---

## 2. 設計原則：UIとロジックの完全分割

**`app.py` を読まなくても、ビジネスロジックが全て把握できる。**

| 層 | ファイル | 責務 | Streamlit依存 |
|---|---|---|---|
| データモデル | `models.py` | 型定義・データ構造 | ❌ |
| プロンプト | `prompt.py` | プロンプト文字列 | ❌ |
| API呼び出し | `converter.py` | Claude API＋パース（純粋関数） | ❌ |
| アクション | `actions.py` | ボタン操作の処理ロジック | ❌ |
| UI | `app.py` | Streamlitレンダリングのみ | ✅ |

**ロジック層（`models/prompt/converter/actions`）はStreamlitに一切依存しない。**  
単体でテスト・実行・理解できる。

---

## 3. 処理フロー

```
[app.py] ユーザーが「生成」ボタンをクリック
    ↓
[actions.py] on_generate(stumbling_point) を呼び出す
    ↓
[converter.py] generate_questions(stumbling_point) → QuestionSet
    ↓
[Claude API] JSON応答
    ↓
[models.py] QuestionSet(cue, gap, anomaly) に格納
    ↓
[actions.py] AppState を更新して返す
    ↓
[app.py] AppState をもとにUIを再レンダリング（st.session_stateに反映）
```

---

## 4. ディレクトリ構成

```
zacitra_question2knowledgeaudit/
├── app.py               # Streamlit UIレンダリングのみ（骨格）
├── models.py            # データモデル（TypedDict）
├── converter.py         # Claude API呼び出し＋パース（純粋関数）
├── prompt.py            # プロンプト文字列定義
├── actions.py           # ボタン操作ロジック（UIに依存しない）
├── examples.json        # few-shot例（参照用）
├── requirements.txt
├── .env                 # APIキー（gitignore対象）
├── .gitignore
└── docs/
    ├── system_design.md
    └── implementation_plan.md
```

---

## 5. データモデル（`models.py`）

```python
from typing import TypedDict

class QuestionSet(TypedDict):
    """Claude APIが返す3形式の問い"""
    cue: str      # 手がかり
    gap: str      # 新人との差
    anomaly: str  # 異常認識

class AppState(TypedDict):
    """アプリ全体のUI状態"""
    stumbling_point: str          # 入力テキスト
    generated: QuestionSet | None # API生成結果（None=未生成）
    confirmed: list[str]          # 確定した問いのリスト
    error: str | None             # エラーメッセージ（None=正常）
```

---

## 6. アクション定義（`actions.py`）

UIに依存せず、入力を受け取って `AppState` を返す純粋関数群。

```python
from models import AppState, QuestionSet
from converter import generate_questions

def on_generate(stumbling_point: str, state: AppState) -> AppState:
    """
    「問いを生成する」ボタンが押されたときの処理。
    - APIを呼び出してQuestionSetを取得
    - stateを更新して返す（副作用なし）
    """

def on_confirm(
    selected_questions: dict[str, str],  # {"cue": "編集後テキスト", ...}
    use_flags: dict[str, bool],          # {"cue": True, "gap": False, ...}
    state: AppState
) -> AppState:
    """
    「確定する」ボタンが押されたときの処理。
    - チェックされたものだけをconfirmedリストに追加
    - stateを更新して返す
    """

def on_reset(state: AppState) -> AppState:
    """
    リセット処理（初期状態に戻す）
    """
```

---

## 7. API呼び出し（`converter.py`）

```python
def generate_questions(stumbling_point: str) -> QuestionSet:
    """
    躓きの核心テキストを受け取り、3形式の問いを返す純粋関数。
    - 副作用：Claude API呼び出し
    - エラー時：ValueError（呼び出し元でハンドリング）
    """
```

---

## 8. UI構造（`app.py`）

```python
# app.py の責務：レンダリングのみ
#
# 1. session_state を AppState として読み込む
# 2. UIを描画する
# 3. ボタンクリック時は actions.py の関数を呼び出す
# 4. 返ってきた AppState を session_state に書き戻す
#
# ビジネスロジックは一切書かない

import streamlit as st
from actions import on_generate, on_confirm, on_reset
from models import AppState

def render_input_section(state: AppState) -> None: ...
def render_draft_section(state: AppState) -> AppState | None: ...
def render_confirmed_section(state: AppState) -> None: ...
```

**UIファイルに書いていいもの：**
- `st.*` の呼び出し
- `actions.py` の関数呼び出し
- `st.session_state` への読み書き

**UIファイルに書いてはいけないもの：**
- APIの呼び出し
- JSONのパース
- ビジネスルールの判定

---

## 9. 画面構成

```
┌───────────────────────────────────────────┐
│  躓き → ナレッジオーディット変換ツール    │
├───────────────────────────────────────────┤
│  [Section 1: 入力]                        │
│  st.text_area（躓きの核心）               │
│  st.button("問いを生成する")              │
├───────────────────────────────────────────┤
│  [Section 2: 草案]（生成後に表示）        │
│                                           │
│  ✅ 手がかり（Cue）                        │
│     st.text_area（編集可・デフォルト=生成値）│
│                                           │
│  ✅ 新人との差（Gap）                      │
│     st.text_area                         │
│                                           │
│  ✅ 異常認識（Anomaly）                    │
│     st.text_area                         │
│                                           │
│  st.button("確定する")                    │
├───────────────────────────────────────────┤
│  [Section 3: 確定]（確定後に表示）        │
│  ・確定した問いリスト                     │
│  st.code（コピー用テキスト）              │
└───────────────────────────────────────────┘
```

---

## 10. 環境・依存関係

| ライブラリ | 用途 |
|---|---|
| streamlit | UI |
| anthropic | Claude API |
| python-dotenv | .envからAPIキー読み込み |

---

## 11. v1スコープ外

- ログ保存・CSV出力
- なぜなぜチェーン全体の一括変換
- ACTAカテゴリ自動判定
- フィッシュボーン連携

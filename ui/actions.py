from src.logger import logger
from ui.state import AppState
from src.converter import generate_knowledge_audit


def on_generate(stumbling_point: str, why_chain: str, state: AppState) -> AppState:
    """
    「問いを生成する」ボタン押下時の処理。

    - 入力が空の場合は警告ログ + errorをセット
    - API呼び出し成功 → generated に KnowledgeAuditSet をセット
    - API呼び出し失敗 → エラーログ + errorをセット
    """
    if not stumbling_point.strip():
        logger.warning("on_generate: empty input")
        return AppState(
            stumbling_point=state.stumbling_point,
            why_chain=state.why_chain,
            generated=state.generated,
            confirmed=state.confirmed,
            error="躓きの核心を入力してください。",
        )

    logger.info("on_generate: start | input=%r", stumbling_point)
    try:
        knowledge_audit = generate_knowledge_audit(stumbling_point, why_chain)
        logger.info("on_generate: done")
        return AppState(
            stumbling_point=stumbling_point,
            why_chain=why_chain,
            generated=knowledge_audit,
            confirmed=[],
            error=None,
        )
    except Exception as e:
        logger.error("on_generate: failed | error=%s", e, exc_info=True)
        return AppState(
            stumbling_point=stumbling_point,
            why_chain=why_chain,
            generated=state.generated,
            confirmed=state.confirmed,
            error=f"生成に失敗しました：{e}",
        )


def on_confirm(
    audit_texts: dict[str, str],
    selected: set[str],
    state: AppState,
) -> AppState:
    """
    「確定する」ボタン押下時の処理。

    Args:
        audit_texts: 編集後の各問いテキスト {"cue": ..., "gap": ..., "anomaly": ...}
        selected:    使用する問いのキーのSet  {"cue", "anomaly"}

    - selected に含まれるキーの問いのみ confirmed に追加する
    - 何も選択されていない場合は警告ログ + errorをセット
    """
    confirmed = [
        text
        for key, text in audit_texts.items()
        if key in selected and text.strip()
    ]

    if not confirmed:
        logger.warning("on_confirm: no question selected")
        return AppState(
            stumbling_point=state.stumbling_point,
            why_chain=state.why_chain,
            generated=state.generated,
            confirmed=state.confirmed,
            error="少なくとも1つの問いを選択してください。",
        )

    logger.info("on_confirm: confirmed %d question(s)", len(confirmed))
    return AppState(
        stumbling_point=state.stumbling_point,
        why_chain=state.why_chain,
        generated=state.generated,
        confirmed=confirmed,
        error=None,
    )


def on_reset() -> AppState:
    """
    「リセット」ボタン押下時の処理。初期状態に戻す。
    """
    logger.info("on_reset: state cleared")
    return AppState()

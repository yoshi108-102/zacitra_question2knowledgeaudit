import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from src.models import KnowledgeAuditSet
from src.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.logger import logger

load_dotenv()

DEFAULT_CONVERT_MODEL = "gpt-5-nano"

def generate_knowledge_audit(stumbling_point: str) -> KnowledgeAuditSet:
    """
    躓きの核心テキストを受け取り、3形式の問いを返す純粋関数。

    Args:
        stumbling_point: 躓きの核心（一文、日本語）

    Returns:
        KnowledgeAuditSet: {cue, gap, anomaly}

    Raises:
        ValueError: APIレスポンスのJSONパースに失敗した場合
        openai.APIError: API呼び出し自体が失敗した場合
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    model = os.getenv("OPENAI_MODEL", DEFAULT_CONVERT_MODEL)
    logger.info("generate_knowledge_audit: start | input=%r model=%s", stumbling_point, model)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    stumbling_point=stumbling_point
                )},
            ],
            response_format={"type": "json_object"},
            max_tokens=1024,
        )
    except Exception:
        logger.exception("generate_knowledge_audit: API call failed")
        raise

    raw = response.choices[0].message.content or ""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("generate_knowledge_audit: JSON parse failed | raw=%r", raw)
        raise ValueError(f"APIレスポンスのJSONパースに失敗しました。raw={raw!r}")

    result = KnowledgeAuditSet(
        cue=parsed["cue"],
        gap=parsed["gap"],
        anomaly=parsed["anomaly"],
    )
    logger.info("generate_knowledge_audit: done | cue=%r", result.cue)
    return result

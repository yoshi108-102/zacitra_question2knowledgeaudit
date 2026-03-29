from dataclasses import dataclass, field

from src.models import KnowledgeAuditSet


@dataclass
class AppState:
    """Streamlit アプリ全体の UI 状態。UIはこれを読み書きするだけ"""
    stumbling_point: str = ""
    why_chain: str = ""
    generated: KnowledgeAuditSet | None = None
    confirmed: list[str] = field(default_factory=list)
    error: str | None = None

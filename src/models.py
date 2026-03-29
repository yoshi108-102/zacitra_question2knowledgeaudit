from dataclasses import dataclass


@dataclass
class KnowledgeAuditSet:
    """なぜなぜ分析によって得られた新人のつまづきをもとに作られたナレッジオーディットの問い"""
    cue: str      # 手がかり　（何を見て判断しているか）
    gap: str      # 新人との差（外から観察した経験を活用）
    anomaly: str  # 異常認識　（失敗状態を起点に逆から引き出す）

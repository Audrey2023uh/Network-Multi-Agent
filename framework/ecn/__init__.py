"""
Enterprise Cognitive Network (ECN) Framework
============================================
Implements the proposed multi-agent cognitive networking system evaluated on
frozen ECNetBench instances. Benchmark data is READ-ONLY.

Architecture
------------
  Observability ──► PerceptionAgent ──► DigitalTwin state
                         │
         ┌───────────────┼────────────────┐
         ▼               ▼                ▼
   AnomalyAgent   PredictionAgent    RCAAgent
         │               │                │
         └───────► Orchestrator ◄─────────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
         ImpactAgent  HealingAgent  Explanations
"""
from __future__ import annotations

__version__ = "1.0.0"

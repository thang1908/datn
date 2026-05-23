"""LangGraph pipeline for Call flow.

read_audio → transcribe_audio
transcribe_audio → [parallel] classify_and_resolved, summarize_conversation
classify_and_resolved → [parallel] score_qa, analyze_negative
score_qa, analyze_negative, summarize_conversation → merge_output → END
"""

from langgraph.graph import END, StateGraph

from .nodes import (
    analyze_negative,
    classify_and_resolved,
    read_audio,
    merge_output,
    score_qa,
    summarize_conversation,
    transcribe_audio,
)
from .state import CallState


builder = StateGraph(CallState)

# Add nodes
builder.add_node("read_audio", read_audio)
builder.add_node("transcribe_audio", transcribe_audio)
builder.add_node("classify_and_resolved", classify_and_resolved)
builder.add_node("score_qa", score_qa)
builder.add_node("analyze_negative", analyze_negative)
builder.add_node("summarize_conversation", summarize_conversation)
builder.add_node("merge_output", merge_output)

# Entry point
builder.set_entry_point("read_audio")

# Edges
builder.add_edge("read_audio", "transcribe_audio")

# After transcription, fan out to classification + summarization in parallel
builder.add_edge("transcribe_audio", "classify_and_resolved")
builder.add_edge("transcribe_audio", "summarize_conversation")

# After classification, always run both score_qa and analyze_negative in parallel
builder.add_edge("classify_and_resolved", "score_qa")
builder.add_edge("classify_and_resolved", "analyze_negative")

# All branches converge into merge
builder.add_edge("score_qa", "merge_output")
builder.add_edge("analyze_negative", "merge_output")
builder.add_edge("summarize_conversation", "merge_output")

builder.add_edge("merge_output", END)

call_graph = builder.compile()

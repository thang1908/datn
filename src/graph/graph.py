"""LangGraph conversation analysis pipeline definition.

One graph is available:
- ``call_graph`` for Type=1 (call) messages
"""

from .call_graph import call_graph

__all__ = ["call_graph"]

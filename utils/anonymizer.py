from typing import List, Dict, Tuple
from models.schemas import Stage1Opinion

def anonymize_opinions(opinions: List[Stage1Opinion]) -> Tuple[str, Dict[int, str]]:
    """
    Formats Stage 1 opinions for anonymous review.
    Returns:
        - A formatted string containing anonymized responses.
        - A mapping of response_id to the actual model name (for transparency later).
    """
    formatted_parts = []
    mapping = {}
    
    for i, op in enumerate(opinions, start=1):
        # We use the response_id assigned in Stage 1
        formatted_parts.append(f"### Response #{op.response_id}\n{op.response}\n")
        mapping[op.response_id] = op.model_id
        
    return "\n---\n".join(formatted_parts), mapping

import os
import re
import spacy
from spacy.matcher import Matcher

# Load the model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback in case loading fails
    nlp = None

def extract_facets_spacy(caption_text: str) -> dict:
    """
    Extracts class, material, and type facets from table captions using spaCy.
    """
    if not caption_text or not nlp:
        return {}
    
    doc = nlp(caption_text)
    matcher = Matcher(nlp.vocab)
    
    # Define patterns
    class_pattern = [{"LOWER": "class"}, {"IS_DIGIT": True}]
    type_pattern = [{"LOWER": "type"}, {"IS_ALPHA": True, "LENGTH": 1}]
    
    matcher.add("CLASS", [class_pattern])
    matcher.add("TYPE", [type_pattern])
    
    matches = matcher(doc)
    facets = {}
    
    # Parse matches
    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        if string_id == "CLASS":
            try:
                facets["class"] = int(span[1].text)
            except ValueError:
                pass
        elif string_id == "TYPE":
            facets["type"] = span[1].text.upper()
            
    # Fallback/Additional simple keyword checks for material
    text_lower = caption_text.lower()
    if "copper" in text_lower:
        facets["material"] = "copper"
    elif "aluminium" in text_lower:
        facets["material"] = "aluminium"
        
    return facets

def classify_clause_layer1(sentence: str) -> Optional[str]:
    """
    Layer 1: Maintained list of boilerplate regex patterns.
    """
    sentence_clean = sentence.strip().lower()
    
    # Patterns to discard (Procedure-only)
    discard_patterns = [
        r"in accordance with",
        r"test method",
        r"determined as described in",
        r"procedure for",
        r"refer to part"
    ]
    if any(re.search(pat, sentence_clean) for pat in discard_patterns):
        return "procedure"
        
    # Patterns to keep (Value / Table lookup intent)
    keep_patterns = [
        r"shall not exceed",
        r"shall be not less than",
        r"shall comply with",
        r"given in table",
        r"specified in table",
        r"limits given in"
    ]
    if any(re.search(pat, sentence_clean) for pat in keep_patterns):
        # Decide if it points directly to a table
        if "table" in sentence_clean:
            return "table"
        return "value"
        
    return None

async def classify_clause_layer2(sentence: str) -> Optional[str]:
    """
    Layer 2: Async LLM call to classify clause reference.
    Enforces structured output with Q&A style restatement before final decision.
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        # Fallback to heuristics if API key is not available
        return None
        
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        
        # Enforced schema using tool calling
        tools = [{
            "type": "function",
            "function": {
                "name": "classify_intent",
                "description": "Classifies the intent of a clause sentence",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restatement": {
                            "type": "string",
                            "description": "Briefly restate what the sentence means in plain English."
                        },
                        "verdict": {
                            "type": "string",
                            "enum": ["value", "table", "procedure"],
                            "description": "The classified category verdict."
                        }
                    },
                    "required": ["restatement", "verdict"]
                }
            }
        }]
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a laboratory compliance classifier. Analyze the sentence and classify its intent."},
                {"role": "user", "content": f"Classify this clause sentence: '{sentence}'"}
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "classify_intent"}}
        )
        
        # Parse output
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            arguments = json.loads(tool_calls[0].function.arguments)
            return arguments.get("verdict")
    except Exception as e:
        print(f"LLM classification failure: {e}")
        
    return None

import json
from typing import Optional

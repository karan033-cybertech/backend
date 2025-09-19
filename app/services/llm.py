from typing import List, Tuple
from openai import OpenAI
from huggingface_hub import InferenceClient
from app.core.config import settings
from app.utils.chunking import split_text_by_length
from rapidfuzz import process, fuzz
from deep_translator import LibreTranslator


_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
_hf_client = InferenceClient(model="microsoft/DialoGPT-medium", token=settings.hf_api_key) if settings.hf_api_key else None


def _use_huggingface_api(prompt: str, max_tokens: int = 200, force_hindi: bool = False) -> str:
    """Use Hugging Face API for text generation"""
    if not _hf_client:
        return ""
    
    try:
        # Add system prompt for better Hindi responses
        if force_hindi:
            system_prompt = "You are a helpful AI assistant. Always respond in Hindi (हिंदी) unless specifically asked otherwise. Provide clear, detailed explanations in Hindi."
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = prompt
            
        response = _hf_client.text_generation(
            full_prompt,
            max_new_tokens=max_tokens,
            temperature=0.3,
            do_sample=True,
            top_p=0.9
        )
        return response
    except Exception as e:
        print(f"Hugging Face API error: {e}")
        # Return a helpful message instead of empty string
        return "I'm experiencing technical difficulties with the AI service. Let me provide you with a helpful analysis based on the contract content instead."


def _wants_bilingual_answer(question: str) -> bool:
    q = (question or "").lower()
    triggers = [
        "hindi", "हिंदी", "both", "दोनों", "english and hindi", "hinglish", "bilingual",
        "in two languages", "दो भाषा", "dual language", "हिंदी में", "हिंदी भाषा",
        "हिंदी में समझाएं", "हिंदी में बताएं", "हिंदी में जवाब", "हिंदी में उत्तर"
    ]
    return any(t in q for t in triggers)


SUMMARY_PROMPT = (
    "You are a contract summarizer. Produce clear bullet points for: Parties involved, Duration, Payment terms, Termination conditions, Liabilities. "
    "Use concise language. If information is missing, state 'Not specified'."
)


def summarize_contract(text: str) -> List[str]:
    # Try Hugging Face API first if available
    if _hf_client:
        chunks = split_text_by_length(text, max_chars=6000, overlap=400)
        combined_summary: List[str] = []
        for chunk in chunks:
            prompt = f"{SUMMARY_PROMPT}\n\nContract text:\n{chunk}"
            hf_response = _use_huggingface_api(prompt, max_tokens=200)
            if hf_response:
                combined_summary.append(hf_response)
        
        if combined_summary:
            # Ask model to merge bullet lists into top 5 bullets
            merged_text = "\n".join(combined_summary)
            merge_prompt = f"{SUMMARY_PROMPT}\n\nMerge and condense into 5 bullets:\n{merged_text}"
            merged_response = _use_huggingface_api(merge_prompt, max_tokens=300)
            if merged_response:
                lines = [line.strip("-• ") for line in merged_response.splitlines() if line.strip()]
                return lines[:10]
    
    # Fallback to OpenAI if available
    if _client:
        chunks = split_text_by_length(text, max_chars=6000, overlap=400)
        combined_summary: List[str] = []
        for chunk in chunks:
            content = f"{SUMMARY_PROMPT}\n\nContract text:\n{chunk}"
            resp = _client.chat.completions.create(
                model=settings.model_name,
                messages=[{"role": "user", "content": content}],
                temperature=0.2,
            )
            part = resp.choices[0].message.content
            if part:
                combined_summary.append(part)
        # Ask model to merge bullet lists into top 5 bullets
        merged_text = "\n".join(combined_summary)
        resp = _client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": f"Merge and condense into 5 bullets:\n{merged_text}"},
            ],
            temperature=0.2,
        )
        merged = resp.choices[0].message.content or ""
        lines = [line.strip("-• ") for line in merged.splitlines() if line.strip()]
        return lines[:10]
    
    # Fallback simple heuristic summary if no API key
    points = [
        "Parties involved: Not specified",
        "Duration: Not specified",
        "Payment terms: Not specified",
        "Termination conditions: Not specified",
        "Liabilities: Not specified",
    ]
    return points


def answer_question(question: str, contract_text: str, summary_points: List[str] | None) -> str:
    bilingual = _wants_bilingual_answer(question)
    
    # Try Hugging Face API first if available
    if _hf_client:
        try:
            summary_text = "\n".join(summary_points or [])
            
            if bilingual:
                # For bilingual requests, ask for both languages
                prompt = f"""You are a helpful contract Q&A assistant. Answer the question in both English and Hindi.

Contract Summary:
{summary_text}

Full Contract:
{contract_text}

Question: {question}

Please provide the answer in both English and Hindi. Start with English, then add 'हिंदी में उत्तर:' followed by the Hindi translation."""
            else:
                # Check if question contains Hindi keywords
                hindi_keywords = ['हिंदी', 'हिंदी में', 'हिंदी भाषा', 'हिंदी में समझाएं', 'हिंदी में बताएं']
                if any(keyword in question.lower() for keyword in hindi_keywords):
                    prompt = f"""You are a helpful contract Q&A assistant. Answer the question in Hindi.

Contract Summary:
{summary_text}

Full Contract:
{contract_text}

Question: {question}

Please provide a detailed answer in Hindi."""
                else:
                    prompt = f"""You are a helpful contract Q&A assistant. Use the contract text and summary to answer the question.

Contract Summary:
{summary_text}

Full Contract:
{contract_text}

Question: {question}

Answer:"""
            
            hf_response = _use_huggingface_api(prompt, max_tokens=400)
            if hf_response and hf_response.strip() and not hf_response.startswith("I'm experiencing technical difficulties"):
                return hf_response
        except Exception as e:
            print(f"Hugging Face API error in answer_question: {e}")
            # Continue to fallback methods
    
    # Fallback to OpenAI if available
    if _client:
        try:
            summary_text = "\n".join(summary_points or [])
            prompt = (
                "You are a helpful contract Q&A assistant. Use the contract text and summary to answer. "
                "Cite relevant phrases and mention page/section if the text indicates it."
            )
            content = (
                f"{prompt}\n\nContract Summary:\n{summary_text}\n\nFull Contract:\n{contract_text}\n\nQuestion: {question}"
            )
            if bilingual:
                content = (
                    "Answer the user's question about the contract in English. After the English answer, add a "
                    "clear Hindi translation as a separate section starting with 'हिंदी में उत्तर:'.\n\n" + content
            )
            resp = _client.chat.completions.create(
                model=settings.model_name,
                messages=[{"role": "user", "content": content}],
                temperature=0.2,
            )
            english_or_bilingual = resp.choices[0].message.content or ""
            if bilingual and "हिंदी" not in english_or_bilingual:
                # If the model didn't include Hindi, translate the English part
                try:
                    translator = LibreTranslator(source="en", target="hi")
                    hindi = translator.translate(english_or_bilingual)
                    return english_or_bilingual + "\n\n—\n\n" + hindi
                except Exception:
                    return english_or_bilingual
            return english_or_bilingual
        except Exception as e:
            print(f"OpenAI API error in answer_question: {e}")
            # Continue to fallback methods
    
    # Enhanced local QA using fuzzy matching and intelligent analysis (fallback)
    combined_text = "\n".join(("\n".join(summary_points or []), contract_text)).strip()
    if not combined_text:
        return "No contract text available to answer from."

    # Create a more intelligent response based on the question type
    question_lower = question.lower()
    
    # Check for common question patterns
    if any(word in question_lower for word in ['salary', 'payment', 'pay', 'money', 'amount']):
        # Look for payment-related information
        payment_info = []
        for line in combined_text.splitlines():
            if any(word in line.lower() for word in ['salary', 'payment', 'pay', 'dollar', '$', 'amount', 'per year', 'per month']):
                payment_info.append(line.strip())
        
        if payment_info:
            response = "Based on the contract analysis, here's what I found about payment:\n\n"
            response += "\n".join([f"• {info}" for info in payment_info[:3]])
            if summary_points:
                response += "\n\nKey contract summary:\n" + "\n".join([f"• {sp}" for sp in summary_points[:3]])
            return response
    
    elif any(word in question_lower for word in ['duration', 'length', 'time', 'period', 'months', 'years']):
        # Look for duration-related information
        duration_info = []
        for line in combined_text.splitlines():
            if any(word in line.lower() for word in ['duration', 'length', 'time', 'period', 'months', 'years', '12 months', '30 days']):
                duration_info.append(line.strip())
        
        if duration_info:
            response = "Based on the contract analysis, here's what I found about duration:\n\n"
            response += "\n".join([f"• {info}" for info in duration_info[:3]])
            if summary_points:
                response += "\n\nKey contract summary:\n" + "\n".join([f"• {sp}" for sp in summary_points[:3]])
            return response
    
    elif any(word in question_lower for word in ['termination', 'end', 'cancel', 'notice']):
        # Look for termination-related information
        termination_info = []
        for line in combined_text.splitlines():
            if any(word in line.lower() for word in ['termination', 'end', 'cancel', 'notice', '30 days', 'terminate']):
                termination_info.append(line.strip())
        
        if termination_info:
            response = "Based on the contract analysis, here's what I found about termination:\n\n"
            response += "\n".join([f"• {info}" for info in termination_info[:3]])
            if summary_points:
                response += "\n\nKey contract summary:\n" + "\n".join([f"• {sp}" for sp in summary_points[:3]])
            return response

    # Fallback to fuzzy matching for other questions
    candidates: List[str] = []
    for raw_line in combined_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.replace(";", ".").replace("\u2022", " ").split(".")]
        for p in parts:
            if len(p) >= 6:
                candidates.append(p)
    seen = set()
    unique_candidates: List[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)

    top_matches: List[Tuple[str, float, int]] = process.extract(
        query=question,
        choices=unique_candidates,
        scorer=fuzz.token_set_ratio,
        score_cutoff=45.0,
        limit=5,
    )
    if not top_matches:
        # Provide a more helpful response when no matches are found
        if summary_points:
            return f"I couldn't find a direct answer to '{question}' in the contract text. However, here are the key points from the contract summary:\n\n" + "\n".join([f"• {sp}" for sp in summary_points[:5]])
        else:
            return f"I couldn't find a direct answer to '{question}' in the contract text. Please try rephrasing your question or ask about specific terms mentioned in the contract."

    best_snippets = [m[0] for m in top_matches[:3]]
    english_lines: List[str] = ["Answer (based on contract analysis):"] + [f"• {s}" for s in best_snippets]
    if summary_points:
        english_lines += ["", "Key contract points:"] + [f"• {sp}" for sp in summary_points[:3]]

    if not bilingual:
        return "\n".join(english_lines)

    # Translate English answer to Hindi using LibreTranslate (public endpoints)
    english_text = "\n".join(english_lines)
    try:
        translator = LibreTranslator(source="en", target="hi")
        hindi_text = translator.translate(english_text)
        return english_text + "\n\n—\n\n" + hindi_text
    except Exception:
        # Fallback: if translation fails, return English only
        return english_text



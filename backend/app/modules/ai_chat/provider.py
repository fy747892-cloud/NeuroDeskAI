from dataclasses import dataclass

from app.modules.ai_chat.retrieval import ContextItem

LOW_CONFIDENCE_THRESHOLD = 0.5
NOT_FOUND_TEXT = "Bu konuda kayıtlı bir veri bulamadım."
LOW_CONFIDENCE_NOTE = "\n\nNot: Bu cevabın güven skoru düşük, lütfen kaynakları kontrol edin."


@dataclass(frozen=True)
class ChatAnswer:
    answer_text: str
    confidence: float
    sources: list[ContextItem]
    input_tokens: int
    output_tokens: int


class MockChatProvider:
    provider_name = "mock"
    model_name = "mock-chat-v1"

    def generate_answer(self, *, question: str, context_items: list[ContextItem]) -> ChatAnswer:
        context_length = sum(len(item.snippet) for item in context_items)
        input_tokens = max(1, (len(question) + context_length) // 4)

        if not context_items:
            return ChatAnswer(
                answer_text=NOT_FOUND_TEXT,
                confidence=0.0,
                sources=[],
                input_tokens=input_tokens,
                output_tokens=max(1, len(NOT_FOUND_TEXT) // 4),
            )

        titles = ", ".join(item.title for item in context_items)
        answer_text = f"İlgili {len(context_items)} kayıt buldum: {titles}."
        # A single weak match stays below the low-confidence threshold on purpose;
        # multiple corroborating matches raise confidence toward the cap.
        confidence = min(0.9, 0.3 + 0.15 * len(context_items))

        if confidence < LOW_CONFIDENCE_THRESHOLD:
            answer_text += LOW_CONFIDENCE_NOTE

        return ChatAnswer(
            answer_text=answer_text,
            confidence=confidence,
            sources=context_items,
            input_tokens=input_tokens,
            output_tokens=max(1, len(answer_text) // 4),
        )

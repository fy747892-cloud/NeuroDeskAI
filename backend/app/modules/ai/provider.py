from dataclasses import dataclass


@dataclass(frozen=True)
class MockAnalysisOutput:
    summary: dict
    tasks: dict
    appointments: dict
    input_tokens: int
    output_tokens: int


class MockAIProvider:
    provider_name = "mock"
    model_name = "mock-analysis-v1"

    async def analyze_conversation(self, *, title: str, transcript_text: str) -> MockAnalysisOutput:
        if "[mock-fail]" in transcript_text.lower():
            raise RuntimeError("Mock provider failed to analyze conversation.")

        clean_text = " ".join(transcript_text.split())
        preview = clean_text[:240]
        summary_text = preview if preview else f"Conversation: {title}"

        tasks = {
            "items": [
                {
                    "title": f"Follow up: {title}",
                    "description": "Review the conversation and confirm next steps.",
                    "confidence": 0.72,
                }
            ]
        }
        appointments = {
            "items": [
                {
                    "title": f"Schedule follow-up for {title}",
                    "proposed_datetime": "2026-07-17T09:00:00+03:00",
                    "time_hint": "next week",
                    "confidence": 0.61,
                }
            ]
        }
        output_text = summary_text + str(tasks) + str(appointments)

        return MockAnalysisOutput(
            summary={
                "summary_text": summary_text,
                "summary_type": "conversation_summary",
                "confidence": 0.82,
            },
            tasks=tasks,
            appointments=appointments,
            input_tokens=max(1, len(transcript_text) // 4),
            output_tokens=max(1, len(output_text) // 4),
        )

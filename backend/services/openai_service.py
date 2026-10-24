import os

from openai import OpenAI


class OpenAIConfigurationError(RuntimeError):
    """Raised when the server has no OpenAI API key configured."""


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIConfigurationError(
            "OpenAI API 키가 설정되지 않았습니다. backend/.env의 OPENAI_API_KEY를 확인하세요."
        )

    return OpenAI(
        api_key=api_key,
        timeout=60.0,
        max_retries=2,
    )


def chat_with_context(
    user_message: str,
    summary: dict | None,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """데이터 요약을 포함한 AI 대화"""

    if summary is None:
        summary_context = (
            "사용자 데이터 요약을 사용할 수 없습니다. 데이터에 접근했다고 주장하거나 "
            "데이터를 추측하지 말고, 대화 내용만으로 답변하세요."
        )
    else:
        summary_context = f"""- 데이터 기간: {summary.get('period', '데이터 없음')}
- 총 레코드: {summary.get('count', 0)}개
- 주요 지표:
  * 합계: {summary.get('metrics', {}).get('total', 0)}
  * 평균: {summary.get('metrics', {}).get('average', 0)}
  * 최대: {summary.get('metrics', {}).get('max', 0)}
  * 최소: {summary.get('metrics', {}).get('min', 0)}
- 최근 트렌드: {summary.get('trend', '분석 불가')}"""

    system_prompt = f"""당신은 사용자의 질문에 친절하고 간결하게 답하는 AI 비서입니다.

[사용자 데이터 요약]
{summary_context}

데이터 요약이 제공된 경우에만 해당 데이터에 기반해 맞춤형 답변을 제공하세요.
요약이 없으면 데이터에 접근했다고 주장하지 말고 대화 내용만으로 답변하세요."""

    history = [
        {"role": message["role"], "content": message["content"]}
        for message in (messages or [])
        if message.get("role") in {"user", "assistant"}
        and isinstance(message.get("content"), str)
        and message["content"].strip()
    ][-40:]
    if not history or history[-1] != {"role": "user", "content": user_message}:
        history.append({"role": "user", "content": user_message})

    response = _client().chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
        messages=[{"role": "system", "content": system_prompt}, *history[-12:]],
        max_completion_tokens=500,
    )

    answer = response.choices[0].message.content
    if not answer:
        raise ValueError("OpenAI API가 비어 있는 응답을 반환했습니다.")
    return answer
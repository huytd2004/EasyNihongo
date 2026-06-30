"""
Review Quiz Generation Pipeline.
Calls Gemini to produce a structured list of multiple-choice questions
from deck vocabulary + JLPT level + recent mistakes context.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

try:
    from .llm_client import LLMClient
except ImportError:
    from llm_client import LLMClient

logger = logging.getLogger(__name__)


def _extract_text_and_check(resp: Any) -> str:
    """Extract text from LLM response and raise if it's an error placeholder."""
    text = resp.get('text', '') if isinstance(resp, dict) else str(resp)
    if (text.startswith('[[Gemini error]]') or 
        text.startswith('[[LLM unavailable]]') or 
        text.startswith('[[OpenAI error]]') or 
        text.startswith('[[Groq error]]')):
        raise RuntimeError(f'LLM error: {text[:300]}')
    return text

# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_quiz_prompt(
    words: List[Dict],
    level: str,
    question_count: int,
    recent_mistakes: List[Dict],
) -> str:
    """Build the Gemini prompt for quiz generation."""

    # Vocabulary block
    words_lines = []
    for w in words:
        line = f"- {w.get('surface', '')} ({w.get('reading', '')}) — {w.get('meaning', '')}"
        if w.get('backNotes') or w.get('back_notes'):
            line += f" [note: {w.get('backNotes') or w.get('back_notes')}]"
        words_lines.append(line)
    words_block = "\n".join(words_lines) if words_lines else "(no vocabulary provided)"

    # Recent mistakes block (top 10 for brevity)
    mistakes_lines = []
    for m in (recent_mistakes or [])[:10]:
        if isinstance(m, dict):
            orig = m.get('original') or m.get('wrong') or ''
            corr = m.get('corrected') or m.get('correct') or ''
            note = m.get('note') or m.get('explanation') or ''
            if orig and corr:
                mistakes_lines.append(f"- Wrong: 「{orig}」→ Correct: 「{corr}」 ({note})")
    mistakes_block = (
        "Recent learner mistakes (prioritize these patterns in questions):\n" +
        "\n".join(mistakes_lines)
    ) if mistakes_lines else ""

    schema_example = json.dumps({
        "questions": [
            {
                "id": 1,
                "type": "multiple_choice",
                "question_ja": "昨日、友達と映画を___。",
                "question_vn": "Hôm qua, tôi đã ___ phim với bạn.",
                "choices": ["見た", "見る", "見て", "見ます"],
                "answer": "見た",
                "explanation_vn": "Vì câu dùng 「昨日」(hôm qua) nên dùng thể た (quá khứ).",
                "target_word": "見る",
                "hint": "時制に注意（昨日＝過去形）"
            }
        ]
    }, ensure_ascii=False, indent=2)

    prompt = f"""You are a Japanese language quiz generator for JLPT {level} learners.

Task: Generate exactly {question_count} multiple-choice questions to test the following vocabulary.
Each question must have a Japanese fill-in-the-blank sentence, 4 answer choices, and one correct answer.

Rules:
1. Base questions primarily on the vocabulary list below.
2. If recent mistakes are provided, create at least {min(3, question_count // 4)} questions targeting those specific error patterns.
3. All choices must be plausible (similar grammar/vocab, not obviously wrong).
4. question_ja is a Japanese sentence with ___ as the blank.
5. question_vn is the Vietnamese translation of question_ja (with ___ too).
6. explanation_vn is a brief Vietnamese explanation of why the answer is correct.
7. target_word is the dictionary form of the tested vocabulary item.
8. hint is a short Japanese grammar hint.
9. Generate EXACTLY {question_count} questions. Do not stop early.
10. Return ONLY valid JSON — no markdown, no explanation outside the JSON.

Vocabulary to test:
{words_block}

{mistakes_block}

Return this exact JSON structure:
{schema_example}

IMPORTANT: The "questions" array must contain exactly {question_count} items."""

    return prompt


# ── Parser ─────────────────────────────────────────────────────────────────────

def _parse_questions(text: str, expected_count: int) -> tuple[List[Dict], bool]:
    """
    Parse LLM output into a list of question dicts.
    Returns (questions, is_complete) where is_complete = len == expected_count.
    """
    # Strip code fences
    cleaned = re.sub(r'```(?:json)?\n?', '', text)
    cleaned = re.sub(r'```\s*$', '', cleaned).strip()

    def try_parse(s: str):
        try:
            return json.loads(s)
        except Exception:
            pass
        # Try greedy outer {...}
        m = re.search(r'\{[\s\S]*\}', s)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return None

    parsed = try_parse(cleaned)
    if isinstance(parsed, dict):
        questions = parsed.get('questions', [])
        if isinstance(questions, list):
            valid = [q for q in questions if isinstance(q, dict) and q.get('question_ja') and q.get('answer')]
            return valid, len(valid) >= expected_count

    # Try extracting partial questions array
    arr_match = re.search(r'"questions"\s*:\s*(\[[\s\S]*)', cleaned)
    if arr_match:
        # Try truncated array
        raw_arr = arr_match.group(1)
        # Close it if truncated
        for closing in ['', ']', ']}']:
            try:
                partial = json.loads(raw_arr + closing)
                if isinstance(partial, list):
                    valid = [q for q in partial if isinstance(q, dict) and q.get('question_ja') and q.get('answer')]
                    return valid, len(valid) >= expected_count
            except Exception:
                pass

    return [], False


# ── Pipeline ──────────────────────────────────────────────────────────────────

class ReviewPipeline:
    """Generates quiz questions using the LLM client."""

    MAX_RETRIES = 2

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_quiz(
        self,
        words: List[Dict],
        level: str = 'N3',
        question_count: int = 20,
        recent_mistakes: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Generate quiz questions.
        Returns { questions: [...], warning: str|None }
        """
        recent_mistakes = recent_mistakes or []
        prompt = _build_quiz_prompt(words, level, question_count, recent_mistakes)

        questions: List[Dict] = []
        warning: Optional[str] = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self.llm.complete(prompt, max_tokens=4096, temperature=0.3)
                text = _extract_text_and_check(resp)
            except RuntimeError as e:
                logger.error('[ReviewPipeline] quiz LLM error on attempt %d: %s', attempt, e)
                raise

            parsed, is_complete = _parse_questions(text, question_count)

            if is_complete:
                questions = parsed
                break

            if attempt < self.MAX_RETRIES:
                # Partial — retry with stronger instruction
                prompt = _build_quiz_prompt(words, level, question_count, recent_mistakes)
                prompt += f"\n\nIMPORTANT RETRY: Previous attempt only generated {len(parsed)} questions. You MUST generate all {question_count}."
            else:
                # Give up — return what we have with warning
                questions = parsed if parsed else []
                if len(questions) < question_count:
                    warning = (
                        f"Chỉ tạo được {len(questions)}/{question_count} câu hỏi. "
                        "Vui lòng thử lại nếu muốn đủ số câu."
                    )

        # Normalise IDs
        for i, q in enumerate(questions, start=1):
            q['id'] = i
            if 'type' not in q:
                q['type'] = 'multiple_choice'

        return {'questions': questions, 'warning': warning}

    def generate_story(
        self,
        words: List[Dict],
        level: str = 'N3',
        recent_mistakes: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an interactive story with embedded vocabulary and questions.
        Returns { title, setting_vn, segments: [...], warning }
        """
        import logging
        logger = logging.getLogger(__name__)

        recent_mistakes = recent_mistakes or []
        prompt = _build_story_prompt(words, level, recent_mistakes)
        logger.info('[ReviewPipeline] generate_story: words=%d, level=%s', len(words), level)

        story: Optional[Dict] = None
        warning: Optional[str] = None
        last_text = ''

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self.llm.complete(prompt, max_tokens=8192, temperature=0.4)
                text = _extract_text_and_check(resp)
            except RuntimeError as e:
                logger.error('[ReviewPipeline] story LLM error on attempt %d: %s', attempt, e)
                if attempt == self.MAX_RETRIES:
                    story = {'title': 'Story', 'setting_vn': '', 'segments': []}
                    warning = f'Lỗi LLM: {str(e)[:200]}. Vui lòng thử lại.'
                    break
                continue

            last_text = text
            logger.info('[ReviewPipeline] attempt %d raw response length: %d, first 500 chars: %s', attempt, len(text), text[:500])

            parsed = _parse_story(text)
            seg_count = len(parsed.get('segments', [])) if parsed else 0
            logger.info('[ReviewPipeline] attempt %d parsed segments: %d', attempt, seg_count)

            if not parsed:
                logger.warning('[ReviewPipeline] attempt %d: _parse_story returned None. Raw text (800 chars): %s', attempt, text[:800])

            # Accept any response with at least 1 segment
            if parsed and seg_count >= 1:
                story = parsed
                if seg_count < 4:
                    warning = f'Câu chuyện chỉ có {seg_count} đoạn (yêu cầu 4-5). Vui lòng thử lại để nhận đủ nội dung.'
                break

            if attempt < self.MAX_RETRIES:
                retry_msg = f'\n\nIMPORTANT RETRY (attempt {attempt + 2}): The previous response was invalid or had 0 parseable segments. You MUST return valid JSON with 4-5 segments. Do not include any text outside the JSON object.'
                prompt = _build_story_prompt(words, level, recent_mistakes) + retry_msg
            else:
                logger.warning('[ReviewPipeline] All retries failed. Last response (%d chars): %s', len(last_text), last_text[:1200])
                story = parsed or {'title': 'Story', 'setting_vn': '', 'segments': []}
                if not story.get('segments'):
                    warning = 'Không thể tạo câu chuyện. Vui lòng thử lại.'

        # Normalise segment IDs
        if story and story.get('segments'):
            for i, seg in enumerate(story['segments'], start=1):
                seg['id'] = i
                if seg.get('question'):
                    seg['question']['id'] = i

        return {
            'title': story.get('title', '') if story else '',
            'setting_vn': story.get('setting_vn', '') if story else '',
            'segments': story.get('segments', []) if story else [],
            'warning': warning,
        }


# ── Story prompt & parser ──────────────────────────────────────────────────────

def _build_story_prompt(
    words: List[Dict],
    level: str,
    recent_mistakes: List[Dict],
) -> str:
    """Build Gemini prompt for interactive story generation."""

    words_lines = []
    for w in words[:15]:  # Limit to 15 words for manageable story
        words_lines.append(f"- {w.get('surface', '')} ({w.get('reading', '')}) — {w.get('meaning', '')}")
    words_block = '\n'.join(words_lines) if words_lines else '(no vocabulary)'

    mistakes_lines = []
    for m in (recent_mistakes or [])[:5]:
        if isinstance(m, dict):
            orig = m.get('original') or ''
            corr = m.get('corrected') or ''
            if orig and corr:
                mistakes_lines.append(f"- Wrong: 「{orig}」→ Correct: 「{corr}」")
    mistakes_block = (
        "Learner's recent mistakes (weave these patterns into the story to practice):\n" +
        '\n'.join(mistakes_lines)
    ) if mistakes_lines else ''

    schema_example = json.dumps({
        "title": "カフェでの出会い",
        "setting_vn": "Một buổi chiều tại quán cà phê nhỏ ở Tokyo. Nhân vật chính (bạn) muốn gọi đồ uống.",
        "segments": [
            {
                "id": 1,
                "scene_vn": "Bạn bước vào quán và nhìn thấy thực đơn.",
                "dialogue_speaker": "Phục vụ",
                "dialogue_ja": "いらっしゃいませ！何にしますか？",
                "dialogue_vn": "Chào mừng quý khách! Quý khách muốn dùng gì ạ?",
                "highlighted_words": [
                    {"word": "何", "reading": "なに", "meaning": "gì, cái gì"}
                ],
                "question": {
                    "prompt_vn": "Bạn muốn gọi một cốc cà phê. Hãy chọn câu đúng:",
                    "choices": [
                        {"ja": "コーヒーをください。", "vn": "Cho tôi cà phê."},
                        {"ja": "コーヒーが好きですか？", "vn": "Bạn có thích cà phê không?"},
                        {"ja": "コーヒーを飲みました。", "vn": "Tôi đã uống cà phê."},
                        {"ja": "コーヒーはありますか？", "vn": "Có cà phê không?"}
                    ],
                    "answer_index": 0,
                    "explanation_vn": "「〜をください」là cách lịch sự để yêu cầu/gọi món.",
                    "hint_ja": "〜をください = xin cho tôi〜"
                }
            }
        ]
    }, ensure_ascii=False, indent=2)

    return f"""You are a Japanese language interactive story generator for JLPT {level} learners.

Task: Create an immersive interactive story using the vocabulary below.
The story should have 4-5 segments, each with a dialogue scene and one multiple-choice question for the learner.

Rules:
1. Use vocabulary from the list naturally in dialogues.
2. Each segment has: scene description (in Vietnamese), a character's dialogue (Japanese + Vietnamese), highlighted vocabulary, and one question.
3. The question should be practical: "how would YOU respond?" or "which word fits here?".
4. All 4 choices must be grammatically plausible but only one is correct.
5. answer_index is 0-based (0 = first choice).
6. Keep Japanese at {level} difficulty. Furigana in highlighted_words.
7. Return ONLY valid JSON — no markdown.
{mistakes_block and chr(10) + mistakes_block or ''}

Vocabulary to incorporate:
{words_block}

Return this exact JSON structure:
{schema_example}

IMPORTANT: Generate exactly 4-5 segments. Each segment MUST have a "question" object."""


def _parse_story(text: str) -> Optional[Dict]:
    """Parse LLM output into a story dict. Tries multiple strategies."""
    if not text or not text.strip():
        return None

    # Strip code fences
    cleaned = re.sub(r'```(?:json)?\n?', '', text)
    cleaned = re.sub(r'```\s*$', '', cleaned).strip()

    def try_json(s: str):
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        return None

    # Strategy 1: direct parse
    parsed = try_json(cleaned)
    if parsed and 'segments' in parsed:
        return parsed

    # Strategy 2: greedy outer {...}
    m = re.search(r'\{[\s\S]*\}', cleaned)
    if m:
        parsed = try_json(m.group(0))
        if parsed and 'segments' in parsed:
            return parsed

    # Strategy 3: extract 'segments' array even if outer JSON is malformed/truncated
    seg_match = re.search(r'"segments"\s*:\s*(\[[\s\S]*)', cleaned)
    if seg_match:
        raw_arr = seg_match.group(1)
        # Try adding various closing chars to fix truncation
        for suffix in ('', ']', ']}', '}\n}', '}\n]}'):
            try:
                partial = json.loads(raw_arr + suffix)
                if isinstance(partial, list) and partial:
                    # Reconstruct minimal story dict
                    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', cleaned)
                    setting_m = re.search(r'"setting_vn"\s*:\s*"([^"]+)"', cleaned)
                    return {
                        'title': title_m.group(1) if title_m else '',
                        'setting_vn': setting_m.group(1) if setting_m else '',
                        'segments': partial,
                    }
            except Exception:
                pass

    return None

def build_prompt(input_text: str, ranked_senses: list[dict], detected_domains: list[str]) -> str:
    """
    Tạo structured prompt cho LLM từ ranked_senses và detected_domains.
    Output yêu cầu LLM trả về JSON với translation + notes.
    """
    domains_str = ", ".join(detected_domains) if detected_domains else "general"

    evidence_lines = []
    for rs in ranked_senses:
        top = rs['top_sense']
        line = (
            f"- Token: {rs['surface']}"
            f" → Sense: {top.get('glossVi', '?')}"
            f" | Domain: {top.get('domain', '?')}"
            f" | Register: {top.get('register', '?')}"
            f" | Score: {rs['score']:.3f}"
        )
        if top.get('culturalNote'):
            line += f"\n  ⚠ Cultural note: {top['culturalNote']}"
        if top.get('usageNote'):
            line += f"\n  📌 Usage: {top['usageNote']}"
        examples = top.get('examples') or []
        if examples and examples[0].get('ja'):
            ex = examples[0]
            line += f"\n  Ví dụ: {ex.get('ja', '')} → {ex.get('vi', '')}"
        evidence_lines.append(line)

    evidence_block = "\n".join(evidence_lines) if evidence_lines else "(không có evidence)"

    prompt = f"""Bạn là dịch giả chuyên ngành Nhật-Việt.
Nhiệm vụ: Dịch đoạn văn tiếng Nhật sang tiếng Việt chính xác và tự nhiên.

- Sử dụng các nghĩa trong "Graph evidence" bên dưới làm định hướng dịch thuật ngữ chuyên ngành bắt buộc.
- Tuy nhiên, hãy điều chỉnh cấu trúc câu, thêm các từ nối phù hợp (ví dụ: "dựa trên", "cơ chế") để câu dịch trôi chảy, tự nhiên và đúng phong cách hành văn kỹ thuật Việt Nam.
- Đối với các thuật ngữ chuyên ngành (đặc biệt là Công nghệ thông tin/Kỹ thuật), nếu "Graph evidence" chứa từ tiếng Anh hoặc từ dịch thô/chưa tối ưu (ví dụ: "node", "failover", "timeout", "nhịp tim"), hãy Việt hóa sang thuật ngữ tiếng Việt chuẩn kỹ thuật và đặt thuật ngữ tiếng Anh gốc trong ngoặc đơn để làm rõ nghĩa (Ví dụ: "nút (node)", "giao thức heartbeat (nhịp tim)", "cơ chế chuyển đổi dự phòng (failover)", "hiện tượng hết thời gian chờ (timeout)", "tiến trình chính (master process)").
- Tránh dịch thô (literal) từng chữ, hãy diễn đạt trôi chảy, đúng ngữ pháp tiếng Việt chuyên ngành.
- Nếu có sắc thái văn hóa, giữ nguyên ý nghĩa văn hóa đó.

Source text:
{input_text}

Graph evidence:
{evidence_block}

Trả về đúng JSON sau (không thêm markdown code block, không giải thích thêm):
{{
  "translation": "<bản dịch đầy đủ, tự nhiên>",
  "notes": []
}}

Lưu ý quan trọng: trường "translation" phải chứa TOÀN BỘ bản dịch, không bao giờ cắt ngang giữa chừng. Trường "notes" có thể để mảng rỗng để tiết kiệm token.
"""
    return prompt

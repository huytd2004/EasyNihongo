package vn.hust.huy.backend.dto.request;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ReviewQuizRequest {
    /** ID của deck để lấy danh sách thẻ */
    private String deckId;
    /** Cấp độ JLPT: N5/N4/N3/N2/N1 */
    private String level;
    /** Số câu hỏi mong muốn */
    private Integer questionCount;
    /** Mistakes gần nhất (frontend truyền thẳng từ RecentMistakesResponse) */
    private List<Map<String, Object>> recentMistakes;
}

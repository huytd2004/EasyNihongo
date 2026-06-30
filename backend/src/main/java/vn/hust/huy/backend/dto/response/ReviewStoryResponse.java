package vn.hust.huy.backend.dto.response;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@Builder
public class ReviewStoryResponse {
    /** Tiêu đề câu chuyện (tiếng Nhật) */
    private String title;
    /** Bối cảnh câu chuyện (tiếng Việt) */
    private String settingVn;
    /** Danh sách đoạn hội thoại với câu hỏi nhúng */
    private List<Map<String, Object>> segments;
    /** Cảnh báo nếu story không đầy đủ */
    private String warning;
}

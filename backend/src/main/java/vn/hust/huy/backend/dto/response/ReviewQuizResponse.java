package vn.hust.huy.backend.dto.response;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@Builder
public class ReviewQuizResponse {
    /** Danh sách câu hỏi trắc nghiệm */
    private List<Map<String, Object>> questions;
    /** Cảnh báo nếu số câu < yêu cầu */
    private String warning;
}

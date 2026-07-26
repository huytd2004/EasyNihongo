package vn.hust.huy.backend.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TaskStatusResponse {
    private String status;  // PENDING, PROCESSING, SUCCESS, FAILED
    private Object result;  // The generated JSON result (e.g. ReviewQuizResponse or ReviewStoryResponse)
    private String warning;
}

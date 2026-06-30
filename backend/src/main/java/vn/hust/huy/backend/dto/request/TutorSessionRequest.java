package vn.hust.huy.backend.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class TutorSessionRequest {
    private String deckId;
    private String scenarioName;
    private String level;
    private Integer durationMinutes;
    private List<Object> targetWords;
}

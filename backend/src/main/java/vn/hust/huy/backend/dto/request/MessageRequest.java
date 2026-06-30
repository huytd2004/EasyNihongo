package vn.hust.huy.backend.dto.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class MessageRequest {
    private String content;
    private String inputMode; // text | voice
}

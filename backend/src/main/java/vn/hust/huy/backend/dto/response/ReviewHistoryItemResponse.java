package vn.hust.huy.backend.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

/**
 * A single history entry (quiz or story) shown in the profile page.
 */
@Getter
@Builder
public class ReviewHistoryItemResponse {
    /** "quiz" or "story" */
    private String type;
    private String id;
    /** Deck name or story title */
    private String title;
    private String level;
    private int score;
    private int totalQuestions;
    private Instant createdAt;
}

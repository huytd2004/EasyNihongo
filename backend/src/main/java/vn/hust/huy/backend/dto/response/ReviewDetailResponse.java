package vn.hust.huy.backend.dto.response;

import com.fasterxml.jackson.annotation.JsonRawValue;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

/**
 * Full detail of a single quiz or story review session.
 */
@Getter
@Builder
public class ReviewDetailResponse {
    /** "quiz" or "story" */
    private String type;
    private String id;
    private String title;
    private String level;
    private int score;
    private int totalQuestions;
    private Instant createdAt;

    /** Raw JSON — questions array for quiz, story object for story */
    @JsonRawValue
    private String questionsData;

    /** Raw JSON — answers map for story (null for quiz) */
    @JsonRawValue
    private String answersData;
}

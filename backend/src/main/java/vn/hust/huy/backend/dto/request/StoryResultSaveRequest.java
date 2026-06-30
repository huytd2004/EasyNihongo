package vn.hust.huy.backend.dto.request;

import lombok.Data;

@Data
public class StoryResultSaveRequest {
    private String deckId;
    private String level;
    private String title;
    private int score;
    private int totalQuestions;
    private Object storyData;
    private Object answersData;
}

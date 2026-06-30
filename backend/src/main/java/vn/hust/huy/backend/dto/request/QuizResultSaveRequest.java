package vn.hust.huy.backend.dto.request;

import lombok.Data;

@Data
public class QuizResultSaveRequest {
    private String deckId;
    private String level;
    private int score;
    private int totalQuestions;
    private Object questionsData;
}

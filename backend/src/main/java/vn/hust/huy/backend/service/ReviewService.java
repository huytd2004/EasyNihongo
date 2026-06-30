package vn.hust.huy.backend.service;

import vn.hust.huy.backend.dto.request.ReviewQuizRequest;
import vn.hust.huy.backend.dto.request.QuizResultSaveRequest;
import vn.hust.huy.backend.dto.request.StoryResultSaveRequest;
import vn.hust.huy.backend.dto.response.ReviewDetailResponse;
import vn.hust.huy.backend.dto.response.ReviewHistoryItemResponse;
import vn.hust.huy.backend.dto.response.ReviewQuizResponse;
import vn.hust.huy.backend.dto.response.ReviewStoryResponse;

import java.util.List;

public interface ReviewService {
    ReviewQuizResponse generateQuiz(ReviewQuizRequest request, String userEmail);
    ReviewStoryResponse generateStory(ReviewQuizRequest request, String userEmail);
    void saveQuizResult(QuizResultSaveRequest request, String userEmail);
    void saveStoryResult(StoryResultSaveRequest request, String userEmail);
    List<ReviewHistoryItemResponse> getHistory(String userEmail, int size);

    ReviewDetailResponse getQuizDetail(String id, String userEmail);

    ReviewDetailResponse getStoryDetail(String id, String userEmail);
}


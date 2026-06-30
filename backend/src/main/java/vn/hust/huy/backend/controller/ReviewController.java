package vn.hust.huy.backend.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import vn.hust.huy.backend.dto.request.ReviewQuizRequest;
import vn.hust.huy.backend.dto.request.QuizResultSaveRequest;
import vn.hust.huy.backend.dto.request.StoryResultSaveRequest;
import vn.hust.huy.backend.dto.response.ApiResponse;
import vn.hust.huy.backend.dto.response.ReviewDetailResponse;
import vn.hust.huy.backend.dto.response.ReviewHistoryItemResponse;
import vn.hust.huy.backend.dto.response.ReviewQuizResponse;
import vn.hust.huy.backend.dto.response.ReviewStoryResponse;
import vn.hust.huy.backend.service.ReviewService;

import java.util.List;

@RestController
@RequestMapping("/api/v1/review")
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;

    /** POST /api/v1/review/quiz/generate */
    @PostMapping("/quiz/generate")
    public ResponseEntity<ApiResponse<ReviewQuizResponse>> generateQuiz(
            @RequestBody ReviewQuizRequest request,
            @AuthenticationPrincipal UserDetails userDetails) {
        ReviewQuizResponse resp = reviewService.generateQuiz(request, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(resp, "Quiz generated"));
    }

    /** POST /api/v1/review/story/generate */
    @PostMapping("/story/generate")
    public ResponseEntity<ApiResponse<ReviewStoryResponse>> generateStory(
            @RequestBody ReviewQuizRequest request,
            @AuthenticationPrincipal UserDetails userDetails) {
        ReviewStoryResponse resp = reviewService.generateStory(request, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(resp, "Story generated"));
    }

    /** POST /api/v1/review/quiz/result */
    @PostMapping("/quiz/result")
    public ResponseEntity<ApiResponse<Void>> saveQuizResult(
            @RequestBody QuizResultSaveRequest request,
            @AuthenticationPrincipal UserDetails userDetails) {
        reviewService.saveQuizResult(request, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(null, "Quiz result saved"));
    }

    /** POST /api/v1/review/story/result */
    @PostMapping("/story/result")
    public ResponseEntity<ApiResponse<Void>> saveStoryResult(
            @RequestBody StoryResultSaveRequest request,
            @AuthenticationPrincipal UserDetails userDetails) {
        reviewService.saveStoryResult(request, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(null, "Story result saved"));
    }

    /**
     * GET /api/v1/review/history?size=10
     * Returns merged quiz + story review history for the authenticated user,
     * sorted by most recent first.
     */
    @GetMapping("/history")
    public ResponseEntity<ApiResponse<List<ReviewHistoryItemResponse>>> getHistory(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestParam(defaultValue = "10") int size) {
        List<ReviewHistoryItemResponse> history = reviewService.getHistory(userDetails.getUsername(), size);
        return ResponseEntity.ok(ApiResponse.success(history, "Lấy lịch sử bài tập thành công"));
    }

    /** GET /api/v1/review/quiz/{id} */
    @GetMapping("/quiz/{id}")
    public ResponseEntity<ApiResponse<ReviewDetailResponse>> getQuizDetail(
            @PathVariable String id,
            @AuthenticationPrincipal UserDetails userDetails) {
        ReviewDetailResponse detail = reviewService.getQuizDetail(id, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(detail, "Lấy chi tiết quiz thành công"));
    }

    /** GET /api/v1/review/story/{id} */
    @GetMapping("/story/{id}")
    public ResponseEntity<ApiResponse<ReviewDetailResponse>> getStoryDetail(
            @PathVariable String id,
            @AuthenticationPrincipal UserDetails userDetails) {
        ReviewDetailResponse detail = reviewService.getStoryDetail(id, userDetails.getUsername());
        return ResponseEntity.ok(ApiResponse.success(detail, "Lấy chi tiết story thành công"));
    }
}


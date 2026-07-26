package vn.hust.huy.backend.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import vn.hust.huy.backend.dto.request.ReviewQuizRequest;
import vn.hust.huy.backend.dto.request.QuizResultSaveRequest;
import vn.hust.huy.backend.dto.request.StoryResultSaveRequest;
import vn.hust.huy.backend.dto.response.ReviewDetailResponse;
import vn.hust.huy.backend.dto.response.ReviewHistoryItemResponse;
import vn.hust.huy.backend.dto.response.ReviewQuizResponse;
import vn.hust.huy.backend.dto.response.ReviewStoryResponse;
import vn.hust.huy.backend.model.entity.Flashcard;
import vn.hust.huy.backend.model.entity.FlashcardDeck;
import vn.hust.huy.backend.model.entity.QuizReview;
import vn.hust.huy.backend.model.entity.StoryReview;
import vn.hust.huy.backend.model.entity.TutorSessionResult;
import vn.hust.huy.backend.model.entity.User;
import vn.hust.huy.backend.model.enums.FlashcardStatus;
import vn.hust.huy.backend.model.enums.JlptLevel;
import vn.hust.huy.backend.repository.FlashcardRepository;
import vn.hust.huy.backend.repository.FlashcardDeckRepository;
import vn.hust.huy.backend.repository.QuizReviewRepository;
import vn.hust.huy.backend.repository.StoryReviewRepository;
import vn.hust.huy.backend.repository.TutorSessionResultRepository;
import vn.hust.huy.backend.repository.UserRepository;
import vn.hust.huy.backend.service.ReviewService;
import vn.hust.huy.backend.service.StreakService;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.*;

@Service
@RequiredArgsConstructor
public class ReviewServiceImpl implements ReviewService {

    private static final Logger log = LoggerFactory.getLogger(ReviewServiceImpl.class);

    private final UserRepository userRepository;
    private final FlashcardRepository flashcardRepository;
    private final TutorSessionResultRepository resultRepository;
    private final FlashcardDeckRepository flashcardDeckRepository;
    private final QuizReviewRepository quizReviewRepository;
    private final StoryReviewRepository storyReviewRepository;
    private final ObjectMapper objectMapper;
    private final StreakService streakService;
    private final org.springframework.amqp.rabbit.core.RabbitTemplate rabbitTemplate;
    private final org.springframework.data.redis.core.StringRedisTemplate stringRedisTemplate;

    @Value("${app.tutor.ai-base-url:http://localhost:8001}")
    private String aiBaseUrl;

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    @Override
    public ReviewQuizResponse generateQuiz(ReviewQuizRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();

        // ── 1. Load deck words ────────────────────────────────────────────────
        List<Map<String, Object>> words = loadDeckWords(request.getDeckId(), user);

        // ── 2. Load recent mistakes (up to 10 from last 5 sessions) ──────────
        List<Map<String, Object>> recentMistakes = loadRecentMistakes(user, request.getRecentMistakes());

        // ── 3. Call Python AI ─────────────────────────────────────────────────
        int questionCount = request.getQuestionCount() != null ? request.getQuestionCount() : 20;
        // Cap question count to available words
        if (!words.isEmpty()) {
            questionCount = Math.min(questionCount, words.size());
        }

        return callPythonQuizGenerate(words, request.getLevel(), questionCount, recentMistakes);
    }

    @Override
    public ReviewStoryResponse generateStory(ReviewQuizRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();

        List<Map<String, Object>> words = loadDeckWords(request.getDeckId(), user);
        List<Map<String, Object>> recentMistakes = loadRecentMistakes(user, request.getRecentMistakes());

        log.info("[ReviewService] generateStory: deckId={}, words={}, level={}",
                request.getDeckId(), words.size(), request.getLevel());

        if (words.isEmpty()) {
            log.warn("[ReviewService] generateStory: no words found for deckId={}", request.getDeckId());
            return ReviewStoryResponse.builder()
                    .title("Story")
                    .settingVn("")
                    .segments(List.of())
                    .warning("Deck không có flashcard nào. Hãy thêm từ vựng vào deck trước khi tạo câu chuyện.")
                    .build();
        }

        return callPythonStoryGenerate(words, request.getLevel(), recentMistakes);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private List<Map<String, Object>> loadDeckWords(String deckId, User user) {
        if (deckId == null || deckId.isBlank()) return List.of();
        try {
            UUID deckUuid = UUID.fromString(deckId);
            // Prefer due cards first, then new cards
            List<Flashcard> dueCards = flashcardRepository.findDueByDeckAndUser(
                    deckUuid, user, Instant.now(),
                    FlashcardStatus.LEARNING, FlashcardStatus.REVIEW);
            List<Flashcard> newCards = flashcardRepository.findNewByDeckAndUser(
                    deckUuid, user, FlashcardStatus.NEW_CARD, PageRequest.of(0, 30));

            Set<UUID> seen = new LinkedHashSet<>();
            List<Flashcard> combined = new ArrayList<>();
            for (Flashcard f : dueCards) { if (seen.add(f.getId())) combined.add(f); }
            for (Flashcard f : newCards)  { if (seen.add(f.getId())) combined.add(f); }

            // Fallback: if no due/new cards, use all flashcards in the deck
            // (e.g. all cards are MASTERED — still useful for story/quiz generation)
            if (combined.isEmpty()) {
                log.info("[ReviewService] loadDeckWords: no due/new cards, falling back to all cards for deckId={}", deckId);
                combined = flashcardRepository.findAllByDeckIdAndDeckUser(deckUuid, user)
                        .stream().limit(30).collect(java.util.stream.Collectors.toList());
            }

            return combined.stream().map(f -> {
                Map<String, Object> w = new LinkedHashMap<>();
                w.put("id", f.getId().toString());
                w.put("surface", f.getFrontText());
                w.put("reading", f.getFrontReading() != null ? f.getFrontReading() : "");
                w.put("meaning", f.getBackText());
                if (f.getBackNotes() != null) w.put("backNotes", f.getBackNotes());
                return w;
            }).toList();
        } catch (Exception e) {
            log.warn("[ReviewService] loadDeckWords failed for deckId={}: {}", deckId, e.getMessage());
            return List.of();
        }
    }

    /**
     * If the frontend already sent recentMistakes, use them directly.
     * Otherwise load from DB.
     */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> loadRecentMistakes(
            User user, List<Map<String, Object>> frontendMistakes) {
        if (frontendMistakes != null && !frontendMistakes.isEmpty()) {
            return frontendMistakes;
        }
        try {
            List<TutorSessionResult> results =
                    resultRepository.findByUser_IdOrderByCreatedAtDesc(user.getId(), PageRequest.of(0, 5));
            List<Map<String, Object>> all = new ArrayList<>();
            for (TutorSessionResult r : results) {
                if (r.getMistakes() == null) continue;
                try {
                    List<Map<String, Object>> ms = objectMapper.readValue(r.getMistakes(), List.class);
                    all.addAll(ms);
                    if (all.size() >= 10) break;
                } catch (Exception ignored) {}
            }
            return all.stream().limit(10).toList();
        } catch (Exception e) {
            log.warn("[ReviewService] loadRecentMistakes failed: {}", e.getMessage());
            return List.of();
        }
    }

    private ReviewQuizResponse callPythonQuizGenerate(
            List<Map<String, Object>> words,
            String level,
            int questionCount,
            List<Map<String, Object>> recentMistakes) {
        try {
            Map<String, Object> payload = Map.of(
                    "words", words,
                    "level", level != null ? level : "N3",
                    "question_count", questionCount,
                    "recent_mistakes", recentMistakes
            );
            String body = objectMapper.writeValueAsString(payload);

            URI uri = URI.create(aiBaseUrl + "/v1/review/quiz/generate");
            HttpRequest httpRequest = HttpRequest.newBuilder(uri)
                    .timeout(Duration.ofSeconds(120)) // LLM may take a while
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                log.warn("[ReviewService] Python quiz generate returned {}: {}", response.statusCode(), response.body());
                throw new IllegalStateException("AI service error: " + response.statusCode());
            }

            JsonNode root = objectMapper.readTree(response.body());
            List<Map<String, Object>> questions = new ArrayList<>();
            JsonNode qNode = root.get("questions");
            if (qNode != null && qNode.isArray()) {
                for (JsonNode q : qNode) {
                    questions.add(objectMapper.convertValue(q, Map.class));
                }
            }
            String warning = root.has("warning") && !root.get("warning").isNull()
                    ? root.get("warning").asText() : null;

            return ReviewQuizResponse.builder()
                    .questions(questions)
                    .warning(warning)
                    .build();

        } catch (Exception e) {
            log.error("[ReviewService] callPythonQuizGenerate failed: {}", e.getMessage());
            throw new RuntimeException("Không thể tạo câu hỏi. Vui lòng thử lại.", e);
        }
    }

    private ReviewStoryResponse callPythonStoryGenerate(
            List<Map<String, Object>> words,
            String level,
            List<Map<String, Object>> recentMistakes) {
        try {
            Map<String, Object> payload = Map.of(
                    "words", words,
                    "level", level != null ? level : "N3",
                    "recent_mistakes", recentMistakes
            );
            String body = objectMapper.writeValueAsString(payload);

            URI uri = URI.create(aiBaseUrl + "/v1/review/story/generate");
            HttpRequest httpRequest = HttpRequest.newBuilder(uri)
                    .timeout(Duration.ofSeconds(120))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                log.warn("[ReviewService] Python story generate returned {}: {}", response.statusCode(), response.body());
                throw new IllegalStateException("AI service error: " + response.statusCode());
            }

            JsonNode root = objectMapper.readTree(response.body());
            List<Map<String, Object>> segments = new ArrayList<>();
            JsonNode sNode = root.get("segments");
            if (sNode != null && sNode.isArray()) {
                for (JsonNode s : sNode) {
                    segments.add(objectMapper.convertValue(s, Map.class));
                }
            }
            String warning = root.has("warning") && !root.get("warning").isNull()
                    ? root.get("warning").asText() : null;

            return ReviewStoryResponse.builder()
                    .title(root.path("title").asText(""))
                    .settingVn(root.path("setting_vn").asText(""))
                    .segments(segments)
                    .warning(warning)
                    .build();

        } catch (Exception e) {
            log.error("[ReviewService] callPythonStoryGenerate failed: {}", e.getMessage());
            throw new RuntimeException("Không thể tạo câu chuyện. Vui lòng thử lại.", e);
        }
    }

    @Override
    public void saveQuizResult(QuizResultSaveRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();

        FlashcardDeck deck = null;
        if (request.getDeckId() != null && !request.getDeckId().isBlank()) {
            try {
                deck = flashcardDeckRepository.findById(UUID.fromString(request.getDeckId())).orElse(null);
            } catch (Exception ignored) {}
        }

        JlptLevel level = JlptLevel.N3;
        try {
            if (request.getLevel() != null) {
                level = JlptLevel.valueOf(request.getLevel().toUpperCase());
            }
        } catch (Exception ignored) {}

        String questionsJson = "[]";
        try {
            if (request.getQuestionsData() != null) {
                questionsJson = objectMapper.writeValueAsString(request.getQuestionsData());
            }
        } catch (Exception e) {
            log.error("Failed to serialize questionsData", e);
        }

        QuizReview review = QuizReview.builder()
                .user(user)
                .deck(deck)
                .level(level)
                .score(request.getScore())
                .totalQuestions(request.getTotalQuestions())
                .questionsData(questionsJson)
                .build();

        quizReviewRepository.save(review);

        // Tính streak: hoàn thành quiz tính là hoạt động học trong ngày
        streakService.updateStreak(user);
    }

    @Override
    public void saveStoryResult(StoryResultSaveRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();

        FlashcardDeck deck = null;
        if (request.getDeckId() != null && !request.getDeckId().isBlank()) {
            try {
                deck = flashcardDeckRepository.findById(UUID.fromString(request.getDeckId())).orElse(null);
            } catch (Exception ignored) {}
        }

        JlptLevel level = JlptLevel.N3;
        try {
            if (request.getLevel() != null) {
                level = JlptLevel.valueOf(request.getLevel().toUpperCase());
            }
        } catch (Exception ignored) {}

        String storyJson = "{}";
        String answersJson = "{}";
        try {
            if (request.getStoryData() != null) {
                storyJson = objectMapper.writeValueAsString(request.getStoryData());
            }
            if (request.getAnswersData() != null) {
                answersJson = objectMapper.writeValueAsString(request.getAnswersData());
            }
        } catch (Exception e) {
            log.error("Failed to serialize story/answers data", e);
        }

        StoryReview review = StoryReview.builder()
                .user(user)
                .deck(deck)
                .level(level)
                .title(request.getTitle() != null ? request.getTitle() : "Untitled Story")
                .score(request.getScore())
                .totalQuestions(request.getTotalQuestions())
                .storyData(storyJson)
                .answersData(answersJson)
                .build();

        storyReviewRepository.save(review);

        // Tính streak: hoàn thành story tính là hoạt động học trong ngày
        streakService.updateStreak(user);
    }

    @Override
    public List<ReviewHistoryItemResponse> getHistory(String userEmail, int size) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();
        UUID userId = user.getId();

        List<QuizReview> quizzes = quizReviewRepository.findByUser_IdOrderByCreatedAtDesc(
                userId, PageRequest.of(0, size));
        List<StoryReview> stories = storyReviewRepository.findByUser_IdOrderByCreatedAtDesc(
                userId, PageRequest.of(0, size));

        List<ReviewHistoryItemResponse> result = new ArrayList<>();

        for (QuizReview q : quizzes) {
            String title = q.getDeck() != null ? q.getDeck().getName() : "Quiz " + q.getLevel().name();
            result.add(ReviewHistoryItemResponse.builder()
                    .type("quiz")
                    .id(q.getId().toString())
                    .title(title)
                    .level(q.getLevel().name())
                    .score(q.getScore())
                    .totalQuestions(q.getTotalQuestions())
                    .createdAt(q.getCreatedAt())
                    .build());
        }

        for (StoryReview s : stories) {
            result.add(ReviewHistoryItemResponse.builder()
                    .type("story")
                    .id(s.getId().toString())
                    .title(s.getTitle())
                    .level(s.getLevel().name())
                    .score(s.getScore())
                    .totalQuestions(s.getTotalQuestions())
                    .createdAt(s.getCreatedAt())
                    .build());
        }

        // Sort by createdAt desc, then take top `size` items
        result.sort((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()));
        return result.stream().limit(size).toList();
    }

    @Override
    public ReviewDetailResponse getQuizDetail(String id, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();
        QuizReview q = quizReviewRepository.findById(UUID.fromString(id))
                .orElseThrow(() -> new IllegalArgumentException("Không tìm thấy quiz review"));
        
        if (!q.getUser().getId().equals(user.getId())) {
            throw new SecurityException("Không có quyền truy cập thông tin này");
        }

        String title = q.getDeck() != null ? q.getDeck().getName() : "Quiz " + q.getLevel().name();
        return ReviewDetailResponse.builder()
                .type("quiz")
                .id(q.getId().toString())
                .title(title)
                .level(q.getLevel().name())
                .score(q.getScore())
                .totalQuestions(q.getTotalQuestions())
                .createdAt(q.getCreatedAt())
                .questionsData(q.getQuestionsData())
                .build();
    }

    @Override
    public ReviewDetailResponse getStoryDetail(String id, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();
        StoryReview s = storyReviewRepository.findById(UUID.fromString(id))
                .orElseThrow(() -> new IllegalArgumentException("Không tìm thấy story review"));

        if (!s.getUser().getId().equals(user.getId())) {
            throw new SecurityException("Không có quyền truy cập thông tin này");
        }

        return ReviewDetailResponse.builder()
                .type("story")
                .id(s.getId().toString())
                .title(s.getTitle())
                .level(s.getLevel().name())
                .score(s.getScore())
                .totalQuestions(s.getTotalQuestions())
                .createdAt(s.getCreatedAt())
                .questionsData(s.getStoryData())
                .answersData(s.getAnswersData())
                .build();
    }

    @Override
    public String enqueueQuizGeneration(ReviewQuizRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();
        List<Map<String, Object>> words = loadDeckWords(request.getDeckId(), user);
        List<Map<String, Object>> recentMistakes = loadRecentMistakes(user, request.getRecentMistakes());

        int questionCount = request.getQuestionCount() != null ? request.getQuestionCount() : 20;
        if (!words.isEmpty()) {
            questionCount = Math.min(questionCount, words.size());
        }

        String taskId = UUID.randomUUID().toString();
        Map<String, Object> payload = Map.of(
            "taskId", taskId,
            "words", words,
            "level", request.getLevel() != null ? request.getLevel() : "N3",
            "questionCount", questionCount,
            "recentMistakes", recentMistakes
        );

        try {
            String jsonPayload = objectMapper.writeValueAsString(payload);
            stringRedisTemplate.opsForValue().set("task:status:" + taskId, "PENDING", java.time.Duration.ofHours(1));
            rabbitTemplate.convertAndSend(
                vn.hust.huy.backend.config.RabbitMQConfig.REVIEW_EXCHANGE,
                vn.hust.huy.backend.config.RabbitMQConfig.QUIZ_ROUTING_KEY,
                jsonPayload
            );
            return taskId;
        } catch (Exception e) {
            log.error("Failed to enqueue quiz generation to RabbitMQ for user {}", userEmail, e);
            throw new RuntimeException("Không thể gửi yêu cầu tạo quiz vào hàng đợi.", e);
        }
    }

    @Override
    public String enqueueStoryGeneration(ReviewQuizRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail).orElseThrow();
        List<Map<String, Object>> words = loadDeckWords(request.getDeckId(), user);
        List<Map<String, Object>> recentMistakes = loadRecentMistakes(user, request.getRecentMistakes());

        String taskId = UUID.randomUUID().toString();
        Map<String, Object> payload = Map.of(
            "taskId", taskId,
            "words", words,
            "level", request.getLevel() != null ? request.getLevel() : "N3",
            "recentMistakes", recentMistakes
        );

        try {
            String jsonPayload = objectMapper.writeValueAsString(payload);
            stringRedisTemplate.opsForValue().set("task:status:" + taskId, "PENDING", java.time.Duration.ofHours(1));
            rabbitTemplate.convertAndSend(
                vn.hust.huy.backend.config.RabbitMQConfig.REVIEW_EXCHANGE,
                vn.hust.huy.backend.config.RabbitMQConfig.STORY_ROUTING_KEY,
                jsonPayload
            );
            return taskId;
        } catch (Exception e) {
            log.error("Failed to enqueue story generation to RabbitMQ for user {}", userEmail, e);
            throw new RuntimeException("Không thể gửi yêu cầu tạo câu chuyện vào hàng đợi.", e);
        }
    }

    @Override
    public vn.hust.huy.backend.dto.response.TaskStatusResponse getTaskStatus(String taskId) {
        String status = stringRedisTemplate.opsForValue().get("task:status:" + taskId);
        if (status == null) {
            return vn.hust.huy.backend.dto.response.TaskStatusResponse.builder()
                .status("NOT_FOUND")
                .build();
        }

        if ("SUCCESS".equals(status)) {
            String resultJson = stringRedisTemplate.opsForValue().get("task:result:" + taskId);
            try {
                Object resultObj = objectMapper.readValue(resultJson, Object.class);
                return vn.hust.huy.backend.dto.response.TaskStatusResponse.builder()
                    .status(status)
                    .result(resultObj)
                    .build();
            } catch (Exception e) {
                log.error("Failed to parse task result JSON from Redis for task {}", taskId, e);
                return vn.hust.huy.backend.dto.response.TaskStatusResponse.builder()
                    .status("FAILED")
                    .warning("Lỗi phân giải kết quả nhiệm vụ.")
                    .build();
            }
        }

        return vn.hust.huy.backend.dto.response.TaskStatusResponse.builder()
            .status(status)
            .build();
    }
}


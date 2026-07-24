package vn.hust.huy.backend.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import vn.hust.huy.backend.dto.request.QuickTranslateRequest;
import vn.hust.huy.backend.dto.response.ApiResponse;
import vn.hust.huy.backend.dto.response.DeepTranslateResponse;
import vn.hust.huy.backend.dto.response.DeepTranslateResponse.KeyVocabularyItem;
import vn.hust.huy.backend.dto.response.DeepTranslateResponse.TranslationNote;
import vn.hust.huy.backend.dto.response.QuickTranslateResponse;
import vn.hust.huy.backend.exception.AppException;
import vn.hust.huy.backend.exception.ErrorCode;
import vn.hust.huy.backend.service.TranslateService;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class TranslateServiceImpl implements TranslateService {

    private static final String DEFAULT_SOURCE_LANG = "ja";
    private static final String DEFAULT_TARGET_LANG = "vi";

    private final ObjectMapper objectMapper;

    @Value("${app.translate.quick-url:https://translate.googleapis.com/translate_a/single}")
    private String quickTranslateUrl;

    @Value("${app.tutor.ai-base-url:http://localhost:8001}")
    private String aiBaseUrl;

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @Override
    public ApiResponse<QuickTranslateResponse> quickTranslate(QuickTranslateRequest request) {
        String sourceText = request.getText().trim();
        String sourceLang = normalizeLang(request.getSourceLang(), DEFAULT_SOURCE_LANG);
        String targetLang = normalizeLang(request.getTargetLang(), DEFAULT_TARGET_LANG);

        String translatedText = translateWithGoogleEndpoint(sourceText, sourceLang, targetLang);

        QuickTranslateResponse response = QuickTranslateResponse.builder()
                .sourceText(sourceText)
                .translatedText(translatedText)
                .sourceLang(sourceLang)
                .targetLang(targetLang)
                .provider("google-translate-public")
                .build();

        return ApiResponse.success(response, "Dịch nhanh thành công");
    }

    @Override
    public ApiResponse<DeepTranslateResponse> deepTranslate(QuickTranslateRequest request) {
        String sourceText = request.getText().trim();
        String sourceLang = normalizeLang(request.getSourceLang(), DEFAULT_SOURCE_LANG);
        String targetLang = normalizeLang(request.getTargetLang(), DEFAULT_TARGET_LANG);

        JsonNode payload = runPythonPipeline(sourceText);
        DeepTranslateResponse response = mapDeepTranslateResponse(payload, sourceText, sourceLang, targetLang);

        return ApiResponse.success(response, "Phân tích chuyên sâu thành công");
    }

    private JsonNode runPythonPipeline(String sourceText) {
        try {
            String requestBody = objectMapper.writeValueAsString(Map.of("text", sourceText));

            URI uri = URI.create(aiBaseUrl + "/v1/translate/deep");
            HttpRequest request = HttpRequest.newBuilder(uri)
                    .timeout(Duration.ofSeconds(60))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody, StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            int status = response.statusCode();
            String respBody = response.body();
            if (status != 200) {
                log.warn("Deep translate REST call returned non-200 ({}): {}", status, respBody);
                throw new AppException(ErrorCode.DEEP_TRANSLATION_FAILED);
            }

            if (respBody == null || respBody.isBlank()) {
                throw new AppException(ErrorCode.DEEP_TRANSLATION_FAILED);
            }

            return objectMapper.readTree(respBody);
        } catch (AppException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error("Deep translate REST API error: {}", ex.getMessage(), ex);
            throw new AppException(ErrorCode.DEEP_TRANSLATION_FAILED);
        }
    }

    private DeepTranslateResponse mapDeepTranslateResponse(
            JsonNode payload,
            String sourceText,
            String sourceLang,
            String targetLang) {

        String translatedText = payload.path("translation").asText("");
        if (translatedText.isBlank()) {
            throw new AppException(ErrorCode.DEEP_TRANSLATION_FAILED);
        }

        // detectedDomains
        List<String> detectedDomains = readTextList(payload.path("detectedDomains"));

        // keyVocabulary
        List<KeyVocabularyItem> keyVocabulary = new ArrayList<>();
        JsonNode kvNode = payload.path("keyVocabulary");
        if (kvNode.isArray()) {
            for (JsonNode kv : kvNode) {
                keyVocabulary.add(KeyVocabularyItem.builder()
                        .surface(kv.path("surface").asText(null))
                        .reading(kv.path("reading").asText(null))
                        .jlpt(kv.path("jlpt").isNull() ? null : kv.path("jlpt").asInt())
                        .glossVi(kv.path("glossVi").asText(null))
                        .domain(kv.path("domain").asText(null))
                        .register(kv.path("register").asText(null))
                        .build());
            }
        }

        // notes
        List<TranslationNote> notes = readNoteList(payload.path("notes"));
        List<TranslationNote> warnings = readNoteList(payload.path("warnings"));
        String model = payload.path("model").asText("unknown");

        return DeepTranslateResponse.builder()
                .sourceText(sourceText)
                .translatedText(translatedText)
                .sourceLang(sourceLang)
                .targetLang(targetLang)
                .provider("python_pipeline")
                .detectedDomains(detectedDomains)
                .keyVocabulary(keyVocabulary)
                .notes(notes)
                .warnings(warnings)
                .model(model)
                .build();
    }

    private List<TranslationNote> readNoteList(JsonNode node) {
        List<TranslationNote> result = new ArrayList<>();
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                result.add(TranslationNote.builder()
                        .type(item.path("type").asText(null))
                        .token(item.path("token").asText(null))
                        .content(item.path("content").asText(null))
                        .build());
            }
        }
        return result;
    }

    private List<String> readTextList(JsonNode node) {
        List<String> values = new ArrayList<>();
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                String value = item.asText(null);
                if (value != null && !value.isBlank()) {
                    values.add(value);
                }
            }
        }
        return values;
    }

    // Decoupled: CLI helper methods resolveAiRoot and resolvePythonExecutable removed as we now use REST API.


    private String translateWithGoogleEndpoint(String text, String sourceLang, String targetLang) {
        try {
            String encodedText = URLEncoder.encode(text, StandardCharsets.UTF_8);
            String endpoint = String.format(
                    "%s?client=gtx&sl=%s&tl=%s&dt=t&q=%s",
                    quickTranslateUrl,
                    sourceLang,
                    targetLang,
                    encodedText
            );

            HttpRequest request = HttpRequest.newBuilder(URI.create(endpoint))
                    .timeout(Duration.ofSeconds(20))
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() >= 400) {
                log.warn("Quick translate provider returned HTTP {}", response.statusCode());
                throw new AppException(ErrorCode.TRANSLATION_FAILED);
            }

            JsonNode root = objectMapper.readTree(response.body());
            JsonNode segments = root.path(0);
            if (!segments.isArray() || segments.isEmpty()) {
                throw new AppException(ErrorCode.TRANSLATION_FAILED);
            }

            StringBuilder translated = new StringBuilder();
            for (JsonNode segment : segments) {
                String piece = segment.path(0).asText();
                if (!piece.isBlank()) {
                    translated.append(piece);
                }
            }

            String finalText = translated.toString().trim();
            if (finalText.isBlank()) {
                throw new AppException(ErrorCode.TRANSLATION_FAILED);
            }

            return finalText;
        } catch (AppException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error("Quick translate error: {}", ex.getMessage(), ex);
            throw new AppException(ErrorCode.TRANSLATION_FAILED);
        }
    }

    private String normalizeLang(String lang, String fallback) {
        if (lang == null || lang.isBlank()) {
            return fallback;
        }
        return lang.trim().toLowerCase();
    }
}

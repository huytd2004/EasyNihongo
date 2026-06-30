package vn.hust.huy.backend.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import vn.hust.huy.backend.dto.request.ChangePasswordRequest;
import vn.hust.huy.backend.dto.request.UpdateTargetLevelRequest;
import vn.hust.huy.backend.dto.response.ApiResponse;
import vn.hust.huy.backend.dto.response.RecentMistakesResponse;
import vn.hust.huy.backend.dto.response.UserProfileResponse;
import vn.hust.huy.backend.dto.response.UserResponse;
import vn.hust.huy.backend.exception.AppException;
import vn.hust.huy.backend.exception.ErrorCode;
import vn.hust.huy.backend.model.entity.TutorSessionResult;
import vn.hust.huy.backend.model.entity.User;
import vn.hust.huy.backend.model.entity.UserProfile;
import vn.hust.huy.backend.repository.TutorSessionResultRepository;
import vn.hust.huy.backend.repository.UserProfileRepository;
import vn.hust.huy.backend.repository.UserRepository;
import vn.hust.huy.backend.service.UserService;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final UserProfileRepository userProfileRepository;
    private final TutorSessionResultRepository tutorSessionResultRepository;
    private final PasswordEncoder passwordEncoder;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    @Transactional(readOnly = true)
    public ApiResponse<UserResponse> getCurrentUser(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
        return ApiResponse.success(UserResponse.fromEntity(user), "Lấy thông tin người dùng thành công");
    }

    @Override
    @Transactional(readOnly = true)
    public ApiResponse<UserProfileResponse> getUserProfile(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
        UserProfile profile = userProfileRepository.findByUser_Id(user.getId())
                .orElseGet(() -> UserProfile.builder().user(user).build());
        return ApiResponse.success(UserProfileResponse.fromEntity(profile), "Lấy thông tin profile thành công");
    }

    @Override
    @Transactional(readOnly = true)
    public ApiResponse<RecentMistakesResponse> getRecentMistakes(String email, int limit) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
        List<TutorSessionResult> recentResults =
                tutorSessionResultRepository.findByUser_IdOrderByCreatedAtDesc(user.getId(), PageRequest.of(0, limit));
        List<Object> allMistakes = new ArrayList<>();
        for (TutorSessionResult r : recentResults) {
            allMistakes.addAll(readJsonList(r.getMistakes()));
        }
        return ApiResponse.success(
                RecentMistakesResponse.builder()
                        .mistakeCount(allMistakes.size())
                        .mistakes(allMistakes)
                        .build(),
                "Lấy danh sách lỗi sai thành công"
        );
    }

    @Override
    @Transactional
    public ApiResponse<UserResponse> updateTargetLevel(String email, UpdateTargetLevelRequest request) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
        user.setTargetLevel(request.getTargetLevel());
        userRepository.save(user);
        return ApiResponse.success(UserResponse.fromEntity(user), "Cập nhật mục tiêu thành công");
    }

    @Override
    @Transactional
    public ApiResponse<Void> changePassword(String email, ChangePasswordRequest request) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPasswordHash())) {
            throw new AppException(ErrorCode.WRONG_PASSWORD);
        }
        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);
        return ApiResponse.success(null, "Đổi mật khẩu thành công");
    }

    @SuppressWarnings("unchecked")
    private List<Object> readJsonList(String json) {
        if (json == null || json.isBlank()) return List.of();
        try {
            return objectMapper.readValue(json, List.class);
        } catch (Exception e) {
            return List.of();
        }
    }
}

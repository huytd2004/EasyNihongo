package vn.hust.huy.backend.service;

import vn.hust.huy.backend.dto.request.ChangePasswordRequest;
import vn.hust.huy.backend.dto.request.UpdateTargetLevelRequest;
import vn.hust.huy.backend.dto.response.ApiResponse;
import vn.hust.huy.backend.dto.response.RecentMistakesResponse;
import vn.hust.huy.backend.dto.response.UserProfileResponse;
import vn.hust.huy.backend.dto.response.UserResponse;

public interface UserService {

    ApiResponse<UserResponse> getCurrentUser(String email);

    ApiResponse<UserProfileResponse> getUserProfile(String email);

    ApiResponse<RecentMistakesResponse> getRecentMistakes(String email, int limit);

    ApiResponse<UserResponse> updateTargetLevel(String email, UpdateTargetLevelRequest request);

    ApiResponse<Void> changePassword(String email, ChangePasswordRequest request);
}

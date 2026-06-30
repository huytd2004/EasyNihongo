package vn.hust.huy.backend.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import vn.hust.huy.backend.dto.request.ChangePasswordRequest;
import vn.hust.huy.backend.dto.request.UpdateTargetLevelRequest;
import vn.hust.huy.backend.dto.response.ApiResponse;
import vn.hust.huy.backend.dto.response.RecentMistakesResponse;
import vn.hust.huy.backend.dto.response.UserProfileResponse;
import vn.hust.huy.backend.dto.response.UserResponse;
import vn.hust.huy.backend.service.UserService;

/**
 * User profile endpoints — all require a valid JWT.
 */
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * GET /api/v1/users/me
     * Returns the profile of the currently authenticated user.
     */
    @GetMapping("/me")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<ApiResponse<UserResponse>> getCurrentUser(
            @AuthenticationPrincipal UserDetails userDetails) {
        return ResponseEntity.ok(userService.getCurrentUser(userDetails.getUsername()));
    }

    /**
     * GET /api/v1/users/me/profile
     * Returns streak count and last active time for the authenticated user.
     */
    @GetMapping("/me/profile")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<ApiResponse<UserProfileResponse>> getUserProfile(
            @AuthenticationPrincipal UserDetails userDetails) {
        return ResponseEntity.ok(userService.getUserProfile(userDetails.getUsername()));
    }

    /**
     * GET /api/v1/users/me/mistakes?limit=5
     * Returns recent mistakes extracted from tutor session results.
     */
    @GetMapping("/me/mistakes")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<ApiResponse<RecentMistakesResponse>> getRecentMistakes(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestParam(defaultValue = "5") int limit) {
        return ResponseEntity.ok(userService.getRecentMistakes(userDetails.getUsername(), limit));
    }

    /**
     * PATCH /api/v1/users/me/target-level
     * Updates the authenticated user's JLPT target level.
     */
    @PatchMapping("/me/target-level")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<ApiResponse<UserResponse>> updateTargetLevel(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestBody UpdateTargetLevelRequest request) {
        return ResponseEntity.ok(userService.updateTargetLevel(userDetails.getUsername(), request));
    }

    /**
     * PATCH /api/v1/users/me/change-password
     * Changes the authenticated user's password.
     */
    @PatchMapping("/me/change-password")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> changePassword(
            @AuthenticationPrincipal UserDetails userDetails,
            @Valid @RequestBody ChangePasswordRequest request) {
        return ResponseEntity.ok(userService.changePassword(userDetails.getUsername(), request));
    }
}

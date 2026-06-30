package vn.hust.huy.backend.dto.response;

import lombok.Builder;
import lombok.Getter;
import vn.hust.huy.backend.model.entity.UserProfile;

import java.time.Instant;

/**
 * Exposes minimal UserProfile stats for the profile page.
 */
@Getter
@Builder
public class UserProfileResponse {

    private int streakCount;
    private Instant lastActive;

    public static UserProfileResponse fromEntity(UserProfile p) {
        return UserProfileResponse.builder()
                .streakCount(p.getStreakCount())
                .lastActive(p.getLastActive())
                .build();
    }
}

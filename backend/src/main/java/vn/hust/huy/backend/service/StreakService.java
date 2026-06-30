package vn.hust.huy.backend.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import vn.hust.huy.backend.model.entity.User;
import vn.hust.huy.backend.model.entity.UserProfile;
import vn.hust.huy.backend.repository.UserProfileRepository;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;

/**
 * Shared service that updates the user's daily learning streak.
 *
 * <p>Rules:
 * <ul>
 *   <li>First activity ever → streak = 1</li>
 *   <li>Last active was <b>today</b> → no change (already counted)</li>
 *   <li>Last active was <b>yesterday</b> → streak += 1</li>
 *   <li>Last active was <b>≥ 2 days ago</b> → streak reset to 1</li>
 * </ul>
 *
 * <p>Uses {@code REQUIRES_NEW} propagation so that a streak-update failure
 * never rolls back the primary activity transaction.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class StreakService {

    private static final ZoneId ZONE = ZoneId.of("Asia/Ho_Chi_Minh");

    private final UserProfileRepository userProfileRepository;

    /**
     * Updates the streak for the given user.
     * Safe to call from within any other {@code @Transactional} method.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateStreak(User user) {
        try {
            UserProfile profile = userProfileRepository.findByUser_Id(user.getId())
                    .orElseGet(() -> UserProfile.builder().user(user).build());

            Instant now = Instant.now();
            LocalDate today = now.atZone(ZONE).toLocalDate();

            if (profile.getLastActive() != null) {
                LocalDate lastDay = profile.getLastActive().atZone(ZONE).toLocalDate();
                long daysDiff = ChronoUnit.DAYS.between(lastDay, today);

                if (daysDiff == 0) {
                    // Already logged activity today — nothing to do
                    return;
                } else if (daysDiff == 1) {
                    // Consecutive day
                    profile.setStreakCount(profile.getStreakCount() + 1);
                } else {
                    // Gap in learning — reset
                    profile.setStreakCount(1);
                }
            } else {
                // Very first activity
                profile.setStreakCount(1);
            }

            profile.setLastActive(now);
            userProfileRepository.save(profile);

            log.debug("[Streak] user={} streak={}", user.getEmail(), profile.getStreakCount());

        } catch (Exception e) {
            // Non-critical — log and swallow so it never breaks the main flow
            log.warn("[Streak] Failed to update streak for user={}: {}", user.getEmail(), e.getMessage());
        }
    }
}

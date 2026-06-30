package vn.hust.huy.backend.dto.response;

import lombok.Builder;
import lombok.Data;

import java.util.List;

/**
 * Summary of recent mistakes collected across the latest N tutor sessions.
 * Used by ReviewSetupView to populate the "smart suggestion" banner.
 */
@Data
@Builder
public class RecentMistakesResponse {
    /** Total unique mistakes collected from the recent sessions. */
    private int mistakeCount;
    /** Flattened list of mistake objects from the last N sessions' `mistakes` column. */
    private List<Object> mistakes;
}

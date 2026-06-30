package vn.hust.huy.backend.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;
import vn.hust.huy.backend.model.enums.JlptLevel;

/**
 * Request body for updating the authenticated user's target JLPT level.
 */
@Getter
@Setter
public class UpdateTargetLevelRequest {
    @NotNull
    private JlptLevel targetLevel;
}

package vn.hust.huy.backend.model.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import vn.hust.huy.backend.model.enums.JlptLevel;

import java.time.Instant;
import java.util.UUID;

/**
 * Story review history record.
 * Maps to the {@code story_reviews} table.
 */
@Entity
@Table(name = "story_reviews")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StoryReview {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(updatable = false, nullable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "deck_id")
    private FlashcardDeck deck;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "level", nullable = false, columnDefinition = "target_level_enum")
    private JlptLevel level;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "score", nullable = false)
    private int score;

    @Column(name = "total_questions", nullable = false)
    private int totalQuestions;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "story_data", nullable = false, columnDefinition = "jsonb")
    private String storyData;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "answers_data", nullable = false, columnDefinition = "jsonb")
    private String answersData;

    @Column(name = "created_at", nullable = false, updatable = false)
    @Builder.Default
    private Instant createdAt = Instant.now();
}

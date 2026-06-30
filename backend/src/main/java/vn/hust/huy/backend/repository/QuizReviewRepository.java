package vn.hust.huy.backend.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import vn.hust.huy.backend.model.entity.QuizReview;

import java.util.List;
import java.util.UUID;

@Repository
public interface QuizReviewRepository extends JpaRepository<QuizReview, UUID> {
    List<QuizReview> findByUser_IdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
}

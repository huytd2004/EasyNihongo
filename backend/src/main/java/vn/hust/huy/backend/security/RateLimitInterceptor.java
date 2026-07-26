package vn.hust.huy.backend.security;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;
import vn.hust.huy.backend.annotation.RateLimit;

import java.util.concurrent.TimeUnit;

@Component
@RequiredArgsConstructor
@Slf4j
public class RateLimitInterceptor implements HandlerInterceptor {

    private final StringRedisTemplate redisTemplate;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if (!(handler instanceof HandlerMethod)) {
            return true;
        }

        HandlerMethod handlerMethod = (HandlerMethod) handler;
        RateLimit rateLimit = handlerMethod.getMethodAnnotation(RateLimit.class);

        if (rateLimit == null) {
            return true;
        }

        String username = "anonymous";
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof UserDetails) {
            username = ((UserDetails) principal).getUsername();
        } else if (principal instanceof String) {
            username = (String) principal;
        }

        String keyPrefix = rateLimit.key().isEmpty() ? handlerMethod.getMethod().getName() : rateLimit.key();
        String redisKey = "rate_limit:" + keyPrefix + ":" + username;

        String currentVal = redisTemplate.opsForValue().get(redisKey);

        if (currentVal == null) {
            redisTemplate.opsForValue().set(redisKey, "1", rateLimit.duration(), TimeUnit.SECONDS);
        } else {
            int count = Integer.parseInt(currentVal);
            if (count >= rateLimit.limit()) {
                log.warn("Rate limit exceeded for user: {}, key: {}", username, redisKey);
                response.setStatus(429); // Too Many Requests
                response.setContentType("application/json;charset=UTF-8");
                response.getWriter().write("{\"code\":429,\"message\":\"Bạn đã vượt quá giới hạn lượt yêu cầu cho phép. Vui lòng thử lại sau.\",\"status\":\"error\"}");
                return false;
            }
            redisTemplate.opsForValue().increment(redisKey);
        }

        return true;
    }
}

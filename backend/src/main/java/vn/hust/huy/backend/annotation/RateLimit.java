package vn.hust.huy.backend.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimit {
    int limit() default 5; // maximum number of requests allowed
    int duration() default 60; // window duration in seconds
    String key() default ""; // unique prefix key for redis
}

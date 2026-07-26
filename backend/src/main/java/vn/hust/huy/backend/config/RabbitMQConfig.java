package vn.hust.huy.backend.config;

import org.springframework.amqp.core.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String REVIEW_EXCHANGE = "review.exchange";
    
    public static final String QUIZ_QUEUE = "review.quiz.queue";
    public static final String STORY_QUEUE = "review.story.queue";
    
    public static final String QUIZ_ROUTING_KEY = "review.quiz.generate";
    public static final String STORY_ROUTING_KEY = "review.story.generate";

    @Bean
    public TopicExchange reviewExchange() {
        return new TopicExchange(REVIEW_EXCHANGE);
    }

    @Bean
    public Queue quizQueue() {
        return QueueBuilder.durable(QUIZ_QUEUE).build();
    }

    @Bean
    public Queue storyQueue() {
        return QueueBuilder.durable(STORY_QUEUE).build();
    }

    @Bean
    public Binding bindingQuiz(Queue quizQueue, TopicExchange reviewExchange) {
        return BindingBuilder.bind(quizQueue).to(reviewExchange).with(QUIZ_ROUTING_KEY);
    }

    @Bean
    public Binding bindingStory(Queue storyQueue, TopicExchange reviewExchange) {
        return BindingBuilder.bind(storyQueue).to(reviewExchange).with(STORY_ROUTING_KEY);
    }
}

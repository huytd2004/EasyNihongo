import api from '@/services/api'

export const reviewService = {
  /** Generate quiz questions */
  generateQuiz(payload) {
    return api.post('/api/v1/review/quiz/generate', payload)
  },
  /** Generate quiz questions asynchronously */
  generateQuizAsync(payload) {
    return api.post('/api/v1/review/quiz/generate-async', payload)
  },
  /** Generate interactive story */
  generateStory(payload) {
    return api.post('/api/v1/review/story/generate', payload)
  },
  /** Generate interactive story asynchronously */
  generateStoryAsync(payload) {
    return api.post('/api/v1/review/story/generate-async', payload)
  },
  /** Get asynchronous task status and results */
  getTaskStatus(taskId) {
    return api.get(`/api/v1/review/task/${taskId}`)
  },
  /** Save quiz results */
  saveQuizResult(payload) {
    return api.post('/api/v1/review/quiz/result', payload)
  },
  /** Save story results */
  saveStoryResult(payload) {
    return api.post('/api/v1/review/story/result', payload)
  },
}

export default reviewService

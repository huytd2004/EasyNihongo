import api from '@/services/api'

export const reviewService = {
  /** Generate quiz questions */
  generateQuiz(payload) {
    return api.post('/api/v1/review/quiz/generate', payload)
  },
  /** Generate interactive story */
  generateStory(payload) {
    return api.post('/api/v1/review/story/generate', payload)
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

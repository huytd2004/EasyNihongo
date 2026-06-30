import api from '@/services/api'

export const tutorService = {
  createSession(payload) {
    return api.post('/api/v1/tutor/sessions', payload)
  },

  sendMessage(sessionId, payload, config) {
    return api.post(`/api/v1/tutor/sessions/${sessionId}/messages`, payload, config)
  },

  finishSession(sessionId) {
    return api.patch(`/api/v1/tutor/sessions/${sessionId}/finish`)
  },

  getResult(sessionId) {
    return api.get(`/api/v1/tutor/sessions/${sessionId}/result`)
  },

  getDecks() {
    return api.get('/api/v1/decks')
  },

  getDeckDue(deckId, maxNew = 10) {
    return api.get(`/api/v1/decks/${deckId}/due?maxNew=${maxNew}`)
  },

  /** Lấy danh sách mistakes gần nhất từ N session cuối. */
  getRecentMistakes(limit = 5) {
    return api.get(`/api/v1/tutor/sessions/results/recent?limit=${limit}`)
  },
}

export default tutorService

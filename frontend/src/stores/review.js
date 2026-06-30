import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'reviewQuizSession'

export const useReviewStore = defineStore('review', () => {
  // ── Quiz data ───────────────────────────────────────────────
  const questions = ref([])    // { id, type, question_ja, question_vn, choices, answer, explanation_vn, target_word, hint }
  const currentIndex = ref(0)
  const answers = ref({})      // { [questionId]: selectedChoice }
  const warning = ref(null)    // partial-result warning from AI

  // ── Story data ──────────────────────────────────────────────
  const storyData = ref(null)  // { title, settingVn, segments: [...] }
  const storySegmentIndex = ref(0)
  const storyAnswers = ref({}) // { [segmentId]: answerIndex }

  // ── Setup metadata (for display in quiz header) ─────────────
  const deckId = ref(null)
  const deckName = ref('')
  const level = ref('N3')
  const questionCount = ref(0)

  // ── State machine ────────────────────────────────────────────
  // 'idle' | 'loading' | 'active' | 'finished'
  const status = ref('idle')
  const startError = ref(null)

  // ── Computed ─────────────────────────────────────────────────
  const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
  const totalQuestions = computed(() => questions.value.length)
  const isLast = computed(() => currentIndex.value >= questions.value.length - 1)
  const progress = computed(() =>
    totalQuestions.value > 0
      ? Math.round((currentIndex.value / totalQuestions.value) * 100)
      : 0
  )

  const score = computed(() => {
    let correct = 0
    for (const q of questions.value) {
      if (answers.value[q.id] === q.answer) correct++
    }
    return correct
  })

  const isAnswered = (questionId) => questionId in answers.value
  const isCorrect = (questionId) => answers.value[questionId] === questions.value.find(q => q.id === questionId)?.answer

  // ── Persist / Hydrate ────────────────────────────────────────
  function persist() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        questions: questions.value,
        currentIndex: currentIndex.value,
        answers: answers.value,
        warning: warning.value,
        deckId: deckId.value,
        deckName: deckName.value,
        level: level.value,
        questionCount: questionCount.value,
        status: status.value,
        storyData: storyData.value,
        storySegmentIndex: storySegmentIndex.value,
        storyAnswers: storyAnswers.value,
      }))
    } catch (e) {
      console.warn('[reviewStore] persist failed', e)
    }
  }

  function hydrate() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY)
      if (!raw) return false
      const p = JSON.parse(raw)
      questions.value = p.questions || []
      currentIndex.value = p.currentIndex ?? 0
      answers.value = p.answers || {}
      warning.value = p.warning || null
      deckId.value = p.deckId || null
      deckName.value = p.deckName || ''
      level.value = p.level || 'N3'
      questionCount.value = p.questionCount || 0
      status.value = p.status || 'idle'
      storyData.value = p.storyData || null
      storySegmentIndex.value = p.storySegmentIndex ?? 0
      storyAnswers.value = p.storyAnswers || {}
      return questions.value.length > 0 || !!storyData.value
    } catch (e) {
      console.warn('[reviewStore] hydrate failed', e)
      return false
    }
  }

  // ── Actions ───────────────────────────────────────────────────
  function setQuestions(qs, meta = {}) {
    questions.value = qs
    currentIndex.value = 0
    answers.value = {}
    deckId.value = meta.deckId || null
    deckName.value = meta.deckName || ''
    level.value = meta.level || 'N3'
    questionCount.value = qs.length
    status.value = 'active'
    persist()
  }

  function submitAnswer(questionId, choice) {
    answers.value = { ...answers.value, [questionId]: choice }
    persist()
  }

  function nextQuestion() {
    if (currentIndex.value < questions.value.length - 1) {
      currentIndex.value++
      persist()
    }
  }

  function prevQuestion() {
    if (currentIndex.value > 0) {
      currentIndex.value--
      persist()
    }
  }

  function finishQuiz() {
    status.value = 'finished'
    persist()
  }

  function setStory(data, meta = {}) {
    storyData.value = data
    storySegmentIndex.value = 0
    storyAnswers.value = {}
    warning.value = data.warning || null
    deckId.value = meta.deckId || null
    deckName.value = meta.deckName || ''
    level.value = meta.level || 'N3'
    status.value = 'active'
    persist()
  }

  function submitStoryAnswer(segmentId, answerIndex) {
    storyAnswers.value = { ...storyAnswers.value, [segmentId]: answerIndex }
    persist()
  }

  function nextStorySegment() {
    const total = storyData.value?.segments?.length ?? 0
    if (storySegmentIndex.value < total - 1) {
      storySegmentIndex.value++
      persist()
    } else {
      status.value = 'finished'
      persist()
    }
  }

  function prevStorySegment() {
    if (storySegmentIndex.value > 0) {
      storySegmentIndex.value--
      persist()
    }
  }

  function restartQuiz() {
    currentIndex.value = 0
    answers.value = {}
    status.value = 'active'
    persist()
  }

  function restartStory() {
    storySegmentIndex.value = 0
    storyAnswers.value = {}
    status.value = 'active'
    persist()
  }

  /** Called when user exits quiz or completes it — clears storage. */
  function clearSession() {
    questions.value = []
    currentIndex.value = 0
    answers.value = {}
    warning.value = null
    deckId.value = null
    deckName.value = ''
    level.value = 'N3'
    questionCount.value = 0
    status.value = 'idle'
    startError.value = null
    storyData.value = null
    storySegmentIndex.value = 0
    storyAnswers.value = {}
    try { sessionStorage.removeItem(STORAGE_KEY) } catch (e) {}
  }

  return {
    // state
    questions, currentIndex, answers, warning,
    deckId, deckName, level, questionCount, status, startError,
    storyData, storySegmentIndex, storyAnswers,
    // computed
    currentQuestion, totalQuestions, isLast, progress, score,
    // methods
    isAnswered, isCorrect,
    persist, hydrate,
    setQuestions, submitAnswer, nextQuestion, prevQuestion,
    finishQuiz, clearSession, restartQuiz,
    setStory, submitStoryAnswer, nextStorySegment, prevStorySegment, restartStory,
  }
})

export default useReviewStore

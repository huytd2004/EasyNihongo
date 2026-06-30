<template>
  <div class="fixed top-0 bottom-0 right-0 left-0 md:left-64 z-[45] bg-surface flex flex-col font-body text-on-surface antialiased overflow-hidden">

    <!-- ── Loading screen ─────────────────────────────────────── -->
    <div v-if="reviewStore.status === 'idle' || reviewStore.status === 'loading'" class="flex-1 flex flex-col items-center justify-center gap-6 p-8">
      <div class="w-20 h-20 rounded-[2rem] bg-primary-container flex items-center justify-center ambient-shadow animate-pulse">
        <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
      </div>
      <div class="text-center">
        <h2 class="text-2xl font-headline font-extrabold text-on-surface mb-2 tracking-tight">Đang tạo câu hỏi...</h2>
        <p class="text-on-surface-variant text-sm">AI đang sinh quiz từ bộ từ vựng của bạn</p>
      </div>
    </div>

    <!-- ── No questions ───────────────────────────────────────── -->
    <div v-else-if="!reviewStore.totalQuestions" class="flex-1 flex flex-col items-center justify-center gap-6 p-8">
      <div class="w-20 h-20 rounded-[2rem] bg-surface-container-high flex items-center justify-center mb-2">
        <span class="material-symbols-outlined text-4xl text-on-surface-variant">quiz</span>
      </div>
      <div class="text-center max-w-sm">
        <h2 class="text-2xl font-headline font-bold text-on-surface mb-2 tracking-tight">Không có câu hỏi</h2>
        <p class="text-on-surface-variant text-sm mb-8 leading-relaxed">Hãy quay lại và chọn deck có thẻ để tạo quiz học tập.</p>
        <RouterLink 
          to="/review" 
          @click="reviewStore.clearSession()" 
          class="px-8 py-4 rounded-full bg-primary text-on-primary font-bold hover:bg-gradient-to-br hover:from-primary hover:to-primary-container hover:text-on-primary-fixed transition-all duration-300 inline-block ambient-shadow"
        >
          Quay lại thiết lập
        </RouterLink>
      </div>
    </div>

    <!-- ── Result screen ──────────────────────────────────────── -->
    <div v-else-if="reviewStore.status === 'finished'" class="flex-1 overflow-y-auto">
      <ResultScreen @restart="handleRestart" @exit="handleExit" @finish="handleSaveAndExit" />
    </div>

    <!-- ── Active quiz ────────────────────────────────────────── -->
    <template v-else-if="reviewStore.status === 'active' && reviewStore.currentQuestion">
      <!-- Top bar -->
      <header class="h-20 shrink-0 z-40 bg-surface-container-low/95 backdrop-blur-xl px-6 md:px-10 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button
            @click="handleExit"
            class="p-2.5 rounded-full hover:bg-surface-container-high transition-colors flex items-center justify-center cursor-pointer"
          >
            <span class="material-symbols-outlined text-on-surface-variant text-xl">arrow_back</span>
          </button>
          <div class="hidden sm:block">
            <p class="text-[10px] font-bold text-primary uppercase tracking-widest">{{ reviewStore.deckName || 'Review' }}</p>
            <p class="text-sm font-bold text-on-primary-fixed">{{ reviewStore.level }} Quiz</p>
          </div>
        </div>

        <!-- Progress -->
        <div class="flex-1 max-w-xs mx-4">
          <div class="flex items-center justify-between text-xs text-on-surface-variant mb-1.5">
            <span class="font-medium">{{ reviewStore.currentIndex + 1 }} / {{ reviewStore.totalQuestions }}</span>
            <span class="font-bold text-primary">{{ reviewStore.progress }}%</span>
          </div>
          <div class="h-2 w-full bg-surface-container-high rounded-full overflow-hidden">
            <!-- Progress using signature gradient -->
            <div
              class="h-full bg-gradient-to-r from-primary to-primary-container rounded-full transition-all duration-500"
              :style="{ width: reviewStore.progress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Score so far -->
        <div class="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 text-secondary">
          <span class="material-symbols-outlined text-base" style="font-variation-settings: 'FILL' 1;">stars</span>
          <span class="text-xs font-bold">{{ reviewStore.score }} đúng</span>
        </div>
      </header>

      <!-- Warning banner (partial quiz) -->
      <div v-if="reviewStore.warning" class="mx-6 mt-4 p-4 rounded-2xl bg-secondary/10 text-secondary text-sm flex items-center gap-3">
        <span class="material-symbols-outlined text-lg shrink-0">warning</span>
        <span class="font-medium">{{ reviewStore.warning }}</span>
      </div>

      <!-- Question area -->
      <section class="flex-grow flex items-center justify-center p-6 md:p-12 overflow-y-auto">
        <div class="max-w-3xl w-full flex flex-col gap-10">

          <!-- Question label + text -->
          <div class="text-center">
            <span class="inline-block px-4 py-1.5 rounded-full bg-primary-container/50 text-on-primary-fixed text-xs font-bold mb-8 tracking-wider uppercase">
              Câu {{ reviewStore.currentIndex + 1 }} — {{ reviewStore.level }}
            </span>
            <!-- Japanese sentence with blank highlighted -->
            <div
              class="text-2xl md:text-4xl font-headline font-extrabold text-on-surface leading-loose tracking-wide"
              v-html="highlightedQuestion"
            ></div>
            <!-- Vietnamese translation -->
            <p v-if="reviewStore.currentQuestion.question_vn" class="mt-4 text-on-surface-variant text-base md:text-lg italic opacity-85 leading-relaxed">
              「{{ reviewStore.currentQuestion.question_vn }}」
            </p>
          </div>

          <!-- Answer grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              v-for="(choice, idx) in reviewStore.currentQuestion.choices"
              :key="choice"
              type="button"
              @click="selectAnswer(choice)"
              :disabled="isAnsweredCurrent"
              class="group flex items-center p-5 rounded-3xl transition-all duration-300 text-left border-none"
              :class="choiceClass(choice)"
            >
              <div class="w-10 h-10 shrink-0 rounded-xl flex items-center justify-center font-bold text-sm mr-4 transition-colors"
                :class="choiceLabelClass(choice)">
                {{ String.fromCharCode(65 + idx) }}
              </div>
              <span class="text-lg font-medium font-headline tracking-wide leading-relaxed">{{ choice }}</span>
              <!-- Correct/wrong icon after answering -->
              <span v-if="isAnsweredCurrent && choice === reviewStore.currentQuestion.answer"
                class="material-symbols-outlined ml-auto text-primary" style="font-variation-settings: 'FILL' 1;">check_circle</span>
              <span v-else-if="isAnsweredCurrent && choice === selectedChoice && choice !== reviewStore.currentQuestion.answer"
                class="material-symbols-outlined ml-auto text-secondary" style="font-variation-settings: 'FILL' 1;">cancel</span>
            </button>
          </div>

          <!-- Explanation (shown after answering) -->
          <Transition name="slide-up">
            <div v-if="isAnsweredCurrent" class="p-6 rounded-[2rem] flex gap-4 items-start ambient-shadow"
              :class="isCorrectCurrent ? 'bg-primary/10' : 'bg-secondary/10'">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                :class="isCorrectCurrent ? 'bg-primary/20 text-primary' : 'bg-secondary/20 text-secondary'">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">
                  {{ isCorrectCurrent ? 'check_circle' : 'cancel' }}
                </span>
              </div>
              <div class="flex-1">
                <p class="font-headline font-bold text-base mb-1" :class="isCorrectCurrent ? 'text-on-primary-fixed' : 'text-secondary'">
                  {{ isCorrectCurrent ? 'Chính xác! 🎉' : `Đáp án đúng: ${reviewStore.currentQuestion.answer}` }}
                </p>
                <p v-if="reviewStore.currentQuestion.explanation_vn" class="text-sm text-on-surface-variant leading-relaxed">
                  {{ reviewStore.currentQuestion.explanation_vn }}
                </p>
                <p v-if="reviewStore.currentQuestion.hint" class="text-xs text-primary mt-2 font-semibold">
                  💡 {{ reviewStore.currentQuestion.hint }}
                </p>
              </div>
            </div>
          </Transition>

          <!-- Footer actions -->
          <div class="flex items-center justify-between gap-4">
            <button
              v-if="reviewStore.currentIndex > 0"
              @click="reviewStore.prevQuestion()"
              class="px-6 py-3.5 rounded-full text-on-surface-variant font-semibold hover:bg-surface-container-high transition-all flex items-center gap-2 cursor-pointer"
            >
              <span class="material-symbols-outlined text-lg">arrow_back</span>
              Câu trước
            </button>
            <div v-else></div>

            <button
              v-if="isAnsweredCurrent && !reviewStore.isLast"
              @click="reviewStore.nextQuestion()"
              class="px-8 py-3.5 rounded-full bg-primary text-on-primary font-bold hover:bg-gradient-to-br hover:from-primary hover:to-primary-container hover:text-on-primary-fixed transition-all duration-300 flex items-center gap-2 ambient-shadow cursor-pointer"
            >
              <span>Câu tiếp theo</span>
              <span class="material-symbols-outlined text-lg">arrow_forward</span>
            </button>
            <button
              v-else-if="isAnsweredCurrent && reviewStore.isLast"
              @click="handleFinish"
              class="px-8 py-3.5 rounded-full bg-secondary text-on-secondary font-bold hover:opacity-95 transition-all duration-300 flex items-center gap-2 ambient-shadow cursor-pointer"
            >
              <span>Xem kết quả</span>
              <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">flag</span>
            </button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import { reviewService } from '@/services/review'
import ResultScreen from './ResultScreen.vue'

const router = useRouter()
const reviewStore = useReviewStore()

// ── Hydrate on mount (handles page reload) ────────────────────
onMounted(() => {
  if (reviewStore.status === 'idle') {
    const restored = reviewStore.hydrate()
    if (!restored) {
      // Nothing persisted, redirect back to setup
      router.replace('/review')
    }
  }
})

// ── Current question helpers ──────────────────────────────────
const q = computed(() => reviewStore.currentQuestion)
const selectedChoice = computed(() => q.value ? reviewStore.answers[q.value.id] : null)
const isAnsweredCurrent = computed(() => q.value ? reviewStore.isAnswered(q.value.id) : false)
const isCorrectCurrent = computed(() => q.value ? reviewStore.isCorrect(q.value.id) : false)

/** Replace ___ in question_ja with a styled span */
const highlightedQuestion = computed(() => {
  if (!q.value?.question_ja) return ''
  return q.value.question_ja.replace(
    /___/g,
    '<span class="mx-2 px-6 py-0.5 bg-surface-container-high text-transparent rounded-xl inline-block align-middle relative after:content-[\'\'] after:absolute after:bottom-1 after:left-4 after:right-4 after:h-[3px] after:bg-primary/60">___</span>'
  )
})

function selectAnswer(choice) {
  if (!q.value || isAnsweredCurrent.value) return
  reviewStore.submitAnswer(q.value.id, choice)
}

// ── Choice button classes ─────────────────────────────────────
function choiceClass(choice) {
  if (!isAnsweredCurrent.value) {
    return 'bg-surface-container-lowest text-on-surface hover:bg-primary-container/20 hover:scale-[1.01] active:scale-[0.99] cursor-pointer ambient-shadow'
  }
  if (choice === q.value.answer) {
    return 'bg-primary/10 text-primary cursor-default'
  }
  if (choice === selectedChoice.value) {
    return 'bg-secondary/10 text-secondary cursor-default'
  }
  return 'bg-surface-container-lowest text-on-surface opacity-55 cursor-default'
}

function choiceLabelClass(choice) {
  if (!isAnsweredCurrent.value) return 'bg-surface-container text-on-surface-variant group-hover:bg-primary group-hover:text-on-primary'
  if (choice === q.value.answer) return 'bg-primary text-on-primary'
  if (choice === selectedChoice.value) return 'bg-secondary text-on-secondary'
  return 'bg-surface-container text-on-surface-variant/40'
}

// ── Navigation ────────────────────────────────────────────────
function handleFinish() {
  reviewStore.finishQuiz()
}

async function handleSaveAndExit() {
  try {
    const questionsData = reviewStore.questions.map(q => ({
      id: q.id,
      question_ja: q.question_ja,
      question_vn: q.question_vn,
      choices: q.choices,
      answer: q.answer,
      user_answer: reviewStore.answers[q.id] || null,
      is_correct: reviewStore.isCorrect(q.id)
    }))

    await reviewService.saveQuizResult({
      deckId: reviewStore.deckId,
      level: reviewStore.level,
      score: reviewStore.score,
      totalQuestions: reviewStore.totalQuestions,
      questionsData: questionsData
    })
  } catch (err) {
    console.error('Failed to save quiz result:', err)
  }
  reviewStore.clearSession()
  router.push('/review')
}

function handleExit() {
  reviewStore.clearSession()
  router.push('/review')
}

function handleRestart() {
  reviewStore.restartQuiz()
}
</script>

<style scoped>
.slide-up-enter-active {
  transition: all 0.3s ease-out;
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
</style>

<template>
  <div class="fixed top-0 bottom-0 right-0 left-0 md:left-64 z-[45] bg-surface flex flex-col font-body text-on-surface antialiased overflow-hidden">

    <!-- ── Loading ────────────────────────────────────────────── -->
    <div v-if="!reviewStore.storyData || reviewStore.status === 'idle' || reviewStore.status === 'loading'"
      class="flex-1 flex flex-col items-center justify-center gap-6 p-8 bg-surface">
      <div class="w-20 h-20 rounded-[2rem] bg-primary-container flex items-center justify-center ambient-shadow animate-pulse">
        <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
      </div>
      <div class="text-center">
        <h2 class="text-2xl font-headline font-extrabold text-on-surface mb-2 tracking-tight">Đang tạo câu chuyện...</h2>
        <p class="text-on-surface-variant text-sm">AI đang sinh interactive story từ bộ từ vựng của bạn</p>
      </div>
    </div>

    <!-- ── Finished ───────────────────────────────────────────── -->
    <div v-else-if="reviewStore.status === 'finished'"
      class="flex-1 overflow-y-auto flex flex-col items-center justify-center p-6 md:p-12">
      <StoryResultScreen @exit="handleExit" @restart="handleRestart" @finish="handleSaveAndExit" />
    </div>

    <!-- ── TopAppBar ──────────────────────────────────────────── -->
    <template v-else-if="reviewStore.storyData && currentSegment">
      <header class="h-20 shrink-0 z-40 bg-surface-container-low/95 backdrop-blur-xl px-8 md:px-12 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button @click="handleExit" class="p-2.5 rounded-full hover:bg-surface-container-high transition-colors flex items-center justify-center cursor-pointer">
            <span class="material-symbols-outlined text-on-surface-variant">arrow_back</span>
          </button>
          <h2 class="text-lg font-bold text-primary">Review Center</h2>
        </div>
        <div class="flex items-center gap-4 md:gap-8">
          <!-- Story title + progress -->
          <div class="hidden md:flex items-center gap-4">
            <div class="flex-1 min-w-[160px]">
              <div class="flex items-center justify-between text-xs text-on-surface-variant mb-1">
                <span class="truncate max-w-[180px] font-semibold">{{ reviewStore.storyData.title }}</span>
                <span class="ml-2 font-bold text-primary">{{ storyProgress }}%</span>
              </div>
              <div class="h-2 bg-surface-container-high rounded-full overflow-hidden w-40">
                <div class="h-full bg-gradient-to-r from-primary to-primary-container rounded-full transition-all duration-500" :style="{ width: storyProgress + '%' }"></div>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-4 text-primary">
            <span class="material-symbols-outlined hover:text-primary-dim cursor-pointer transition-colors" style="font-variation-settings: 'FILL' 1;">local_fire_department</span>
            <span class="material-symbols-outlined hover:text-primary-dim cursor-pointer transition-colors">notifications</span>
          </div>
        </div>
      </header>

      <!-- ── Warning banner ─────────────────────────────────────── -->
      <div v-if="reviewStore.warning"
        class="mx-8 mt-4 p-4 rounded-2xl bg-secondary/10 text-secondary text-sm flex items-center gap-3 shrink-0">
        <span class="material-symbols-outlined text-lg shrink-0">warning</span>
        <span class="font-medium">{{ reviewStore.warning }}</span>
      </div>

      <!-- ── Main Canvas ────────────────────────────────────────── -->
      <main class="flex-grow overflow-hidden flex flex-col items-center bg-surface">
        <div class="w-full max-w-6xl h-full p-6 md:p-8 grid grid-cols-12 gap-8">

          <!-- Left: Illustration card (col-span 7) -->
          <div class="col-span-12 lg:col-span-7 flex flex-col gap-6 h-full">

            <!-- Progress + Chapter label -->
            <div class="flex items-center gap-4 px-4 shrink-0">
              <div class="flex-1 h-2 bg-surface-container-high rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-primary to-primary-container rounded-full transition-all duration-500" :style="{ width: storyProgress + '%' }"></div>
              </div>
              <span class="text-xs font-bold text-primary tracking-widest uppercase whitespace-nowrap">
                Đoạn {{ reviewStore.storySegmentIndex + 1 }}: {{ storyChapterLabel }}
              </span>
            </div>

            <!-- Illustration Card (No border, ambient shadow) -->
            <div class="flex-1 min-h-0 bg-surface-container-lowest rounded-[2rem] overflow-hidden relative ambient-shadow group">
              <img
                class="w-full h-full object-cover opacity-90 transition-transform duration-1000 group-hover:scale-105"
                :src="STORY_IMG"
                alt="Japanese scene illustration"
              />

              <!-- Glassmorphic Character Popover (No border, ambient shadow) -->
              <div class="absolute bottom-8 left-8 right-8 bg-surface/75 backdrop-blur-xl p-6 rounded-2xl flex items-start gap-4 ambient-shadow">
                <div class="w-12 h-12 rounded-xl bg-primary-container flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">person</span>
                </div>
                <div class="flex-1 min-w-0">
                  <span v-if="currentSegment.dialogue_speaker" class="text-xs font-bold text-primary-dim uppercase tracking-wider block mb-1">
                    {{ currentSegment.dialogue_speaker }}
                  </span>
                  <p class="text-lg md:text-xl font-headline font-extrabold text-on-primary-fixed leading-relaxed tracking-wide" style="letter-spacing: 0.04em;">
                    {{ currentSegment.dialogue_ja }}
                  </p>
                  <p v-if="currentSegment.dialogue_vn" class="text-sm font-body font-normal text-on-surface-variant italic mt-1.5 leading-relaxed">
                    ({{ currentSegment.dialogue_vn }})
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Narrative + Choices (col-span 5) -->
          <div class="col-span-12 lg:col-span-5 flex flex-col justify-center gap-8 py-4 overflow-y-auto pr-2 custom-scrollbar">

            <!-- Story Narrative -->
            <div class="px-4">
              <h2 class="text-3xl md:text-4xl font-headline font-extrabold text-on-primary-fixed leading-tight mb-4">
                {{ reviewStore.storyData.title }}
              </h2>
              <p class="text-on-surface-variant text-base md:text-lg leading-relaxed font-body">
                {{ currentSegment.scene_vn }}
              </p>

              <!-- Vocab chips (No border!) -->
              <div v-if="currentSegment.highlighted_words?.length" class="flex flex-wrap gap-2 mt-5">
                <div v-for="hw in currentSegment.highlighted_words" :key="hw.word"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-container text-on-primary-container font-semibold text-xs ambient-shadow hover:scale-105 transition-transform duration-200 cursor-default">
                  <span class="font-bold text-primary" style="letter-spacing: 0.06em;">{{ hw.word }}</span>
                  <span class="text-on-surface-variant/80 font-medium">{{ hw.reading }}</span>
                  <span class="text-on-surface-variant/50 font-normal">— {{ hw.meaning }}</span>
                </div>
              </div>

              <div v-if="currentSegment.question" class="mt-6 flex items-center gap-2">
                <span class="w-8 h-px bg-outline-variant/60"></span>
                <span class="text-xs text-outline font-semibold tracking-widest uppercase">Hãy chọn cách trả lời đúng</span>
              </div>
            </div>

            <!-- Choice Cards (No border, custom labels and classes) -->
            <div v-if="currentSegment.question" class="flex flex-col gap-4">
              <button
                v-for="(choice, idx) in currentSegment.question.choices"
                :key="idx"
                type="button"
                @click="selectAnswer(idx)"
                :disabled="isAnswered"
                class="group flex items-center justify-between p-5 md:p-6 transition-all duration-300 rounded-3xl text-left border-none active:scale-[0.98]"
                :class="choiceClass(idx)"
              >
                <div class="flex items-center gap-4 md:gap-5">
                  <div class="w-10 h-10 shrink-0 rounded-xl flex items-center justify-center text-sm font-bold transition-colors"
                    :class="labelClass(idx)">
                    {{ String.fromCharCode(65 + idx) }}
                  </div>
                  <div>
                    <p class="text-base md:text-lg font-headline font-bold text-on-surface" style="letter-spacing: 0.04em; line-height: 1.6;"
                      :class="{ 'group-hover:text-on-primary-container': !isAnswered }">
                      {{ choice.ja }}
                    </p>
                    <p class="text-sm text-on-surface-variant mt-0.5"
                      :class="{ 'group-hover:text-on-primary-container/70': !isAnswered }">
                      {{ choice.vn }}
                    </p>
                  </div>
                </div>
                <span v-if="isAnswered && idx === currentSegment.question.answer_index"
                  class="material-symbols-outlined text-primary shrink-0 text-xl" style="font-variation-settings: 'FILL' 1;">check_circle</span>
                <span v-else-if="isAnswered && myAnswer === idx && idx !== currentSegment.question.answer_index"
                  class="material-symbols-outlined text-secondary shrink-0 text-xl" style="font-variation-settings: 'FILL' 1;">cancel</span>
                <span v-else-if="!isAnswered" class="material-symbols-outlined text-outline-variant group-hover:text-primary transition-colors">chevron_right</span>
              </button>
            </div>

            <!-- Explanation after answer (No border!) -->
            <Transition name="slide-up">
              <div v-if="isAnswered && currentSegment.question"
                class="mx-4 p-6 rounded-[2rem] flex items-start gap-4 ambient-shadow"
                :class="isCorrect ? 'bg-primary/10' : 'bg-secondary/10'">
                <span class="material-symbols-outlined text-lg shrink-0 mt-0.5"
                  :class="isCorrect ? 'text-primary' : 'text-secondary'"
                  style="font-variation-settings: 'FILL' 1;">
                  {{ isCorrect ? 'check_circle' : 'cancel' }}
                </span>
                <div>
                  <p class="font-headline font-bold text-base mb-1" :class="isCorrect ? 'text-on-primary-fixed' : 'text-secondary'">
                    {{ isCorrect ? 'Chính xác! 🎉' : `Đáp án đúng: ${currentSegment.question.choices[currentSegment.question.answer_index]?.ja}` }}
                  </p>
                  <p v-if="currentSegment.question.explanation_vn" class="text-xs text-on-surface-variant leading-relaxed">
                    {{ currentSegment.question.explanation_vn }}
                  </p>
                  <p v-if="currentSegment.question.hint_ja" class="text-xs text-primary mt-2 font-semibold">
                    💡 {{ currentSegment.question.hint_ja }}
                  </p>
                </div>
              </div>
            </Transition>

            <!-- Contextual Hint (no question) -->
            <div v-if="!currentSegment.question" class="mx-4 p-5 bg-primary/10 rounded-3xl flex items-start gap-4 ambient-shadow">
              <span class="material-symbols-outlined text-primary mt-0.5">lightbulb</span>
              <p class="text-sm text-on-surface-variant font-medium leading-relaxed">
                <strong class="block mb-1 text-primary">Đọc hiểu:</strong>
                Đọc đoạn hội thoại và tiếp tục câu chuyện.
              </p>
            </div>
          </div>

        </div>
      </main>

      <!-- ── Floating Actions ─────────────────────────────────── -->
      <div class="fixed bottom-10 right-10 flex gap-4 z-50">
        <!-- Translate (Vocabulary list drawer trigger) -->
        <button
          class="w-14 h-14 bg-surface-container-lowest text-primary ambient-shadow rounded-full flex items-center justify-center hover:scale-110 active:scale-90 transition-all cursor-pointer"
          @click="showVocab = !showVocab"
          title="Từ vựng"
        >
          <span class="material-symbols-outlined">translate</span>
        </button>
        <!-- Next Segment (Primary with signature gradient) -->
        <button
          v-if="isAnswered || !currentSegment.question"
          @click="handleNextSegment"
          class="bg-gradient-to-br from-primary to-primary-container text-on-primary-fixed hover:text-on-primary-fixed px-8 py-4 rounded-full font-bold transition-all flex items-center gap-3 ambient-shadow cursor-pointer hover:scale-105 duration-250"
        >
          <span>{{ isLastSegment ? 'Kết thúc' : 'Tiếp theo' }}</span>
          <span class="material-symbols-outlined">{{ isLastSegment ? 'flag' : 'arrow_forward' }}</span>
        </button>
      </div>

      <!-- Glassmorphic Vocabulary Popover -->
      <Transition name="fade">
        <div 
          v-if="showVocab && currentSegment.highlighted_words?.length" 
          class="fixed bottom-28 right-10 w-80 max-w-sm glass-morphism rounded-[2rem] p-6 ambient-shadow z-50 flex flex-col gap-4 border-none"
        >
          <div class="flex items-center justify-between">
            <h4 class="font-headline font-bold text-sm text-on-primary-fixed flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-lg">translate</span>
              Từ vựng trong đoạn
            </h4>
            <button @click="showVocab = false" class="p-1 rounded-full hover:bg-surface-container-high transition-colors cursor-pointer flex items-center">
              <span class="material-symbols-outlined text-sm text-on-surface-variant">close</span>
            </button>
          </div>
          
          <div class="space-y-3 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
            <div v-for="hw in currentSegment.highlighted_words" :key="hw.word" class="bg-surface-container-lowest/60 rounded-xl p-3">
              <div class="flex items-baseline gap-2 mb-1">
                <span class="font-headline font-bold text-base text-primary tracking-wide">{{ hw.word }}</span>
                <span class="text-xs text-on-surface-variant/80 font-medium">({{ hw.reading }})</span>
              </div>
              <p class="text-xs text-on-surface leading-normal">{{ hw.meaning }}</p>
            </div>
          </div>
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import { reviewService } from '@/services/review'
import StoryResultScreen from './StoryResultScreen.vue'

const router = useRouter()
const reviewStore = useReviewStore()
const showVocab = ref(false)

// ── Mock illustration ─────────────────────────────────────────
const STORY_IMG = 'https://lh3.googleusercontent.com/aida-public/AB6AXuCWp6svrcCQp81pH1ZxO1Pr-AMW3frWh2ZzLStbL5zIicAH6Mo4DMs7bCRNOHhmji8QCG-sU3xnOTlCKXtPK5QS4oOqhD_diQzrMJy9OJa1w85LeD__1hqBYubkGIT5QhUgDmx4cQeDX8q820TOC3ubj3rQnRRuqVCbAdnjdep6WYY9CPsgm9MFoTNOjF8wDU-moBZy3pQPKSQqnOsT38nKtNe1U5kMhpCU3DjMHxnFGddrIdE5wAujb3ZiaC7Wa0H9blAUeipynH8'

// ── Hydrate on mount ──────────────────────────────────────────
onMounted(() => {
  if (!reviewStore.storyData && reviewStore.status === 'idle') {
    const restored = reviewStore.hydrate()
    if (!restored || !reviewStore.storyData) {
      router.replace('/review')
    }
  }
})

// ── Computed ──────────────────────────────────────────────────
const currentSegment = computed(() =>
  reviewStore.storyData?.segments?.[reviewStore.storySegmentIndex] || null
)
const totalSegments = computed(() => reviewStore.storyData?.segments?.length ?? 0)
const isLastSegment = computed(() => reviewStore.storySegmentIndex >= totalSegments.value - 1)

const storyProgress = computed(() =>
  totalSegments.value > 0
    ? Math.round(((reviewStore.storySegmentIndex + 1) / totalSegments.value) * 100)
    : 0
)

const storyChapterLabel = computed(() => {
  const seg = currentSegment.value
  if (!seg) return ''
  if (seg.scene_vn && seg.scene_vn.length <= 30) return seg.scene_vn
  return seg.scene_vn?.slice(0, 28) + '…' || `Đoạn ${reviewStore.storySegmentIndex + 1}`
})

const myAnswer = computed(() =>
  currentSegment.value ? reviewStore.storyAnswers[currentSegment.value.id] : undefined
)
const isAnswered = computed(() =>
  currentSegment.value?.id !== undefined && currentSegment.value.id in reviewStore.storyAnswers
)
const isCorrect = computed(() =>
  isAnswered.value && myAnswer.value === currentSegment.value?.question?.answer_index
)

// ── Actions ───────────────────────────────────────────────────
function selectAnswer(idx) {
  if (!currentSegment.value || isAnswered.value) return
  reviewStore.submitStoryAnswer(currentSegment.value.id, idx)
}

function handleNextSegment() {
  reviewStore.nextStorySegment()
}

async function handleSaveAndExit() {
  try {
    const segments = reviewStore.storyData?.segments || []
    const totalWithQuestion = segments.filter(s => s.question).length
    let correct = 0
    for (const seg of segments) {
      if (!seg.question) continue
      const ans = reviewStore.storyAnswers[seg.id]
      if (ans === seg.question.answer_index) correct++
    }

    await reviewService.saveStoryResult({
      deckId: reviewStore.deckId,
      level: reviewStore.level,
      title: reviewStore.storyData?.title || 'Untitled Story',
      score: correct,
      totalQuestions: totalWithQuestion,
      storyData: reviewStore.storyData,
      answersData: reviewStore.storyAnswers
    })
  } catch (err) {
    console.error('Failed to save story result:', err)
  }
  reviewStore.clearSession()
  router.push('/review')
}

function handleExit() {
  reviewStore.clearSession()
  router.push('/review')
}

function handleRestart() {
  reviewStore.restartStory()
}

// ── Choice styles (mirrors stitch.html hover states) ──────────
function choiceClass(idx) {
  if (!isAnswered.value) {
    return 'bg-surface-container-lowest text-on-surface hover:bg-primary-container/20 hover:scale-[1.01] active:scale-[0.99] cursor-pointer ambient-shadow'
  }
  if (idx === currentSegment.value.question.answer_index) {
    return 'bg-primary/10 text-primary cursor-default'
  }
  if (idx === myAnswer.value) {
    return 'bg-secondary/10 text-secondary cursor-default'
  }
  return 'bg-surface-container-lowest text-on-surface opacity-55 cursor-default'
}

function labelClass(idx) {
  if (!isAnswered.value) {
    return 'bg-surface-container-high text-on-surface-variant group-hover:bg-primary group-hover:text-on-primary'
  }
  if (idx === currentSegment.value.question.answer_index) return 'bg-primary text-on-primary'
  if (idx === myAnswer.value) return 'bg-secondary text-on-secondary'
  return 'bg-surface-container text-on-surface-variant/40'
}
</script>

<style scoped>
.slide-up-enter-active { transition: all 0.3s ease-out; }
.slide-up-enter-from  { opacity: 0; transform: translateY(12px); }

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-outline-variant);
  border-radius: 99px;
  opacity: 0.3;
}
</style>

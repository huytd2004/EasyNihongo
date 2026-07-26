<template>
  <div class="w-full">
    <!-- Error Banner -->
    <div v-if="errorMessage" class="mb-8 p-4 md:p-5 rounded-2xl bg-error-container text-on-error-container flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <p class="text-sm font-medium">{{ errorMessage }}</p>
      <button class="px-4 py-2 rounded-full bg-on-error-container text-error-container font-semibold text-sm transition-transform active:scale-95" @click="retryLoad">
        Thử lại
      </button>
    </div>

    <!-- Smart Suggestion Banner -->
    <section class="mb-12">
      <div class="bg-primary-container/30 border border-primary-container p-6 rounded-3xl flex items-center gap-6">
        <div class="w-16 h-16 rounded-2xl bg-primary-container flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-primary text-3xl" style="font-variation-settings: 'FILL' 1;">psychology_alt</span>
        </div>
        <div class="flex-1">
          <h3 class="font-headline font-bold text-on-primary-fixed text-xl mb-1">Đề xuất tối ưu cho bạn</h3>
          <p v-if="loadingMistakes" class="text-on-primary-fixed-variant opacity-80 text-sm">
            Đang phân tích lịch sử học tập...
          </p>
          <p v-else-if="recentMistakeCount > 0" class="text-on-primary-fixed-variant opacity-80 leading-relaxed text-sm">
            Hệ thống phát hiện <span class="font-bold underline">{{ recentMistakeCount }} lỗi sai</span> trong các phiên luyện tập gần nhất. Hãy ôn lại để củng cố ghi nhớ!
          </p>
          <p v-else class="text-on-primary-fixed-variant opacity-80 leading-relaxed text-sm">
            Chưa có dữ liệu lỗi sai. Hãy hoàn thành ít nhất một phiên AI Tutor để nhận đề xuất cá nhân hoá.
          </p>
        </div>
        <!-- Streak (mock) -->
        <div class="hidden md:flex flex-col items-center gap-1 shrink-0 px-4 py-3 rounded-2xl bg-secondary-container/40">
          <span class="material-symbols-outlined text-secondary text-2xl" style="font-variation-settings: 'FILL' 1;">local_fire_department</span>
          <span class="text-2xl font-headline font-extrabold text-on-secondary-container">{{ mockStreak }}</span>
          <span class="text-[10px] font-bold text-on-secondary-container/70 uppercase tracking-wider">Ngày</span>
        </div>
      </div>
    </section>

    <!-- Step 1: Deck Selection -->
    <section class="mb-16">
      <div class="flex items-baseline justify-between mb-8">
        <div class="flex flex-col">
          <span class="text-xs font-bold text-primary tracking-[0.2em] uppercase mb-1">Bước 01</span>
          <h2 class="text-3xl font-headline font-extrabold text-on-surface">Chọn bộ thẻ ôn tập</h2>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loadingDecks" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="i in 4" :key="i" class="p-6 rounded-2xl bg-surface-container-lowest shadow-sm animate-pulse">
          <div class="h-4 w-20 rounded-full bg-surface-container-highest mb-4"></div>
          <div class="h-6 w-3/4 rounded-full bg-surface-container-highest mb-3"></div>
          <div class="h-4 w-1/2 rounded-full bg-surface-container-highest"></div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!decks.length" class="p-8 rounded-3xl bg-surface-container-lowest shadow-sm text-center">
        <div class="mx-auto mb-4 w-14 h-14 rounded-full bg-surface-container flex items-center justify-center text-primary">
          <span class="material-symbols-outlined">library_books</span>
        </div>
        <h4 class="text-lg font-semibold text-on-surface mb-2">Chưa có deck nào</h4>
        <p class="text-sm text-on-surface-variant max-w-md mx-auto">Hãy tạo bộ thẻ flashcard trước, sau đó quay lại để chọn deck ôn tập.</p>
      </div>

      <!-- Deck grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          v-for="deck in decks"
          :key="deck.id"
          type="button"
          @click="selectDeck(deck)"
          class="p-6 rounded-2xl text-left transition-all duration-200 bg-surface-container-lowest shadow-sm hover:shadow-md active:scale-[0.99] border-2"
          :class="selectedDeckId === deck.id
            ? 'border-primary bg-primary-container/20 shadow-lg shadow-primary/10'
            : 'border-transparent hover:border-primary-container/40'"
        >
          <div class="flex items-start justify-between gap-4 mb-4">
            <span class="material-symbols-outlined text-3xl" :class="selectedDeckId === deck.id ? 'text-primary' : 'text-on-surface-variant'">menu_book</span>
            <span v-if="selectedDeckId === deck.id" class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">check_circle</span>
          </div>
          <h4 class="font-bold text-lg mb-1 text-on-surface">{{ deck.name }}</h4>
          <p class="text-sm mb-4" :class="selectedDeckId === deck.id ? 'text-on-surface/80' : 'text-on-surface-variant'">{{ deck.description || 'Chưa có mô tả.' }}</p>
          <div class="flex flex-wrap gap-2 text-xs">
            <span class="px-3 py-1 rounded-full" :class="selectedDeckId === deck.id ? 'bg-primary/10 text-primary' : 'bg-surface-container-highest text-on-surface-variant'">
              Tổng: {{ deck.cardStats?.total ?? 0 }}
            </span>
            <span class="px-3 py-1 rounded-full" :class="selectedDeckId === deck.id ? 'bg-primary/10 text-primary' : 'bg-surface-container-highest text-on-surface-variant'">
              Đến hạn: {{ deck.cardStats?.dueToday ?? 0 }}
            </span>
          </div>
        </button>
      </div>
    </section>

    <!-- Step 2: General settings -->
    <section class="mb-16">
      <div class="flex flex-col mb-8">
        <span class="text-xs font-bold text-primary tracking-[0.2em] uppercase mb-1">Bước 02</span>
        <h2 class="text-3xl font-headline font-extrabold text-on-surface">Thiết lập chung</h2>
      </div>

      <div class="p-6 rounded-3xl bg-surface-container-lowest shadow-sm">
        <!-- JLPT Level — áp dụng cho cả Quiz & Story -->
        <div class="mb-6">
          <div class="flex items-center gap-2 mb-3">
            <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-widest">Cấp độ JLPT</p>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-tertiary-container text-on-tertiary-container tracking-wide">Quiz & Story</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="lvl in jlptLevels"
              :key="lvl"
              type="button"
              @click="selectedLevel = lvl"
              class="px-5 py-2.5 rounded-full font-semibold text-sm transition-all"
              :class="selectedLevel === lvl
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'bg-surface-container-highest text-on-surface-variant hover:bg-surface-container-high'"
            >
              {{ lvl }}
            </button>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-outline-variant/30 mb-6"></div>

        <!-- Question count — chỉ Quiz -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-widest">Số câu hỏi</p>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary-container/60 text-on-primary-container tracking-wide">Chỉ Quiz</span>
            </div>
            <span v-if="selectedDeck" class="text-xs text-on-surface-variant">
              Deck có <span class="font-semibold text-on-surface">{{ selectedDeck.cardStats?.total ?? '?' }}</span> thẻ
              <span v-if="effectiveQuestionCount < selectedQuestionCount" class="text-primary font-semibold"> · Tự động giới hạn {{ effectiveQuestionCount }} câu</span>
            </span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="count in questionCountOptions"
              :key="count"
              type="button"
              @click="selectedQuestionCount = count"
              class="px-5 py-2.5 rounded-full font-semibold text-sm transition-all"
              :class="selectedQuestionCount === count
                ? 'bg-secondary-container text-on-secondary-container shadow-sm'
                : 'bg-surface-container-highest text-on-surface-variant hover:bg-surface-container-high'"
            >
              {{ count }} câu
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Step 3: Review Mode -->

    <section>
      <div class="flex flex-col mb-8">
        <span class="text-xs font-bold text-primary tracking-[0.2em] uppercase mb-1">Bước 03</span>
        <h2 class="text-3xl font-headline font-extrabold text-on-surface">Chọn chế độ ôn tập</h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Mode: Quiz -->
        <button
          type="button"
          @click="selectedMode = 'quiz'"
          class="group cursor-pointer block text-left w-full"
        >
          <div
            class="relative overflow-hidden rounded-[2.5rem] p-1 border-2 transition-all duration-300 shadow-sm"
            :class="selectedMode === 'quiz'
              ? 'border-primary bg-primary-container/10 shadow-xl shadow-primary/10'
              : 'border-transparent bg-surface-container-lowest hover:border-primary/40 hover:shadow-lg'"
          >
            <div class="p-8 flex flex-col h-full rounded-[2.25rem]" :class="selectedMode === 'quiz' ? 'bg-primary-container/5' : 'bg-surface-container-lowest'">
              <div class="flex items-center justify-between mb-6">
                <div class="flex items-center gap-4">
                  <div class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0" :class="selectedMode === 'quiz' ? 'bg-primary/20' : 'bg-primary/10'">
                    <span class="material-symbols-outlined text-primary text-2xl">edit_note</span>
                  </div>
                  <div>
                    <h3 class="text-2xl font-headline font-bold text-on-surface">Quiz / Fill-in-the-blank</h3>
                    <p class="text-sm text-on-surface-variant font-medium mt-1">Luyện tập trí nhớ chủ động</p>
                  </div>
                </div>
                <!-- Selected check -->
                <span v-if="selectedMode === 'quiz'" class="material-symbols-outlined text-primary text-2xl shrink-0" style="font-variation-settings: 'FILL' 1;">check_circle</span>
              </div>

              <div class="space-y-4 mb-10">
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-primary/70">check_circle</span>
                  <span class="text-sm font-medium">Trắc nghiệm 4 đáp án chọn Kanji đúng</span>
                </div>
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-primary/70">check_circle</span>
                  <span class="text-sm font-medium">Điền từ vào chỗ trống theo ngữ cảnh</span>
                </div>
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-primary/70">check_circle</span>
                  <span class="text-sm font-medium">Gõ Hiragana cho Kanji hiển thị</span>
                </div>
              </div>

              <div class="mt-auto">
                <div class="h-40 w-full rounded-2xl bg-surface-container overflow-hidden">
                  <img class="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB5MUHQ4nliKt8TejltzFIBCVgaLhX_9z6Mu4I0Wdi15c7eejeykYlAONxev3oBwXwDh4p6t9ATebh_fT7dnR9ROGwrJjSKl0VN0fx18SrMBA8UKDTtednimiYpakBqys3f3dcwAHY3rfVrWi55fRrwtb_T-iWK1nBap3aSw1B_ONThk0Iyi99iBmUVJTkQJ0htuuB39vR-_7QKAeHvCYbZbc2IkRwthuw20U7hoDvNsFCEmlcMlubAc6oyGptyXo3Zo4ph1lyUodI"/>
                </div>
              </div>
            </div>
          </div>
        </button>

        <!-- Mode: Interactive Story -->
        <button
          type="button"
          @click="selectedMode = 'story'"
          class="group cursor-pointer block text-left w-full"
        >
          <div
            class="relative overflow-hidden rounded-[2.5rem] p-1 border-2 transition-all duration-300 shadow-sm"
            :class="selectedMode === 'story'
              ? 'border-secondary bg-secondary-container/10 shadow-xl shadow-secondary/10'
              : 'border-transparent bg-surface-container-lowest hover:border-secondary/40 hover:shadow-lg'"
          >
            <div class="p-8 flex flex-col h-full rounded-[2.25rem]" :class="selectedMode === 'story' ? 'bg-secondary-container/5' : 'bg-surface-container-lowest'">
              <div class="flex items-center justify-between mb-6">
                <div class="flex items-center gap-4">
                  <div class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0" :class="selectedMode === 'story' ? 'bg-secondary/20' : 'bg-secondary/10'">
                    <span class="material-symbols-outlined text-secondary text-2xl" style="font-variation-settings: 'FILL' 1;">auto_stories</span>
                  </div>
                  <div>
                    <h3 class="text-2xl font-headline font-bold text-on-surface">Interactive Story</h3>
                    <p class="text-sm text-on-surface-variant font-medium mt-1">Học qua bối cảnh câu chuyện</p>
                  </div>
                </div>
                <!-- Selected check -->
                <span v-if="selectedMode === 'story'" class="material-symbols-outlined text-secondary text-2xl shrink-0" style="font-variation-settings: 'FILL' 1;">check_circle</span>
              </div>

              <div class="space-y-4 mb-10">
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-secondary/70">check_circle</span>
                  <span class="text-sm font-medium">Nhập vai nhân vật trong tình huống giả định</span>
                </div>
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-secondary/70">check_circle</span>
                  <span class="text-sm font-medium">Học cách sử dụng từ vựng tự nhiên nhất</span>
                </div>
                <div class="flex items-center gap-3 text-on-surface-variant">
                  <span class="material-symbols-outlined text-lg text-secondary/70">check_circle</span>
                  <span class="text-sm font-medium">Kết nối các từ đã học thành một mạch truyện</span>
                </div>
              </div>

              <div class="mt-auto">
                <div class="h-40 w-full rounded-2xl bg-surface-container overflow-hidden">
                  <img class="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC7cpmspiSTuIpqj_Es8s4R0kAlS7WsuNhtKY9XWO0jobLqkKvwgZyDuV-wABsXvkUUTmN_5_tsrunNR-KDTVQgLfuORSTxWfzjhCM954YdWjDM3iHeDyyFr97hcEfYE9Gt9AlcT-bpRIsHJ2HjdPIJygLR_6z0GPBrSxpa-yEiB72CQMHvsFpYpYliq5Tz7SEeNqpSimR1KVXGhAkQU-sa1Or9FNbePWDoyBroF3WlMueIqpjDPgBZTLN48ZZW3Xo8U05KxO4YwD8"/>
                </div>
              </div>
            </div>
          </div>
        </button>
      </div>

      <!-- Session summary + Start button -->

      <div class="mt-12 flex flex-col md:flex-row items-center justify-between gap-6 p-8 rounded-3xl bg-surface-container-low shadow-sm">
        <div class="space-y-1">
          <p class="text-sm font-semibold text-on-surface">Tóm tắt phiên ôn tập</p>
          <p class="text-sm text-on-surface-variant">
            Deck: <span class="font-semibold text-on-surface">{{ selectedDeck?.name || 'Chưa chọn' }}</span>
            &nbsp;•&nbsp; Chế độ: <span class="font-semibold text-on-surface">{{ selectedMode === 'quiz' ? 'Quiz' : selectedMode === 'story' ? 'Story' : 'Chưa chọn' }}</span>
            &nbsp;•&nbsp; Cấp độ: <span class="font-semibold text-on-surface">{{ selectedLevel }}</span>
            <template v-if="selectedMode === 'quiz'">&nbsp;•&nbsp; Số câu: <span class="font-semibold text-on-surface">{{ effectiveQuestionCount }}</span></template>
          </p>
          <p v-if="startError" class="text-xs text-error font-medium">{{ startError }}</p>
          <p v-else-if="!selectedDeckId" class="text-xs text-on-surface-variant">Hãy chọn deck ở Bước 01.</p>
          <p v-else-if="!selectedMode" class="text-xs text-amber-600 font-medium">↑ Chọn một chế độ ôn tập ở trên.</p>
          <p v-else class="text-xs text-green-600 font-medium">Sẵn sàng! Nhấn bắt đầu để tạo quiz bằng AI.</p>
        </div>
        <button
          @click="startQuiz"
          :disabled="!canStart"
          class="bg-gradient-to-r from-primary to-primary-dim text-white px-12 py-5 rounded-full font-headline font-bold text-lg shadow-xl shadow-primary/30 transition-all active:scale-95 flex items-center gap-4 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          <span v-if="starting">Đang tạo quiz...</span>
          <span v-else>Bắt đầu ôn tập</span>
          <span v-if="starting" class="material-symbols-outlined animate-spin">progress_activity</span>
          <span v-else class="material-symbols-outlined">rocket_launch</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { tutorService } from '@/services/tutor'
import { reviewService } from '@/services/review'
import { useReviewStore } from '@/stores/review'

const router = useRouter()
const reviewStore = useReviewStore()

// ── Deck state ────────────────────────────────────────────────
const decks = ref([])
const selectedDeckId = ref(null)
const loadingDecks = ref(false)
const deckError = ref('')

// ── Quiz settings ─────────────────────────────────────────────
const jlptLevels = ['N5', 'N4', 'N3', 'N2', 'N1']
const selectedLevel = ref('N3')

const questionCountOptions = [10, 20, 30]
const selectedQuestionCount = ref(20)

// ── Start state ───────────────────────────────────────────────
const starting = ref(false)
const startError = ref('')
const selectedMode = ref(null) // 'quiz' | 'story'

// ── Mistakes banner ───────────────────────────────────────────
const recentMistakeCount = ref(0)
const loadingMistakes = ref(false)

// ── Mock streak ───────────────────────────────────────────────
const mockStreak = ref(7)

// ── Computed ──────────────────────────────────────────────────
const selectedDeck = computed(() => decks.value.find(d => d.id === selectedDeckId.value) || null)
const errorMessage = computed(() => deckError.value)
const canStart = computed(() => !!selectedDeckId.value && !!selectedMode.value && !starting.value)

/** Số câu thực tế = min(chọn, tổng thẻ trong deck). Fallback về selectedQuestionCount nếu chưa chọn deck. */
const effectiveQuestionCount = computed(() => {
  const total = selectedDeck.value?.cardStats?.total
  if (!total) return selectedQuestionCount.value
  return Math.min(selectedQuestionCount.value, total)
})

// ── Helpers ───────────────────────────────────────────────────
function unwrapListResponse(response) {
  const payload = response?.data ?? response
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.data)) return payload.data
  return []
}

// ── Data loading ──────────────────────────────────────────────
async function loadDecks() {
  loadingDecks.value = true
  deckError.value = ''
  try {
    const response = await tutorService.getDecks()
    decks.value = unwrapListResponse(response)
  } catch (error) {
    console.error('[ReviewSetupView] loadDecks failed:', error)
    deckError.value = 'Không thể tải danh sách bộ thẻ. Vui lòng thử lại.'
    decks.value = []
  } finally {
    loadingDecks.value = false
  }
}

async function loadRecentMistakes() {
  loadingMistakes.value = true
  try {
    const response = await tutorService.getRecentMistakes(5)
    const payload = response?.data ?? response
    recentMistakeCount.value = payload?.data?.mistakeCount ?? payload?.mistakeCount ?? 0
  } catch (error) {
    console.warn('[ReviewSetupView] loadRecentMistakes failed:', error)
    recentMistakeCount.value = 0
  } finally {
    loadingMistakes.value = false
  }
}

function selectDeck(deck) {
  if (!deck || deck.id === selectedDeckId.value) return
  selectedDeckId.value = deck.id
}

async function startQuiz() {
  if (!canStart.value) return
  starting.value = true
  startError.value = ''

  try {
    // Load recent mistakes to pass along
    let recentMistakes = []
    try {
      const mRes = await tutorService.getRecentMistakes(5)
      const mPayload = mRes?.data ?? mRes
      recentMistakes = mPayload?.data?.mistakes ?? mPayload?.mistakes ?? []
    } catch (e) {
      console.warn('[ReviewSetupView] getRecentMistakes failed, proceeding without', e)
    }

    const meta = {
      deckId: selectedDeckId.value,
      deckName: selectedDeck.value?.name || '',
      level: selectedLevel.value
    }
    let taskId = null
    if (selectedMode.value === 'story') {
      // ── Story mode (Async) ──────────────────────────────────
      const response = await reviewService.generateStoryAsync({
        deckId: selectedDeckId.value,
        level: selectedLevel.value,
        recentMistakes,
      })
      const envelope = response?.data ?? response
      const payload = envelope?.data ?? envelope
      taskId = payload?.taskId
    } else {
      // ── Quiz mode (Async) ───────────────────────────────────
      const response = await reviewService.generateQuizAsync({
        deckId: selectedDeckId.value,
        level: selectedLevel.value,
        questionCount: effectiveQuestionCount.value,
        recentMistakes,
      })
      const envelope = response?.data ?? response
      const payload = envelope?.data ?? envelope
      taskId = payload?.taskId
    }

    if (!taskId) {
      startError.value = 'Không thể khởi tạo tiến trình tạo bài tập bằng AI.'
      return
    }

    // ── Polling loop ─────────────────────────────────────────
    let status = 'PENDING'
    let taskResult = null
    let pollAttempts = 0
    const maxPollAttempts = 40 // 40 * 3s = 120s max duration

    while ((status === 'PENDING' || status === 'PROCESSING') && pollAttempts < maxPollAttempts) {
      await new Promise(resolve => setTimeout(resolve, 3000))
      pollAttempts++

      const pollRes = await reviewService.getTaskStatus(taskId)
      const envelope = pollRes?.data ?? pollRes
      const payload = envelope?.data ?? envelope

      status = payload?.status || 'FAILED'
      taskResult = payload?.result

      if (status === 'SUCCESS') {
        break
      } else if (status === 'FAILED') {
        startError.value = payload?.warning || 'Tiến trình tạo bài tập bằng AI thất bại.'
        return
      }
    }

    if (status !== 'SUCCESS') {
      startError.value = 'Thời gian xử lý của AI quá lâu. Vui lòng thử lại.'
      return
    }

    // ── Handle task result ───────────────────────────────────
    if (selectedMode.value === 'story') {
      const segments = taskResult?.segments ?? []
      if (!segments.length) {
        startError.value = taskResult?.warning || 'Không thể tạo câu chuyện. Vui lòng thử lại.'
        return
      }
      reviewStore.setStory(taskResult, meta)
      await router.push('/review/story')
    } else {
      const questions = taskResult?.questions ?? []
      if (!questions.length) {
        startError.value = 'Không thể tạo câu hỏi. Vui lòng thử lại.'
        return
      }
      reviewStore.warning = taskResult?.warning ?? null
      reviewStore.setQuestions(questions, meta)
      await router.push('/review/quiz')
    }
  } catch (error) {
    console.error('[ReviewSetupView] startQuiz failed:', error)
    startError.value = error?.response?.data?.message || 'Không thể bắt đầu ôn tập. Vui lòng thử lại.'
  } finally {
    starting.value = false
  }
}

async function retryLoad() {
  await loadDecks()
}

// ── Init ──────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadDecks(), loadRecentMistakes()])

  // Auto-select if only one deck
  if (decks.value.length === 1) {
    selectedDeckId.value = decks.value[0].id
  }
})
</script>

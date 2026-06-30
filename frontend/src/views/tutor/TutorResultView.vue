<template>
  <div class="w-full">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-32 gap-4">
      <div class="w-12 h-12 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
      <p class="text-on-surface-variant text-sm">Đang tải kết quả phiên học...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-32 gap-4 text-center">
      <span class="material-symbols-outlined text-error text-5xl">error_outline</span>
      <p class="text-on-surface-variant">{{ error }}</p>
      <RouterLink to="/tutor" class="mt-4 px-6 py-3 bg-primary text-on-primary rounded-full text-sm font-semibold">
        Quay lại
      </RouterLink>
    </div>

    <template v-else-if="result">
      <!-- ── Hero: Header + Stats grid ───────────────────────────────────── -->
      <section class="mb-16 flex flex-col md:flex-row items-center gap-12">
        <div class="w-full md:w-1/2">
          <h1 class="text-display-lg font-bold text-on-primary-fixed mb-2 tracking-tight leading-tight" style="font-size:3.5rem;">完了</h1>
          <h2 class="text-3xl font-headline font-semibold text-primary mb-4">Phiên học hoàn tất</h2>
          <p class="text-on-surface-variant text-base leading-relaxed max-w-md">
            Bạn đã hoàn thành phiên luyện tập hội thoại tiếng Nhật.
            Dưới đây là phân tích chi tiết về phiên học của bạn.
          </p>

          <div class="mt-8 flex gap-4 flex-wrap">
            <RouterLink to="/tutor"
              class="bg-gradient-to-r from-primary to-primary-dim text-on-primary px-8 py-4 rounded-full font-semibold hover:opacity-90 transition-all flex items-center gap-2 shadow-xl shadow-primary/10">
              Học tiếp
              <span class="material-symbols-outlined">arrow_forward</span>
            </RouterLink>
            <RouterLink to="/dashboard"
              class="text-on-surface border border-outline-variant/30 px-8 py-4 rounded-full font-medium hover:bg-surface-container-low transition-all">
              Dashboard
            </RouterLink>
          </div>
        </div>

        <!-- Bento Stats -->
        <div class="w-full md:w-1/2 grid grid-cols-2 gap-4">
          <!-- Duration -->
          <div class="bg-surface-container-lowest p-8 rounded-[2rem] flex flex-col items-center justify-center text-center shadow-sm border border-outline-variant/10">
            <span class="material-symbols-outlined text-primary text-3xl mb-2" style="font-variation-settings:'FILL' 1;">schedule</span>
            <span class="text-4xl font-headline font-bold text-primary mb-1">{{ result.durationMinutes ?? '—' }}</span>
            <span class="text-xs uppercase tracking-widest text-on-surface-variant font-medium">Phút luyện tập</span>
          </div>

          <!-- Turns -->
          <div class="bg-primary-container p-8 rounded-[2rem] flex flex-col items-center justify-center text-center shadow-sm">
            <span class="material-symbols-outlined text-on-primary-container text-3xl mb-2" style="font-variation-settings:'FILL' 1;">forum</span>
            <span class="text-4xl font-headline font-bold text-on-primary-container mb-1">{{ result.userTurns ?? '—' }}</span>
            <span class="text-xs uppercase tracking-widest text-on-primary-container/70 font-medium">Lượt phản hồi</span>
          </div>

          <!-- Stats row: real metrics only -->
          <div class="bg-surface-container-low col-span-2 p-8 rounded-[2rem] flex items-center justify-around border border-outline-variant/10">
            <div class="text-center">
              <div class="text-2xl font-headline font-bold mb-1"
                :class="corrections.length > 0 ? 'text-error' : 'text-primary'">
                {{ corrections.length }}
              </div>
              <div class="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">Lỗi sai</div>
            </div>
            <div class="w-px h-12 bg-outline-variant/20"></div>
            <div class="text-center">
              <div class="text-2xl font-headline font-bold text-secondary mb-1">
                {{ newVocabulary.length }}
              </div>
              <div class="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">Từ mới</div>
            </div>
            <div class="w-px h-12 bg-outline-variant/20"></div>
            <div class="text-center">
              <div class="text-2xl font-headline font-bold text-on-surface mb-1">
                {{ result.assistantTurns ?? '—' }}
              </div>
              <div class="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">Lượt AI</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Insights Grid ───────────────────────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left: Corrections + Vocabulary -->
        <div class="lg:col-span-2 space-y-10">

          <!-- Grammar Corrections -->
          <div>
            <h3 class="text-xl font-headline font-semibold px-2 flex items-center gap-3 mb-6">
              <span class="material-symbols-outlined text-error" style="font-variation-settings:'FILL' 1;">auto_fix_high</span>
              Phân tích lỗi sai ({{ corrections.length }} lỗi)
            </h3>

            <div v-if="corrections.length === 0"
              class="bg-surface-container-lowest p-8 rounded-[1.5rem] flex items-center gap-4 border border-outline-variant/10">
              <span class="material-symbols-outlined text-primary text-4xl" style="font-variation-settings:'FILL' 1;">check_circle</span>
              <div>
                <p class="font-semibold text-on-surface">Xuất sắc! Không có lỗi nào được ghi nhận.</p>
                <p class="text-sm text-on-surface-variant mt-1">Bạn đã sử dụng tiếng Nhật rất chính xác trong phiên này.</p>
              </div>
            </div>

            <div v-for="(c, i) in corrections" :key="i"
              class="bg-surface-container-lowest p-6 rounded-[1.5rem] border-l-4 border-error/40 shadow-sm mb-4 hover:bg-white transition-all">
              <div class="flex items-center gap-2 mb-4">
                <span class="text-xs font-bold uppercase tracking-widest bg-error-container text-on-error-container px-3 py-1 rounded-full">
                  Lỗi {{ i + 1 }}
                </span>
              </div>
              <div class="space-y-3">
                <div class="flex gap-3 items-start">
                  <span class="material-symbols-outlined text-error mt-0.5 flex-shrink-0">close</span>
                  <p class="text-on-surface-variant italic">「{{ c.original }}」</p>
                </div>
                <div class="flex gap-3 items-start">
                  <span class="material-symbols-outlined text-primary mt-0.5 flex-shrink-0">check_circle</span>
                  <p class="text-on-surface font-semibold">「{{ c.corrected }}」</p>
                </div>
              </div>
              <div v-if="c.note || c.explanation" class="mt-4 pt-4 border-t border-outline-variant/10">
                <p class="text-sm text-on-surface-variant leading-relaxed">
                  <strong class="text-on-surface">Giải thích: </strong>{{ c.note || c.explanation }}
                </p>
              </div>
            </div>
          </div>

          <!-- New Vocabulary -->
          <div>
            <h3 class="text-xl font-headline font-semibold px-2 flex items-center gap-3 mb-6">
              <span class="material-symbols-outlined text-secondary" style="font-variation-settings:'FILL' 1;">auto_stories</span>
              Từ vựng mới trong phiên ({{ newVocabulary.length }} từ)
            </h3>

            <div v-if="newVocabulary.length === 0"
              class="bg-surface-container-lowest p-6 rounded-[1.5rem] border border-outline-variant/10 text-on-surface-variant text-sm">
              Không có từ vựng mới nào được ghi nhận trong phiên này.
            </div>

            <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div v-for="(v, i) in newVocabulary" :key="i"
                class="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/10 hover:border-secondary/30 transition-all shadow-sm flex justify-between items-start">
                <div>
                  <div class="flex items-baseline gap-2 mb-1">
                    <span class="text-2xl font-bold text-on-surface font-headline">{{ v.surface }}</span>
                    <span class="text-xs text-on-surface-variant">{{ v.reading }}</span>
                  </div>
                  <p class="text-sm text-secondary font-medium">{{ v.meaning }}</p>
                </div>
                <button
                  @click="handleAddToFlashcardClick(v)"
                  class="p-2 hover:bg-surface-container text-on-surface-variant hover:text-primary rounded-full transition-all flex items-center justify-center shrink-0"
                  title="Thêm vào flashcard"
                >
                  <span class="material-symbols-outlined text-xl">bookmark_add</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Sidebar -->
        <div class="space-y-6">
          <!-- Motivational card -->
          <div class="relative overflow-hidden rounded-[2rem] bg-on-primary-fixed p-8 text-on-primary min-h-[220px] flex flex-col justify-end shadow-lg shadow-primary-fixed/20">
            <div class="relative z-10">
              <span class="material-symbols-outlined text-primary-fixed mb-3 text-4xl" style="font-variation-settings:'FILL' 1;">self_improvement</span>
              <h4 class="text-2xl font-headline font-bold mb-2">Hành trình ngàn dặm</h4>
              <p class="text-primary-fixed/80 text-sm leading-relaxed">
                Bắt đầu từ một bước chân duy nhất. Hôm nay bạn đã tiến xa hơn hôm qua một bước.
              </p>
            </div>
          </div>

          <!-- Session summary -->
          <div class="bg-surface-container-high p-6 rounded-[2rem] border border-outline-variant/10">
            <h4 class="text-on-surface font-semibold mb-5 flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">summarize</span>
              Tóm tắt phiên học
            </h4>
            <div class="space-y-4 text-sm">
              <div class="flex justify-between items-center">
                <span class="text-on-surface-variant">Thời lượng</span>
                <span class="font-semibold text-on-surface">{{ result.durationMinutes ?? 0 }} phút</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-on-surface-variant">Lượt bạn nói</span>
                <span class="font-semibold text-on-surface">{{ result.userTurns ?? 0 }} lượt</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-on-surface-variant">Lượt AI phản hồi</span>
                <span class="font-semibold text-on-surface">{{ result.assistantTurns ?? 0 }} lượt</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-on-surface-variant">Số lỗi sai</span>
                <span class="font-semibold" :class="corrections.length > 0 ? 'text-error' : 'text-primary'">
                  {{ corrections.length }} lỗi
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-on-surface-variant">Từ vựng mới</span>
                <span class="font-semibold text-secondary">{{ newVocabulary.length }} từ</span>
              </div>
            </div>
          </div>

          <!-- Summary text if available -->
          <div v-if="result.summary" class="bg-surface-container-lowest p-6 rounded-[2rem] border border-outline-variant/10">
            <h4 class="text-on-surface font-semibold mb-3 flex items-center gap-2 text-sm">
              <span class="material-symbols-outlined text-tertiary text-base">notes</span>
              Nhận xét
            </h4>
            <p class="text-sm text-on-surface-variant leading-relaxed">{{ result.summary }}</p>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Add to Flashcard Modal ──────────────────────────────────────── -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div class="bg-surface-container-lowest rounded-[2.5rem] max-w-md w-full p-10 animate-in" style="box-shadow: 0 20px 40px rgba(45, 52, 53, 0.08), 0 8px 16px rgba(45, 52, 53, 0.04); backdrop-filter: blur(4px);">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-xl font-display font-bold text-on-surface">Thêm vào Flashcard</h2>
          <button
            @click="closeModal"
            class="p-2.5 rounded-full hover:bg-surface-container/50 transition-colors text-on-surface-variant hover:text-on-surface"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <!-- Success state -->
        <div v-if="addSuccess" class="text-center py-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-primary/15 rounded-full mb-6">
            <span class="material-symbols-outlined text-3xl text-primary">check_circle</span>
          </div>
          <p class="text-lg font-semibold text-on-surface mb-2">Thêm thành công!</p>
          <p class="text-sm text-on-surface-variant">Từ vựng đã được thêm vào bộ thẻ.</p>
        </div>

        <!-- Loading state -->
        <div v-else-if="loadingDecks" class="space-y-4">
          <div class="h-12 bg-surface-container-low rounded-[1.5rem] animate-pulse"></div>
          <div class="h-40 bg-surface-container-low rounded-[1.5rem] animate-pulse"></div>
        </div>

        <!-- Deck selection -->
        <div v-else class="space-y-6">
          <!-- Word preview -->
          <div class="p-6 bg-surface-container-low rounded-[1.75rem]">
            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-3">Từ vựng</p>
            <p class="text-4xl font-display font-bold text-on-surface mb-2">{{ selectedEntry?.text }}</p>
            <p class="text-sm text-on-surface-variant mb-3 font-medium">{{ selectedEntry?.reading }}</p>
            <p class="text-base text-secondary font-bold leading-relaxed">{{ selectedEntry?.meaningVn }}</p>
          </div>

          <!-- Deck selection -->
          <div v-if="!showCreateDeckForm">
            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-4">Chọn bộ thẻ</p>
            <div v-if="decks.length === 0" class="p-8 text-center rounded-[1.75rem] bg-surface-container-low">
              <span class="material-symbols-outlined text-5xl text-on-surface-variant/30 mb-3 block">folder_open</span>
              <p class="text-sm text-on-surface-variant mb-6 font-medium">Bạn chưa có bộ thẻ nào</p>
              <button
                @click="showCreateDeckForm = true"
                class="px-6 py-2.5 bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-full font-semibold text-sm transition-all hover:shadow-lg"
              >
                Tạo bộ thẻ mới
              </button>
            </div>
            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
              <label
                v-for="deck in decks"
                :key="deck.id"
                class="flex items-start p-4 rounded-[1.25rem] cursor-pointer hover:bg-surface-container-low transition-all"
                style="border: 1px solid rgba(173, 179, 180, 0.15);"
              >
                <input
                  type="radio"
                  :value="deck.id"
                  v-model="selectedDeckId"
                  class="mt-1.5 cursor-pointer accent-primary"
                />
                <div class="ml-4 flex-1">
                  <p class="font-semibold text-on-surface text-sm">{{ deck.name }}</p>
                  <p class="text-xs text-on-surface-variant mt-1">{{ deck.description }}</p>
                  <p class="text-xs text-on-surface-variant mt-2">
                    {{ deck.cardStats?.total || 0 }} từ
                  </p>
                </div>
              </label>

              <!-- Create new deck button -->
              <button
                @click="showCreateDeckForm = true"
                class="w-full p-4 rounded-[1.25rem] font-semibold text-sm text-on-surface-variant hover:text-primary transition-all mt-3 flex items-center justify-center gap-2"
                style="border: 1px solid rgba(173, 179, 180, 0.2); background: rgba(199, 206, 207, 0.05);"
              >
                <span class="material-symbols-outlined text-lg">add</span>
                <span>Tạo bộ thẻ mới</span>
              </button>
            </div>
          </div>

          <!-- Create Deck Form -->
          <div v-else>
            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-6">Tạo bộ thẻ mới</p>
            <div class="space-y-5">
              <div>
                <label class="block text-sm font-semibold text-on-surface mb-2.5">Tên bộ thẻ</label>
                <input
                  v-model="newDeckName"
                  type="text"
                  placeholder="Nhập tên bộ thẻ..."
                  class="w-full px-4 py-3 rounded-[1.25rem] bg-surface-container-high text-on-surface placeholder:text-on-surface-variant/50 transition-all text-sm"
                  style="border: 1px solid rgba(173, 179, 180, 0.15);"
                  @focus="$event.target.style.borderColor = 'rgba(69, 97, 125, 0.2)'"
                  @blur="$event.target.style.borderColor = 'rgba(173, 179, 180, 0.15)'"
                />
              </div>
              <div>
                <label class="block text-sm font-semibold text-on-surface mb-2.5">Mô tả (tùy chọn)</label>
                <textarea
                  v-model="newDeckDescription"
                  placeholder="Nhập mô tả bộ thẻ..."
                  class="w-full px-4 py-3 rounded-[1.25rem] bg-surface-container-high text-on-surface placeholder:text-on-surface-variant/50 resize-none transition-all text-sm"
                  style="border: 1px solid rgba(173, 179, 180, 0.15);"
                  rows="3"
                  @focus="$event.target.style.borderColor = 'rgba(69, 97, 125, 0.2)'"
                  @blur="$event.target.style.borderColor = 'rgba(173, 179, 180, 0.15)'"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-3 pt-6">
            <button
              @click="closeModal"
              class="flex-1 py-3 px-4 rounded-full font-semibold text-sm text-on-surface-variant hover:text-on-surface transition-all"
              style="border: 1px solid rgba(173, 179, 180, 0.2); background: rgba(199, 206, 207, 0.03);"
            >
              {{ showCreateDeckForm ? 'Quay lại' : 'Hủy' }}
            </button>
            <button
              v-if="showCreateDeckForm"
              @click="createNewDeck"
              :disabled="!newDeckName.trim() || creatingDeck"
              class="flex-1 py-3 px-4 rounded-full font-semibold text-sm bg-gradient-to-br from-primary to-primary-container text-on-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 hover:shadow-lg"
            >
              <span v-if="creatingDeck" class="material-symbols-outlined animate-spin text-lg">progress_activity</span>
              <span>{{ creatingDeck ? 'Đang tạo...' : 'Tạo' }}</span>
            </button>
            <button
              v-else
              @click="addToFlashcard"
              :disabled="!selectedDeckId || addingFlashcard || decks.length === 0"
              class="flex-1 py-3 px-4 rounded-full font-semibold text-sm bg-gradient-to-br from-primary to-primary-container text-on-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 hover:shadow-lg"
            >
              <span v-if="addingFlashcard" class="material-symbols-outlined animate-spin text-lg">progress_activity</span>
              <span>{{ addingFlashcard ? 'Đang thêm...' : 'Thêm' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useTutorStore } from '@/stores/tutor'
import api from '@/services/api'

const route = useRoute()
const store = useTutorStore()

// ── Add to Flashcard Modal ────────────────────────────────────────────────
const showAddModal = ref(false)
const decks = ref([])
const selectedDeckId = ref(null)
const loadingDecks = ref(false)
const addingFlashcard = ref(false)
const addSuccess = ref(false)
const selectedEntry = ref(null)

// ── Create New Deck ───────────────────────────────────────────────────────
const showCreateDeckForm = ref(false)
const newDeckName = ref('')
const newDeckDescription = ref('')
const creatingDeck = ref(false)

function handleAddToFlashcardClick(v) {
  selectedEntry.value = {
    text: v.surface,
    reading: v.reading || '',
    meaningVn: v.meaning || '',
    explanationShort: 'Từ vựng mới từ phiên hội thoại AI Tutor'
  }
  loadDecks()
}

async function loadDecks() {
  if (decks.value.length > 0) {
    showAddModal.value = true
    return
  }

  loadingDecks.value = true
  try {
    const res = await api.get('/api/v1/decks')
    decks.value = res.data || []
    if (decks.value.length > 0) {
      selectedDeckId.value = decks.value[0].id
    }
  } catch (err) {
    console.error('Error loading decks:', err)
  } finally {
    loadingDecks.value = false
    showAddModal.value = true
  }
}

async function addToFlashcard() {
  if (!selectedDeckId.value || !selectedEntry.value) return

  addingFlashcard.value = true
  try {
    await api.post('/api/v1/flashcards', {
      deckId: selectedDeckId.value,
      frontText: selectedEntry.value.text,
      frontReading: selectedEntry.value.reading || '',
      backText: selectedEntry.value.meaningVn || '',
      backNotes: selectedEntry.value.explanationShort || '',
    })
    addSuccess.value = true
    setTimeout(() => {
      showAddModal.value = false
      addSuccess.value = false
    }, 2000)
  } catch (err) {
    console.error('Error adding flashcard:', err)
  } finally {
    addingFlashcard.value = false
  }
}

function closeModal() {
  showAddModal.value = false
  addSuccess.value = false
  showCreateDeckForm.value = false
  newDeckName.value = ''
  newDeckDescription.value = ''
}

async function createNewDeck() {
  if (!newDeckName.value.trim()) return

  creatingDeck.value = true
  try {
    const res = await api.post('/api/v1/decks', {
      name: newDeckName.value.trim(),
      description: newDeckDescription.value.trim(),
      isPublic: false,
    })
    const newDeck = res.data
    decks.value.push(newDeck)
    selectedDeckId.value = newDeck.id
    showCreateDeckForm.value = false
    newDeckName.value = ''
    newDeckDescription.value = ''
  } catch (err) {
    console.error('Error creating deck:', err)
  } finally {
    creatingDeck.value = false
  }
}

const loading = ref(true)
const error = ref(null)

const result = computed(() => store.result)

const corrections = computed(() => {
  const raw = result.value?.corrections
  if (!Array.isArray(raw)) return []
  return raw.filter(c => c && (c.original || c.corrected))
})

const newVocabulary = computed(() => {
  const raw = result.value?.newVocabulary
  if (!Array.isArray(raw)) return []
  return raw.filter(v => v && v.surface)
})

onMounted(async () => {
  try {
    const sessionId = route.query.sessionId || store.sessionId
    if (!sessionId) {
      error.value = 'Không tìm thấy thông tin phiên học.'
      return
    }
    await store.loadResult(sessionId)
    if (!store.result) {
      error.value = 'Không có kết quả cho phiên học này.'
    }
  } catch (e) {
    console.error(e)
    error.value = 'Không thể tải kết quả. Vui lòng thử lại.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.animate-spin { animation: spin 0.8s linear infinite; }

@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
.animate-pulse { animation: pulse 1.5s ease-in-out infinite; }

@keyframes slideUp { from { transform: translateY(1rem); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.animate-in { animation: slideUp 0.3s ease-out; }
</style>

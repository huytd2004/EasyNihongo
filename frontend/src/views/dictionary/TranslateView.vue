<template>
  <div class="w-full pt-6">
    <!-- Header / Title -->
    <div class="flex flex-col mb-8 px-2">
      <h1 class="text-3xl font-headline font-bold text-on-primary-fixed mb-2">Dịch thuật & Phân tích</h1>
      <p class="text-on-surface-variant">Dịch câu tiếng Nhật và phân tích cấu trúc ngữ pháp, từ vựng chi tiết bằng AI.</p>
    </div>

    <div class="space-y-10">
      <!-- Translation Interface -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
        <!-- Source Input -->
        <div class="space-y-4 h-full flex flex-col">
          <div class="flex items-center justify-between px-2">
            <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Văn bản nguồn (Tiếng Nhật)</label>
            <div class="flex items-center gap-2 text-primary cursor-pointer">
              <span class="text-xs font-medium">Tự động phát hiện</span>
              <span class="material-symbols-outlined text-sm">expand_more</span>
            </div>
          </div>
          <div class="bg-surface-container-lowest rounded-[2rem] p-8 shadow-sm transition-shadow hover:shadow-md border border-outline-variant/10 flex-1 flex flex-col min-h-[360px]">
            <textarea
              v-model="sourceText"
              class="w-full flex-1 bg-transparent border-none focus:ring-0 text-xl md:text-2xl font-medium leading-relaxed resize-none min-h-0 placeholder:text-outline/50 outline-none"
              placeholder="Nhập đoạn văn bản tiếng Nhật chuyên ngành cần dịch và phân tích vào đây..."
            ></textarea>
            <p v-if="quickError" class="text-sm text-error mt-3">{{ quickError }}</p>
            <div class="flex justify-between items-center pt-4 border-t border-outline-variant/10 mt-2">
              <button
                class="material-symbols-outlined p-2.5 rounded-full transition-colors flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed mt-4"
                :class="isSpeakingJa ? 'bg-primary text-on-primary animate-pulse' : 'bg-surface-container-highest text-on-surface-variant hover:bg-outline-variant/30'"
                :disabled="!sourceText.trim()"
                @click="speakText(sourceText, 'ja-JP')"
                title="Phát âm văn bản gốc (Tiếng Nhật)"
              >
                volume_up
              </button>
              <button
                class="bg-primary text-on-primary px-8 py-3 mt-4 rounded-full font-bold flex items-center gap-2 hover:opacity-90 transition-all hover:scale-[1.02] shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="isTranslating"
                @click="translateNow"
              >
                <span class="material-symbols-outlined">translate</span>
                {{ isTranslating ? 'Đang dịch...' : 'Dịch ngay' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Result Output -->
        <div class="space-y-4 h-full flex flex-col">
          <div class="flex items-center justify-between px-2">
            <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Bản dịch nhanh (Tiếng Việt)</label>
            <button
              class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!translatedText"
              @click="copyTranslation"
              :title="showCopyTooltip ? 'Đã sao chép!' : 'Sao chép bản dịch'"
            >
              {{ showCopyTooltip ? 'check' : 'content_copy' }}
            </button>
          </div>
          <div class="bg-surface-container-low rounded-[2rem] p-8 flex-1 min-h-[360px] flex flex-col justify-between border border-transparent">
            <p v-if="translatedText" class="flex-1 text-xl md:text-2xl font-medium leading-relaxed text-on-surface italic">
              {{ translatedText }}
            </p>
            <p v-else class="flex-1 text-lg md:text-xl font-medium leading-relaxed text-on-surface-variant italic">
              Bản dịch sẽ hiển thị ở đây sau khi bạn nhấn Dịch ngay.
            </p>
            <div class="flex items-center justify-between pt-6 mt-4 border-t border-outline-variant/10">
              <div class="flex items-center gap-4 mt-2 relative">
                <button
                  class="material-symbols-outlined p-2.5 rounded-full transition-colors flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                  :class="isSpeakingVi ? 'bg-primary text-on-primary animate-pulse' : 'bg-surface-container-highest text-on-surface-variant hover:bg-outline-variant/30'"
                  :disabled="!translatedText"
                  @click="speakText(translatedText, 'vi-VN')"
                  title="Phát âm bản dịch (Tiếng Việt)"
                >
                  volume_up
                </button>
                <button
                  class="material-symbols-outlined p-2.5 rounded-full transition-colors flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                  :class="showShareTooltip ? 'bg-green-600 text-white' : 'bg-surface-container-highest text-on-surface-variant hover:bg-outline-variant/30'"
                  :disabled="!translatedText"
                  @click="shareTranslation"
                  title="Chia sẻ bản dịch"
                >
                  {{ showShareTooltip ? 'check' : 'share' }}
                </button>
                <span v-if="showShareTooltip" class="absolute left-24 -top-8 bg-on-surface text-surface text-[10px] px-2 py-1 rounded whitespace-nowrap shadow-sm">
                  Đã copy link chia sẻ!
                </span>
              </div>
              <button
                class="mt-2 inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                :class="isDeepAnalysisEnabled ? 'bg-primary text-on-primary' : 'bg-surface-container-highest text-on-surface-variant hover:bg-outline-variant/20'"
                :disabled="isAnalyzing"
                @click="toggleDeepAnalysis"
              >
                <span class="material-symbols-outlined text-sm">auto_awesome</span>
                {{ isAnalyzing ? 'Đang phân tích...' : isDeepAnalysisEnabled ? 'Tắt phân tích chuyên sâu' : 'Phân tích chuyên sâu' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Deep Analysis Feature (Active State) -->
      <section class="space-y-8 border-t border-surface-container pt-12">
        <div class="flex flex-col gap-2">
          <h2 class="text-3xl font-bold text-on-primary-fixed leading-tight font-headline">Phân tích chuyên sâu</h2>
          <p class="text-on-surface-variant max-w-2xl">Cấu trúc ngữ pháp và từ vựng chi tiết dựa trên ngữ cảnh thực tế của câu.</p>
          <p v-if="analysisError" class="text-sm text-error">{{ analysisError }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
          <!-- Advanced Translation Card -->
          <div class="md:col-span-4 bg-surface-container-lowest rounded-[2rem] p-8 space-y-6 shadow-sm border border-outline-variant/10 h-fit">
            <div class="flex items-center gap-3 text-secondary">
              <span class="material-symbols-outlined">auto_awesome</span>
              <h3 class="font-bold">{{ deepAnalysis ? 'Bản dịch nâng cao' : 'Chờ phân tích' }}</h3>
            </div>
            <p class="text-sm leading-relaxed text-on-surface-variant">
              {{ analysisSummary }}
            </p>
            <div class="bg-secondary-container/20 p-4 rounded-xl">
              <p class="text-xs font-bold text-secondary uppercase tracking-tighter mb-2">Ghi chú ngữ cảnh</p>
              <p class="text-xs text-on-secondary-container">{{ analysisContext }}</p>
            </div>
          </div>

          <!-- Highlighted Breakdown -->
          <div class="md:col-span-8 bg-surface-container-low rounded-[3rem] p-10 relative overflow-hidden">
            <div class="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
            <div class="relative space-y-8">
              <div class="flex flex-wrap items-end gap-x-2 gap-y-6 text-3xl md:text-4xl font-light">
                <span v-if="!analysisTokens.length" class="text-on-surface-variant text-2xl md:text-3xl">Bật phân tích chuyên sâu để xem các token được chấm điểm từ graph.</span>
                <template v-else>
                  <div
                    v-for="item in analysisTokens"
                    :key="item.surface"
                    class="group relative px-2 py-1 bg-primary-container/40 rounded-lg cursor-default transition-all hover:bg-primary-container"
                  >
                    <span class="text-on-primary-container font-medium">{{ item.surface }}</span>
                    <div class="absolute -top-10 left-1/2 -translate-x-1/2 bg-on-surface text-surface text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                      {{ item.glossVi || '—' }}
                    </div>
                  </div>
                </template>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-6">
                <div
                  v-for="item in analysisCards"
                  :key="item.surface"
                  class="bg-surface-container-lowest p-5 rounded-2xl flex items-center justify-between group hover:scale-[1.02] transition-transform shadow-sm border border-transparent hover:border-outline-variant/10"
                >
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="text-lg font-bold text-on-surface">{{ item.token }}</span>
                      <span class="text-[10px] text-on-surface-variant font-medium bg-surface-container px-2 py-0.5 rounded">{{ item.badge }}</span>
                    </div>
                    <p class="text-xs text-on-surface-variant italic">{{ item.detail }}</p>
                    <p class="text-[10px] text-on-surface-variant">{{ item.extra }}</p>
                  </div>
                  <button
                    @click="handleAddToFlashcardClick(item)"
                    class="flex flex-col items-center gap-1 text-primary group-hover:text-primary-dim transition-colors"
                  >
                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">style</span>
                    <span class="text-[9px] font-bold uppercase">Tạo thẻ</span>
                  </button>
                </div>

                <div
                  v-if="!analysisCards.length"
                  class="border-2 border-dashed border-outline-variant/30 rounded-2xl flex items-center justify-center p-5 cursor-pointer hover:border-primary/50 hover:bg-surface-container-highest/30 transition-colors sm:col-span-2"
                >
                  <div class="flex items-center gap-3 text-on-surface-variant">
                    <span class="material-symbols-outlined">add_circle</span>
                    <span class="text-sm font-medium">Bật phân tích để nhận gợi ý từ GraphRAG</span>
                  </div>
                </div>
              </div>

              <!-- Notes section -->
              <div v-if="analysisNotes.length" class="pt-4 space-y-2">
                <p class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Ghi chú dịch thuật</p>
                <div
                  v-for="(note, i) in analysisNotes"
                  :key="i"
                  class="flex items-start gap-2 bg-surface-container-lowest rounded-xl px-4 py-3"
                >
                  <span class="material-symbols-outlined text-sm text-secondary mt-0.5">info</span>
                  <div>
                    <span class="text-xs font-bold text-secondary">{{ note.token }}</span>
                    <span class="text-xs text-on-surface-variant ml-2">{{ note.content }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Learning Context Suggestions -->
      <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-primary/5 p-8 rounded-[2rem] space-y-4 border border-primary/10 relative overflow-hidden">
          <div class="relative z-10">
            <span class="material-symbols-outlined text-primary text-3xl mb-2 block" style="font-variation-settings: 'FILL' 1;">lightbulb</span>
            <h4 class="font-bold text-on-primary-fixed text-lg">Mẹo ghi nhớ</h4>
            <p class="text-sm text-on-surface-variant leading-relaxed">Khi gặp các thuật ngữ Katakana dài như 'クラウドベース' (Cloud-based) hay 'ハートビート' (Heartbeat), hãy đối chiếu với Graph evidence để giữ tính đồng bộ cho toàn hệ thống.</p>
          </div>
        </div>

        <div class="bg-surface-container-low p-8 rounded-[2rem] space-y-4">
          <span class="material-symbols-outlined text-on-surface-variant text-3xl mb-2 block">history</span>
          <h4 class="font-bold text-on-surface text-lg">Bản dịch gần đây</h4>
          <div class="space-y-2 mt-4 max-h-[120px] overflow-y-auto pr-1">
            <template v-if="recentTranslations.length > 0">
              <div
                v-for="(text, idx) in recentTranslations"
                :key="idx"
                @click="loadRecentTranslation(text)"
                class="text-sm truncate text-on-surface-variant bg-surface-container-highest/50 hover:bg-outline-variant/20 hover:text-on-surface px-3 py-2 rounded-lg cursor-pointer transition-colors"
                :title="text"
              >
                {{ text }}
              </div>
            </template>
            <p v-else class="text-xs text-on-surface-variant italic">
              Chưa có lịch sử dịch gần đây.
            </p>
          </div>
        </div>

        <div class="bg-surface-container-highest p-8 rounded-[2rem] flex flex-col justify-between">
          <div class="space-y-2">
            <h4 class="font-bold text-on-surface text-lg">Sẵn sàng học chưa?</h4>
            <p class="text-sm text-on-surface-variant">Bắt đầu bài kiểm tra dựa trên các từ vựng vừa dịch.</p>
          </div>
          <button
            @click="router.push('/review')"
            class="mt-6 bg-on-surface text-surface py-3 rounded-full text-sm font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
          >
            <span class="material-symbols-outlined text-sm">school</span>
            Bắt đầu Test
          </button>
        </div>
      </section>
    </div>
  </div>

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
          <p class="text-3xl font-display font-bold text-on-surface mb-1">{{ selectedVocab?.token }}</p>
          <p class="text-sm text-on-surface-variant mb-3">{{ selectedVocab?.reading }}</p>
          <p class="text-sm text-on-surface leading-relaxed">{{ selectedVocab?.detail }}</p>
        </div>

        <!-- Deck selection -->
        <div v-if="!showCreateDeckForm">
          <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-4">Chọn bộ thẻ</p>
          <div v-if="decks.length === 0" class="p-8 text-center rounded-[1.75rem] bg-surface-container-low">
            <span class="material-symbols-outlined text-5xl text-on-surface-variant/30 mb-3 block">folder_open</span>
            <p class="text-on-surface-variant mb-6 font-medium">Bạn chưa có bộ thẻ nào</p>
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
                class="w-full px-4 py-3 rounded-[1.25rem] bg-surface-container-high text-on-surface placeholder:text-on-surface-variant/50 transition-all"
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
                class="w-full px-4 py-3 rounded-[1.25rem] bg-surface-container-high text-on-surface placeholder:text-on-surface-variant/50 resize-none transition-all"
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
</template>

<script setup>
import { computed, ref, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { translateService } from '@/services/translate'
import api from '@/services/api'

const recentTranslations = ref([])

const router = useRouter()

const sourceText = ref('')
const translatedText = ref('')
const isTranslating = ref(false)
const quickError = ref('')
const isDeepAnalysisEnabled = ref(false)
const isAnalyzing = ref(false)
const analysisError = ref('')
const deepAnalysis = ref(null)

const isSpeakingJa = ref(false)
const isSpeakingVi = ref(false)
const showCopyTooltip = ref(false)
const showShareTooltip = ref(false)

// ── Add to Flashcard Modal ────────────────────────────────────────────────
const showAddModal = ref(false)
const decks = ref([])
const selectedDeckId = ref(null)
const loadingDecks = ref(false)
const addingFlashcard = ref(false)
const addSuccess = ref(false)
const selectedVocab = ref(null)

// ── Create New Deck ───────────────────────────────────────────────────────
const showCreateDeckForm = ref(false)
const newDeckName = ref('')
const newDeckDescription = ref('')
const creatingDeck = ref(false)

const analysisTokens = computed(() => deepAnalysis.value?.keyVocabulary?.slice(0, 4) ?? [])

const analysisCards = computed(() => {
  const vocab = deepAnalysis.value?.keyVocabulary ?? []
  return vocab.map((item) => ({
    token:    item.surface || 'Unknown',
    badge:    item.domain || item.register || 'Graph',
    detail:   item.glossVi || '—',
    extra:    [
      item.reading ? `読み: ${item.reading}` : null,
      item.jlpt    ? `JLPT N${item.jlpt}` : null,
      item.register,
    ].filter(Boolean).join(' · '),
    surface:  item.surface,
    reading:  item.reading || '',
  }))
})

const analysisNotes = computed(() => deepAnalysis.value?.notes ?? [])

const topVocab = computed(() => analysisTokens.value[0] ?? null)

const analysisSummary = computed(() => {
  if (!isDeepAnalysisEnabled.value) {
    return 'Bật công tắc phân tích chuyên sâu để backend gọi python_pipeline và lấy evidence từ Neo4j.'
  }
  if (isAnalyzing.value) {
    return 'Đang truy vấn GraphRAG và dựng phân tích từ ngữ cảnh của câu...'
  }
  if (!deepAnalysis.value) {
    return 'Không lấy được evidence từ graph cho câu hiện tại.'
  }
  if (!topVocab.value) {
    return 'Bản dịch đã sẵn sàng nhưng chưa có từ vựng nào được highlight từ graph.'
  }
  const domains = (deepAnalysis.value.detectedDomains ?? []).join(', ') || 'general'
  return `Phát hiện domain: ${domains}. Token "${topVocab.value.surface}" → "${topVocab.value.glossVi || '?'}".`
})

const analysisContext = computed(() => {
  if (!isDeepAnalysisEnabled.value) return 'Chưa bật phân tích chuyên sâu.'
  if (isAnalyzing.value) return 'Đang lấy kết quả từ backend.'
  const kvCount = deepAnalysis.value?.keyVocabulary?.length ?? 0
  const noteCount = deepAnalysis.value?.notes?.length ?? 0
  const domains = (deepAnalysis.value?.detectedDomains ?? []).join(', ') || 'general'
  const modelUsed = deepAnalysis.value?.model || 'unknown'
  return `Domain: ${domains} · ${kvCount} từ vựng · ${noteCount} ghi chú · Model: ${modelUsed}`
})

async function translateNow() {
  if (!sourceText.value.trim()) {
    quickError.value = 'Vui lòng nhập câu tiếng Nhật cần dịch.'
    translatedText.value = ''
    return
  }

  isTranslating.value = true
  quickError.value = ''

  try {
    const res = await translateService.quick({
      text: sourceText.value,
      sourceLang: 'ja',
      targetLang: 'vi',
    })

    translatedText.value = cleanTranslationText(res.data?.translatedText ?? '')
    if (!translatedText.value) {
      quickError.value = 'Không nhận được nội dung bản dịch.'
    } else {
      addTranslationToHistory(sourceText.value)
    }

    if (isDeepAnalysisEnabled.value) {
      await fetchDeepAnalysis()
    }
  } catch (error) {
    quickError.value = error?.response?.data?.message || 'Không thể dịch lúc này, vui lòng thử lại.'
    translatedText.value = ''
  } finally {
    isTranslating.value = false
  }
}

async function fetchDeepAnalysis() {
  if (!sourceText.value.trim()) {
    analysisError.value = 'Vui lòng nhập câu tiếng Nhật trước khi phân tích.'
    deepAnalysis.value = null
    return
  }

  isAnalyzing.value = true
  analysisError.value = ''

  try {
    const res = await translateService.deep({
      text: sourceText.value,
      sourceLang: 'ja',
      targetLang: 'vi',
    })

    deepAnalysis.value = res.data ?? null
    if (!deepAnalysis.value) {
      analysisError.value = 'Không nhận được dữ liệu phân tích chuyên sâu.'
    } else if (deepAnalysis.value.translatedText) {
      translatedText.value = cleanTranslationText(deepAnalysis.value.translatedText)
    }
  } catch (error) {
    analysisError.value = error?.response?.data?.message || 'Không thể phân tích chuyên sâu lúc này, vui lòng thử lại.'
    deepAnalysis.value = null
  } finally {
    isAnalyzing.value = false
  }
}

async function toggleDeepAnalysis() {
  isDeepAnalysisEnabled.value = !isDeepAnalysisEnabled.value

  if (!isDeepAnalysisEnabled.value) {
    analysisError.value = ''
    deepAnalysis.value = null
    await translateNow()
    return
  }

  await fetchDeepAnalysis()
}

async function copyTranslation() {
  if (!translatedText.value) return

  try {
    await navigator.clipboard.writeText(translatedText.value)
    showCopyTooltip.value = true
    setTimeout(() => {
      showCopyTooltip.value = false
    }, 2000)
  } catch {
    quickError.value = 'Không thể sao chép bản dịch.'
  }
}

function speakText(text, lang = 'ja-JP') {
  if (!text || !window.speechSynthesis) return

  // If already speaking, toggle off/stop
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel()
    if (lang === 'ja-JP' && isSpeakingJa.value) {
      isSpeakingJa.value = false
      return
    }
    if (lang === 'vi-VN' && isSpeakingVi.value) {
      isSpeakingVi.value = false
      return
    }
  }

  isSpeakingJa.value = lang === 'ja-JP'
  isSpeakingVi.value = lang === 'vi-VN'

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = lang
  utterance.rate = lang === 'ja-JP' ? 0.85 : 1.0

  utterance.onend = () => {
    if (lang === 'ja-JP') isSpeakingJa.value = false
    if (lang === 'vi-VN') isSpeakingVi.value = false
  }

  utterance.onerror = () => {
    if (lang === 'ja-JP') isSpeakingJa.value = false
    if (lang === 'vi-VN') isSpeakingVi.value = false
  }

  window.speechSynthesis.speak(utterance)
}

async function shareTranslation() {
  if (!translatedText.value) return

  const shareData = {
    title: 'Bản dịch Tiếng Nhật - Antigravity',
    text: `Tiếng Nhật: ${sourceText.value}\nBản dịch: ${translatedText.value}`,
    url: window.location.href
  }

  try {
    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      await navigator.share(shareData)
    } else {
      const shareText = `[Bản dịch Nhật - Việt]\n🇯🇵 Tiếng Nhật: ${sourceText.value}\n🇻🇳 Bản dịch: ${translatedText.value}`
      await navigator.clipboard.writeText(shareText)
      showShareTooltip.value = true
      setTimeout(() => {
        showShareTooltip.value = false
      }, 2000)
    }
  } catch (err) {
    console.warn('Share failed or cancelled:', err)
  }
}

onBeforeUnmount(() => {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
})

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
    analysisError.value = 'Không thể tải danh sách bộ thẻ'
  } finally {
    loadingDecks.value = false
    showAddModal.value = true
  }
}

function handleAddToFlashcardClick(item) {
  selectedVocab.value = item
  loadDecks()
}

async function addToFlashcard() {
  if (!selectedDeckId.value || !selectedVocab.value) return

  addingFlashcard.value = true
  try {
    await api.post('/api/v1/flashcards', {
      deckId: selectedDeckId.value,
      frontText: selectedVocab.value.token,
      frontReading: selectedVocab.value.reading || '',
      backText: selectedVocab.value.detail,
      backNotes: selectedVocab.value.extra || '',
    })
    addSuccess.value = true
    setTimeout(() => {
      showAddModal.value = false
      addSuccess.value = false
      selectedVocab.value = null
    }, 2000)
  } catch (err) {
    console.error('Error adding flashcard:', err)
    analysisError.value = 'Không thể thêm vào flashcard. Vui lòng thử lại.'
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
  if (!newDeckName.value.trim()) {
    analysisError.value = 'Vui lòng nhập tên bộ thẻ'
    return
  }

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
    analysisError.value = 'Không thể tạo bộ thẻ. Vui lòng thử lại.'
  } finally {
    creatingDeck.value = false
  }
}

// ── Translation History (Local) ───────────────────────────────────────────
const MAX_HISTORY = 5

function loadHistory() {
  try {
    const data = localStorage.getItem('recent_translations')
    recentTranslations.value = data ? JSON.parse(data) : []
  } catch (e) {
    console.error('Failed to load history:', e)
    recentTranslations.value = []
  }
}

function saveHistory() {
  try {
    localStorage.setItem('recent_translations', JSON.stringify(recentTranslations.value))
  } catch (e) {
    console.error('Failed to save history:', e)
  }
}

function addTranslationToHistory(text) {
  const trimmed = text.trim()
  if (!trimmed) return

  recentTranslations.value = recentTranslations.value.filter(t => t !== trimmed)
  recentTranslations.value.unshift(trimmed)
  if (recentTranslations.value.length > MAX_HISTORY) {
    recentTranslations.value = recentTranslations.value.slice(0, MAX_HISTORY)
  }
  saveHistory()
}

function loadRecentTranslation(text) {
  sourceText.value = text
  translateNow()
}

function cleanTranslationText(text) {
  if (!text) return ''
  const trimmed = text.trim()
  if (trimmed.startsWith('{') && trimmed.includes('"translation"')) {
    try {
      const parsed = JSON.parse(trimmed)
      if (parsed && parsed.translation) {
        return parsed.translation
      }
    } catch (e) {
      const match = trimmed.match(/"translation"\s*:\s*"((?:[^"\\]|\\.)*)/)
      if (match) {
        return match[1].replace(/\\"/g, '"')
      }
    }
  }
  return text
}

onMounted(() => {
  loadHistory()
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

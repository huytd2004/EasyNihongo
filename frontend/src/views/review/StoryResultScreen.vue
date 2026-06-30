<template>
  <div class="max-w-2xl mx-auto w-full p-6 md:p-8 flex flex-col items-center gap-10 bg-surface">
    <!-- Score hero -->
    <div class="text-center">
      <div 
        class="w-32 h-32 mx-auto rounded-[2rem] flex flex-col items-center justify-center mb-8 ambient-shadow transition-transform hover:scale-105 duration-300"
        :class="scoreBgClass"
      >
        <span class="text-4xl md:text-5xl font-headline font-extrabold tracking-tight" :class="scoreTextClass">
          {{ storyScore }}
        </span>
        <span class="text-xs uppercase tracking-widest opacity-60 font-semibold" :class="scoreTextClass">
          trên {{ totalWithQuestion }}
        </span>
      </div>
      
      <h2 class="text-3xl font-headline font-extrabold text-on-surface mb-3 tracking-tight">
        {{ resultTitle }}
      </h2>
      <p class="text-on-surface-variant text-base leading-relaxed max-w-md mx-auto mb-6">
        {{ resultSubtitle }}
      </p>
      
      <div class="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-secondary/10 text-secondary font-semibold text-sm ambient-shadow">
        <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">auto_stories</span>
        <span>Hoàn thành {{ totalSegments }} đoạn · Đúng {{ Math.round(pct) }}%</span>
      </div>
    </div>

    <!-- Segment breakdown -->
    <div class="bg-surface-container-low rounded-[2rem] p-6 md:p-8 w-full mb-6 ambient-shadow">
      <h3 class="font-headline font-bold text-lg text-on-primary-fixed mb-6 flex items-center gap-3">
        <span class="material-symbols-outlined text-primary text-xl">analytics</span>
        Chi tiết từng đoạn
      </h3>
      
      <div class="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
        <div 
          v-for="(seg, idx) in segments" 
          :key="seg.id"
          class="bg-surface-container-lowest rounded-2xl p-5 flex items-start gap-4 transition-all hover:scale-[1.01] duration-200"
        >
          <!-- Status Icon -->
          <div 
            class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            :class="segResultClass(seg)"
          >
            <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1;">
              {{ segIcon(seg) }}
            </span>
          </div>
          
          <!-- Content -->
          <div class="flex-grow min-w-0">
            <div class="flex justify-between items-center mb-1">
              <span class="text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest">
                Đoạn {{ idx + 1 }} — {{ seg.dialogue_speaker || 'Narrator' }}
              </span>
              <span 
                v-if="seg.question"
                class="text-xs px-2 py-0.5 rounded-md font-semibold"
                :class="reviewStore.storyAnswers[seg.id] === seg.question.answer_index ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'"
              >
                {{ reviewStore.storyAnswers[seg.id] === seg.question.answer_index ? 'Đúng' : 'Sai' }}
              </span>
              <span v-else class="text-xs px-2 py-0.5 rounded-md bg-surface-container-high text-on-surface-variant font-semibold">
                Đọc hiểu
              </span>
            </div>
            
            <p class="text-base font-medium text-on-surface leading-relaxed mb-2">{{ seg.dialogue_ja }}</p>
            <p v-if="seg.question" class="text-xs text-on-surface-variant/80 italic">
              Câu hỏi: {{ seg.question.prompt_vn }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex flex-col sm:flex-row gap-4 w-full justify-center items-center">
      <!-- Về thiết lập -->
      <button 
        @click="$emit('exit')"
        class="w-full sm:w-auto px-8 py-4 rounded-full text-on-surface font-semibold hover:bg-surface-container-high transition-all flex items-center justify-center gap-2 cursor-pointer"
      >
        <span class="material-symbols-outlined text-lg">settings</span>
        Về thiết lập
      </button>
      
      <!-- Đọc lại (Sakura wood) -->
      <button 
        @click="$emit('restart')"
        class="w-full sm:w-auto px-8 py-4 rounded-full bg-secondary/10 text-secondary font-bold hover:bg-secondary/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
      >
        <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">replay</span>
        Đọc lại
      </button>
      
      <!-- Kết thúc (Primary with Signature Gradient on hover) -->
      <button 
        @click="$emit('finish')"
        class="w-full sm:w-auto px-8 py-4 rounded-full bg-primary text-on-primary font-bold hover:bg-gradient-to-br hover:from-primary hover:to-primary-container hover:text-on-primary-fixed transition-all duration-300 flex items-center justify-center gap-2 ambient-shadow cursor-pointer"
      >
        <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">done_all</span>
        Kết thúc
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useReviewStore } from '@/stores/review'

defineEmits(['exit', 'restart', 'finish'])

const reviewStore = useReviewStore()

const segments = computed(() => reviewStore.storyData?.segments || [])
const totalSegments = computed(() => segments.value.length)
const totalWithQuestion = computed(() => segments.value.filter(s => s.question).length)

const storyScore = computed(() => {
  let correct = 0
  for (const seg of segments.value) {
    if (!seg.question) continue
    if (reviewStore.storyAnswers[seg.id] === seg.question.answer_index) correct++
  }
  return correct
})

const pct = computed(() =>
  totalWithQuestion.value > 0
    ? (storyScore.value / totalWithQuestion.value) * 100
    : 100
)

const scoreBgClass = computed(() => {
  if (pct.value >= 80) return 'bg-gradient-to-br from-primary to-primary-container'
  if (pct.value >= 50) return 'bg-surface-container-high'
  return 'bg-secondary/10'
})

const scoreTextClass = computed(() => {
  if (pct.value >= 80) return 'text-on-primary-fixed font-bold'
  if (pct.value >= 50) return 'text-primary font-bold'
  return 'text-secondary font-bold'
})

const resultTitle = computed(() => {
  if (pct.value >= 90) return 'Xuất sắc! 🏆'
  if (pct.value >= 70) return 'Tốt lắm! 🎉'
  if (pct.value >= 50) return 'Khá tốt! 💪'
  return 'Cần luyện thêm 📖'
})

const resultSubtitle = computed(() => {
  if (pct.value >= 80) return 'Bạn hiểu câu chuyện rất tốt!'
  if (pct.value >= 50) return 'Hãy đọc lại các đoạn chưa nắm vững.'
  return 'Đừng nản, hãy thử lại nhé!'
})

function segResultClass(seg) {
  if (!seg.question) return 'bg-surface-container-high text-on-surface-variant'
  const ans = reviewStore.storyAnswers[seg.id]
  if (ans === seg.question.answer_index) return 'bg-primary/10 text-primary'
  if (ans !== undefined) return 'bg-secondary/10 text-secondary'
  return 'bg-surface-container-high text-on-surface-variant'
}

function segIcon(seg) {
  if (!seg.question) return 'book'
  const ans = reviewStore.storyAnswers[seg.id]
  if (ans === seg.question.answer_index) return 'check_circle'
  if (ans !== undefined) return 'cancel'
  return 'help_outline'
}
</script>

<style scoped>
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

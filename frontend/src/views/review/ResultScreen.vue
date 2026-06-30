<template>
  <div class="min-h-full flex flex-col items-center justify-center p-8 md:p-16 bg-surface">
    <!-- Score card -->
    <div class="max-w-2xl w-full">
      <!-- Hero score -->
      <div class="text-center mb-12">
        <div 
          class="w-32 h-32 mx-auto rounded-[2rem] flex flex-col items-center justify-center mb-8 ambient-shadow transition-transform hover:scale-105 duration-300"
          :class="scoreBgClass"
        >
          <span class="text-4xl md:text-5xl font-headline font-extrabold tracking-tight" :class="scoreTextClass">
            {{ reviewStore.score }}
          </span>
          <span class="text-xs uppercase tracking-widest opacity-60 font-semibold" :class="scoreTextClass">
            trên {{ reviewStore.totalQuestions }}
          </span>
        </div>
        
        <h2 class="text-3xl md:text-4xl font-headline font-extrabold text-on-surface mb-3 tracking-tight">
          {{ resultTitle }}
        </h2>
        <p class="text-on-surface-variant text-base leading-relaxed max-w-md mx-auto">
          {{ resultSubtitle }}
        </p>
        
        <div class="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary-container text-on-primary-container font-semibold text-sm ambient-shadow">
          <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
          <span>Chính xác {{ pct }}%</span>
        </div>
      </div>

      <!-- Answer breakdown -->
      <div class="bg-surface-container-low rounded-[2rem] p-6 md:p-8 mb-10 ambient-shadow">
        <h3 class="font-headline font-bold text-lg text-on-primary-fixed mb-6 flex items-center gap-3">
          <span class="material-symbols-outlined text-primary text-xl">analytics</span>
          Chi tiết từng câu
        </h3>
        
        <div class="space-y-4 max-h-[340px] overflow-y-auto pr-2 custom-scrollbar">
          <div
            v-for="(q, idx) in reviewStore.questions"
            :key="q.id"
            class="bg-surface-container-lowest rounded-2xl p-5 flex items-start gap-4 transition-all hover:scale-[1.01] duration-200"
          >
            <!-- Status icon -->
            <div 
              class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              :class="reviewStore.isCorrect(q.id) ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'"
            >
              <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1;">
                {{ reviewStore.isCorrect(q.id) ? 'check_circle' : 'cancel' }}
              </span>
            </div>
            
            <!-- Question info -->
            <div class="flex-grow min-w-0">
              <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest">Câu {{ idx + 1 }}</span>
                <span 
                  class="text-xs px-2 py-0.5 rounded-md font-semibold"
                  :class="reviewStore.isCorrect(q.id) ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'"
                >
                  {{ reviewStore.isCorrect(q.id) ? 'Đúng' : 'Sai' }}
                </span>
              </div>
              <p class="text-base font-medium text-on-surface leading-relaxed mb-3">{{ q.question_ja }}</p>
              
              <div class="flex flex-wrap gap-2 text-xs">
                <span class="px-3 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-medium">
                  Đúng: <strong class="text-on-surface">{{ q.answer }}</strong>
                </span>
                <span 
                  v-if="!reviewStore.isCorrect(q.id) && reviewStore.answers[q.id]"
                  class="px-3 py-1 rounded-full bg-secondary/10 text-secondary font-medium"
                >
                  Chọn: {{ reviewStore.answers[q.id] }}
                </span>
                <span 
                  v-else-if="!reviewStore.answers[q.id]"
                  class="px-3 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-medium"
                >
                  Chưa trả lời
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
        <!-- Về thiết lập (Tertiary styled but soft filled to make it highly clickable) -->
        <button
          @click="$emit('exit')"
          class="w-full sm:w-auto px-8 py-4 rounded-full text-on-surface font-semibold hover:bg-surface-container-high transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span class="material-symbols-outlined text-lg">settings</span>
          Về thiết lập
        </button>
        
        <!-- Luyện lại (Sakura wood) -->
        <button
          @click="$emit('restart')"
          class="w-full sm:w-auto px-8 py-4 rounded-full bg-secondary/10 text-secondary font-bold hover:bg-secondary/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">replay</span>
          Luyện lại
        </button>

        <!-- Kết thúc (Primary) -->
        <button
          @click="$emit('finish')"
          class="w-full sm:w-auto px-8 py-4 rounded-full bg-primary text-on-primary font-bold hover:bg-gradient-to-br hover:from-primary hover:to-primary-container hover:text-on-primary-fixed transition-all duration-300 flex items-center justify-center gap-2 ambient-shadow cursor-pointer"
        >
          <span class="material-symbols-outlined text-lg" style="font-variation-settings: 'FILL' 1;">done_all</span>
          Kết thúc
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useReviewStore } from '@/stores/review'

defineEmits(['exit', 'restart', 'finish'])

const reviewStore = useReviewStore()

const pct = computed(() => reviewStore.totalQuestions > 0
  ? Math.round((reviewStore.score / reviewStore.totalQuestions) * 100)
  : 0
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
  if (pct.value >= 90) return 'Bạn đã nắm vững từ vựng này rồi!'
  if (pct.value >= 70) return 'Tiếp tục ôn luyện để đạt kết quả tốt hơn.'
  if (pct.value >= 50) return 'Hãy xem lại các câu sai và thử lại nhé.'
  return 'Đừng nản, hãy luyện thêm nhé!'
})
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

<template>
  <header class="mb-12 text-center md:text-left">
    <h1 class="text-4xl font-extrabold text-on-surface tracking-tight mb-4">Tra cứu&nbsp;</h1>
    <div class="flex justify-center md:justify-start mb-8">
      <div class="bg-surface-container-high p-1 rounded-2xl flex gap-1">
        <RouterLink to="/dictionary" active-class="bg-surface-container-lowest text-primary shadow-sm" class="px-6 py-2.5 rounded-xl text-sm font-bold text-on-surface-variant hover:text-on-surface transition-colors">Từ vựng</RouterLink>
        <RouterLink to="/kanji" active-class="bg-surface-container-lowest text-primary shadow-sm" class="px-6 py-2.5 rounded-xl text-sm font-bold text-on-surface-variant hover:text-on-surface transition-colors">Kanji</RouterLink>
        <RouterLink to="/grammar" active-class="bg-surface-container-lowest text-primary shadow-sm" class="px-6 py-2.5 rounded-xl text-sm font-bold text-on-surface-variant hover:text-on-surface transition-colors">Ngữ pháp</RouterLink>
      </div>
    </div>
    
    <div class="relative max-w-2xl" ref="searchContainer">
      <div class="absolute inset-y-0 left-6 flex items-center pointer-events-none">
        <span class="material-symbols-outlined text-outline">search</span>
      </div>
      <input 
        class="w-full bg-surface-container-high border-none rounded-2xl py-5 px-6 pl-14 focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all text-lg placeholder:text-outline" 
        :placeholder="placeholder" 
        type="text" 
        v-model="searchQuery" 
        @input="onInput"
        @keyup.enter="handleSearch"
        @focus="showDropdown = true"
      >
      
      <!-- Extra tools for Kanji (draw, category) -->
      <div class="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2" v-if="showExtraTools">
        <button class="p-2 hover:bg-surface-container-highest rounded-lg transition-colors">
          <span class="material-symbols-outlined text-sm">draw</span>
        </button>
        <button class="p-2 hover:bg-surface-container-highest rounded-lg transition-colors">
          <span class="material-symbols-outlined text-sm">category</span>
        </button>
      </div>
      
      <!-- Search button for others -->
      <div class="absolute inset-y-2 right-2" v-else>
        <button class="h-full px-6 bg-primary text-white rounded-xl font-bold text-sm hover:opacity-90 transition-opacity" @click="handleSearch">Tìm kiếm</button>
      </div>

      <!-- Dropdown list -->
      <div 
        v-if="showDropdown && (results.length > 0 || loading)" 
        class="absolute left-0 right-0 top-full mt-2 bg-surface-container-lowest border border-outline-variant/30 rounded-2xl shadow-xl z-50 overflow-hidden max-h-60 overflow-y-auto"
      >
        <div v-if="loading" class="p-4 text-center text-sm text-on-surface-variant flex items-center justify-center gap-2">
          <span class="material-symbols-outlined animate-spin text-primary text-sm">progress_activity</span>
          <span>Đang tìm kiếm...</span>
        </div>
        <template v-else>
          <div 
            v-for="(item, idx) in results" 
            :key="item.id || idx"
            class="px-6 py-4 hover:bg-surface-container-low cursor-pointer transition-colors flex justify-between items-center border-b border-outline-variant/10 last:border-0"
            @click="selectResult(item)"
          >
            <div class="flex items-baseline gap-2 min-w-0">
              <span class="font-display text-base font-bold text-on-surface shrink-0">{{ item.text }}</span>
              <span v-if="item.reading" class="text-xs text-on-surface-variant truncate">({{ item.reading }})</span>
            </div>
            <span class="text-sm text-primary font-medium truncate ml-4 max-w-[50%]">{{ item.meaningVn }}</span>
          </div>
        </template>
      </div>
    </div>
    
    <div class="flex flex-wrap gap-2 mt-4 justify-center md:justify-start" v-if="suggestions.length > 0">
      <span class="text-xs text-on-surface-variant uppercase tracking-widest mr-2 py-1">Gợi ý:</span>
      <button 
        v-for="suggestion in suggestions" 
        :key="suggestion.label" 
        class="px-3 py-1 bg-surface-container-highest rounded-md text-xs font-medium text-on-tertiary-container hover:bg-primary-container transition-colors" 
        @click="selectSuggestion(suggestion.value)"
      >
        {{ suggestion.label }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Nhập từ khóa tìm kiếm...'
  },
  suggestions: {
    type: Array,
    default: () => []
  },
  showExtraTools: {
    type: Boolean,
    default: false
  },
  results: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  query: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['search', 'update:query', 'select-result'])

const searchQuery = ref(props.query)
const searchContainer = ref(null)
const showDropdown = ref(false)

watch(() => props.query, (newVal) => {
  searchQuery.value = newVal
})

const onInput = () => {
  emit('update:query', searchQuery.value)
  showDropdown.value = true
}

const selectResult = (item) => {
  searchQuery.value = item.text
  emit('select-result', item)
  showDropdown.value = false
}

const handleSearch = () => {
  if (props.results && props.results.length > 0) {
    selectResult(props.results[0])
  } else {
    if (searchQuery.value.trim()) {
      emit('search', searchQuery.value)
    }
  }
  showDropdown.value = false
}

const selectSuggestion = (value) => {
  searchQuery.value = value
  emit('update:query', value)
  emit('search', value)
  showDropdown.value = false
}

const handleClickOutside = (event) => {
  if (searchContainer.value && !searchContainer.value.contains(event.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.animate-spin { animation: spin 0.8s linear infinite; }
</style>

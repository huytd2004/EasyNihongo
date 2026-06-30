<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// ── User data từ auth store ──────────────────────────────
const user = computed(() => authStore.user || {})
const username = computed(() => user.value.username || '')
const targetLevel = computed(() => user.value.targetLevel || '—')

// Avatar: chữ cái đầu của username (viết hoa)
const avatarLetter = computed(() => {
  const name = username.value
  return name ? name.charAt(0).toUpperCase() : '?'
})

// ── Profile stats (streak) ───────────────────────────────
const streakCount = ref(0)
const loadingProfile = ref(true)

// ── Lỗi sai từ tutor sessions ───────────────────────────
const mistakes = ref([])
const loadingMistakes = ref(true)

// ── Lịch sử bài tập ─────────────────────────────────────
const history = ref([])
const loadingHistory = ref(true)

// ── Nhắc nhở học tập (Browser Notification 8h/ngày) ────────
const reminderEnabled = ref(false)
const reminderPermission = ref(Notification?.permission ?? 'default')
let reminderInterval = null

function loadReminderState() {
  reminderEnabled.value = localStorage.getItem('studyReminder') === 'true'
}

function scheduleReminderCheck() {
  clearInterval(reminderInterval)
  reminderInterval = setInterval(() => {
    if (!reminderEnabled.value) return
    const now = new Date()
    if (now.getHours() === 8 && now.getMinutes() === 0) {
      fireStudyNotification()
    }
  }, 60 * 1000) // kiểm tra mỗi phút
}

function fireStudyNotification() {
  if (Notification.permission !== 'granted') return
  const notif = new Notification('🌸 EasyNihongo — Giờ học rồi!', {
    body: 'Hôm nay bạn chưa học. Hãy dành 10 phút ôn tập để duy trì chuỗi học nhé! 🔥',
    icon: '/favicon.ico',
    tag: 'study-reminder',   // tag giúp không spam nhiều thông báo
    requireInteraction: false,
  })
  notif.onclick = () => {
    window.focus()
    notif.close()
  }
}

async function toggleReminder() {
  if (!('Notification' in window)) {
    alert('Trình duyệt của bạn không hỗ trợ thông báo.')
    return
  }

  if (reminderEnabled.value) {
    // Tắt nhắc nhở
    reminderEnabled.value = false
    localStorage.setItem('studyReminder', 'false')
    clearInterval(reminderInterval)
    return
  }

  // Bật nhắc nhở — xin quyền nếu chưa có
  if (Notification.permission === 'denied') {
    alert('Bạn đã chặn thông báo. Vui lòng mở lại quyền trong cài đặt trình duyệt.')
    return
  }

  if (Notification.permission !== 'granted') {
    const perm = await Notification.requestPermission()
    reminderPermission.value = perm
    if (perm !== 'granted') return
  }

  reminderEnabled.value = true
  localStorage.setItem('studyReminder', 'true')
  scheduleReminderCheck()

  // Gửi thông báo xác nhận ngay
  new Notification('✅ Nhắc nhở đã bật!', {
    body: 'Mỗi ngày lúc 8:00 sáng, EasyNihongo sẽ nhắc bạn học tập.',
    icon: '/favicon.ico',
    tag: 'study-reminder-confirm',
  })
}

async function fetchProfile() {
  try {
    const res = await api.get('/api/v1/users/me/profile')
    if (res.status === 'success') {
      streakCount.value = res.data.streakCount ?? 0
    }
  } catch (e) {
    console.warn('[ProfileView] fetchProfile failed', e)
  } finally {
    loadingProfile.value = false
  }
}

async function fetchMistakes() {
  try {
    const res = await api.get('/api/v1/users/me/mistakes?limit=4')
    if (res.status === 'success') {
      mistakes.value = res.data.mistakes || []
    }
  } catch (e) {
    console.warn('[ProfileView] fetchMistakes failed', e)
  } finally {
    loadingMistakes.value = false
  }
}

async function fetchHistory() {
  try {
    const res = await api.get('/api/v1/review/history?size=4')
    if (res.status === 'success') {
      history.value = res.data || []
    }
  } catch (e) {
    console.warn('[ProfileView] fetchHistory failed', e)
  } finally {
    loadingHistory.value = false
  }
}

// ── Thay đổi mục tiêu JLPT ─────────────────────────────
const JLPT_LEVELS = ['N5', 'N4', 'N3']
const showLevelModal = ref(false)
const selectedLevel = ref('')
const savingLevel = ref(false)
const levelSaveError = ref('')

function openLevelModal() {
  selectedLevel.value = targetLevel.value
  levelSaveError.value = ''
  showLevelModal.value = true
}

async function saveTargetLevel() {
  if (!selectedLevel.value || selectedLevel.value === targetLevel.value) {
    showLevelModal.value = false
    return
  }
  savingLevel.value = true
  levelSaveError.value = ''
  try {
    const res = await api.patch('/api/v1/users/me/target-level', { targetLevel: selectedLevel.value })
    if (res.status === 'success') {
      // Cập nhật store auth để toàn app phản ánh ngay
      await authStore.fetchMe()
      showLevelModal.value = false
    } else {
      levelSaveError.value = res.message || 'Cập nhật thất bại'
    }
  } catch (e) {
    levelSaveError.value = 'Lỗi kết nối, vui lòng thử lại'
  } finally {
    savingLevel.value = false
  }
}

// ── Chi tiết bài tập ──────────────────────────────────────
const showDetailModal = ref(false)
const loadingDetail = ref(false)
const selectedDetail = ref(null)

async function viewDetail(item) {
  loadingDetail.value = true
  selectedDetail.value = null
  showDetailModal.value = true
  try {
    const res = await api.get(`/api/v1/review/${item.type}/${item.id}`)
    if (res.status === 'success') {
      selectedDetail.value = res.data
    }
  } catch (err) {
    console.error('[ProfileView] fetch detail failed:', err)
  } finally {
    loadingDetail.value = false
  }
}

// ── Xem tất cả Lỗi sai ─────────────────────────────────────
const showAllMistakesModal = ref(false)
const loadingAllMistakes = ref(false)
const allMistakes = ref([])

async function openAllMistakesModal() {
  showAllMistakesModal.value = true
  loadingAllMistakes.value = true
  allMistakes.value = []
  try {
    const res = await api.get('/api/v1/users/me/mistakes?limit=50')
    if (res.status === 'success') {
      allMistakes.value = res.data.mistakes || []
    }
  } catch (e) {
    console.warn('[ProfileView] fetch all mistakes failed', e)
  } finally {
    loadingAllMistakes.value = false
  }
}

// ── Xem tất cả Lịch sử ────────────────────────────────────
const showAllHistoryModal = ref(false)
const loadingAllHistory = ref(false)
const allHistory = ref([])

async function openAllHistoryModal() {
  showAllHistoryModal.value = true
  loadingAllHistory.value = true
  allHistory.value = []
  try {
    const res = await api.get('/api/v1/review/history?size=50')
    if (res.status === 'success') {
      allHistory.value = res.data || []
    }
  } catch (e) {
    console.warn('[ProfileView] fetch all history failed', e)
  } finally {
    loadingAllHistory.value = false
  }
}


// Scroll đến hash anchor (ví dụ: #settings)
function scrollToHash(hash) {

  if (!hash) return
  const id = hash.replace('#', '')
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

onMounted(async () => {
  // Đảm bảo user đã được load
  if (!authStore.user) await authStore.fetchMe()
  fetchProfile()
  fetchMistakes()
  fetchHistory()
  // Khôi phục trạng thái reminder và bắt đầu interval nếu đang bật
  loadReminderState()
  if (reminderEnabled.value && Notification?.permission === 'granted') {
    scheduleReminderCheck()
  }
  // Scroll đến hash sau khi data đã fetch và DOM render xong
  if (route.hash) {
    await nextTick()
    setTimeout(() => scrollToHash(route.hash), 120)
  }
})

// Theo dõi hash thay đổi khi user đang ở trang profile rồi mới click settings
watch(() => route.hash, async (hash) => {
  if (hash) {
    await nextTick()
    scrollToHash(hash)
  }
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

// ── Tài khoản & Bảo mật: đổi mật khẩu ─────────────────
const showSecurityModal = ref(false)
const securityTab = ref('info') // 'info' | 'password'

// Change password form
const cpForm = ref({ current: '', newPass: '', confirm: '' })
const cpLoading = ref(false)
const cpError = ref('')
const cpSuccess = ref(false)

const cpNewPassError = computed(() => {
  if (!cpForm.value.newPass) return ''
  if (cpForm.value.newPass.length < 6) return 'Mật khẩu mới phải có ít nhất 6 ký tự'
  return ''
})

const cpConfirmError = computed(() => {
  if (!cpForm.value.confirm) return ''
  if (cpForm.value.confirm !== cpForm.value.newPass) return 'Mật khẩu xác nhận không khớp'
  return ''
})

const cpCanSubmit = computed(() =>
  cpForm.value.current &&
  cpForm.value.newPass &&
  !cpNewPassError.value &&
  !cpConfirmError.value
)

function openSecurityModal(tab = 'info') {
  securityTab.value = tab
  cpForm.value = { current: '', newPass: '', confirm: '' }
  cpError.value = ''
  cpSuccess.value = false
  showSecurityModal.value = true
}

async function submitChangePassword() {
  if (!cpCanSubmit.value) return
  cpLoading.value = true
  cpError.value = ''
  cpSuccess.value = false
  try {
    const res = await api.patch('/api/v1/users/me/change-password', {
      currentPassword: cpForm.value.current,
      newPassword: cpForm.value.newPass
    })
    if (res.status === 'success') {
      cpSuccess.value = true
      cpForm.value = { current: '', newPass: '', confirm: '' }
    } else {
      cpError.value = res.message || 'Đổi mật khẩu thất bại'
    }
  } catch (e) {
    cpError.value = e?.response?.data?.message || 'Lỗi kết nối, vui lòng thử lại'
  } finally {
    cpLoading.value = false
  }
}

// Helpers
function getMistakeCategory(m) {
  return m?.category || m?.type || 'Lỗi ngữ pháp'
}

function getMistakeText(m) {
  return m?.original || m?.user_said || m?.mistake || m?.text || '(không rõ)'
}

function getMistakeCorrected(m) {
  return m?.corrected || m?.correction || m?.correct || m?.fixed || ''
}

function getMistakeNote(m) {
  return m?.explanation || m?.note || m?.reason || ''
}

// Format ngày đơn giản
function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return `${d.getDate().toString().padStart(2,'0')}/${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getFullYear()}`
}

// Format ngày giờ đầy đủ
function formatDateTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return `${d.getDate().toString().padStart(2,'0')}/${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getFullYear()}`
}
</script>

<template>
  <div class="w-full max-w-screen-2xl pt-6">
    <!-- Profile Header Section -->
    <section class="flex flex-col md:flex-row items-start md:items-center justify-between gap-12 mb-16">
      <div class="flex items-center gap-8">
        <!-- Avatar từ chữ cái đầu username -->
        <div class="relative">
          <div
            class="w-32 h-32 md:w-40 md:h-40 rounded-full flex items-center justify-center ambient-shadow select-none"
            style="background: linear-gradient(135deg, var(--color-primary), var(--color-secondary, #7c3aed));"
          >
            <span
              class="font-display font-bold text-on-primary"
              style="font-size: 4rem; line-height: 1;"
            >{{ avatarLetter }}</span>
          </div>
        </div>

        <div>
          <h1 class="font-headline text-4xl md:text-5xl font-bold text-on-surface tracking-tight mb-2">
            {{ username || 'Người dùng' }}
          </h1>
          <div class="flex items-center gap-3">
            <span class="px-4 py-1.5 bg-primary-container text-on-primary-container rounded-full text-sm font-medium font-body flex items-center gap-2">
              <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">flag</span>
              Mục tiêu JLPT {{ targetLevel }}
            </span>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="flex gap-4 self-start md:self-center">
        <button class="px-6 py-3 bg-surface-container-low text-on-surface-variant font-medium rounded-full hover:bg-surface-variant transition-colors flex items-center gap-2">
          <span class="material-symbols-outlined text-lg">share</span>
          Chia sẻ
        </button>
      </div>
    </section>

    <!-- Stats Row: Target Level + Streak -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
      <!-- Target Level Card -->
      <div class="bg-surface-container-lowest rounded-xl p-8 ambient-shadow flex flex-col justify-between group overflow-hidden relative">
        <div class="absolute -right-8 -top-8 w-32 h-32 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
        <div class="relative z-10">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <div class="p-3 bg-primary-container text-on-primary-container rounded-full">
                <span class="material-symbols-outlined">star_rate</span>
              </div>
              <h3 class="font-headline text-lg font-semibold text-on-surface">Mục tiêu</h3>
            </div>
            <button
              @click="openLevelModal"
              class="text-xs font-semibold text-primary hover:bg-primary-container/40 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1"
            >
              <span class="material-symbols-outlined text-sm">edit</span>
              Thay đổi
            </button>
          </div>
          <div>
            <span class="font-display text-6xl font-bold text-primary">{{ targetLevel }}</span>
            <p class="text-sm text-on-surface-variant mt-2">Trình độ JLPT mục tiêu</p>
          </div>
        </div>
      </div>

      <!-- Streak Card -->
      <div class="bg-surface-container-lowest rounded-xl p-8 ambient-shadow relative overflow-hidden group">
        <div class="absolute top-0 right-0 w-32 h-32 bg-secondary-fixed-dim/20 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-700"></div>
        <div class="flex flex-col h-full relative z-10">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-3 bg-secondary-container text-on-secondary-container rounded-full">
              <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">local_fire_department</span>
            </div>
            <h3 class="font-headline text-lg font-semibold text-on-surface">Chuỗi học</h3>
          </div>
          <div class="mt-auto">
            <div v-if="loadingProfile" class="h-16 w-24 bg-surface-container rounded-xl animate-pulse"></div>
            <template v-else>
              <div class="flex items-baseline gap-2">
                <span class="font-display text-6xl font-bold text-secondary">{{ streakCount }}</span>
                <span class="text-on-surface-variant font-medium">ngày</span>
              </div>
              <p class="text-sm text-on-surface-variant mt-2 leading-relaxed">
                {{ streakCount > 0 ? 'Kỷ luật là sức mạnh của bạn.' : 'Hãy bắt đầu chuỗi học hôm nay!' }}
              </p>
            </template>
          </div>
        </div>
      </div>
    </section>

    <!-- Content Sections: Mistakes & History -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-20">
      <!-- Lỗi sai từ Tutor Sessions -->
      <section>
        <div class="flex items-center justify-between mb-8">
          <h2 class="font-headline text-2xl font-bold text-on-surface">Lỗi sai đã gặp</h2>
          <button
            v-if="mistakes.length > 3"
            @click="openAllMistakesModal"
            class="text-sm font-semibold text-primary hover:opacity-85 transition-opacity flex items-center gap-1"
          >
            Xem tất cả
            <span class="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingMistakes" class="space-y-4">
          <div v-for="n in 3" :key="n" class="bg-surface-container-lowest rounded-xl p-6 ambient-shadow">
            <div class="h-5 w-40 bg-surface-container rounded animate-pulse mb-3"></div>
            <div class="h-4 w-full bg-surface-container rounded animate-pulse"></div>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-else-if="mistakes.length === 0"
          class="bg-surface-container-lowest rounded-xl p-10 ambient-shadow flex flex-col items-center justify-center text-center gap-4"
        >
          <span class="material-symbols-outlined text-4xl text-on-surface-variant">sentiment_satisfied</span>
          <p class="text-on-surface-variant">Chưa có lỗi sai nào được ghi nhận từ các buổi luyện tập.</p>
        </div>

        <!-- Danh sách lỗi -->
        <div v-else class="space-y-4">
          <div
            v-for="(mistake, idx) in mistakes.slice(0, 3)"
            :key="idx"
            class="bg-surface-container-lowest rounded-xl p-6 ambient-shadow border-l-4 border-error/40 group hover:bg-surface-bright transition-colors"
          >
            <div class="flex justify-between items-start mb-3">
              <span class="px-2 py-1 bg-error-container/20 text-error text-[10px] uppercase font-bold rounded">
                {{ getMistakeCategory(mistake) }}
              </span>
            </div>
            <!-- Sai → Đúng -->
            <div class="flex items-center gap-3 flex-wrap mb-2">
              <span class="text-error font-bold font-display text-lg line-through opacity-80">
                {{ getMistakeText(mistake) }}
              </span>
              <span class="material-symbols-outlined text-on-surface-variant text-base">arrow_forward</span>
              <span class="text-primary font-bold font-display text-lg">
                {{ getMistakeCorrected(mistake) }}
              </span>
            </div>
            <!-- Giải thích -->
            <p v-if="getMistakeNote(mistake)" class="text-on-surface-variant text-sm leading-relaxed">
              {{ getMistakeNote(mistake) }}
            </p>
          </div>
        </div>
      </section>

      <!-- Lịch sử làm bài tập -->
      <section>
        <div class="flex items-center justify-between mb-8">
          <h2 class="font-headline text-2xl font-bold text-on-surface">Lịch sử làm bài tập</h2>
          <button
            v-if="history.length > 3"
            @click="openAllHistoryModal"
            class="text-sm font-semibold text-primary hover:opacity-85 transition-opacity flex items-center gap-1"
          >
            Xem tất cả
            <span class="material-symbols-outlined text-sm">chevron_right</span>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingHistory" class="bg-surface-container-lowest rounded-xl ambient-shadow overflow-hidden">
          <div v-for="n in 3" :key="n" class="flex gap-4 px-6 py-4 border-b border-outline-variant/10 last:border-0">
            <div class="flex-1 h-4 bg-surface-container rounded animate-pulse"></div>
            <div class="w-16 h-4 bg-surface-container rounded animate-pulse"></div>
            <div class="w-24 h-4 bg-surface-container rounded animate-pulse"></div>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-else-if="history.length === 0"
          class="bg-surface-container-lowest rounded-xl p-10 ambient-shadow flex flex-col items-center justify-center text-center gap-4"
        >
          <span class="material-symbols-outlined text-4xl text-on-surface-variant">history</span>
          <p class="text-on-surface-variant">Lịch sử bài tập sẽ xuất hiện tại đây sau khi hoàn thành quiz hoặc story.</p>
        </div>

        <!-- Table -->
        <div v-else class="bg-surface-container-lowest rounded-xl ambient-shadow overflow-hidden">
          <table class="w-full text-left">
            <thead class="bg-surface-container-low/50">
              <tr>
                <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Bài tập</th>
                <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Điểm số</th>
                <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Ngày</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant/10">
              <tr
                v-for="item in history.slice(0, 3)"
                :key="item.id"
                @click="viewDetail(item)"
                class="hover:bg-surface-bright transition-colors cursor-pointer"
              >
                <td class="px-6 py-4">
                  <div class="flex flex-col">
                    <span class="font-medium text-on-surface">{{ item.title }}</span>
                    <span class="text-xs text-on-surface-variant capitalize">{{ item.type === 'quiz' ? 'Trắc nghiệm' : 'Story' }} · {{ item.level }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span class="text-primary font-bold">{{ item.score }}/{{ item.totalQuestions }}</span>
                </td>
                <td class="px-6 py-4 text-sm text-on-surface-variant">{{ formatDate(item.createdAt) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- Preferences Section -->
    <section id="settings" class="max-w-3xl scroll-mt-24">
      <h2 class="font-headline text-2xl font-bold text-on-surface mb-8">Cài đặt &amp; Tùy chỉnh</h2>
      <div class="space-y-4">
        <!-- Notifications Toggle -->
        <div
          class="bg-surface-container-lowest rounded-xl p-6 ambient-shadow flex items-center justify-between group hover:bg-surface-bright transition-colors cursor-pointer"
          @click="toggleReminder"
        >
          <div class="flex items-center gap-6">
            <div
              class="p-4 rounded-full transition-colors"
              :class="reminderEnabled
                ? 'bg-primary-container text-on-primary-container'
                : 'bg-surface-container-low text-on-surface-variant group-hover:bg-primary-container group-hover:text-on-primary-container'"
            >
              <span class="material-symbols-outlined" :style="reminderEnabled ? 'font-variation-settings: \'FILL\' 1;' : ''">notifications_active</span>
            </div>
            <div>
              <h4 class="font-headline text-lg font-medium text-on-surface mb-1">Nhắc nhở học tập</h4>
              <p class="text-sm text-on-surface-variant leading-relaxed">
                <template v-if="reminderEnabled">
                  <span class="font-semibold" style="color:#45617d;">Đang bật</span> — 8:00 sáng mỗi ngày
                </template>
                <template v-else>
                  Nhận thông báo hàng ngày để duy trì chuỗi học.
                </template>
              </p>
            </div>
          </div>
          <!-- Toggle pill -->
          <div
            class="w-12 h-6 rounded-full relative flex-shrink-0 transition-colors duration-300"
            :style="reminderEnabled ? 'background:#45617d;' : 'background:#c5cacc;'"
          >
            <div
              class="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-300"
              :class="reminderEnabled ? 'right-1' : 'left-1'"
            ></div>
          </div>
        </div>

        <!-- Account Settings -->
        <div
          class="bg-surface-container-lowest rounded-xl p-6 ambient-shadow flex items-center justify-between group hover:bg-surface-bright transition-colors cursor-pointer mt-8"
          @click="openSecurityModal('info')"
        >
          <div class="flex items-center gap-6">
            <div class="p-4 bg-surface-container-low rounded-full text-on-surface-variant group-hover:bg-tertiary-container group-hover:text-on-tertiary-container transition-colors">
              <span class="material-symbols-outlined">manage_accounts</span>
            </div>
            <div>
              <h4 class="font-headline text-lg font-medium text-on-surface mb-1">Tài khoản &amp; Bảo mật</h4>
              <p class="text-sm text-on-surface-variant leading-relaxed">Quản lý email, mật khẩu và dữ liệu cá nhân.</p>
            </div>
          </div>
          <span class="material-symbols-outlined text-on-surface-variant group-hover:text-on-surface transition-colors">chevron_right</span>
        </div>
      </div>
    </section>

    <!-- Logout Action -->
    <div class="mt-16 mb-12 max-w-3xl flex justify-end">
      <button
        @click="handleLogout"
        class="px-6 py-3 text-secondary font-medium rounded-full hover:bg-secondary-container/50 transition-colors flex items-center gap-2"
      >
        <span class="material-symbols-outlined">logout</span>
        Đăng xuất
      </button>
    </div>

    <!-- Modal Tài khoản & Bảo mật -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showSecurityModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="showSecurityModal = false"
        >
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>

          <!-- Dialog -->
          <div class="relative z-10 bg-surface-container-lowest rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-8 pt-8 pb-0">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-tertiary-container text-on-tertiary-container rounded-xl">
                  <span class="material-symbols-outlined">manage_accounts</span>
                </div>
                <div>
                  <h3 class="font-headline text-xl font-bold text-on-surface">Tài khoản &amp; Bảo mật</h3>
                  <p class="text-sm text-on-surface-variant">Quản lý thông tin và bảo mật tài khoản</p>
                </div>
              </div>
              <button
                @click="showSecurityModal = false"
                class="p-2 rounded-full hover:bg-surface-container text-on-surface-variant transition-colors"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <!-- Tabs -->
            <div class="flex gap-1 px-8 mt-6 border-b border-outline-variant/20">
              <button
                @click="securityTab = 'info'; cpSuccess = false; cpError = ''"
                :class="[
                  'px-4 py-2.5 text-sm font-semibold rounded-t-lg transition-colors flex items-center gap-2 -mb-px border-b-2',
                  securityTab === 'info'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-on-surface-variant hover:text-on-surface'
                ]"
              >
                <span class="material-symbols-outlined text-base">person</span>
                Thông tin
              </button>
              <button
                @click="securityTab = 'password'; cpSuccess = false; cpError = ''"
                :class="[
                  'px-4 py-2.5 text-sm font-semibold rounded-t-lg transition-colors flex items-center gap-2 -mb-px border-b-2',
                  securityTab === 'password'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-on-surface-variant hover:text-on-surface'
                ]"
              >
                <span class="material-symbols-outlined text-base">lock</span>
                Đổi mật khẩu
              </button>
            </div>

            <!-- Tab: Thông tin tài khoản -->
            <div v-if="securityTab === 'info'" class="px-8 py-6 space-y-4">
              <!-- Username -->
              <div class="bg-surface-container-low rounded-xl p-4 flex items-center gap-4">
                <div class="p-2.5 bg-primary-container/50 text-on-primary-container rounded-lg">
                  <span class="material-symbols-outlined text-lg">badge</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-0.5">Tên người dùng</p>
                  <p class="text-on-surface font-medium truncate">{{ username || '—' }}</p>
                </div>
              </div>
              <!-- Email -->
              <div class="bg-surface-container-low rounded-xl p-4 flex items-center gap-4">
                <div class="p-2.5 bg-secondary-container/50 text-on-secondary-container rounded-lg">
                  <span class="material-symbols-outlined text-lg">email</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-0.5">Email</p>
                  <p class="text-on-surface font-medium truncate">{{ user.email || '—' }}</p>
                </div>
              </div>
              <!-- Role -->
              <div class="bg-surface-container-low rounded-xl p-4 flex items-center gap-4">
                <div class="p-2.5 bg-tertiary-container/50 text-on-tertiary-container rounded-lg">
                  <span class="material-symbols-outlined text-lg">verified_user</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-0.5">Loại tài khoản</p>
                  <p class="text-on-surface font-medium">{{ user.role === 'ADMIN' ? 'Quản trị viên' : 'Người dùng' }}</p>
                </div>
              </div>
              <!-- Joined date -->
              <div class="bg-surface-container-low rounded-xl p-4 flex items-center gap-4">
                <div class="p-2.5 bg-surface-container text-on-surface-variant rounded-lg">
                  <span class="material-symbols-outlined text-lg">calendar_today</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-0.5">Ngày tham gia</p>
                  <p class="text-on-surface font-medium">{{ formatDateTime(user.createdAt) }}</p>
                </div>
              </div>
              <!-- Shortcut to change password -->
              <button
                @click="securityTab = 'password'"
                class="w-full mt-2 py-3 rounded-xl border-2 border-dashed border-outline-variant/40 text-on-surface-variant hover:border-primary hover:text-primary transition-colors text-sm font-semibold flex items-center justify-center gap-2"
              >
                <span class="material-symbols-outlined text-base">lock_reset</span>
                Đổi mật khẩu
              </button>
            </div>

            <!-- Tab: Đổi mật khẩu -->
            <div v-else class="px-8 py-6">
              <!-- Success state -->
              <div v-if="cpSuccess" class="flex flex-col items-center gap-4 py-6 text-center">
                <div class="w-16 h-16 rounded-full bg-primary-container flex items-center justify-center">
                  <span class="material-symbols-outlined text-3xl text-on-primary-container" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <div>
                  <p class="font-headline text-lg font-bold text-on-surface mb-1">Đổi mật khẩu thành công!</p>
                  <p class="text-sm text-on-surface-variant">Mật khẩu của bạn đã được cập nhật.</p>
                </div>
                <button
                  @click="cpSuccess = false; cpForm = { current: '', newPass: '', confirm: '' }"
                  class="px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold hover:opacity-90 transition-opacity"
                >
                  Đổi lại
                </button>
              </div>

              <!-- Form -->
              <form v-else @submit.prevent="submitChangePassword" class="space-y-4">
                <!-- Current password -->
                <div>
                  <label class="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-1.5">Mật khẩu hiện tại</label>
                  <input
                    v-model="cpForm.current"
                    type="password"
                    placeholder="Nhập mật khẩu hiện tại"
                    autocomplete="current-password"
                    class="w-full px-4 py-3 bg-surface-container rounded-xl text-on-surface placeholder-on-surface-variant/50 border border-outline-variant/30 focus:outline-none focus:border-primary focus:bg-surface transition-colors"
                  />
                </div>

                <!-- New password -->
                <div>
                  <label class="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-1.5">Mật khẩu mới</label>
                  <input
                    v-model="cpForm.newPass"
                    type="password"
                    placeholder="Ít nhất 6 ký tự"
                    autocomplete="new-password"
                    :class="[
                      'w-full px-4 py-3 bg-surface-container rounded-xl text-on-surface placeholder-on-surface-variant/50 border focus:outline-none transition-colors',
                      cpNewPassError ? 'border-error focus:border-error' : 'border-outline-variant/30 focus:border-primary focus:bg-surface'
                    ]"
                  />
                  <p v-if="cpNewPassError" class="text-error text-xs mt-1 flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">error</span>
                    {{ cpNewPassError }}
                  </p>
                </div>

                <!-- Confirm password -->
                <div>
                  <label class="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-1.5">Xác nhận mật khẩu mới</label>
                  <input
                    v-model="cpForm.confirm"
                    type="password"
                    placeholder="Nhập lại mật khẩu mới"
                    autocomplete="new-password"
                    :class="[
                      'w-full px-4 py-3 bg-surface-container rounded-xl text-on-surface placeholder-on-surface-variant/50 border focus:outline-none transition-colors',
                      cpConfirmError ? 'border-error focus:border-error' : 'border-outline-variant/30 focus:border-primary focus:bg-surface'
                    ]"
                  />
                  <p v-if="cpConfirmError" class="text-error text-xs mt-1 flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">error</span>
                    {{ cpConfirmError }}
                  </p>
                </div>

                <!-- Server error -->
                <div v-if="cpError" class="flex items-center gap-2 p-3 bg-error-container/20 rounded-xl">
                  <span class="material-symbols-outlined text-error text-base">warning</span>
                  <p class="text-error text-sm">{{ cpError }}</p>
                </div>

                <!-- Actions -->
                <div class="flex gap-3 justify-end pt-2">
                  <button
                    type="button"
                    @click="showSecurityModal = false"
                    class="px-5 py-2.5 rounded-full text-on-surface-variant font-medium hover:bg-surface-container transition-colors"
                  >
                    Huỷ
                  </button>
                  <button
                    type="submit"
                    :disabled="cpLoading || !cpCanSubmit"
                    class="px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
                  >
                    <span v-if="cpLoading" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                    Xác nhận
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal Xem tất cả lỗi sai đã gặp -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showAllMistakesModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="showAllMistakesModal = false"
        >
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/45 backdrop-blur-[6px]"></div>

          <!-- Dialog content -->
          <div
            class="relative z-10 bg-surface-container-lowest rounded-[2rem] w-full max-w-xl max-h-[80vh] flex flex-col overflow-hidden"
            style="
              box-shadow: 0 12px 48px rgba(45, 52, 53, 0.12), 0 2px 16px rgba(45, 52, 53, 0.06);
              font-family: 'Inter', sans-serif;
            "
          >
            <!-- Header -->
            <div class="px-8 pt-8 pb-4 flex items-center justify-between shrink-0">
              <div>
                <h3
                  class="font-bold text-on-surface"
                  style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.35rem;"
                >
                  Tất cả lỗi sai đã gặp
                </h3>
                <p class="text-xs text-on-surface-variant mt-1">
                  Tổng hợp các lỗi sai từ các buổi Tutor Chat của bạn
                </p>
              </div>
              <button
                @click="showAllMistakesModal = false"
                class="p-2 -mr-2 -mt-2 rounded-full transition-colors hover:bg-black/5 text-on-surface-variant/70"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-grow overflow-y-auto px-8 pb-8">
              <div v-if="loadingAllMistakes" class="py-20 flex flex-col items-center justify-center gap-4">
                <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
                <p class="text-sm text-on-surface-variant">Đang tải danh sách lỗi sai...</p>
              </div>
              <div v-else-if="allMistakes.length === 0" class="py-20 text-center text-on-surface-variant">
                Chưa có lỗi sai nào được ghi nhận.
              </div>
              <div v-else class="space-y-4">
                <div
                  v-for="(mistake, idx) in allMistakes"
                  :key="idx"
                  class="bg-surface-container-low rounded-xl p-5 border-l-4 border-error/40 hover:bg-surface-bright transition-colors"
                >
                  <div class="flex justify-between items-start mb-2">
                    <span class="px-2 py-0.5 bg-error-container/20 text-error text-[10px] uppercase font-bold rounded">
                      {{ getMistakeCategory(mistake) }}
                    </span>
                  </div>
                  <!-- Sai → Đúng -->
                  <div class="flex items-center gap-3 flex-wrap mb-1.5">
                    <span class="text-error font-bold font-display text-base line-through opacity-85">
                      {{ getMistakeText(mistake) }}
                    </span>
                    <span class="material-symbols-outlined text-on-surface-variant text-sm">arrow_forward</span>
                    <span class="text-primary font-bold font-display text-base">
                      {{ getMistakeCorrected(mistake) }}
                    </span>
                  </div>
                  <!-- Giải thích -->
                  <p v-if="getMistakeNote(mistake)" class="text-on-surface-variant text-xs leading-relaxed">
                    {{ getMistakeNote(mistake) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal Xem tất cả lịch sử làm bài tập -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showAllHistoryModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="showAllHistoryModal = false"
        >
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/45 backdrop-blur-[6px]"></div>

          <!-- Dialog content -->
          <div
            class="relative z-10 bg-surface-container-lowest rounded-[2rem] w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden"
            style="
              box-shadow: 0 12px 48px rgba(45, 52, 53, 0.12), 0 2px 16px rgba(45, 52, 53, 0.06);
              font-family: 'Inter', sans-serif;
            "
          >
            <!-- Header -->
            <div class="px-8 pt-8 pb-4 flex items-center justify-between shrink-0">
              <div>
                <h3
                  class="font-bold text-on-surface"
                  style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.35rem;"
                >
                  Tất cả lịch sử làm bài tập
                </h3>
                <p class="text-xs text-on-surface-variant mt-1">
                  Bấm vào bài tập bất kỳ để xem chi tiết đáp án
                </p>
              </div>
              <button
                @click="showAllHistoryModal = false"
                class="p-2 -mr-2 -mt-2 rounded-full transition-colors hover:bg-black/5 text-on-surface-variant/70"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-grow overflow-y-auto px-8 pb-8">
              <div v-if="loadingAllHistory" class="py-20 flex flex-col items-center justify-center gap-4">
                <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
                <p class="text-sm text-on-surface-variant">Đang tải lịch sử bài tập...</p>
              </div>
              <div v-else-if="allHistory.length === 0" class="py-20 text-center text-on-surface-variant">
                Chưa làm bài tập nào.
              </div>
              <div v-else class="bg-surface-container-low rounded-2xl overflow-hidden shadow-sm">
                <table class="w-full text-left text-sm">
                  <thead class="bg-surface-container-high/60 border-b border-outline-variant/10">
                    <tr>
                      <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Bài tập</th>
                      <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Điểm số</th>
                      <th class="px-6 py-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Ngày làm</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-outline-variant/10">
                    <tr
                      v-for="item in allHistory"
                      :key="item.id"
                      @click="showAllHistoryModal = false; viewDetail(item)"
                      class="hover:bg-surface-bright transition-colors cursor-pointer"
                    >
                      <td class="px-6 py-4">
                        <div class="flex flex-col">
                          <span class="font-semibold text-on-surface text-sm">{{ item.title }}</span>
                          <span class="text-xs text-on-surface-variant capitalize mt-0.5">
                            {{ item.type === 'quiz' ? 'Trắc nghiệm' : 'Story' }} · {{ item.level }}
                          </span>
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <span class="text-primary font-bold">{{ item.score }}/{{ item.totalQuestions }}</span>
                      </td>
                      <td class="px-6 py-4 text-xs text-on-surface-variant">{{ formatDate(item.createdAt) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal chi tiết bài tập (The Meditative Canvas style) -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showDetailModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="showDetailModal = false"
        >
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/45 backdrop-blur-[6px]"></div>

          <!-- Dialog content -->
          <div
            class="relative z-10 bg-surface-container-lowest rounded-[2rem] w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden"
            style="
              box-shadow: 0 12px 48px rgba(45, 52, 53, 0.12), 0 2px 16px rgba(45, 52, 53, 0.06);
              font-family: 'Inter', sans-serif;
            "
          >
            <!-- Header section (Tonal Layer or subtle background, no border) -->
            <div class="px-8 pt-8 pb-6 flex items-start justify-between relative shrink-0">
              <div class="min-w-0 flex-1">
                <span class="inline-block px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase mb-2"
                  :style="selectedDetail?.type === 'quiz' ? 'background:#eef3f8; color:#45617d;' : 'background:#f5e8e8; color:#7c5556;'"
                >
                  {{ selectedDetail?.type === 'quiz' ? 'Trắc nghiệm' : 'Story' }} · {{ selectedDetail?.level }}
                </span>
                <h3
                  class="font-bold text-on-surface leading-tight truncate pr-4"
                  style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.35rem;"
                >
                  {{ selectedDetail?.title || 'Đang tải chi tiết...' }}
                </h3>
                <p class="text-xs text-on-surface-variant mt-1.5" v-if="selectedDetail">
                  Hoàn thành lúc: {{ formatDate(selectedDetail.createdAt) }}
                </p>
              </div>

              <!-- Score Badge -->
              <div
                v-if="selectedDetail"
                class="flex flex-col items-center justify-center px-4 py-2 rounded-2xl shrink-0"
                style="background: #f2f4f4;"
              >
                <span class="text-xs text-on-surface-variant font-medium">Kết quả</span>
                <span class="text-xl font-black" style="color:#45617d; font-family:'Plus Jakarta Sans',sans-serif;">
                  {{ selectedDetail.score }}/{{ selectedDetail.totalQuestions }}
                </span>
              </div>

              <button
                @click="showDetailModal = false"
                class="p-2 -mr-2 -mt-2 rounded-full transition-colors hover:bg-black/5 text-on-surface-variant/70 hover:text-on-surface ml-4"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <!-- Scrollable Content area -->
            <div class="flex-grow overflow-y-auto px-8 pb-8">
              <!-- Loading spinner -->
              <div v-if="loadingDetail || !selectedDetail" class="py-20 flex flex-col items-center justify-center gap-4">
                <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
                <p class="text-sm text-on-surface-variant">Đang tải chi tiết bài làm...</p>
              </div>

              <div v-else class="space-y-6">
                <!-- ── QUIZ DETAIL VIEW ── -->
                <div v-if="selectedDetail.type === 'quiz'" class="space-y-6">
                  <div
                    v-for="(q, idx) in selectedDetail.questionsData"
                    :key="q.id || idx"
                    class="bg-surface-container-low rounded-2xl p-6 flex flex-col gap-4"
                  >
                    <!-- Question tag -->
                    <div class="flex items-center justify-between">
                      <span class="text-xs font-bold text-primary-dim uppercase tracking-wider">Câu {{ idx + 1 }}</span>
                      <span
                        class="flex items-center gap-1 text-xs font-bold"
                        :style="q.is_correct ? 'color:#2e7d32;' : 'color:#c62828;'"
                      >
                        <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">
                          {{ q.is_correct ? 'check_circle' : 'cancel' }}
                        </span>
                        {{ q.is_correct ? 'Chính xác' : 'Sai' }}
                      </span>
                    </div>

                    <!-- Question Japanese sentence -->
                    <p
                      class="text-lg font-headline font-semibold text-on-surface leading-loose"
                      style="letter-spacing:0.02em;"
                    >
                      {{ q.question_ja }}
                    </p>
                    <p class="text-xs text-on-surface-variant italic opacity-85 mt-0.5">
                      Ý nghĩa: {{ q.question_vn }}
                    </p>

                    <!-- Choices List -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                      <div
                        v-for="choice in q.choices"
                        :key="choice"
                        class="flex items-center gap-3 px-4 py-3 rounded-xl border text-sm"
                        :style="
                          choice === q.answer
                            ? 'background:#e8f5e9; border-color:#a5d6a7; color:#2e7d32; font-weight:600;'
                            : choice === q.user_answer && !q.is_correct
                              ? 'background:#ffebee; border-color:#ef9a9a; color:#c62828; font-weight:600;'
                              : 'background:#ffffff; border-color:#e4e9ea; color:#5a6061;'
                        "
                      >
                        <span
                          class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                          :style="
                            choice === q.answer
                              ? 'background:#2e7d32; color:#fff;'
                              : choice === q.user_answer && !q.is_correct
                                ? 'background:#c62828; color:#fff;'
                                : 'background:#f2f4f4; color:#5a6061;'
                          "
                        >
                          ✓
                        </span>
                        <span>{{ choice }}</span>
                      </div>
                    </div>

                    <!-- Explanation -->
                    <div
                      v-if="q.explanation_vn"
                      class="mt-2 p-4 bg-white/60 rounded-xl text-xs text-on-surface-variant leading-relaxed border-l-2"
                      :style="q.is_correct ? 'border-color:#2e7d32;' : 'border-color:#c62828;'"
                    >
                      <strong class="block mb-1">Giải thích:</strong>
                      {{ q.explanation_vn }}
                    </div>
                  </div>
                </div>

                <!-- ── STORY DETAIL VIEW ── -->
                <div v-else-if="selectedDetail.type === 'story'" class="space-y-8">
                  <!-- Story segments timeline -->
                  <div
                    v-for="(seg, idx) in selectedDetail.questionsData?.segments"
                    :key="seg.id || idx"
                    class="bg-surface-container-low rounded-2xl p-6 flex flex-col gap-4 relative overflow-hidden"
                  >
                    <!-- Header of Segment -->
                    <div class="flex items-center justify-between border-b border-outline-variant/10 pb-3 shrink-0">
                      <span class="text-xs font-bold text-[#7c5556] uppercase tracking-wider">Đoạn {{ idx + 1 }}</span>
                      <span
                        v-if="seg.question"
                        class="flex items-center gap-1 text-xs font-bold"
                        :style="selectedDetail.answersData?.[seg.id] === seg.question.answer_index ? 'color:#2e7d32;' : 'color:#c62828;'"
                      >
                        <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">
                          {{ selectedDetail.answersData?.[seg.id] === seg.question.answer_index ? 'check_circle' : 'cancel' }}
                        </span>
                        {{ selectedDetail.answersData?.[seg.id] === seg.question.answer_index ? 'Đúng' : 'Sai' }}
                      </span>
                    </div>

                    <!-- Scene Description (narration) -->
                    <p class="text-sm text-on-surface leading-relaxed italic bg-white/40 p-4 rounded-xl">
                      {{ seg.scene_vn }}
                    </p>

                    <!-- Speaker Dialogue -->
                    <div class="flex flex-col gap-1 pl-4 border-l-2 border-primary/20">
                      <span class="text-xs font-bold text-primary uppercase tracking-wider" v-if="seg.dialogue_speaker">
                        {{ seg.dialogue_speaker }}
                      </span>
                      <p class="text-base font-headline font-semibold text-on-surface leading-loose">
                        「{{ seg.dialogue_ja }}」
                      </p>
                      <p class="text-xs text-on-surface-variant italic" v-if="seg.dialogue_vn">
                        ({{ seg.dialogue_vn }})
                      </p>
                    </div>

                    <!-- Highlighted vocabulary -->
                    <div v-if="seg.highlighted_words?.length" class="flex flex-wrap gap-1.5 mt-1">
                      <span
                        v-for="hw in seg.highlighted_words"
                        :key="hw.word"
                        class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] bg-white border border-[#45617d]/10 text-on-surface-variant"
                      >
                        <strong class="text-primary">{{ hw.word }}</strong>
                        <span class="opacity-60">({{ hw.reading }})</span>
                        <span class="opacity-40">—</span>
                        <span>{{ hw.meaning }}</span>
                      </span>
                    </div>

                    <!-- Question inside Segment (if present) -->
                    <div v-if="seg.question" class="mt-2 bg-white/50 p-4 rounded-xl flex flex-col gap-3">
                      <p class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Câu hỏi tương tác:</p>
                      
                      <!-- Choices -->
                      <div class="grid grid-cols-1 gap-2">
                        <div
                          v-for="(choice, cIdx) in seg.question.choices"
                          :key="cIdx"
                          class="flex items-center gap-3 px-4 py-2.5 rounded-xl border text-xs"
                          :style="
                            cIdx === seg.question.answer_index
                              ? 'background:#e8f5e9; border-color:#a5d6a7; color:#2e7d32; font-weight:600;'
                              : cIdx === selectedDetail.answersData?.[seg.id]
                                ? 'background:#ffebee; border-color:#ef9a9a; color:#c62828; font-weight:600;'
                                : 'background:#ffffff; border-color:#e4e9ea; color:#5a6061;'
                          "
                        >
                          <span
                            class="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
                            :style="
                              cIdx === seg.question.answer_index
                                ? 'background:#2e7d32; color:#fff;'
                                : cIdx === selectedDetail.answersData?.[seg.id]
                                  ? 'background:#c62828; color:#fff;'
                                  : 'background:#f2f4f4; color:#5a6061;'
                            "
                          >
                            {{ String.fromCharCode(65 + cIdx) }}
                          </span>
                          <div>
                            <span class="font-semibold">{{ choice.ja }}</span>
                            <span class="block opacity-65 mt-0.5">{{ choice.vn }}</span>
                          </div>
                        </div>
                      </div>

                      <!-- Explanation -->
                      <p v-if="seg.question.explanation_vn" class="text-xs text-on-surface-variant mt-1 leading-relaxed">
                        <strong>Giải nghĩa câu hỏi:</strong> {{ seg.question.explanation_vn }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal thay đổi mục tiêu JLPT -->

    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showLevelModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="showLevelModal = false"
        >
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>

          <!-- Dialog -->
          <div class="relative z-10 bg-surface-container-lowest rounded-2xl shadow-2xl w-full max-w-sm p-8 flex flex-col gap-6">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-primary-container text-on-primary-container rounded-xl">
                <span class="material-symbols-outlined">flag</span>
              </div>
              <div>
                <h3 class="font-headline text-xl font-bold text-on-surface">Thay đổi mục tiêu</h3>
                <p class="text-sm text-on-surface-variant">Chọn cấp độ JLPT bạn muốn đạt được</p>
              </div>
            </div>

            <!-- Level Buttons -->
            <div class="grid grid-cols-3 gap-3">
              <button
                v-for="level in JLPT_LEVELS"
                :key="level"
                @click="selectedLevel = level"
                :class="[
                  'py-4 rounded-xl font-display text-2xl font-bold border-2 transition-all',
                  selectedLevel === level
                    ? 'bg-primary text-on-primary border-primary shadow-lg scale-105'
                    : 'bg-surface-container text-on-surface-variant border-outline-variant hover:border-primary hover:text-primary'
                ]"
              >
                {{ level }}
              </button>
            </div>

            <!-- Error -->
            <p v-if="levelSaveError" class="text-error text-sm text-center">{{ levelSaveError }}</p>

            <!-- Actions -->
            <div class="flex gap-3 justify-end">
              <button
                @click="showLevelModal = false"
                class="px-5 py-2.5 rounded-full text-on-surface-variant font-medium hover:bg-surface-container transition-colors"
              >
                Huỷ
              </button>
              <button
                @click="saveTargetLevel"
                :disabled="savingLevel || !selectedLevel"
                class="px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
              >
                <span v-if="savingLevel" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                Lưu
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.fade-enter-active .relative.z-10,
.fade-leave-active .relative.z-10 {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.fade-enter-from .relative.z-10,
.fade-leave-to .relative.z-10 {
  transform: scale(0.95);
  opacity: 0;
}
</style>

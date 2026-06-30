<template>
  <div class="bg-background text-on-surface min-h-screen flex flex-col">
    <!-- TopNavBar -->
    <header class="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl flex justify-end items-center px-8 gap-4 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] font-['Plus_Jakarta_Sans'] text-sm tracking-wide hidden md:flex">
      <div class="flex items-center gap-4">

        <!-- ── Nút Thông báo (Streak) ───────────────────────── -->
        <div class="relative" ref="notifRef">
          <button
            @click="toggleNotif"
            class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2 transition-all opacity-80 hover:opacity-100 relative"
            title="Thông báo"
          >
            <span class="material-symbols-outlined text-slate-700 dark:text-slate-300">notifications</span>
            <!-- Badge dot — Sakura tone -->
            <span
              v-if="streakCount > 0"
              class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full ring-2 ring-white dark:ring-slate-950"
              style="background-color:#7c5556;"
            ></span>
          </button>

          <!-- Glassmorphic Notification Panel — The Meditative Canvas -->
          <Transition name="notif-drop">
            <div
              v-if="showNotif"
              class="absolute right-0 top-full mt-3 w-[22rem] rounded-2xl overflow-hidden z-50"
              style="
                background: rgba(249,249,249,0.9);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                box-shadow: 0 8px 40px rgba(45,52,53,0.09), 0 2px 12px rgba(45,52,53,0.04);
              "
            >
              <!-- Header — whitespace creates separation, no border -->
              <div class="px-6 pt-6 pb-0 flex items-start justify-between">
                <div>
                  <h3 style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1rem;font-weight:700;color:#2d3435;line-height:1.25;">Thông báo</h3>
                  <p class="mt-0.5" style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#5a6061;">Hôm nay</p>
                </div>
                <button
                  @click="showNotif = false"
                  class="p-1.5 rounded-full transition-colors hover:bg-black/5"
                  style="color:#adb3b4;"
                >
                  <span class="material-symbols-outlined" style="font-size:1.1rem;">close</span>
                </button>
              </div>

              <!-- Streak Hero — Sakura gradient per design.md secondary tones -->
              <div
                class="mx-4 mt-4 rounded-xl overflow-hidden relative"
                style="padding:1.25rem 1.5rem;background:linear-gradient(135deg,#7c5556 0%,#a07070 60%,#c49090 100%);"
              >
                <!-- Ambient light blobs — large blur, diffused -->
                <div class="absolute" style="right:-20px;top:-20px;width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,0.12);"></div>
                <div class="absolute" style="right:20px;bottom:-30px;width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,0.08);"></div>

                <div class="relative flex items-center gap-4">
                  <span
                    class="select-none flex-shrink-0"
                    :class="streakCount > 0 ? 'animate-streak-bounce' : 'opacity-30'"
                    style="font-size:2.75rem;line-height:1;"
                  >🔥</span>
                  <div class="flex-1 min-w-0">
                    <p style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:rgba(255,255,255,0.7);font-weight:600;font-family:'Plus Jakarta Sans',sans-serif;">
                      Chuỗi học hằng ngày
                    </p>
                    <div v-if="loadingStreak" class="h-9 w-20 rounded-lg animate-pulse" style="background:rgba(255,255,255,0.2);margin-top:4px;"></div>
                    <p v-else style="font-family:'Plus Jakarta Sans',sans-serif;font-size:2.25rem;font-weight:900;line-height:1;color:#fff;margin-top:2px;">
                      {{ streakCount }}<span style="font-size:0.875rem;font-weight:600;color:rgba(255,255,255,0.75);margin-left:4px;">ngày</span>
                    </p>
                  </div>
                </div>

                <!-- body-md, line-height 1.6 for legibility per design.md -->
                <p class="relative mt-3" style="font-size:0.8rem;color:rgba(255,255,255,0.85);line-height:1.6;">
                  <template v-if="loadingStreak">Đang tải...</template>
                  <template v-else-if="streakCount === 0">Hôm nay chưa học gì. Hãy bắt đầu ngay! 🌸</template>
                  <template v-else-if="streakCount === 1">Ngày đầu tiên! Duy trì chuỗi học nhé 💪</template>
                  <template v-else-if="streakCount < 7">Đang vào guồng rồi đó! Tiếp tục giữ đà này 🚀</template>
                  <template v-else-if="streakCount < 30">{{ streakCount }} ngày liên tiếp — thật tuyệt vời! ⭐</template>
                  <template v-else>Kỷ luật thép! {{ streakCount }} ngày không nghỉ 👑</template>
                </p>
              </div>

              <!-- Milestones — tonal chips, surface-container-low vs surface-container-highest -->
              <div class="px-4 pt-3 pb-0 grid grid-cols-4 gap-2">
                <div
                  v-for="milestone in milestones"
                  :key="milestone.days"
                  class="flex flex-col items-center gap-1.5 py-3 rounded-xl transition-all"
                  :style="streakCount >= milestone.days ? 'background:#f5e8e8;' : 'background:#f2f4f4;'"
                >
                  <span class="text-xl" :style="streakCount >= milestone.days ? '' : 'filter:grayscale(1);opacity:0.35;'">{{ milestone.icon }}</span>
                  <span class="text-[10px] font-bold" :style="streakCount >= milestone.days ? 'color:#7c5556;' : 'color:#adb3b4;'">{{ milestone.days }}d</span>
                </div>
              </div>

              <!-- Footer — soft-fill button, no explicit border -->
              <div class="px-4 pt-3 pb-5">
                <RouterLink
                  to="/profile"
                  @click="showNotif = false"
                  class="block w-full text-center py-2.5 rounded-xl transition-all"
                  style="font-size:0.8rem;font-weight:600;color:#45617d;background:#eef3f8;font-family:'Plus Jakarta Sans',sans-serif;"
                  onmouseover="this.style.background='#dde8f0'"
                  onmouseout="this.style.background='#eef3f8'"
                >
                  Xem hồ sơ đầy đủ →
                </RouterLink>
              </div>
            </div>
          </Transition>
        </div>

        <RouterLink
          to="/profile#settings"
          title="Cài đặt"
          class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2 transition-all opacity-80 hover:opacity-100"
        >
          <span class="material-symbols-outlined text-slate-700 dark:text-slate-300">settings</span>
        </RouterLink>
        <button
          @click="handleLogout"
          title="Đăng xuất"
          class="hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full p-2 transition-all opacity-70 hover:opacity-100 group"
        >
          <span class="material-symbols-outlined text-slate-500 group-hover:text-red-500 transition-colors">logout</span>
        </button>
        <div class="h-8 w-px bg-outline-variant/20 mx-2"></div>
        <RouterLink to="/profile" class="flex items-center gap-3 cursor-pointer group">
          <div class="text-right">
            <p class="font-semibold text-on-surface leading-tight">{{ authStore.user?.username || authStore.user?.email || 'Người dùng' }}</p>
            <p class="text-[10px] text-on-surface-variant uppercase tracking-widest">{{ authStore.user?.targetLevel ? 'JLPT ' + authStore.user.targetLevel : 'Learner' }}</p>
          </div>
          <!-- Avatar chữ cái đầu username -->
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center border-2 border-primary-container group-hover:border-primary transition-colors select-none shrink-0"
            style="background: linear-gradient(135deg, var(--color-primary), var(--color-secondary, #7c3aed));"
          >
            <span class="font-bold text-on-primary text-base leading-none">{{ avatarLetter }}</span>
          </div>
        </RouterLink>
      </div>
    </header>

    <!-- SideNavBar -->
    <aside class="h-screen w-64 flex-col fixed left-0 top-0 bg-slate-50 dark:bg-slate-900 font-['Plus_Jakarta_Sans'] antialiased py-6 space-y-2 z-50 hidden md:flex">
      <div class="px-6 mb-10">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-dim flex items-center justify-center text-on-primary shadow-sm">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">spa</span>
          </div>
          <div>
            <h1 class="text-xl font-bold tracking-tight text-slate-800 dark:text-slate-100">EasyNihongo</h1>
            <p class="text-xs text-slate-500 font-medium">Study Zen</p>
          </div>
        </div>
      </div>
      <nav class="flex flex-col h-full">
        <!-- Links -->
        <RouterLink to="/dashboard" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-semibold rounded-xl mx-2 shadow-sm px-4 py-3 flex items-center gap-3 transition-all duration-200 ease-out">
          <span class="material-symbols-outlined">dashboard</span>
          <span>Dashboard</span>
        </RouterLink>
        <RouterLink to="/dictionary" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-4 py-3 mx-2 transition-colors hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl flex items-center gap-3">
          <span class="material-symbols-outlined">search</span>
          <span>Tra cứu</span>
        </RouterLink>
        <RouterLink to="/translate" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-4 py-3 mx-2 transition-colors hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl flex items-center gap-3">
          <span class="material-symbols-outlined">translate</span>
          <span>Dịch thuật</span>
        </RouterLink>
        <RouterLink to="/flashcards" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-4 py-3 mx-2 transition-colors hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl flex items-center gap-3">
          <span class="material-symbols-outlined">style</span>
          <span>Flashcards</span>
        </RouterLink>
        <RouterLink to="/tutor" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-4 py-3 mx-2 transition-colors hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl flex items-center gap-3">
          <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">psychology</span>
          <span>AI Tutor</span>
        </RouterLink>
        <RouterLink to="/review" active-class="bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/20 text-blue-900 dark:text-blue-200" class="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-4 py-3 mx-2 transition-colors hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl flex items-center gap-3">
          <span class="material-symbols-outlined">rebase_edit</span>
          <span>Ôn tập</span>
        </RouterLink>

        <!-- Streak mini badge ở sidebar bottom -->
        <div class="mt-auto mx-4 mb-4">
          <div
            v-if="!loadingStreak && streakCount > 0"
            class="flex items-center gap-3 px-4 py-3 rounded-xl"
            style="background: linear-gradient(135deg, rgba(124,85,86,0.08) 0%, rgba(160,112,112,0.06) 100%);"
          >
            <span class="text-xl select-none">🔥</span>
            <div class="min-w-0">
              <p class="text-xs font-bold leading-none truncate" style="color:#7c5556;">{{ streakCount }} ngày liên tiếp</p>
              <p class="text-[10px] mt-0.5 truncate" style="color:#5a6061;">Tiếp tục duy trì!</p>
            </div>
          </div>
        </div>
      </nav>
    </aside>


    <main class="flex-1 md:ml-64 pt-20 pb-12 px-4 md:px-8">
      <RouterView />
    </main>

    <!-- Footer -->
<footer class="md:ml-64 bg-slate-50 dark:bg-slate-900 border-t border-slate-200/10 dark:border-slate-800/10 py-12">
<div class="flex flex-col items-center justify-center gap-6 w-full max-w-screen-xl mx-auto px-8">
<div class="flex gap-8 font-['Plus_Jakarta_Sans'] text-xs uppercase tracking-widest font-semibold">
<a class="text-slate-400 hover:text-slate-800 transition-colors" href="#">Privacy</a>
<a class="text-slate-400 hover:text-slate-800 transition-colors" href="#">Terms</a>
<a class="text-slate-400 hover:text-slate-800 transition-colors" href="#">Support</a>
<a class="text-slate-400 hover:text-slate-800 transition-colors" href="#">Contact</a>
</div>
<p class="text-slate-400 dark:text-slate-500 font-['Plus_Jakarta_Sans'] text-xs uppercase tracking-widest">© 2024 THE MEDITATIVE CANVAS. ALL RIGHTS RESERVED.</p>
</div>
</footer>

    <!-- Mobile Navigation (BottomNavBar) -->
<nav class="md:hidden fixed bottom-0 left-0 right-0 glass-panel border-t border-outline-variant/10 px-6 py-3 flex justify-between items-center z-50">
<button class="flex flex-col items-center gap-1 text-outline">
<span class="material-symbols-outlined">menu_book</span>
<span class="text-[10px] uppercase font-bold">Học</span>
</button>
<button class="flex flex-col items-center gap-1 text-outline">
<span class="material-symbols-outlined">search</span>
<span class="text-[10px] uppercase font-bold">Tra cứu</span>
</button>
<button class="w-12 h-12 sakura-gradient rounded-full flex items-center justify-center -translate-y-6 shadow-lg shadow-primary/30">
<span class="material-symbols-outlined text-white">draw</span>
</button>
<button class="flex flex-col items-center gap-1 text-outline">
<span class="material-symbols-outlined">layers</span>
<span class="text-[10px] uppercase font-bold">Thẻ</span>
</button>
        <RouterLink to="/profile" active-class="text-primary" class="flex flex-col items-center gap-1 text-outline">
          <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">person</span>
          <span class="text-[10px] uppercase font-bold">Tôi</span>
        </RouterLink>
</nav>

    <!-- ── Streak Toast (Meditative Canvas style) ──────────────── -->
    <Teleport to="body">
      <Transition name="streak-toast">
        <div
          v-if="showStreakToast"
          class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[9999] pointer-events-none"
        >
          <div
            class="flex items-center gap-4 rounded-2xl"
            style="
              padding: 1rem 1.5rem;
              background: linear-gradient(135deg, #7c5556 0%, #a07070 100%);
              box-shadow: 0 12px 40px rgba(124, 85, 86, 0.35), 0 4px 16px rgba(45, 52, 53, 0.08);
              font-family: 'Plus Jakarta Sans', sans-serif;
            "
          >
            <span style="font-size:2rem; line-height:1;">🔥</span>
            <div>
              <p style="font-size:1.1rem; font-weight:900; color:#fff; line-height:1;">{{ streakCount }} ngày liên tiếp!</p>
              <p style="font-size:0.8rem; color:rgba(255,255,255,0.78); margin-top:3px;">{{ streakToastMessage }}</p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { RouterView, RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()
const router = useRouter()

const avatarLetter = computed(() => {
  const name = authStore.user?.username || authStore.user?.email || ''
  return name ? name.charAt(0).toUpperCase() : '?'
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

// ── Streak state ─────────────────────────────────────────────────
const streakCount = ref(0)
const loadingStreak = ref(true)
const prevStreakCount = ref(0)

// Notification dropdown
const showNotif = ref(false)
const notifRef = ref(null)

// Toast
const showStreakToast = ref(false)
let toastTimer = null

const streakToastMessage = computed(() => {
  const n = streakCount.value
  if (n === 1)  return 'Ngày đầu tiên! Cố lên! 💪'
  if (n < 7)   return 'Đang vào guồng rồi đó! 🚀'
  if (n === 7)  return 'Một tuần học liên tiếp! 🌟'
  if (n === 30) return 'Một tháng! Bạn thật phi thường! 👑'
  if (n % 10 === 0) return `Cột mốc ${n} ngày! Tuyệt vời! ⭐`
  return 'Kỷ luật là sức mạnh của bạn!'
})

const milestones = [
  { days: 3,  icon: '🌱' },
  { days: 7,  icon: '⭐' },
  { days: 14, icon: '🏅' },
  { days: 30, icon: '👑' },
]

async function fetchStreak() {
  if (!authStore.user) return
  try {
    const res = await api.get('/api/v1/users/me/profile')
    if (res.status === 'success') {
      const newCount = res.data.streakCount ?? 0
      // Nếu streak tăng lên (user vừa hoàn thành hoạt động), hiện toast
      if (newCount > prevStreakCount.value && prevStreakCount.value >= 0 && newCount > 0) {
        streakCount.value = newCount
        triggerStreakToast()
      } else {
        streakCount.value = newCount
      }
      prevStreakCount.value = newCount
    }
  } catch (e) {
    console.warn('[AppLayout] fetchStreak failed', e)
  } finally {
    loadingStreak.value = false
  }
}

function triggerStreakToast() {
  showStreakToast.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { showStreakToast.value = false }, 4000)
}

function toggleNotif() {
  showNotif.value = !showNotif.value
  // Khi mở panel, refresh streak
  if (showNotif.value) fetchStreak()
}

// Click outside để đóng dropdown
function onClickOutside(e) {
  if (notifRef.value && !notifRef.value.contains(e.target)) {
    showNotif.value = false
  }
}

// Lắng nghe sự kiện streak-updated được emit từ các trang con
function onStreakUpdated() {
  const old = streakCount.value
  prevStreakCount.value = old
  fetchStreak()
}

onMounted(async () => {
  if (!authStore.user) await authStore.fetchMe()
  fetchStreak()
  document.addEventListener('click', onClickOutside, true)
  window.addEventListener('streak-updated', onStreakUpdated)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
  window.removeEventListener('streak-updated', onStreakUpdated)
  clearTimeout(toastTimer)
})
</script>

<style scoped>
/* Notification dropdown animation — subtle float down */
.notif-drop-enter-active,
.notif-drop-leave-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.notif-drop-enter-from,
.notif-drop-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.96);
}

/* Streak toast — slides up from bottom */
.streak-toast-enter-active,
.streak-toast-leave-active {
  transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.streak-toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(24px) scale(0.93);
}
.streak-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px) scale(0.97);
}

/* Streak flame bounce */
@keyframes streak-bounce {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25%       { transform: scale(1.2) rotate(-8deg); }
  60%       { transform: scale(1.1) rotate(5deg); }
}
.animate-streak-bounce {
  display: inline-block;
  animation: streak-bounce 1.6s ease-in-out infinite;
}
</style>

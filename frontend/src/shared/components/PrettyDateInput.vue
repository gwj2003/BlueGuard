<template>
  <div class="pretty-date" :class="{ 'is-disabled': disabled, compact }" @click="toggleCalendar">
    <input
      ref="nativeInput"
      :id="id"
      type="date"
      class="pretty-date__input"
      :value="modelValue"
      :min="min"
      :max="max"
      readonly
      :disabled="disabled"
      :aria-label="ariaLabel"
      @input="onInput"
      @change="onChange"
    />
    <span class="pretty-date__icon" aria-hidden="true"></span>
  </div>

  <teleport to="body">
    <div
      v-if="state.isCalendarOpen"
      ref="calendarPanel"
      class="pretty-date__calendar"
      :style="calendarStyle"
      @click.stop
    >
      <div class="calendar-header">
        <button class="cal-nav" @click.stop="prevMonth">‹</button>
        <button
          class="calendar-title calendar-title--button"
          :class="{ 'is-range-title': state.isYearRangeOpen }"
          @click.stop="onTitleClick"
        >
          {{ titleText }}
        </button>
        <button class="cal-nav" @click.stop="nextMonth">›</button>
      </div>
      <div v-if="state.isYearPickerOpen" class="year-picker">
        <div class="year-picker__header">
          <button class="cal-nav" @click.stop="changeYearBlock(-1)">‹</button>
          <div class="year-picker__title">{{ state.yearBlockStart }} - {{ state.yearBlockEnd }}</div>
          <button class="cal-nav" @click.stop="changeYearBlock(1)">›</button>
        </div>
        <div class="year-grid">
          <button
            v-for="year in state.yearOptions"
            :key="year"
            class="year-cell"
            :class="{ active: year === state.viewYear }"
            @click.stop="selectYear(year)"
          >
            {{ year }}
          </button>
        </div>
      </div>
      <div v-else-if="state.isYearOnlyView" class="months-picker">
        <div class="months-grid">
          <button
            v-for="m in 12"
            :key="m"
            class="month-cell"
            :class="{ disabled: state.viewYear > currentYear || (state.viewYear === currentYear && (m-1) > todayMonth) }"
            :disabled="state.viewYear > currentYear || (state.viewYear === currentYear && (m-1) > todayMonth)"
            @click.stop="selectMonth(m-1)"
          >{{ m }} 月</button>
        </div>
      </div>
      <div v-else-if="state.isYearRangeOpen" class="recent-picker">
        <div class="recent-grid">
          <button
            v-for="year in state.recentYears"
            :key="year + '-recent'"
            class="year-cell"
            :class="{ active: year === state.viewYear, disabled: year > currentYear }"
            :disabled="year > currentYear"
            @click.stop="selectRecentYear(year)"
          >
            {{ year }}
          </button>
        </div>
      </div>
      <div v-else class="calendar-grid">
        <div class="weekday" v-for="d in ['日','一','二','三','四','五','六']" :key="d">{{ d }}</div>
        <button
          v-for="(day, idx) in state.days"
          :key="idx"
          class="cal-day"
          :class="{ empty: !day, disabled: isFutureDay(day) }"
          @click.stop="pickDay(day)"
          :disabled="!day || isFutureDay(day)"
        >{{ day || '' }}</button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  id: {
    type: String,
    default: undefined,
  },
  min: {
    type: String,
    default: undefined,
  },
  max: {
    type: String,
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  ariaLabel: {
    type: String,
    default: '选择日期',
  },
})

const emit = defineEmits(['update:modelValue'])

import { computed, nextTick, onBeforeUnmount, reactive, ref } from 'vue'

const nativeInput = ref(null)
const calendarPanel = ref(null)
const calendarStyle = ref({})

function openPicker(event) {
  if (props.disabled) return
  // Prefer our custom calendar popup for consistent styling
  openCalendar()
}

// Lightweight in-component calendar popup fallback
const state = reactive({
  isCalendarOpen: false,
  isYearPickerOpen: false,
  isYearOnlyView: false,
  isYearRangeOpen: false,
  viewYear: 0,
  viewMonth: 0,
  days: [],
  yearBlockStart: 0,
  yearBlockEnd: 0,
  yearOptions: [],
  recentYears: [],
  recentAnchorYear: null,
  yearRangeStart: null,
  yearRangeEnd: null,
})

const currentYear = new Date().getFullYear()
const todayMonth = new Date().getMonth()

const titleText = computed(() => {
  if (state.isYearOnlyView) return `${state.viewYear} 年`
  if (state.isYearRangeOpen) return `${state.yearRangeStart} - ${state.yearRangeEnd}`
  return `${state.viewYear} 年 ${state.viewMonth + 1} 月`
})

function isFutureDay(day) {
  if (!day) return false
  const picked = new Date(state.viewYear, state.viewMonth, day)
  const now = new Date()
  // compare only date portion
  return picked.setHours(0,0,0,0) > now.setHours(0,0,0,0)
}

function onTitleClick() {
  if (!state.isCalendarOpen) return
  // first click: show months of the year
  if (!state.isYearOnlyView && !state.isYearRangeOpen && !state.isYearPickerOpen) {
    state.isYearOnlyView = true
    return
  }
  // second click from months view: show recent N-year range
  if (state.isYearOnlyView) {
    buildRecentYears(state.viewYear, 12)
    state.isYearOnlyView = false
    state.isYearRangeOpen = true
    return
  }
  // if year picker open (old behavior), toggle it
  if (state.isYearPickerOpen) {
    toggleYearPicker()
    return
  }
}

function buildRecentYears(anchorYear, count = 12) {
  const cur = new Date()
  const maxYear = Math.min(cur.getFullYear(), anchorYear)
  const start = Math.max(maxYear - (count - 1), 0)
  const years = []
  for (let y = start; y <= maxYear; y++) years.push(y)
  state.recentYears = years
  state.yearRangeStart = start
  state.yearRangeEnd = maxYear
}

function selectRecentYear(year) {
  if (year > currentYear) return
  state.viewYear = year
  state.isYearRangeOpen = false
  state.isYearOnlyView = true
}

function selectMonth(monthIndex) {
  // prevent selecting future month
  const today = new Date()
  if (state.viewYear > today.getFullYear() || (state.viewYear === today.getFullYear() && monthIndex > today.getMonth())) return
  state.viewMonth = monthIndex
  buildCalendar(state.viewYear, state.viewMonth)
  state.isYearOnlyView = false
}

function buildCalendar(year, month) {
  const first = new Date(year, month, 1)
  const startDay = first.getDay() // 0-6 (Sun-Sat)
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const days = []
  // pad previous month
  for (let i = 0; i < startDay; i++) days.push(null)
  for (let d = 1; d <= daysInMonth; d++) days.push(d)
  state.days = days
}

function buildYearOptions(anchorYear = state.viewYear) {
  const blockSize = 12
  const start = Math.floor(anchorYear / blockSize) * blockSize
  state.yearBlockStart = start
  state.yearBlockEnd = start + blockSize - 1
  state.yearOptions = Array.from({ length: blockSize }, (_, index) => start + index)
}

function toggleYearPicker() {
  state.isYearPickerOpen = !state.isYearPickerOpen
  if (state.isYearPickerOpen) {
    buildYearOptions(state.viewYear)
  }
}

function changeYearBlock(direction) {
  buildYearOptions(state.yearBlockStart + direction * 12)
}

function selectYear(year) {
  state.viewYear = year
  state.isYearPickerOpen = false
  buildCalendar(state.viewYear, state.viewMonth)
}

function openCalendar() {
  if (props.disabled) return
  const el = nativeInput.value
  const cur = el && el.value ? new Date(el.value) : new Date()
  state.viewYear = cur.getFullYear()
  state.viewMonth = cur.getMonth()
  state.isYearPickerOpen = false
  state.isYearOnlyView = false
  state.isYearRangeOpen = false
  buildCalendar(state.viewYear, state.viewMonth)
  state.isCalendarOpen = true
  nextTick(() => {
    updateCalendarPosition()
  })
  // attach outside click
  document.addEventListener('click', onDocClick)
  window.addEventListener('resize', updateCalendarPosition)
  window.addEventListener('scroll', updateCalendarPosition, true)
}

function closeCalendar() {
  state.isCalendarOpen = false
  state.isYearPickerOpen = false
  state.isYearOnlyView = false
  state.isYearRangeOpen = false
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('resize', updateCalendarPosition)
  window.removeEventListener('scroll', updateCalendarPosition, true)
}

function toggleCalendar() {
  if (state.isCalendarOpen) closeCalendar()
  else openCalendar()
}

function onDocClick(e) {
  const root = e.target.closest && e.target.closest('.pretty-date')
  const popup = e.target.closest && e.target.closest('.pretty-date__calendar')
  if (!root && !popup) closeCalendar()
}

function updateCalendarPosition() {
  const el = nativeInput.value
  const panel = calendarPanel.value
  if (!el || !panel) return
  const rect = el.getBoundingClientRect()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0
  const panelWidth = panel.offsetWidth || 288
  const preferredLeft = rect.left + rect.width / 2 + window.scrollX
  const minLeft = window.scrollX + 8 + panelWidth / 2
  const maxLeft = window.scrollX + viewportWidth - 8 - panelWidth / 2
  const centeredLeft = Math.min(Math.max(preferredLeft, minLeft), maxLeft)
  calendarStyle.value = {
    position: 'absolute',
    left: `${centeredLeft}px`,
    top: `${rect.bottom + window.scrollY + 8}px`,
    transform: 'translateX(-50%)',
  }
}

function prevMonth() {
  if (state.isYearPickerOpen) {
    changeYearBlock(-1)
    return
  }
  // if in months-only view, change the displayed year
  if (state.isYearOnlyView) {
    state.viewYear = state.viewYear - 1
    return
  }
  // if in year-range view, shift the range backward by 12 years
  if (state.isYearRangeOpen) {
    const count = state.recentYears.length || 12
    const currentEnd = state.yearRangeEnd ?? state.viewYear
    const newEnd = Math.max(currentEnd - count, count - 1)
    buildRecentYears(newEnd, count)
    return
  }
  // default: navigate month (prevent going before year 0)
  if (state.viewMonth === 0) {
    state.viewMonth = 11
    state.viewYear -= 1
  } else {
    state.viewMonth -= 1
  }
  buildCalendar(state.viewYear, state.viewMonth)
}

function nextMonth() {
  if (state.isYearPickerOpen) {
    changeYearBlock(1)
    return
  }
  // if in months-only view, change the displayed year forward
  if (state.isYearOnlyView) {
    const today = new Date()
    if (state.viewYear + 1 > today.getFullYear()) return
    state.viewYear = state.viewYear + 1
    return
  }
  // if in year-range view, shift the range forward by count years (cap to currentYear)
  if (state.isYearRangeOpen) {
    const count = state.recentYears.length || 12
    const maxEnd = currentYear
    const currentEnd = state.yearRangeEnd ?? currentYear
    if (currentEnd >= maxEnd) return
    const desiredEnd = currentEnd + count
    const newEnd = Math.min(desiredEnd, maxEnd)
    buildRecentYears(newEnd, count)
    return
  }
  // default: navigate month (prevent navigating into future months)
  const candidateYear = state.viewMonth === 11 ? state.viewYear + 1 : state.viewYear
  const candidateMonth = state.viewMonth === 11 ? 0 : state.viewMonth + 1
  const today = new Date()
  if (candidateYear > today.getFullYear() || (candidateYear === today.getFullYear() && candidateMonth > today.getMonth())) {
    return
  }
  if (state.viewMonth === 11) {
    state.viewMonth = 0
    state.viewYear += 1
  } else {
    state.viewMonth += 1
  }
  buildCalendar(state.viewYear, state.viewMonth)
}

function pickDay(day) {
  if (!day) return
  const yyyy = String(state.viewYear).padStart(4, '0')
  const mm = String(state.viewMonth + 1).padStart(2, '0')
  const dd = String(day).padStart(2, '0')
  const val = `${yyyy}-${mm}-${dd}`
  // prevent selecting future dates
  const picked = new Date(state.viewYear, state.viewMonth, day)
  const today = new Date()
  if (picked > today) return
  emit('update:modelValue', val)
  // set native value for consistency
  try { nativeInput.value.value = val } catch (e) {}
  closeCalendar()
}

onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
onBeforeUnmount(() => {
  window.removeEventListener('resize', updateCalendarPosition)
  window.removeEventListener('scroll', updateCalendarPosition, true)
})

function onInput(event) {
  emit('update:modelValue', event.target.value)
}

function onChange(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.pretty-date {
  position: relative;
  width: 100%;
}

.pretty-date__input {
  width: 100%;
  min-height: 3rem;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 1px solid #d4dde8;
  border-radius: 0.25rem;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  color: #334155;
  box-shadow: 0 6px 16px rgba(17, 52, 72, 0.06);
  cursor: pointer;
  font: 400 0.875rem/1.375rem 'Open Sans', sans-serif;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

.pretty-date.compact .pretty-date__input {
  min-height: 2.75rem;
  padding-top: 0.65rem;
  padding-bottom: 0.65rem;
}

.pretty-date__input:hover {
  border-color: #b9c7d6;
  box-shadow: 0 10px 22px rgba(17, 52, 72, 0.1);
}

.year-grid,
.recent-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-top: 6px;
}

.months-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-top: 8px;
}

.month-cell {
  padding: 8px 6px;
  border-radius: 0.25rem;
  border: 1px solid transparent;
  background: transparent;
  color: #334155;
  cursor: pointer;
}

.month-cell:hover:not(:disabled),
.month-cell:focus-visible:not(:disabled) {
  background: #eef9f4;
  border-color: #cdeee3;
  outline: none;
}

.month-cell:focus,
.month-cell:focus-visible {
  outline: none;
  box-shadow: none;
}

.month-cell:disabled {
  opacity: 0.45;
  background: rgba(127, 140, 153, 0.08);
  border-color: rgba(127, 140, 153, 0.12);
  cursor: not-allowed;
}

.year-cell {
  padding: 8px 6px;
  border-radius: 0.25rem;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
}

.year-cell:hover:not(:disabled),
.year-cell:focus-visible:not(:disabled) {
  background: #eef9f4;
  border-color: #cdeee3;
  outline: none;
}

.year-cell.active {
  background: #eef9f4;
  border-color: #cdeee3;
}

.year-cell.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.year-cell:disabled {
  background: rgba(127, 140, 153, 0.08);
  border-color: rgba(127, 140, 153, 0.12);
}

.country-picker__header,
.recent-picker__header {
  font-weight: 600;
  margin-bottom: 8px;
}

.pretty-date__input:focus,
.pretty-date__input:focus-visible {
  outline: none;
  border-color: #d4dde8;
  box-shadow: 0 6px 16px rgba(17, 52, 72, 0.06);
}

.pretty-date__input:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.pretty-date__input::-webkit-calendar-picker-indicator {
  opacity: 0;
  display: none;
}

.pretty-date__input::-webkit-clear-button,
.pretty-date__input::-webkit-inner-spin-button {
  display: none;
}

.pretty-date__icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  width: 1.05rem;
  height: 1rem;
  transform: translateY(-50%);
  border: 1.8px solid #5d7083;
  border-radius: 4px;
  pointer-events: auto;
  cursor: pointer;
  opacity: 0.92;
}

.pretty-date__icon::before {
  content: '';
  position: absolute;
  left: -1px;
  right: -1px;
  top: -5px;
  height: 5px;
  border-radius: 4px 4px 0 0;
  background: #5d7083;
}

.pretty-date__icon::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 3px;
  width: 5px;
  height: 1px;
  background: #5d7083;
  box-shadow:
    0 3px 0 #5d7083,
    4px 0 0 #5d7083,
    4px 3px 0 #5d7083;
}

.pretty-date.is-disabled .pretty-date__icon {
  opacity: 0.5;
}

.pretty-date__calendar {
  position: absolute;
  z-index: 99999;
  right: 0;
  top: calc(100% + 8px);
  width: 18rem;
  background: #fff;
  border: 1px solid #e6eef6;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(17,52,72,0.12);
  padding: 10px;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.calendar-title {
  font-weight: 600;
  color: #334155;
}

.calendar-title--button {
  background: transparent;
  border: none;
  cursor: pointer;
  font: inherit;
  padding: 2px 8px;
  border-radius: 8px;
}

.calendar-title--button:not(.is-range-title):hover {
  background: #eef7f3;
}

.calendar-title--button:focus,
.calendar-title--button:focus-visible {
  outline: none;
  box-shadow: none;
  background: transparent;
}

.calendar-title--button:not(.is-range-title):active {
  background: #e4f3ed;
}

/* when title represents a year-range, do not highlight on hover/focus/active */
.calendar-title--button.is-range-title:hover,
.calendar-title--button.is-range-title:focus,
.calendar-title--button.is-range-title:focus-visible,
.calendar-title--button.is-range-title:active {
  background: transparent;
}

.cal-nav {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 4px 8px;
}

.cal-nav:hover,
.cal-nav:focus,
.cal-nav:focus-visible {
  background: transparent;
  outline: none;
  box-shadow: none;
}

.year-picker {
  display: grid;
  gap: 10px;
}

.year-picker__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.year-picker__title {
  font-weight: 600;
  color: #334155;
}

.year-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.year-cell {
  min-height: 2.4rem;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #334155;
  cursor: pointer;
}

.year-cell:hover:not(:disabled),
.year-cell:focus-visible:not(:disabled) {
  background: #eef7f3;
  border-color: #cdeee3;
  outline: none;
}

.year-cell:focus,
.year-cell:focus-visible {
  outline: none;
  box-shadow: none;
}

.year-cell.active {
  background: #eef7f3;
  border-color: #cdeee3;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.weekday {
  text-align: center;
  color: #7b8b9a;
  font-size: 0.8rem;
}

.cal-day {
  min-height: 2.4rem;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
}

.cal-day.empty {
  background: transparent;
  cursor: default;
}

.cal-day:hover:not(.empty) {
  background: #eef7f3;
}

.cal-day:focus,
.cal-day:focus-visible {
  outline: none;
  box-shadow: none;
}

.cal-day:disabled {
  opacity: 0.35;
  background: rgba(127, 140, 153, 0.08);
  cursor: default;
}

.cal-day:disabled:hover {
  background: rgba(127, 140, 153, 0.08);
}
</style>
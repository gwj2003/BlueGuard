<template>
  <div ref="rootRef" class="pretty-select" :class="{ 'is-open': isOpen, 'is-disabled': disabled }">
    <button
      type="button"
      class="pretty-select__button"
      :class="{ 'is-placeholder': !selectedOption }"
      :disabled="disabled"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      @click="toggleOpen"
      @keydown.down.prevent="openAndFocusFirst"
      @keydown.up.prevent="openAndFocusLast"
      @keydown.enter.prevent="selectFocusedOption"
      @keydown.space.prevent="toggleOpen"
      @keydown.esc.prevent="closeDropdown"
    >
      <span class="pretty-select__value">{{ selectedLabel }}</span>
      <span class="pretty-select__icon" aria-hidden="true"></span>
    </button>

  </div>

  <teleport to="body">
    <Transition name="pretty-select-pop">
      <div
        v-if="isOpen"
        ref="panelRef"
        class="pretty-select__panel"
        :style="panelStyle"
        role="listbox"
      >
        <button
          v-for="(option, index) in options"
          :key="optionKey(option, index)"
          ref="optionRefs"
          type="button"
          class="pretty-select__option"
          :class="{
            'is-selected': isSelected(option),
            'is-active': index === activeIndex,
          }"
          role="option"
          :aria-selected="isSelected(option)"
          @mouseenter="activeIndex = index"
          @click="selectOption(option)"
        >
          <span class="pretty-select__option-label">{{ option.label }}</span>
          <span v-if="isSelected(option)" class="pretty-select__check" aria-hidden="true">✓</span>
        </button>
      </div>
    </Transition>
  </teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Array, Object],
    default: '',
  },
  options: {
    type: Array,
    required: true,
  },
  placeholder: {
    type: String,
    default: '请选择',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const rootRef = ref(null)
const panelRef = ref(null)
const panelStyle = ref({})
const isOpen = ref(false)
const activeIndex = ref(-1)

const selectedOption = computed(() => props.options.find((option) => Object.is(option.value, props.modelValue)))
const selectedLabel = computed(() => selectedOption.value?.label ?? props.placeholder)

function optionKey(option, index) {
  return `${String(option.value)}-${index}`
}

function isSelected(option) {
  return Object.is(option.value, props.modelValue)
}

function openDropdown() {
  if (props.disabled) {
    return
  }

  isOpen.value = true
  activeIndex.value = Math.max(0, props.options.findIndex((option) => Object.is(option.value, props.modelValue)))
  nextTick(() => {
    updatePanelPosition()
  })

  window.addEventListener('resize', updatePanelPosition)
  window.addEventListener('scroll', updatePanelPosition, true)
}

function closeDropdown() {
  isOpen.value = false
  activeIndex.value = -1
  window.removeEventListener('resize', updatePanelPosition)
  window.removeEventListener('scroll', updatePanelPosition, true)
}

function toggleOpen() {
  if (isOpen.value) {
    closeDropdown()
    return
  }

  openDropdown()
}

function selectOption(option) {
  emit('update:modelValue', option.value)
  closeDropdown()
}

function openAndFocusFirst() {
  openDropdown()
  activeIndex.value = 0
}

function openAndFocusLast() {
  openDropdown()
  activeIndex.value = Math.max(props.options.length - 1, 0)
}

function selectFocusedOption() {
  if (!isOpen.value) {
    openDropdown()
    return
  }

  const focusedOption = props.options[activeIndex.value]
  if (focusedOption) {
    selectOption(focusedOption)
  }
}

function handleDocumentClick(event) {
  if (!rootRef.value || rootRef.value.contains(event.target) || panelRef.value?.contains(event.target)) {
    return
  }

  closeDropdown()
}

function updatePanelPosition() {
  const root = rootRef.value
  const panel = panelRef.value
  if (!root || !panel) return

  const rect = root.getBoundingClientRect()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0
  const panelWidth = rect.width
  const centerX = rect.left + rect.width / 2 + window.scrollX
  const minCenter = window.scrollX + panelWidth / 2 + 8
  const maxCenter = window.scrollX + viewportWidth - panelWidth / 2 - 8
  const clampedCenter = Math.min(Math.max(centerX, minCenter), maxCenter)

  panelStyle.value = {
    position: 'absolute',
    left: `${clampedCenter}px`,
    top: `${rect.bottom + window.scrollY + 8}px`,
    width: `${panelWidth}px`,
    transform: 'translateX(-50%)',
  }
}

watch(
  () => props.modelValue,
  () => {
    if (!isOpen.value) {
      return
    }

    activeIndex.value = Math.max(0, props.options.findIndex((option) => Object.is(option.value, props.modelValue)))
  },
)

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentClick)
  document.addEventListener('touchstart', handleDocumentClick, { passive: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleDocumentClick)
  document.removeEventListener('touchstart', handleDocumentClick)
  window.removeEventListener('resize', updatePanelPosition)
  window.removeEventListener('scroll', updatePanelPosition, true)
})
</script>

<style scoped>
.pretty-select {
  position: relative;
  width: 100%;
}

.pretty-select__button {
  width: 100%;
  min-height: 3rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0.75rem 0.95rem 0.75rem 1rem;
  border: 1px solid #d4dde8;
  border-radius: 0.25rem;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  color: #334155;
  box-shadow: 0 6px 16px rgba(17, 52, 72, 0.06);
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease,
    background-color 0.2s ease;
  text-align: left;
}

.pretty-select__button:hover {
  border-color: #b9c7d6;
  box-shadow: 0 10px 22px rgba(17, 52, 72, 0.1);
}

.pretty-select__button:focus,
.pretty-select__button:focus-visible {
  outline: none;
  border-color: #14bf98;
  box-shadow:
    0 0 0 4px rgba(20, 191, 152, 0.16),
    0 10px 22px rgba(17, 52, 72, 0.1);
}

.pretty-select.is-open .pretty-select__button {
  border-color: #14bf98;
  box-shadow:
    0 0 0 4px rgba(20, 191, 152, 0.16),
    0 10px 22px rgba(17, 52, 72, 0.1);
}

.pretty-select__button.is-placeholder {
  color: #8896a8;
}

.pretty-select__value {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.pretty-select__icon {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-right: 2px solid #5d7083;
  border-bottom: 2px solid #5d7083;
  transform: translateY(-2px) rotate(45deg);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.pretty-select.is-open .pretty-select__icon {
  transform: translateY(2px) rotate(225deg);
  border-color: #14bf98;
}

.pretty-select__panel {
  position: absolute;
  z-index: 99999;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  padding: 8px;
  border: 1px solid rgba(20, 191, 152, 0.16);
  border-radius: 0.25rem;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 60px rgba(17, 52, 72, 0.18);
  backdrop-filter: blur(10px);
  max-height: 280px;
  overflow: auto;
}

.pretty-select__option {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0.7rem 0.85rem;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: #334155;
  cursor: pointer;
  text-align: left;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.pretty-select__option:hover,
.pretty-select__option.is-active {
  background: #effaf7;
  color: #0f6c56;
}

.pretty-select__option.is-selected {
  background: linear-gradient(90deg, rgba(20, 191, 152, 0.14), rgba(20, 191, 152, 0.06));
  color: #0f6c56;
}

.pretty-select__option + .pretty-select__option {
  margin-top: 4px;
}

.pretty-select__option-label {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.pretty-select__check {
  color: #14bf98;
  font-weight: 700;
}

.pretty-select-pop-enter-active,
.pretty-select-pop-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.pretty-select-pop-enter-from,
.pretty-select-pop-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
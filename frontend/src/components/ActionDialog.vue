<template>
  <teleport to="body">
    <div v-if="open" class="dialog-mask" @click.self="handleCancel">
      <div class="dialog-card" :class="`severity-${severity}`" role="dialog" aria-modal="true">
        <div class="dialog-head">
          <div>
            <div class="dialog-title">{{ title }}</div>
            <div v-if="message" class="dialog-message">{{ message }}</div>
          </div>
          <button class="dialog-close" type="button" @click="handleCancel" aria-label="关闭">×</button>
        </div>

        <div v-if="variant === 'input'" class="dialog-body">
          <label class="dialog-label">
            <span>{{ inputLabel }}</span>
            <input
              ref="inputEl"
              v-model="draftValue"
              :type="inputType"
              :placeholder="inputPlaceholder"
              :min="inputMin"
              :step="inputStep"
            >
          </label>
          <div v-if="hint" class="dialog-hint">{{ hint }}</div>
        </div>

        <div class="dialog-actions">
          <button type="button" class="dialog-btn dialog-cancel" @click="handleCancel">{{ cancelText }}</button>
          <button type="button" class="dialog-btn dialog-confirm" @click="handleConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  variant: { type: String, default: 'confirm' },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  hint: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  inputLabel: { type: String, default: '' },
  inputPlaceholder: { type: String, default: '' },
  inputType: { type: String, default: 'text' },
  inputMin: { type: [String, Number], default: undefined },
  inputStep: { type: [String, Number], default: undefined },
  inputValue: { type: [String, Number], default: '' },
  severity: { type: String, default: 'primary' },
})

const emit = defineEmits(['confirm', 'cancel'])

const draftValue = ref('')
const inputEl = ref(null)

watch(
  () => [props.open, props.inputValue, props.variant],
  async ([isOpen]) => {
    if (props.variant === 'input') {
      draftValue.value = props.inputValue == null ? '' : String(props.inputValue)
      if (isOpen) {
        await nextTick()
        inputEl.value?.focus?.()
        inputEl.value?.select?.()
      }
    }
  },
  { immediate: true }
)

function handleCancel() {
  emit('cancel')
}

function handleConfirm() {
  emit('confirm', props.variant === 'input' ? draftValue.value : true)
}
</script>

<style scoped>
.dialog-mask {
  position: fixed;
  inset: 0;
  z-index: 400;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(8px);
}

.dialog-card {
  width: min(480px, 100%);
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.18);
}

.dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 22px 14px;
}

.dialog-title {
  color: #101828;
  font-size: 18px;
  font-weight: 850;
}

.dialog-message {
  margin-top: 6px;
  color: #667085;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-line;
}

.dialog-close {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: #f3f4f6;
  color: #475467;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}

.dialog-body {
  padding: 0 22px 18px;
}

.dialog-label {
  display: grid;
  gap: 8px;
  color: #344054;
  font-size: 14px;
  font-weight: 700;
}

.dialog-label input {
  width: 100%;
  height: 42px;
  border: 1px solid #d0d5dd;
  border-radius: 10px;
  padding: 0 12px;
  font: inherit;
  color: #101828;
  outline: none;
}

.dialog-label input:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
}

.dialog-hint {
  margin-top: 10px;
  color: #98a2b3;
  font-size: 12px;
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 22px 22px;
}

.dialog-btn {
  min-width: 88px;
  height: 38px;
  border-radius: 10px;
  border: 1px solid #d0d5dd;
  background: #fff;
  color: #344054;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.dialog-confirm {
  border-color: #10b981;
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
}

.severity-danger .dialog-confirm {
  border-color: #ef4444;
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

.severity-warning .dialog-confirm {
  border-color: #d97706;
  background: linear-gradient(135deg, #d97706, #f59e0b);
}

.severity-neutral .dialog-confirm,
.severity-primary .dialog-confirm {
  border-color: #10b981;
}

@media (max-width: 640px) {
  .dialog-mask {
    padding: 16px;
  }

  .dialog-head,
  .dialog-body,
  .dialog-actions {
    padding-left: 18px;
    padding-right: 18px;
  }

  .dialog-actions {
    flex-direction: column-reverse;
  }

  .dialog-btn {
    width: 100%;
  }
}
</style>

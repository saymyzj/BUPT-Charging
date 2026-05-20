import { ref } from 'vue'

function createDialogState(overrides = {}) {
  return {
    open: false,
    variant: 'confirm',
    title: '',
    message: '',
    hint: '',
    confirmText: '确认',
    cancelText: '取消',
    inputLabel: '',
    inputPlaceholder: '',
    inputType: 'text',
    inputMin: undefined,
    inputStep: undefined,
    inputValue: '',
    severity: 'primary',
    ...overrides,
  }
}

export function useActionDialog() {
  const dialog = ref(createDialogState())
  let resolver = null

  function resetDialog() {
    dialog.value = createDialogState()
  }

  function closeDialog(payload = null) {
    const done = resolver
    resolver = null
    dialog.value = createDialogState()
    if (done) done(payload)
  }

  function openConfirm(options = {}) {
    return new Promise((resolve) => {
      resolver = resolve
      dialog.value = createDialogState({ open: true, variant: 'confirm', ...options })
    })
  }

  function openInput(options = {}) {
    return new Promise((resolve) => {
      resolver = resolve
      dialog.value = createDialogState({
        open: true,
        variant: 'input',
        inputValue: options.inputValue ?? '',
        ...options,
      })
    })
  }

  function openMessage(options = {}) {
    return new Promise((resolve) => {
      resolver = resolve
      dialog.value = createDialogState({ open: true, variant: 'message', ...options })
    })
  }

  function confirmDialog(value) {
    closeDialog(value ?? true)
  }

  function cancelDialog() {
    closeDialog(null)
  }

  return {
    dialog,
    openConfirm,
    openInput,
    openMessage,
    confirmDialog,
    cancelDialog,
    resetDialog,
  }
}

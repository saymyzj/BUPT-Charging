import { REQUEST_STATUS } from '@/constants/enums'

function formatMinutesUntil(time, nowMs = Date.now()) {
  if (!time) return '--'
  const target = new Date(time).getTime()
  if (Number.isNaN(target)) return '--'
  const minutes = Math.max(0, Math.ceil((target - nowMs) / 60000))
  return `${minutes} min`
}

function formatSeconds(seconds) {
  const n = Number(seconds)
  if (!Number.isFinite(n)) return '--'
  return `${Math.ceil(Math.max(0, n) / 60)} min`
}

export function formatRequestRemainingText(request, now = Date.now()) {
  if (!request) return '--'

  const status = request.request_status
  if (status === REQUEST_STATUS.CHARGING) {
    const remainingText = formatSeconds(request.charge_remaining_seconds)
    if (remainingText !== '--') return remainingText
    return formatMinutesUntil(request.estimated_finish_time, now)
  }

  if (status === REQUEST_STATUS.WAITING_AREA || status === REQUEST_STATUS.QUEUED) {
    const remainingText = formatSeconds(request.estimated_wait_remaining_seconds ?? request.queue_wait_remaining_seconds)
    if (remainingText !== '--') return remainingText

    const startText = formatMinutesUntil(request.estimated_start_time, now)
    if (startText !== '--') return startText

    return formatSeconds(request.estimated_wait_seconds)
  }

  return formatSeconds(request.estimated_wait_seconds)
}

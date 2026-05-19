import { REQUEST_STATUS } from '@/constants/enums'

function formatMinutesUntil(time, nowMs = Date.now()) {
  if (!time) return '--'
  const target = new Date(time).getTime()
  if (Number.isNaN(target)) return '--'
  const minutes = Math.max(0, Math.ceil((target - nowMs) / 60000))
  return `${minutes} min`
}

export function formatRequestRemainingText(request, now = Date.now()) {
  if (!request) return '--'

  const status = request.request_status
  if (status === REQUEST_STATUS.CHARGING) {
    return formatMinutesUntil(request.estimated_finish_time, now)
  }

  if (status === REQUEST_STATUS.WAITING_AREA || status === REQUEST_STATUS.QUEUED) {
    const startText = formatMinutesUntil(request.estimated_start_time, now)
    if (startText !== '--') return startText

    const seconds = Number(request.estimated_wait_seconds)
    if (!Number.isFinite(seconds)) return '--'
    return `${Math.ceil(Math.max(0, seconds) / 60)} min`
  }

  const seconds = Number(request.estimated_wait_seconds)
  if (Number.isFinite(seconds) && seconds >= 0) {
    return `${Math.ceil(seconds / 60)} min`
  }

  return '--'
}

import { reportContactClick } from '../services/contacts'

const HOVER_TRACK_DELAY_MS = 2000

export function useContactPopoverTracking(isSmallScreen) {
  const hoverTrackTimers = new Map()

  function clearHoverTrackTimer(contactId) {
    const timer = hoverTrackTimers.get(contactId)
    if (!timer) {
      return
    }
    clearTimeout(timer)
    hoverTrackTimers.delete(contactId)
  }

  function handleContactPopoverChange(item, open) {
    const contactId = Number.parseInt(String(item?.id || ''), 10)
    if (!Number.isInteger(contactId) || contactId <= 0) {
      return
    }

    if (!open) {
      clearHoverTrackTimer(contactId)
      return
    }

    if (isSmallScreen.value) {
      clearHoverTrackTimer(contactId)
      reportContactClick(contactId)
      return
    }

    clearHoverTrackTimer(contactId)
    hoverTrackTimers.set(
      contactId,
      window.setTimeout(() => {
        hoverTrackTimers.delete(contactId)
        reportContactClick(contactId)
      }, HOVER_TRACK_DELAY_MS)
    )
  }

  function disposeContactPopoverTracking() {
    hoverTrackTimers.forEach((timer) => {
      clearTimeout(timer)
    })
    hoverTrackTimers.clear()
  }

  return {
    handleContactPopoverChange,
    disposeContactPopoverTracking,
  }
}

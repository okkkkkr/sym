export const PERSISTED_RESOURCE_STATE = 'persisted'
export const TRANSIENT_RESOURCE_STATE = 'transient'

export function normalizeManagedUploadFileList(fileList = []) {
  return fileList.filter(Boolean).map((file) => ({
    ...file,
    resourceState: file.resourceState || (file.rawUrl ? PERSISTED_RESOURCE_STATE : ''),
  }))
}

export function markUploadFilesPersisted(fileList = []) {
  return normalizeManagedUploadFileList(fileList).map((file) => ({
    ...file,
    resourceState: PERSISTED_RESOURCE_STATE,
  }))
}

export function collectTransientResourceKeys(fileList = []) {
  return normalizeManagedUploadFileList(fileList)
    .filter((file) => file.resourceState === TRANSIENT_RESOURCE_STATE)
    .map((file) => String(file.rawUrl || '').trim())
    .filter(Boolean)
}

export function findRemovedUploadFiles(previousFileList = [], nextFileList = []) {
  const nextFileIds = new Set(normalizeManagedUploadFileList(nextFileList).map((file) => file.id))
  return normalizeManagedUploadFileList(previousFileList).filter(
    (file) => !nextFileIds.has(file.id)
  )
}

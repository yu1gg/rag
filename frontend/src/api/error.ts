export function getErrorMessage(
  error: unknown,
  fallback = '请求失败，请稍后重试。',
): string {
  if (error instanceof Error) {
    const message = error.message.trim()
    if (message) {
      return message
    }
  }

  if (error instanceof TypeError) {
    return '网络连接失败，请检查网络后重试。'
  }

  return fallback
}

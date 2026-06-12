import { describe, it, expect, beforeEach } from 'vitest'
import { useChatWorkspace } from '../chatWorkspace'

describe('chatWorkspace', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('initializes with default mode qa', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    expect(store.currentMode.value).toBe('qa')
    expect(store.activeSession.value).not.toBeNull()
  })

  it('creates a new session', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const initialCount = store.sessions.value.length
    store.createSession('summary')
    expect(store.sessions.value.length).toBe(initialCount + 1)
    expect(store.currentMode.value).toBe('summary')
  })

  it('appends and updates messages', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const session = store.activeSession.value!

    const msg = store.appendMessage({
      role: 'user', mode: 'qa', text: 'hello', status: 'success',
    })
    expect(session.messages.length).toBe(1)
    expect(session.messages[0].text).toBe('hello')

    store.updateMessage(session.id, msg.id, { text: 'updated' })
    expect(session.messages[0].text).toBe('updated')
  })

  it('deletes sessions', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const session = store.activeSession.value!
    store.deleteSession(session.id)
    expect(store.sessions.value.length).toBe(1)
  })

  it('normalizes mode to qa when restoring from localStorage', () => {
    localStorage.setItem(
      'project-x-chat-workspace:v1',
      JSON.stringify({
        activeSessionId: 'session_1',
        sessions: [
          {
            id: 'session_1',
            title: 'test',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            lastMode: 'unknown',
            messages: [],
          },
        ],
      }),
    )
    const store = useChatWorkspace()
    store.hydrateWorkspace('summary')
    expect(store.currentMode.value).toBe('summary')
    expect(store.activeSession.value!.lastMode).toBe('summary')
  })
})

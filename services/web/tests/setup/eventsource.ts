/** Controllable EventSource: MockEventSource.last().emit('stage.started', {...}). */
export class MockEventSource {
  static instances: MockEventSource[] = []
  url: string
  closed = false
  listeners: Record<string, ((e: MessageEvent) => void)[]> = {}

  constructor(url: string) {
    this.url = url
    MockEventSource.instances.push(this)
  }

  addEventListener(type: string, fn: (e: MessageEvent) => void) {
    ;(this.listeners[type] ??= []).push(fn)
  }

  removeEventListener(type: string, fn: (e: MessageEvent) => void) {
    this.listeners[type] = (this.listeners[type] ?? []).filter((f) => f !== fn)
  }

  close() {
    this.closed = true
  }

  emit(type: string, data: unknown) {
    const ev = new MessageEvent(type, {
      data: typeof data === 'string' ? data : JSON.stringify(data),
    })
    for (const fn of this.listeners[type] ?? []) fn(ev)
  }

  static last(): MockEventSource {
    return MockEventSource.instances[MockEventSource.instances.length - 1]
  }

  static reset() {
    MockEventSource.instances = []
  }
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { wsUrl } from '../lib/api'

export function useChatSocket(onEvent) {
  const socketRef = useRef(null)
  const eventRef = useRef(onEvent)
  const [connected, setConnected] = useState(false)
  const [enabled, setEnabled] = useState(true)

  useEffect(() => {
    eventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!enabled) return undefined
    let socket = null
    let retryTimer = null
    let disposed = false

    const connect = () => {
      if (disposed) return
      socket = new WebSocket(wsUrl())
      socketRef.current = socket

      socket.onopen = () => {
        if (socketRef.current === socket) setConnected(true)
      }
      socket.onmessage = (event) => {
        if (socketRef.current !== socket) return
        try {
          eventRef.current(JSON.parse(event.data))
        } catch {
          socket.close()
        }
      }
      socket.onclose = (closeEvent) => {
        if (socketRef.current !== socket) return
        socketRef.current = null
        setConnected(false)
        if (!disposed && !closeEvent.wasClean) {
          retryTimer = setTimeout(connect, 2500)
        }
      }
      socket.onerror = () => socket.close()
    }

    connect()
    return () => {
      disposed = true
      clearTimeout(retryTimer)
      if (socketRef.current === socket) {
        socketRef.current = null
        setConnected(false)
      }
      socket?.close()
    }
  }, [enabled])

  const send = useCallback((payload) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload))
      return true
    }
    return false
  }, [])

  const disconnect = useCallback(() => {
    setEnabled(false)
    socketRef.current?.close()
  }, [])

  return { connected, send, disconnect }
}

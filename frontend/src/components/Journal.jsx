import { useState } from 'react'
import Chat from './Chat'
import NotesSidebar from './NotesSidebar'

export default function Journal({ username, onLogout }) {
  const [notesOpen, setNotesOpen] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand small">
          <span className="brand-mark">✒</span>
          <span className="brand-name">Inkwell</span>
        </div>
        <div className="topbar-right">
          <button
            type="button"
            className="ghost"
            onClick={() => setNotesOpen((open) => !open)}
          >
            {notesOpen ? 'Hide journal' : 'Show journal'}
          </button>
          <span className="who">{username}</span>
          <button type="button" className="ghost" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>
      <main className="layout">
        <NotesSidebar visible={notesOpen} refreshKey={refreshKey} />
        <Chat onNoteSaved={() => setRefreshKey((key) => key + 1)} />
      </main>
    </div>
  )
}

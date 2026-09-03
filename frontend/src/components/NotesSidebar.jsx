import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function NotesSidebar({ visible, refreshKey }) {
  const [notes, setNotes] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!visible) return
    let cancelled = false
    api('/notes/')
      .then((data) => {
        if (!cancelled) setNotes(data)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [visible, refreshKey])

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api('/notes/', { method: 'POST', body: { title, content } })
      setTitle('')
      setContent('')
      setNotes(await api('/notes/'))
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id) => {
    await api(`/notes/${id}/`, { method: 'DELETE' })
    setNotes(await api('/notes/'))
  }

  if (!visible) return null

  return (
    <aside className="notes-panel">
      <h2>Journal</h2>
      <form className="note-form" onSubmit={save}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title (optional)"
          maxLength={200}
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What happened today?"
          rows={4}
          required
        />
        <button className="primary wide" type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Write it down'}
        </button>
        {error && <p className="form-error">{error}</p>}
      </form>
      <div className="notes-list">
        {notes.length === 0 && <p className="empty">Nothing written yet. The first entry is the hardest.</p>}
        {notes.map((note) => (
          <article key={note.id} className="note">
            <div className="note-date">{new Date(note.created_at).toLocaleDateString()}</div>
            {note.title && <h3>{note.title}</h3>}
            <p>{note.content}</p>
            <button type="button" className="ghost small" onClick={() => remove(note.id)}>
              Delete
            </button>
          </article>
        ))}
      </div>
    </aside>
  )
}

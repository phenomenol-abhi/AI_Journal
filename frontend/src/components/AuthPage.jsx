import { useState } from 'react'
import { api } from '../lib/api'

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const path = mode === 'login' ? '/auth/login/' : '/auth/register/'
      const data = await api(path, { method: 'POST', body: { username, password } })
      onAuth(data, username)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-stage">
      <div className="auth-card">
        <div className="brand">
          <span className="brand-mark">✒</span>
          <h1>Inkwell</h1>
          <p className="brand-sub">a private journal, remembered</p>
        </div>
        <div className="auth-tabs">
          <button
            type="button"
            className={mode === 'login' ? 'tab active' : 'tab'}
            onClick={() => { setMode('login'); setError('') }}
          >
            Log in
          </button>
          <button
            type="button"
            className={mode === 'signup' ? 'tab active' : 'tab'}
            onClick={() => { setMode('signup'); setError('') }}
          >
            Sign up
          </button>
        </div>
        <form onSubmit={submit}>
          <label>
            <span>Username</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              minLength={3}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              minLength={6}
            />
          </label>
          <button className="primary wide" type="submit" disabled={busy}>
            {busy ? '…' : mode === 'login' ? 'Enter the study' : 'Begin the journal'}
          </button>
        </form>
        {error && <p className="form-error">{error}</p>}
        <p className="auth-foot">Your entries stay yours. Answers come only from what you wrote.</p>
      </div>
    </div>
  )
}

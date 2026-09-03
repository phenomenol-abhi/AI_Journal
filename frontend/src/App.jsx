import { useEffect, useState } from 'react'
import AuthPage from './components/AuthPage'
import Journal from './components/Journal'
import { clearAuth, getAuth, setAuth } from './lib/api'

export default function App() {
  const [auth, setAuthState] = useState(getAuth())
  const [theme, setTheme] = useState(() => localStorage.getItem('inkwell_theme') || 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('inkwell_theme', theme)
  }, [theme])

  const handleAuth = (data, username) => {
    setAuth({ access: data.access, username })
    setAuthState({ access: data.access, username })
  }

  const handleLogout = () => {
    clearAuth()
    setAuthState(null)
  }

  return (
    <>
      <button
        type="button"
        className="theme-toggle"
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        title="Switch theme"
      >
        {theme === 'dark' ? '☀ Light' : '☾ Dark'}
      </button>
      {!auth?.access ? <AuthPage onAuth={handleAuth} /> : <Journal username={auth.username} onLogout={handleLogout} />}
    </>
  )
}

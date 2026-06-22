import { createContext, useContext, useEffect, useLayoutEffect, useState } from 'react'

export type ThemeMode = 'light' | 'dark'

type ThemeCtx = {
  mode: ThemeMode
  resolved: ThemeMode
  setMode: (mode: ThemeMode) => void
  toggleMode: () => void
}

const STORAGE_KEY = 'ngp:theme'
const LEGACY_KEY = 'avs-theme'

const Ctx = createContext<ThemeCtx>({
  mode: 'light',
  resolved: 'light',
  setMode: () => {},
  toggleMode: () => {},
})

function systemPrefersDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function readStoredMode(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
  if (stored === 'light' || stored === 'dark') return stored

  const legacy = localStorage.getItem(LEGACY_KEY)
  if (legacy === 'dark') return 'dark'
  if (legacy === 'light') return 'light'
  if (legacy === 'system') return systemPrefersDark() ? 'dark' : 'light'

  return systemPrefersDark() ? 'dark' : 'light'
}

function applyTheme(resolved: ThemeMode) {
  document.documentElement.dataset.theme = resolved
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => readStoredMode())

  useLayoutEffect(() => {
    applyTheme(mode)
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      if (!localStorage.getItem(STORAGE_KEY)) {
        const next = mq.matches ? 'dark' : 'light'
        setModeState(next)
        applyTheme(next)
      }
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  function setMode(next: ThemeMode) {
    setModeState(next)
  }

  function toggleMode() {
    setModeState((current) => (current === 'light' ? 'dark' : 'light'))
  }

  return (
    <Ctx.Provider value={{ mode, resolved: mode, setMode, toggleMode }}>
      {children}
    </Ctx.Provider>
  )
}

export function useTheme() {
  return useContext(Ctx)
}

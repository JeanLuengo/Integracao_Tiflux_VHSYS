import { useEffect } from 'react'
import { useCommandPalette } from './useCommandPalette'
import { useTheme } from '@/contexts/ThemeProvider'

export function useShortcuts() {
  const { toggle, setOpen } = useCommandPalette()
  const { toggleMode } = useTheme()

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const mod = e.metaKey || e.ctrlKey
      if (mod && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        toggle()
        return
      }
      if (e.key === 'Escape') {
        setOpen(false)
      }
      if (mod && e.shiftKey && e.key.toLowerCase() === 'l') {
        e.preventDefault()
        toggleMode()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [toggle, setOpen, toggleMode])
}

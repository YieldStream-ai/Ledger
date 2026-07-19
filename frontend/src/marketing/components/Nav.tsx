import { useState, useEffect } from 'react'
import { Menu, X } from 'lucide-react'
import { Container } from './ui/Container'
import { Button } from './ui/Button'
import { nav } from '../content'

export function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 h-16 transition-all duration-150 ${
        scrolled
          ? 'border-b border-[var(--border)] bg-white/80 backdrop-blur-md'
          : 'bg-transparent'
      }`}
    >
      <Container className="flex h-full items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold tracking-tight text-[var(--text-primary)]">
            Ledger
          </span>
          <span className="text-xs text-[var(--text-tertiary)]">by YieldStream</span>
        </div>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-8 md:flex">
          {nav.links.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Desktop CTAs */}
        <div className="hidden items-center gap-3 md:flex">
          <Button href="/app" variant="secondary" size="sm">
            TRY FOR FREE
          </Button>
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </Container>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-b border-[var(--border)] bg-white px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {nav.links.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm text-[var(--text-secondary)]"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <hr className="border-[var(--border)]" />
            <Button href="/app" size="sm">
              TRY FOR FREE
            </Button>
          </nav>
        </div>
      )}
    </header>
  )
}

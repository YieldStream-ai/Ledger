import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { clsx } from 'clsx'

interface Tab {
  label: string
  language: string
  code: string
}

interface CodeBlockProps {
  tabs?: Tab[]
  code?: string
  language?: string
  className?: string
}

export function CodeBlock({ tabs, code, language, className }: CodeBlockProps) {
  const [activeTab, setActiveTab] = useState(0)
  const [copied, setCopied] = useState(false)

  const activeCode = tabs ? tabs[activeTab].code : code || ''
  const activeLang = tabs ? tabs[activeTab].language : language || ''

  const handleCopy = async () => {
    await navigator.clipboard.writeText(activeCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={clsx('overflow-hidden rounded-lg bg-[var(--code-bg)]', className)}>
      {/* Tab bar */}
      {tabs && tabs.length > 1 && (
        <div className="flex items-center border-b border-white/10 px-4">
          {tabs.map((tab, i) => (
            <button
              key={tab.label}
              onClick={() => setActiveTab(i)}
              className={clsx(
                'px-3 py-2.5 text-xs font-medium transition-colors',
                i === activeTab
                  ? 'border-b border-white/60 text-white'
                  : 'text-[#71717A] hover:text-[#A1A1AA]'
              )}
            >
              {tab.label}
            </button>
          ))}
          {/* Copy button in tab bar */}
          <button
            onClick={handleCopy}
            className="ml-auto flex items-center gap-1 rounded px-2 py-1 text-xs text-[#71717A] transition-colors hover:text-white"
            aria-label="Copy code"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      )}

      {/* Code content */}
      <div className="relative overflow-x-auto p-4">
        {!tabs && (
          <button
            onClick={handleCopy}
            className="absolute top-3 right-3 flex items-center gap-1 rounded px-2 py-1 text-xs text-[#71717A] transition-colors hover:text-white"
            aria-label="Copy code"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        )}
        <pre className="font-[var(--font-mono)] text-sm leading-relaxed">
          <code className={clsx('block', `language-${activeLang}`)}>
            {highlightSyntax(activeCode, activeLang)}
          </code>
        </pre>
      </div>
    </div>
  )
}

function highlightSyntax(code: string, language: string): React.ReactNode[] {
  const lines = code.split('\n')
  return lines.map((line, i) => (
    <span key={i} className="block">
      {tokenizeLine(line, language)}
    </span>
  ))
}

function tokenizeLine(line: string, language: string): React.ReactNode[] {
  const tokens: React.ReactNode[] = []
  let remaining = line
  let key = 0

  while (remaining.length > 0) {
    let matched = false

    // Comments
    const commentPattern =
      language === 'python'
        ? /^(#.*)$/
        : language === 'bash'
          ? /^(#.*)$/
          : /^(\/\/.*)$/
    const commentMatch = remaining.match(commentPattern)
    if (commentMatch) {
      tokens.push(
        <span key={key++} className="text-[#6A9955]">
          {commentMatch[1]}
        </span>
      )
      remaining = remaining.slice(commentMatch[1].length)
      matched = true
      continue
    }

    // Strings (double and single quoted)
    const stringMatch = remaining.match(/^("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/)
    if (stringMatch) {
      tokens.push(
        <span key={key++} className="text-[#CE9178]">
          {stringMatch[1]}
        </span>
      )
      remaining = remaining.slice(stringMatch[1].length)
      matched = true
      continue
    }

    // Numbers
    const numMatch = remaining.match(/^(\b\d+\.?\d*\b)/)
    if (numMatch) {
      tokens.push(
        <span key={key++} className="text-[#B5CEA8]">
          {numMatch[1]}
        </span>
      )
      remaining = remaining.slice(numMatch[1].length)
      matched = true
      continue
    }

    // Keywords by language
    const keywords = getKeywords(language)
    const kwMatch = remaining.match(new RegExp(`^\\b(${keywords.join('|')})\\b`))
    if (kwMatch) {
      tokens.push(
        <span key={key++} className="text-[#569CD6]">
          {kwMatch[1]}
        </span>
      )
      remaining = remaining.slice(kwMatch[1].length)
      matched = true
      continue
    }

    // Built-ins / functions
    const fnMatch = remaining.match(/^(\w+)(?=\()/)
    if (fnMatch) {
      tokens.push(
        <span key={key++} className="text-[#DCDCAA]">
          {fnMatch[1]}
        </span>
      )
      remaining = remaining.slice(fnMatch[1].length)
      matched = true
      continue
    }

    // Flags (--flag or -f)
    const flagMatch = remaining.match(/^(-{1,2}[\w-]+)/)
    if (flagMatch && (language === 'bash' || language === 'shell')) {
      tokens.push(
        <span key={key++} className="text-[#9CDCFE]">
          {flagMatch[1]}
        </span>
      )
      remaining = remaining.slice(flagMatch[1].length)
      matched = true
      continue
    }

    // Variables ($VAR or ${VAR})
    const varMatch = remaining.match(/^(\$\{?\w+\}?)/)
    if (varMatch) {
      tokens.push(
        <span key={key++} className="text-[#9CDCFE]">
          {varMatch[1]}
        </span>
      )
      remaining = remaining.slice(varMatch[1].length)
      matched = true
      continue
    }

    if (!matched) {
      // Default: plain text, consume one char
      tokens.push(
        <span key={key++} className="text-[#D4D4D4]">
          {remaining[0]}
        </span>
      )
      remaining = remaining.slice(1)
    }
  }

  return tokens
}

function getKeywords(language: string): string[] {
  switch (language) {
    case 'python':
      return ['import', 'from', 'def', 'class', 'return', 'if', 'else', 'True', 'False', 'None', 'async', 'await', 'with', 'as', 'for', 'in', 'not', 'and', 'or']
    case 'javascript':
    case 'typescript':
      return ['import', 'export', 'from', 'const', 'let', 'var', 'function', 'return', 'if', 'else', 'new', 'async', 'await', 'true', 'false', 'null', 'undefined']
    case 'go':
      return ['package', 'import', 'func', 'main', 'var', 'const', 'return', 'if', 'else', 'for', 'range', 'type', 'struct', 'true', 'false', 'nil']
    case 'bash':
    case 'shell':
      return ['curl', 'echo', 'export', 'if', 'then', 'fi', 'for', 'do', 'done']
    default:
      return []
  }
}

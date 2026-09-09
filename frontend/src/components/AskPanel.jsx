import React, { useRef, useState } from 'react'
import { IconSend } from './Icons'

/**
 * Minimal renderer for the subset of markdown the advisory actually uses:
 * `### headings`, `- bullets`, and `**bold**`. Written inline rather than
 * pulling in a markdown library for three constructs, and it never injects
 * raw HTML.
 */
function renderInline(text, keyBase) {
  return text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={`${keyBase}-${i}`} className="font-semibold text-abyss-900">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={`${keyBase}-${i}`}>{part}</React.Fragment>
    )
  )
}

function Advisory({ text }) {
  const blocks = []
  let bullets = []

  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="my-1.5 space-y-1">
          {bullets.map((b, i) => (
            <li key={i} className="flex gap-2 text-[11.5px] leading-relaxed text-slate-700">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-abyss-400" />
              <span>{renderInline(b, `li-${blocks.length}-${i}`)}</span>
            </li>
          ))}
        </ul>
      )
      bullets = []
    }
  }

  for (const raw of String(text).split('\n')) {
    const line = raw.trim()
    if (!line) { flush(); continue }
    if (line.startsWith('###')) {
      flush()
      blocks.push(
        <h4 key={`h-${blocks.length}`}
            className="mt-2.5 text-[11px] font-bold uppercase tracking-wide text-abyss-700 first:mt-0">
          {line.replace(/^#+\s*/, '')}
        </h4>
      )
    } else if (/^[-*]\s+/.test(line)) {
      bullets.push(line.replace(/^[-*]\s+/, ''))
    } else {
      flush()
      blocks.push(
        <p key={`p-${blocks.length}`} className="my-1 text-[11.5px] leading-relaxed text-slate-700">
          {renderInline(line, `p-${blocks.length}`)}
        </p>
      )
    }
  }
  flush()
  return <div>{blocks}</div>
}

const SUGGESTIONS = [
  'Is it safe to fish today?',
  'Cyclone risk near Visakhapatnam',
  'Weather in Paradip',
]

export default function AskPanel({ language, station, t }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const inputRef = useRef(null)

  const ask = async (q) => {
    const text = (q ?? question).trim()
    if (!text || loading) return
    setLoading(true)
    setFailed(false)
    setAnswer(null)
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send the station in view so a question with no place name is
        // answered for the same water the dashboard is showing.
        body: JSON.stringify({
          question: text,
          language,
          lat: station?.lat,
          lon: station?.lon,
        }),
      })
      if (!res.ok) throw new Error(`ask returned ${res.status}`)
      const json = await res.json()
      setAnswer(json.answer)
      setMeta({ live: json.live, observedAt: json.observed_at, sources: json.sources })
    } catch {
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card p-4">
      <h2 className="mb-2.5 text-sm font-bold text-abyss-900">{t('ask')}</h2>

      <div className="relative">
        <textarea
          ref={inputRef}
          rows={2}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              ask()
            }
          }}
          placeholder={t('askPlaceholder')}
          className="focusable w-full resize-none rounded-lg border border-slate-200 bg-slate-50/60 p-2.5 pr-11 text-[11.5px] leading-relaxed text-abyss-900 placeholder:text-slate-400 transition-colors hover:border-slate-300 focus:bg-white"
        />
        <button
          type="button"
          onClick={() => ask()}
          disabled={loading || !question.trim()}
          aria-label={t('askButton')}
          className="focusable absolute bottom-2.5 right-2.5 grid h-7 w-7 place-items-center rounded-md bg-abyss-700 text-white transition-all hover:bg-abyss-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
        >
          {loading ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          ) : (
            <IconSend className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {!answer && !loading && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => { setQuestion(s); ask(s) }}
              className="focusable rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-medium text-slate-600 transition-all hover:border-abyss-300 hover:bg-abyss-50 hover:text-abyss-800"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="mt-3 space-y-2">
          <div className="h-3 w-2/5 rounded shimmer" />
          <div className="h-3 w-full rounded shimmer" />
          <div className="h-3 w-4/5 rounded shimmer" />
        </div>
      )}

      {failed && (
        <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
          The advisory service did not respond. Please try again.
        </p>
      )}

      {answer && (
        <div className="animate-fade-up mt-3 rounded-lg border border-slate-200 bg-gradient-to-b from-white to-slate-50/70 p-3">
          <div className="scroll-slim max-h-72 overflow-y-auto pr-1">
            <Advisory text={answer} />
          </div>
          {meta?.observedAt && (
            <div className="mt-2 border-t border-slate-100 pt-2 font-mono text-[9.5px] text-slate-400">
              {meta.live ? `${t('observed')} ${meta.observedAt}Z` : 'no live feed'}
              {meta.sources?.length ? ` · ${meta.sources.join(', ')}` : ''}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

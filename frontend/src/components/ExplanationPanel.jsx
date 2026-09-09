import React, { useState } from 'react'

/**
 * Renders the XAI auditor's attribution: which driver actually produced the
 * hazard score, and by how much. Bars animate to their share on update.
 */
export default function ExplanationPanel({ data, t }) {
  const [openKey, setOpenKey] = useState(null)
  const explanation = data?.explanation
  const factors = explanation?.factors || []

  if (!factors.length) return null

  return (
    <section className="card p-4">
      <h2 className="mb-2 text-sm font-bold text-abyss-900">{t('why')}</h2>
      <p className="mb-3 text-[11px] leading-relaxed text-slate-600">{explanation.summary}</p>

      <div className="space-y-2">
        {factors.map((f, i) => {
          const pct = Math.round((f.share_of_result || 0) * 100)
          const open = openKey === f.key
          const tone =
            f.influence === 'high'
              ? 'from-abyss-500 to-abyss-700'
              : f.influence === 'medium'
              ? 'from-teal-400 to-teal-600'
              : 'from-slate-300 to-slate-400'

          return (
            <div key={f.key}>
              <button
                type="button"
                onClick={() => setOpenKey(open ? null : f.key)}
                className="focusable group w-full rounded-lg px-1 py-1 text-left transition-colors hover:bg-slate-50"
                aria-expanded={open}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-[11px] font-semibold text-abyss-800">
                    {f.name}
                  </span>
                  <span className="tnum shrink-0 text-[11px] font-bold text-slate-500">
                    {pct}%
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r ${tone}`}
                    style={{
                      width: `${pct}%`,
                      transition: 'width 900ms cubic-bezier(.16,1,.3,1)',
                      transitionDelay: `${i * 80}ms`,
                    }}
                  />
                </div>
              </button>
              {open && f.meaning && (
                <p className="animate-fade-up mt-1 px-1 text-[10.5px] leading-relaxed text-slate-500">
                  {f.meaning}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

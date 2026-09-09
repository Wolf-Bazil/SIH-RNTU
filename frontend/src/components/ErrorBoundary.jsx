import React from 'react'

/**
 * Keeps one failing panel from blanking the entire dashboard. A crash in the
 * map must not take the alert feed and the advisory down with it.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error(`[ORCA] ${this.props.label || 'component'} failed`, error, info)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="flex h-full min-h-[120px] flex-col items-center justify-center gap-2 rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-center">
        <p className="text-[11px] font-semibold text-amber-800">
          {this.props.label || 'This panel'} could not be displayed.
        </p>
        <p className="max-w-xs font-mono text-[10px] leading-relaxed text-amber-700/80">
          {String(this.state.error?.message || this.state.error).slice(0, 160)}
        </p>
        <button
          type="button"
          onClick={() => this.setState({ error: null })}
          className="focusable rounded-md border border-amber-300 bg-white px-2.5 py-1 text-[10px] font-semibold text-amber-800 transition-colors hover:bg-amber-100"
        >
          Retry
        </button>
      </div>
    )
  }
}

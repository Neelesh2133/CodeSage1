// CodePanel renders scrolling mock code for security auditing presentation

export default function CodePanel() {
  const codeLines = [
    { text: 'def get_user_data(user_id):', type: 'plain' },
    { text: '    # WARNING: Potential SQL injection risk', type: 'comment' },
    { text: '    query = "SELECT * FROM users WHERE id=" + user_id', type: 'removed' },
    { text: '    # FIXED: Use parameterized queries to bind variables', type: 'comment' },
    { text: '    query = "SELECT * FROM users WHERE id = %s"', type: 'added' },
    { text: '    result = db.execute(query, (user_id,))', type: 'added' },
    { text: '    return result.fetchone()', type: 'added' },
    { text: '', type: 'plain' },
    { text: 'class ConnectionPool:', type: 'plain' },
    { text: '    def __init__(self, size=10):', type: 'plain' },
    { text: '        self.size = size', type: 'plain' },
    { text: '        self.connections = []', type: 'plain' },
    { text: '        # CRITICAL: SSL/TLS context enforcement', type: 'comment' },
    { text: '        self.ssl_context = create_default_context()', type: 'added' },
  ]

  const tags = [
    { label: 'SQL Injection Remediated', color: 'border-zinc-700 text-zinc-300 bg-zinc-900', top: '15%', delay: '0s' },
    { label: 'SSL/TLS Context Forced', color: 'border-zinc-700 text-zinc-300 bg-zinc-900', top: '48%', delay: '2.5s' },
    { label: 'Clean Code Check Passed', color: 'border-zinc-700 text-zinc-300 bg-zinc-900', top: '75%', delay: '5s' },
  ]

  const doubled = [...codeLines, ...codeLines]

  const renderLine = (line) => {
    if (line.type === 'comment') {
      return <span className="text-zinc-500 italic">{line.text}</span>
    }
    
    const keywords = ['def', 'class', 'return', 'import', 'from', 'self']
    let words = line.text.split(/(\s+|=|\(|\)|,|\+)/)
    
    return words.map((word, idx) => {
      if (keywords.includes(word)) {
        return <span key={idx} className="text-zinc-400 font-semibold">{word}</span>
      }
      if (word.startsWith('"') || word.startsWith("'")) {
        return <span key={idx} className="text-zinc-300">{word}</span>
      }
      if (word.match(/^\d+$/)) {
        return <span key={idx} className="text-zinc-400">{word}</span>
      }
      if (line.type === 'removed') {
        return <span key={idx} className="text-rose-400 line-through decoration-rose-500/50">{word}</span>
      }
      if (line.type === 'added') {
        return <span key={idx} className="text-emerald-400 font-medium">{word}</span>
      }
      return <span key={idx} className="text-zinc-400">{word}</span>
    })
  }

  return (
    <div className="hidden md:flex relative w-1/2 bg-zinc-950 border-r border-zinc-800 overflow-hidden flex-col justify-between p-8 line-grid-bg">
      {/* Subtle top spotlight glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-white/[0.02] rounded-full blur-[120px] pointer-events-none" />

      {/* Header Info */}
      <div className="z-10 flex items-center justify-between">
        <div>
          <p className="text-zinc-500 text-[10px] uppercase tracking-widest font-semibold font-mono">Security Engine</p>
          <h3 className="text-zinc-200 text-sm font-medium mt-0.5 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse" />
            Auditor Core Active
          </h3>
        </div>
        <div className="text-zinc-400 text-[10px] font-mono bg-zinc-900/80 px-2 py-0.5 rounded border border-zinc-800">
          v2.4.0
        </div>
      </div>

      {/* Code window */}
      <div className="relative my-auto w-full max-w-xl mx-auto h-[350px] overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-md p-5 font-mono text-[11px] leading-6 shadow-2xl">
        <div className="absolute top-3 left-4 flex gap-1.5 z-20">
          <div className="w-2 h-2 rounded-full bg-zinc-800" />
          <div className="w-2 h-2 rounded-full bg-zinc-800" />
          <div className="w-2 h-2 rounded-full bg-zinc-800" />
        </div>

        <div className="absolute top-3 right-4 text-[10px] text-zinc-500">review_agent.py</div>

        <div className="mt-6 h-full overflow-hidden relative">
          <div className="animate-scroll-code flex flex-col gap-0.5">
            {doubled.map((line, i) => {
              const bgClass = line.type === 'added' 
                ? 'bg-emerald-950/10 border-l-2 border-emerald-500/50 pl-1' 
                : line.type === 'removed' 
                  ? 'bg-rose-950/10 border-l-2 border-rose-500/50 pl-1' 
                  : 'pl-[3px]'

              return (
                <div key={i} className={`flex items-start gap-4 py-0.5 ${bgClass}`}>
                  <span className="text-zinc-600 select-none text-right w-6 inline-block font-mono text-[10px] pt-0.5">{i + 1}</span>
                  <div className="flex-1 whitespace-pre">
                    {renderLine(line)}
                    {i === codeLines.length - 1 && (
                      <span className="inline-block w-1.5 h-3.5 bg-zinc-400 ml-1 animate-blink align-middle" />
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Floating status tags */}
      {tags.map((tag, i) => (
        <div
          key={i}
          className={`animate-fade-tag absolute right-6 text-[11px] px-3 py-1.5 border rounded-lg shadow-lg font-medium backdrop-blur-sm z-20 flex items-center gap-2 ${tag.color}`}
          style={{ top: tag.top, animationDelay: tag.delay }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
          {tag.label}
        </div>
      ))}

      {/* Footer Info */}
      <div className="z-10 flex justify-between items-center text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
        <div>Client-Side Auditor</div>
        <div className="flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-zinc-800" />
          <span>Local execution</span>
        </div>
      </div>
    </div>
  )
}
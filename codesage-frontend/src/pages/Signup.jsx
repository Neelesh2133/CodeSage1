import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import client from '../api/client'
import CodePanel from '../components/CodePanel'
import { BackgroundPaths } from '../components/ui/background-paths'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await client.post('/auth/signup', { email, password })
      navigate('/login')
    } catch (err) {
      setError(err.response?.status === 400 ? 'That email is already registered.' : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <BackgroundPaths title="CodeSage Auditor">
      <div className="min-h-screen flex text-zinc-100 relative overflow-hidden bg-transparent">
        {/* Left Code Showcase Panel */}
        <CodePanel />

        {/* Right Sign up Card Panel */}
        <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-12 z-10">
          <div className="w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-xl p-8 shadow-2xl relative vercel-panel border-beam-container">
            
            {/* Moving border beam animation */}
            <div className="border-beam-line" />
            
            <div className="mb-8 relative z-10">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded bg-white text-zinc-950 flex items-center justify-center font-bold text-sm shadow-md">
                  S
                </div>
                <h1 className="font-sans text-xl font-bold tracking-tight text-white">
                  CodeSage
                </h1>
              </div>
              <p className="text-xs text-zinc-300">
                Create a free developer account to begin security scans.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-300 mb-1.5 font-mono">
                  Email Address
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                    </svg>
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="developer@company.com"
                    className="w-full bg-zinc-950 border border-zinc-700 text-white rounded-lg pl-9 pr-3.5 py-2 text-xs focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all placeholder:text-zinc-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-300 mb-1.5 font-mono">
                  Password (min 8 characters)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    placeholder="••••••••"
                    className="w-full bg-zinc-950 border border-zinc-700 text-white rounded-lg pl-9 pr-10 py-2 text-xs focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all placeholder:text-zinc-500 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-400 hover:text-white transition-colors focus:outline-none"
                  >
                    {showPassword ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-lg p-3 flex items-center gap-2">
                  <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-white text-zinc-950 py-2.5 rounded-lg text-xs font-bold hover:bg-zinc-200 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none shadow"
              >
                {loading ? 'Initializing account...' : 'Create account'}
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-zinc-800 text-center text-xs text-zinc-400 relative z-10 font-mono">
              Already have an account?{' '}
              <Link to="/login" className="text-white font-medium transition-colors underline">
                Sign in
              </Link>
            </div>

          </div>
        </div>
      </div>
    </BackgroundPaths>
  )
}
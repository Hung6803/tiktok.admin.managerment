export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">TikTok Manager</h1>
        <p className="text-xl text-gray-600 mb-8">
          Multi-account TikTok management and scheduling platform
        </p>
        <div className="space-x-4">
          <a
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Login
          </a>
          <a
            href="/register"
            className="px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
          >
            Register
          </a>
        </div>
      </div>
    </main>
  )
}

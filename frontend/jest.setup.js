import '@testing-library/jest-dom'

// Suppress console warnings during tests
['warn', 'error'].forEach(method => {
  const originalMethod = console[method]
  console[method] = jest.fn((...args) => {
    if (!args[0]?.includes('useAuth must be used within AuthProvider')) {
      originalMethod(...args)
    }
  })
})

// Restore original console methods after tests
afterAll(() => {
  ['warn', 'error'].forEach(method => {
    console[method] = console[method].mockRestore()
  })
})
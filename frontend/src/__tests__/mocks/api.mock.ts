export const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
}

export const mockAuthResponse = {
  access_token: 'fake_access_token',
  refresh_token: 'fake_refresh_token',
  user: {
    id: '123',
    email: 'test@example.com',
    username: 'testuser'
  }
}

export const setupMockApi = () => {
  mockApiClient.post.mockImplementation((url, data) => {
    switch(url) {
      case '/auth/login':
        return Promise.resolve({ data: mockAuthResponse })
      case '/auth/register':
        return Promise.resolve({ data: mockAuthResponse })
      default:
        return Promise.reject(new Error('Not mocked'))
    }
  })

  mockApiClient.get.mockImplementation((url) => {
    switch(url) {
      case '/auth/me':
        return Promise.resolve({ data: mockAuthResponse.user })
      default:
        return Promise.reject(new Error('Not mocked'))
    }
  })
}

// Reset mock implementation before each test
export const resetMockApi = () => {
  mockApiClient.get.mockReset()
  mockApiClient.post.mockReset()
  mockApiClient.put.mockReset()
  mockApiClient.delete.mockReset()
}
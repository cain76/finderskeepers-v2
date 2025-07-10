# React Testing Library Patterns and Best Practices
**Date**: 07-09-2025  
**Source**: React Testing Library Documentation via Context7  
**Library**: @testing-library/react  
**Project**: FindersKeepers v2 - React Testing Implementation  

## Overview

React Testing Library is the standard testing utility for React applications. It provides simple and complete testing utilities that encourage good testing practices by focusing on user interactions rather than implementation details.

## Core Principles

1. **User-Centric Testing**: Tests should resemble how users interact with your application
2. **Accessibility First**: Queries prioritize accessible elements and roles
3. **Implementation Details**: Avoid testing implementation details like state or props directly
4. **Maintainable Tests**: Write tests that can survive refactoring

## Essential Imports

```jsx
import '@testing-library/jest-dom' // Custom matchers
import { render, fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
```

## Basic Component Testing

### Simple Component Test

```jsx
import * as React from 'react'
import { render, fireEvent, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Component under test
function HiddenMessage({children}) {
  const [showMessage, setShowMessage] = React.useState(false)
  return (
    <div>
      <label htmlFor="toggle">Show Message</label>
      <input
        id="toggle"
        type="checkbox"
        onChange={e => setShowMessage(e.target.checked)}
        checked={showMessage}
      />
      {showMessage ? children : null}
    </div>
  )
}

// Test
test('shows the children when the checkbox is checked', () => {
  const testMessage = 'Test Message'
  render(<HiddenMessage>{testMessage}</HiddenMessage>)

  // Initially message should not be visible
  expect(screen.queryByText(testMessage)).toBeNull()

  // Click checkbox to show message
  fireEvent.click(screen.getByLabelText(/show/i))

  // Message should now be visible
  expect(screen.getByText(testMessage)).toBeInTheDocument()
})
```

## Advanced Patterns

### API Integration Testing with Mock Service Worker

```jsx
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import { render, fireEvent, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import Login from '../login'

// Mock API responses
const fakeUserResponse = {token: 'fake_user_token'}
const server = setupServer(
  rest.post('/api/login', (req, res, ctx) => {
    return res(ctx.json(fakeUserResponse))
  }),
)

// Setup and teardown
beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  window.localStorage.removeItem('token')
})
afterAll(() => server.close())

test('allows the user to login successfully', async () => {
  render(<Login />)

  // Fill out the form
  fireEvent.change(screen.getByLabelText(/username/i), {
    target: {value: 'chuck'},
  })
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: {value: 'norris'},
  })

  fireEvent.click(screen.getByText(/submit/i))

  // Wait for async operations
  const alert = await screen.findByRole('alert')

  // Verify success
  expect(alert).toHaveTextContent(/congrats/i)
  expect(window.localStorage.getItem('token')).toEqual(fakeUserResponse.token)
})

test('handles server exceptions', async () => {
  // Mock server error for this test
  server.use(
    rest.post('/api/login', (req, res, ctx) => {
      return res(ctx.status(500), ctx.json({message: 'Internal server error'}))
    }),
  )

  render(<Login />)

  // Fill out form and submit
  fireEvent.change(screen.getByLabelText(/username/i), {
    target: {value: 'chuck'},
  })
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: {value: 'norris'},
  })

  fireEvent.click(screen.getByText(/submit/i))

  // Wait for error message
  const alert = await screen.findByRole('alert')

  expect(alert).toHaveTextContent(/internal server error/i)
  expect(window.localStorage.getItem('token')).toBeNull()
})
```

## Query Methods

### Query Hierarchy (Best Practices)

1. **Accessible by Everyone**
   - `getByRole()` - Best choice for most elements
   - `getByLabelText()` - Form elements
   - `getByPlaceholderText()` - Form elements
   - `getByText()` - Non-interactive elements

2. **Semantic Queries**
   - `getByAltText()` - Images
   - `getByTitle()` - Elements with title attribute

3. **Test IDs (Last Resort)**
   - `getByTestId()` - When other queries aren't feasible

### Query Variants

```jsx
// Throws error if not found
const element = screen.getByText('Hello')

// Returns null if not found
const element = screen.queryByText('Hello')

// Returns promise, waits for element to appear
const element = await screen.findByText('Hello')

// Multiple elements
const elements = screen.getAllByText('Hello')
```

## Testing React Hooks

### Custom Hook Testing

```jsx
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

test('should increment counter', () => {
  const { result } = renderHook(() => useCounter())
  
  act(() => {
    result.current.increment()
  })
  
  expect(result.current.count).toBe(1)
})
```

### Hook with Dependencies

```jsx
import { renderHook } from '@testing-library/react'
import { useWebSocket } from './useWebSocket'

test('should connect to WebSocket', () => {
  const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))
  
  expect(result.current.isConnected).toBe(false)
  
  // Mock WebSocket connection
  act(() => {
    // Simulate connection
  })
  
  expect(result.current.isConnected).toBe(true)
})
```

## User Event vs FireEvent

### FireEvent (Legacy)

```jsx
import { fireEvent } from '@testing-library/react'

// Direct event firing
fireEvent.click(button)
fireEvent.change(input, { target: { value: 'new value' } })
```

### User Event (Recommended)

```jsx
import userEvent from '@testing-library/user-event'

test('user interactions', async () => {
  const user = userEvent.setup()
  
  // More realistic user interactions
  await user.click(button)
  await user.type(input, 'new value')
  await user.keyboard('[Enter]')
})
```

## Async Testing Patterns

### Waiting for Elements

```jsx
// Wait for element to appear
const element = await screen.findByText('Loading complete')

// Wait for element to disappear
await waitForElementToBeRemoved(screen.getByText('Loading...'))

// Wait for condition
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument()
})
```

### Testing Loading States

```jsx
test('shows loading state', async () => {
  render(<AsyncComponent />)
  
  // Should show loading initially
  expect(screen.getByText('Loading...')).toBeInTheDocument()
  
  // Wait for loading to complete
  await waitForElementToBeRemoved(screen.getByText('Loading...'))
  
  // Should show content
  expect(screen.getByText('Content loaded')).toBeInTheDocument()
})
```

## FindersKeepers v2 Testing Patterns

### Chat Component Testing

```jsx
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import ChatInterface from '../components/ChatInterface'

// Mock WebSocket for chat testing
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}

// Mock WebSocket constructor
global.WebSocket = jest.fn(() => mockWebSocket)

test('sends message and displays response', async () => {
  const user = userEvent.setup()
  render(<ChatInterface />)
  
  const input = screen.getByPlaceholderText('Type your message...')
  const sendButton = screen.getByText('Send')
  
  // Type message
  await user.type(input, 'Hello AI')
  await user.click(sendButton)
  
  // Verify message was sent
  expect(mockWebSocket.send).toHaveBeenCalledWith(
    JSON.stringify({
      type: 'chat',
      message: 'Hello AI',
      timestamp: expect.any(String)
    })
  )
  
  // Simulate WebSocket message
  const messageEvent = new MessageEvent('message', {
    data: JSON.stringify({
      type: 'chat_response',
      message: 'Hello! How can I help?'
    })
  })
  
  // Trigger message handler
  mockWebSocket.addEventListener.mock.calls
    .find(([event]) => event === 'message')[1](messageEvent)
  
  // Verify response appears
  expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument()
})
```

### Knowledge Graph Component Testing

```jsx
test('performs knowledge search', async () => {
  const server = setupServer(
    rest.post('/api/knowledge/query', (req, res, ctx) => {
      return res(ctx.json({
        answer: 'Docker is a containerization platform',
        sources: [{ type: 'document', id: 'docker-guide' }]
      }))
    })
  )
  
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())
  
  const user = userEvent.setup()
  render(<KnowledgeSearch />)
  
  const searchInput = screen.getByPlaceholderText('Search knowledge...')
  const searchButton = screen.getByText('Search')
  
  await user.type(searchInput, 'What is Docker?')
  await user.click(searchButton)
  
  // Wait for search results
  const result = await screen.findByText(/Docker is a containerization platform/)
  expect(result).toBeInTheDocument()
  
  // Verify sources are shown
  expect(screen.getByText('Sources:')).toBeInTheDocument()
})
```

## Testing Best Practices

### 1. Use Descriptive Test Names

```jsx
// Good
test('shows error message when login fails with invalid credentials', () => {})

// Bad
test('login error', () => {})
```

### 2. Arrange, Act, Assert

```jsx
test('user can toggle message visibility', () => {
  // Arrange
  render(<HiddenMessage>Secret message</HiddenMessage>)
  
  // Act
  fireEvent.click(screen.getByLabelText(/show/i))
  
  // Assert
  expect(screen.getByText('Secret message')).toBeInTheDocument()
})
```

### 3. Use Realistic Data

```jsx
// Good
const mockUser = {
  id: 'user-123',
  name: 'John Doe',
  email: 'john@example.com'
}

// Bad
const mockUser = {
  id: 1,
  name: 'test',
  email: 'test'
}
```

### 4. Clean Up After Tests

```jsx
afterEach(() => {
  // Clear mocks
  jest.clearAllMocks()
  
  // Reset localStorage
  window.localStorage.clear()
  
  // Reset any global state
  cleanup()
})
```

## Common Jest-DOM Matchers

```jsx
// Presence/absence
expect(element).toBeInTheDocument()
expect(element).not.toBeInTheDocument()

// Visibility
expect(element).toBeVisible()
expect(element).toBeHidden()

// Content
expect(element).toHaveTextContent('Hello')
expect(element).toHaveDisplayValue('input value')

// Attributes
expect(element).toHaveAttribute('disabled')
expect(element).toHaveClass('active')

// Form elements
expect(element).toBeChecked()
expect(element).toBeDisabled()
expect(element).toHaveValue('text')
```

## Testing with Context

```jsx
import { render } from '@testing-library/react'
import { ThemeProvider } from './ThemeContext'

const renderWithTheme = (ui, options = {}) => {
  const Wrapper = ({ children }) => (
    <ThemeProvider value="dark">{children}</ThemeProvider>
  )
  
  return render(ui, { wrapper: Wrapper, ...options })
}

test('renders with theme', () => {
  renderWithTheme(<MyComponent />)
  // Test themed component
})
```

## Required Dependencies

```json
{
  "devDependencies": {
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/user-event": "^14.4.3",
    "msw": "^1.3.0",
    "jest": "^29.0.0"
  }
}
```

## Setup Files

### jest.config.js
```javascript
module.exports = {
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  testEnvironment: 'jsdom',
}
```

### setupTests.js
```javascript
import '@testing-library/jest-dom'

// Mock WebSocket if needed
global.WebSocket = jest.fn(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}))
```

## Resources

- [React Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)
- [Common Testing Patterns](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Testing Playground](https://testing-playground.com/)

## Next Steps for FindersKeepers v2

1. Install React Testing Library and related dependencies
2. Set up Jest configuration with jsdom environment
3. Create test utilities for common patterns
4. Write tests for WebSocket chat functionality
5. Test knowledge graph integration
6. Add continuous integration with test coverage
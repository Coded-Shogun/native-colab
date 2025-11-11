/**
 * Authentication E2E Tests
 * Tests for user registration, login, and logout flows
 */

describe('Authentication Flow', () => {
  const testUser = {
    fullName: 'Test User',
    email: `test-${Date.now()}@example.com`,
    password: 'SecurePass123!',
  }

  beforeEach(() => {
    // Clear localStorage and cookies before each test
    cy.clearLocalStorage()
    cy.clearCookies()
  })

  describe('User Registration', () => {
    it('should register a new user successfully', () => {
      cy.visit('/register')

      // Fill out registration form
      cy.findByLabelText(/full name|name/i).type(testUser.fullName)
      cy.findByLabelText(/email/i).type(testUser.email)
      cy.findByLabelText(/^password$/i).type(testUser.password)

      // Submit form
      cy.findByRole('button', { name: /sign up|register|create account/i }).click()

      // Should redirect to dashboard
      cy.url().should('include', '/dashboard')

      // Should see welcome message or user name
      cy.findByText(testUser.fullName).should('be.visible')
    })

    it('should show error for duplicate email', () => {
      // First registration
      cy.register(testUser.fullName, testUser.email, testUser.password)
      cy.visit('/logout')

      // Try to register again with same email
      cy.visit('/register')
      cy.findByLabelText(/full name|name/i).type('Another User')
      cy.findByLabelText(/email/i).type(testUser.email)
      cy.findByLabelText(/^password$/i).type(testUser.password)
      cy.findByRole('button', { name: /sign up|register|create account/i }).click()

      // Should show error message
      cy.findByText(/email already registered|already exists/i).should('be.visible')
    })

    it('should validate password strength', () => {
      cy.visit('/register')

      cy.findByLabelText(/full name|name/i).type('Test User')
      cy.findByLabelText(/email/i).type('test@example.com')
      cy.findByLabelText(/^password$/i).type('weak')

      // Should show validation error
      cy.findByText(/password.*least.*8.*characters|password.*strong/i).should('be.visible')
    })
  })

  describe('User Login', () => {
    beforeEach(() => {
      // Create a test user for login tests
      cy.register(testUser.fullName, testUser.email, testUser.password)
      cy.visit('/logout')
    })

    it('should login successfully with correct credentials', () => {
      cy.login(testUser.email, testUser.password)

      // Should be on dashboard
      cy.url().should('include', '/dashboard')
      cy.findByText(testUser.fullName).should('be.visible')
    })

    it('should show error for incorrect password', () => {
      cy.visit('/login')
      cy.findByLabelText(/email/i).type(testUser.email)
      cy.findByLabelText(/password/i).type('WrongPassword123!')
      cy.findByRole('button', { name: /sign in|login/i }).click()

      // Should show error message
      cy.findByText(/invalid.*credentials|incorrect.*password/i).should('be.visible')
    })

    it('should show error for non-existent user', () => {
      cy.visit('/login')
      cy.findByLabelText(/email/i).type('nonexistent@example.com')
      cy.findByLabelText(/password/i).type('Password123!')
      cy.findByRole('button', { name: /sign in|login/i }).click()

      // Should show error message
      cy.findByText(/user not found|invalid.*credentials/i).should('be.visible')
    })
  })

  describe('User Logout', () => {
    it('should logout successfully', () => {
      cy.register(testUser.fullName, testUser.email, testUser.password)

      // Find and click logout button
      cy.findByRole('button', { name: /sign out|logout/i }).click()

      // Should redirect to login page
      cy.url().should('include', '/login')

      // Should not be able to access protected routes
      cy.visit('/dashboard')
      cy.url().should('include', '/login')
    })
  })

  describe('Protected Routes', () => {
    it('should redirect to login when accessing protected routes without auth', () => {
      cy.visit('/dashboard')
      cy.url().should('include', '/login')

      cy.visit('/chat')
      cy.url().should('include', '/login')

      cy.visit('/projects')
      cy.url().should('include', '/login')
    })

    it('should allow access to protected routes when authenticated', () => {
      cy.register(testUser.fullName, testUser.email, testUser.password)

      // Should be able to access dashboard
      cy.visit('/dashboard')
      cy.url().should('include', '/dashboard')

      // Should be able to access chat
      cy.visit('/chat')
      cy.url().should('include', '/chat')

      // Should be able to access projects
      cy.visit('/projects')
      cy.url().should('include', '/projects')
    })
  })

  describe('Session Persistence', () => {
    it('should maintain session after page reload', () => {
      cy.register(testUser.fullName, testUser.email, testUser.password)

      // Reload page
      cy.reload()

      // Should still be authenticated
      cy.url().should('include', '/dashboard')
      cy.findByText(testUser.fullName).should('be.visible')
    })

    it('should persist token in localStorage', () => {
      cy.register(testUser.fullName, testUser.email, testUser.password)

      // Check if token exists in localStorage
      cy.window().then((win) => {
        const token = win.localStorage.getItem('access_token')
        expect(token).to.exist
        expect(token).to.be.a('string')
        expect(token.length).to.be.greaterThan(0)
      })
    })
  })
})

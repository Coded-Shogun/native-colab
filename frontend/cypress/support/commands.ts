/// <reference types="cypress" />

// ***********************************************
// Custom Cypress Commands
// ***********************************************

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to login
       * @example cy.login('user@example.com', 'password123')
       */
      login(email: string, password: string): Chainable<void>

      /**
       * Custom command to register a new user
       * @example cy.register('John Doe', 'john@example.com', 'password123')
       */
      register(fullName: string, email: string, password: string): Chainable<void>

      /**
       * Custom command to create a workspace
       * @example cy.createWorkspace('My Workspace')
       */
      createWorkspace(name: string): Chainable<void>

      /**
       * Custom command to wait for Socket.io connection
       * @example cy.waitForSocket()
       */
      waitForSocket(): Chainable<void>

      /**
       * Custom command to send a chat message
       * @example cy.sendChatMessage('Hello, world!')
       */
      sendChatMessage(message: string): Chainable<void>
    }
  }
}

// Login command
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login')
  cy.findByLabelText(/email/i).type(email)
  cy.findByLabelText(/password/i).type(password)
  cy.findByRole('button', { name: /sign in|login/i }).click()

  // Wait for navigation to dashboard
  cy.url().should('include', '/dashboard')
  cy.findByText(/dashboard/i).should('be.visible')
})

// Register command
Cypress.Commands.add('register', (fullName: string, email: string, password: string) => {
  cy.visit('/register')
  cy.findByLabelText(/full name|name/i).type(fullName)
  cy.findByLabelText(/email/i).type(email)
  cy.findByLabelText(/^password$/i).type(password)
  cy.findByRole('button', { name: /sign up|register|create account/i }).click()

  // Wait for successful registration
  cy.url().should('include', '/dashboard')
})

// Create workspace command
Cypress.Commands.add('createWorkspace', (name: string) => {
  cy.findByRole('button', { name: /create workspace|new workspace/i }).click()
  cy.findByLabelText(/workspace name|name/i).type(name)
  cy.findByRole('button', { name: /create|save/i }).click()

  // Wait for workspace to be created
  cy.findByText(name).should('be.visible')
})

// Wait for Socket.io connection
Cypress.Commands.add('waitForSocket', () => {
  // Wait for the "Live" indicator or connection status
  cy.window().then((win) => {
    return new Cypress.Promise((resolve) => {
      const checkConnection = () => {
        // Check if socket is connected in the window object
        if ((win as any).socketConnected === true) {
          resolve()
        } else {
          setTimeout(checkConnection, 100)
        }
      }
      checkConnection()
    })
  })
})

// Send chat message
Cypress.Commands.add('sendChatMessage', (message: string) => {
  cy.findByPlaceholderText(/message/i).type(message)
  cy.findByRole('button', { name: /send/i }).click()
})

export {}

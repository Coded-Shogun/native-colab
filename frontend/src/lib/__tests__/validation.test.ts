/**
 * Validation Tests
 * Unit tests for validation utilities
 */

import { describe, it, expect } from 'vitest';
import { validation, validationMessages } from '../validation';

describe('Validation Utilities', () => {
  describe('isEmail', () => {
    it('should validate correct email addresses', () => {
      expect(validation.isEmail('test@example.com')).toBe(true);
      expect(validation.isEmail('user.name@domain.co.uk')).toBe(true);
      expect(validation.isEmail('user+tag@example.com')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(validation.isEmail('invalid')).toBe(false);
      expect(validation.isEmail('invalid@')).toBe(false);
      expect(validation.isEmail('@example.com')).toBe(false);
      expect(validation.isEmail('test@')).toBe(false);
    });
  });

  describe('isStrongPassword', () => {
    it('should validate strong passwords', () => {
      expect(validation.isStrongPassword('Password123')).toBe(true);
      expect(validation.isStrongPassword('MyP@ssw0rd')).toBe(true);
      expect(validation.isStrongPassword('Abcd1234')).toBe(true);
    });

    it('should reject weak passwords', () => {
      expect(validation.isStrongPassword('short')).toBe(false);
      expect(validation.isStrongPassword('alllowercase1')).toBe(false);
      expect(validation.isStrongPassword('ALLUPPERCASE1')).toBe(false);
      expect(validation.isStrongPassword('NoNumbers')).toBe(false);
    });
  });

  describe('isRequired', () => {
    it('should validate non-empty values', () => {
      expect(validation.isRequired('test')).toBe(true);
      expect(validation.isRequired(123)).toBe(true);
      expect(validation.isRequired(true)).toBe(true);
    });

    it('should reject empty values', () => {
      expect(validation.isRequired('')).toBe(false);
      expect(validation.isRequired('   ')).toBe(false);
      expect(validation.isRequired(null)).toBe(false);
      expect(validation.isRequired(undefined)).toBe(false);
    });
  });

  describe('minLength', () => {
    it('should validate minimum length', () => {
      expect(validation.minLength('hello', 3)).toBe(true);
      expect(validation.minLength('hello', 5)).toBe(true);
    });

    it('should reject strings below minimum length', () => {
      expect(validation.minLength('hi', 3)).toBe(false);
      expect(validation.minLength('', 1)).toBe(false);
    });
  });

  describe('isURL', () => {
    it('should validate correct URLs', () => {
      expect(validation.isURL('https://example.com')).toBe(true);
      expect(validation.isURL('http://localhost:3000')).toBe(true);
      expect(validation.isURL('https://sub.domain.com/path')).toBe(true);
    });

    it('should reject invalid URLs', () => {
      expect(validation.isURL('not a url')).toBe(false);
      expect(validation.isURL('example.com')).toBe(false); // Missing protocol
    });
  });
});

describe('Validation Messages', () => {
  it('should provide correct error messages', () => {
    expect(validationMessages.required).toBe('This field is required');
    expect(validationMessages.email).toBe('Please enter a valid email address');
    expect(validationMessages.minLength(8)).toBe('Must be at least 8 characters');
    expect(validationMessages.maxLength(100)).toBe('Must be no more than 100 characters');
  });
});

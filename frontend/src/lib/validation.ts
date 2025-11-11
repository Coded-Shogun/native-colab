/**
 * Validation Utilities
 * Common validation functions for forms and inputs
 */

export const validation = {
  /**
   * Validate email format
   */
  isEmail: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  /**
   * Validate password strength
   * Requires: min 8 chars, 1 uppercase, 1 lowercase, 1 number
   */
  isStrongPassword: (password: string): boolean => {
    if (password.length < 8) return false;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    return hasUpperCase && hasLowerCase && hasNumber;
  },

  /**
   * Validate URL format
   */
  isURL: (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Validate phone number (US format)
   */
  isPhoneNumber: (phone: string): boolean => {
    const phoneRegex = /^[\d\s\-\(\)]+$/;
    const digitsOnly = phone.replace(/\D/g, '');
    return phoneRegex.test(phone) && digitsOnly.length === 10;
  },

  /**
   * Validate required field
   */
  isRequired: (value: any): boolean => {
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  },

  /**
   * Validate minimum length
   */
  minLength: (value: string, min: number): boolean => {
    return value.length >= min;
  },

  /**
   * Validate maximum length
   */
  maxLength: (value: string, max: number): boolean => {
    return value.length <= max;
  },

  /**
   * Validate number range
   */
  inRange: (value: number, min: number, max: number): boolean => {
    return value >= min && value <= max;
  },

  /**
   * Validate file size
   */
  isValidFileSize: (file: File, maxSizeInMB: number): boolean => {
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
    return file.size <= maxSizeInBytes;
  },

  /**
   * Validate file type
   */
  isValidFileType: (file: File, allowedTypes: string[]): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    return extension ? allowedTypes.includes(extension) : false;
  },

  /**
   * Validate date is in the future
   */
  isFutureDate: (date: Date): boolean => {
    return date.getTime() > Date.now();
  },

  /**
   * Validate date is in the past
   */
  isPastDate: (date: Date): boolean => {
    return date.getTime() < Date.now();
  },
};

/**
 * Form validation error messages
 */
export const validationMessages = {
  required: 'This field is required',
  email: 'Please enter a valid email address',
  password: 'Password must be at least 8 characters with uppercase, lowercase, and number',
  url: 'Please enter a valid URL',
  phoneNumber: 'Please enter a valid phone number',
  minLength: (min: number) => `Must be at least ${min} characters`,
  maxLength: (max: number) => `Must be no more than ${max} characters`,
  fileSize: (max: number) => `File size must be less than ${max}MB`,
  fileType: (types: string[]) => `Allowed file types: ${types.join(', ')}`,
};

/**
 * Sanitize input to prevent XSS
 */
export function sanitizeInput(input: string): string {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}

/**
 * Validate form data
 */
export function validateForm<T extends Record<string, any>>(
  data: T,
  rules: Partial<Record<keyof T, (value: any) => string | null>>
): Record<keyof T, string | null> {
  const errors = {} as Record<keyof T, string | null>;

  for (const field in rules) {
    const validator = rules[field];
    if (validator) {
      errors[field] = validator(data[field]);
    }
  }

  return errors;
}

/**
 * Check if form has errors
 */
export function hasErrors<T extends Record<string, any>>(
  errors: Record<keyof T, string | null>
): boolean {
  return Object.values(errors).some((error) => error !== null);
}

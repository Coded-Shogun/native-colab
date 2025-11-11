/**
 * Logger Utility
 * Centralized logging with different levels and optional external service integration
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  data?: any;
  timestamp: string;
  userAgent?: string;
  url?: string;
}

class Logger {
  private isDevelopment: boolean;
  private enableConsole: boolean;

  constructor() {
    this.isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';
    this.enableConsole = this.isDevelopment || import.meta.env.VITE_ENABLE_LOGGING === 'true';
  }

  /**
   * Create log entry with metadata
   */
  private createLogEntry(level: LogLevel, message: string, data?: any): LogEntry {
    return {
      level,
      message,
      data,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
  }

  /**
   * Send log to external service (e.g., Sentry, LogRocket)
   */
  private sendToExternalService(entry: LogEntry): void {
    // Integration with Sentry
    if (import.meta.env.VITE_SENTRY_DSN && entry.level === 'error') {
      // Sentry.captureException(new Error(entry.message), {
      //   extra: entry.data,
      //   level: entry.level,
      // });
    }

    // Integration with custom logging endpoint
    if (import.meta.env.VITE_LOGGING_ENDPOINT) {
      fetch(import.meta.env.VITE_LOGGING_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      }).catch(() => {
        // Silently fail to prevent infinite loops
      });
    }
  }

  /**
   * Debug level logging
   */
  debug(message: string, data?: any): void {
    const entry = this.createLogEntry('debug', message, data);

    if (this.enableConsole) {
      console.debug(`[DEBUG] ${message}`, data);
    }
  }

  /**
   * Info level logging
   */
  info(message: string, data?: any): void {
    const entry = this.createLogEntry('info', message, data);

    if (this.enableConsole) {
      console.info(`[INFO] ${message}`, data);
    }
  }

  /**
   * Warning level logging
   */
  warn(message: string, data?: any): void {
    const entry = this.createLogEntry('warn', message, data);

    if (this.enableConsole) {
      console.warn(`[WARN] ${message}`, data);
    }

    // Always send warnings to external service in production
    if (!this.isDevelopment) {
      this.sendToExternalService(entry);
    }
  }

  /**
   * Error level logging
   */
  error(message: string, error?: Error | any): void {
    const entry = this.createLogEntry('error', message, {
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : error,
    });

    if (this.enableConsole) {
      console.error(`[ERROR] ${message}`, error);
    }

    // Always send errors to external service
    this.sendToExternalService(entry);
  }

  /**
   * Log API call
   */
  logApiCall(method: string, url: string, status: number, duration: number): void {
    const message = `API ${method} ${url} - ${status} (${duration}ms)`;

    if (status >= 500) {
      this.error(message, { method, url, status, duration });
    } else if (status >= 400) {
      this.warn(message, { method, url, status, duration });
    } else {
      this.debug(message, { method, url, status, duration });
    }
  }

  /**
   * Log user action for analytics
   */
  logUserAction(action: string, details?: any): void {
    this.info(`User Action: ${action}`, details);

    // Send to analytics service
    if (import.meta.env.VITE_GOOGLE_ANALYTICS_ID) {
      // Google Analytics event tracking
      if (typeof (window as any).gtag === 'function') {
        (window as any).gtag('event', action, details);
      }
    }

    if (import.meta.env.VITE_MIXPANEL_TOKEN) {
      // Mixpanel event tracking
      if (typeof (window as any).mixpanel === 'object') {
        (window as any).mixpanel.track(action, details);
      }
    }
  }

  /**
   * Log performance metric
   */
  logPerformance(metric: string, value: number, unit: string = 'ms'): void {
    this.debug(`Performance: ${metric} = ${value}${unit}`);

    // Send to performance monitoring service
    if (import.meta.env.VITE_ENABLE_ANALYTICS) {
      // Custom performance tracking
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Convenience exports
export const logDebug = logger.debug.bind(logger);
export const logInfo = logger.info.bind(logger);
export const logWarn = logger.warn.bind(logger);
export const logError = logger.error.bind(logger);
export const logApiCall = logger.logApiCall.bind(logger);
export const logUserAction = logger.logUserAction.bind(logger);
export const logPerformance = logger.logPerformance.bind(logger);

export default logger;

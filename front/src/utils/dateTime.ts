/**
 * Timezone utilities for UTC+3 (Moscow Time)
 * Handles date conversions between UTC and local timezone
 */

const TIMEZONE_OFFSET = 3 * 60 * 60 * 1000 // UTC+3 in milliseconds

/**
 * Convert UTC date string (YYYY-MM-DD) to local timezone string
 * @param dateStr - Date string in YYYY-MM-DD format (interpreted as UTC)
 * @returns Date string in YYYY-MM-DD format (local timezone)
 */
export function utcToLocalDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const utcDate = new Date(Date.UTC(year, month - 1, day))
  const localDate = new Date(utcDate.getTime() + TIMEZONE_OFFSET)

  return localDate.toISOString().split('T')[0]!
}

/**
 * Convert local timezone date string to UTC date string
 * @param dateStr - Date string in YYYY-MM-DD format (local timezone)
 * @returns Date string in YYYY-MM-DD format (UTC)
 */
export function localToUtcDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const localDate = new Date(Date.UTC(year, month - 1, day))
  const utcDate = new Date(localDate.getTime() - TIMEZONE_OFFSET)

  return utcDate.toISOString().split('T')[0]!
}

/**
 * Get current date in local timezone (YYYY-MM-DD format)
 * @returns Date string in YYYY-MM-DD format
 */
export function getCurrentLocalDate(): string {
  const now = new Date()
  const localDate = new Date(now.getTime() + TIMEZONE_OFFSET)
  return localDate.toISOString().split('T')[0]!
}

/**
 * Get a date in local timezone from Date object
 * @param date - Date object
 * @returns Date string in YYYY-MM-DD format (local timezone)
 */
export function dateToLocalDateString(date: Date): string {
  const localDate = new Date(date.getTime() + TIMEZONE_OFFSET)
  return localDate.toISOString().split('T')[0]!
}

/**
 * Check if a date string matches today's date in local timezone
 * @param dateStr - Date string in YYYY-MM-DD format
 * @returns True if date is today
 */
export function isToday(dateStr: string): boolean {
  return dateStr === getCurrentLocalDate()
}

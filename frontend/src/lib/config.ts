/**
 * Payroll Frontend Configuration
 */

// API configuration - shared FastAPI backend
const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8040';
export const API_BASE_URL = `${backendUrl}/api/v1`;

# 🎯 OneTaskAssistant Preview Code System - Frontend Integration Guide

## 📋 Overview

Your backend preview code system is **fully implemented and ready** for frontend integration. This document provides everything your frontend team needs to integrate with the preview code APIs.

## 🔗 API Endpoints

### Base URL
- **Local Development**: `http://localhost:7071/api`
- **Production**: `https://your-function-app.azurewebsites.net/api`

---

## 🔐 User APIs

### 1. **Validate Preview Code**

**Endpoint**: `POST /api/preview-codes/validate`

**Purpose**: Validates a preview code and marks it as used by the current user.

**Request**:
```typescript
interface ValidateCodeRequest {
  code: string;      // The preview code (e.g., "WSHA61P9")
  user_id: string;   // Unique identifier for the user
}
```

**Success Response** (200):
```typescript
interface ValidateCodeResponse {
  valid: true;
  message: "Preview code is valid";
  error_code: null;
}
```

**Error Responses** (400):
```typescript
// Invalid code
{
  valid: false;
  message: "Invalid preview code. Please check your code and try again.";
  error_code: "INVALID_CODE";
}

// Already used code
{
  valid: false;
  message: "This preview code has already been used";
  error_code: "CODE_ALREADY_USED";
}

// Server error
{
  valid: false;
  message: "Server error validating preview code";
  error_code: "SERVER_ERROR";
}
```

**Frontend Example**:
```typescript
async function validatePreviewCode(code: string, userId: string): Promise<boolean> {
  try {
    const response = await fetch('/api/preview-codes/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code.trim().toUpperCase(),
        user_id: userId
      })
    });

    const result = await response.json();
    
    if (result.valid) {
      // Code is valid - allow user to proceed
      return true;
    } else {
      // Show error message to user
      showError(result.message);
      return false;
    }
  } catch (error) {
    showError('Unable to validate preview code. Please try again.');
    return false;
  }
}
```

---

### 2. **Get Preview Code Statistics**

**Endpoint**: `GET /api/preview-codes/stats`

**Purpose**: Returns current usage statistics (useful for admin dashboards or progress indicators).

**Response** (200):
```typescript
interface PreviewCodeStats {
  total_codes: number;      // Total number of codes in system
  used_codes: number;       // Number of codes already used
  remaining_codes: number;  // Number of codes still available
  usage_rate: number;       // Percentage used (0-100)
}
```

**Frontend Example**:
```typescript
async function getPreviewCodeStats(): Promise<PreviewCodeStats | null> {
  try {
    const response = await fetch('/api/preview-codes/stats');
    return await response.json();
  } catch (error) {
    console.error('Failed to get preview code stats:', error);
    return null;
  }
}
```

---

## 👨‍💼 Admin APIs

### 3. **Bulk Load Preview Codes**

**Endpoint**: `POST /api/bulk_load_codes`

**Purpose**: Admin function to create multiple preview codes at once.

**Request**:
```typescript
interface BulkLoadRequest {
  codes: string[];  // Array of preview codes to create
}
```

**Response** (200):
```typescript
interface BulkLoadResponse {
  success: boolean;
  message: string;
  created_count: number;
  failed_codes: string[];  // Codes that failed to create (e.g., duplicates)
}
```

---

### 4. **Reset All Preview Codes**

**Endpoint**: `POST /api/reset_codes`

**Purpose**: Admin function to reset all codes to unused state.

**Response** (200):
```typescript
interface ResetResponse {
  success: boolean;
  message: string;
  reset_count: number;
}
```

---

## 🎫 Available Preview Codes

Your system currently has these **24 unused codes** ready for distribution:

```
F7WQUWYS  1PHZ5MG3  K2TV2NU5  ZLQQX14D  NV9I9IVY
YEW4C753  72SQQPNK  RKAFLHWJ  I4QDZ6WY  BUKEF4R8
9Z1NKGD8  JG7RSHA2  GIV1SGIJ  8U3YEW49  DEBG4CU5
4P2GI8WY  N5X19GBM  5NGHZCGT  7PTE4AMP  24Q4YMG8
ECNLZ3NV  6448ZFBK  PU9II8NN  8TFQ95N6
```

---

## 🎨 Frontend Implementation Guide

### Step 1: Add Preview Code Input to Profile Setup

```jsx
// ProfileSetup.jsx
import React, { useState } from 'react';

function ProfileSetup() {
  const [previewCode, setPreviewCode] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isCodeValid, setIsCodeValid] = useState(false);
  const [codeError, setCodeError] = useState('');

  const validateCode = async (code) => {
    if (!code.trim()) {
      setCodeError('Please enter a preview code');
      setIsCodeValid(false);
      return;
    }

    setIsValidating(true);
    setCodeError('');

    try {
      const response = await fetch('/api/preview-codes/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code.trim().toUpperCase(),
          user_id: getCurrentUserId() // Your user ID logic
        })
      });

      const result = await response.json();

      if (result.valid) {
        setIsCodeValid(true);
        setCodeError('');
      } else {
        setIsCodeValid(false);
        setCodeError(result.message);
      }
    } catch (error) {
      setIsCodeValid(false);
      setCodeError('Unable to validate code. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="profile-setup">
      {/* Your existing profile fields */}
      
      <div className="preview-code-section">
        <label htmlFor="previewCode">Preview Code *</label>
        <input
          type="text"
          id="previewCode"
          value={previewCode}
          onChange={(e) => setPreviewCode(e.target.value)}
          onBlur={() => validateCode(previewCode)}
          placeholder="Enter your preview code"
          maxLength={8}
          style={{
            borderColor: codeError ? '#ef4444' : isCodeValid ? '#10b981' : '#d1d5db'
          }}
        />
        
        {isValidating && (
          <div className="text-blue-600">Validating code...</div>
        )}
        
        {codeError && (
          <div className="text-red-600">{codeError}</div>
        )}
        
        {isCodeValid && (
          <div className="text-green-600">✓ Valid preview code</div>
        )}
      </div>

      <button 
        type="submit" 
        disabled={!isCodeValid || isValidating}
        className="submit-btn"
      >
        Complete Setup
      </button>
    </div>
  );
}
```

### Step 2: Add Error Handling

```typescript
// utils/previewCodeApi.ts
export enum PreviewCodeError {
  INVALID_CODE = 'INVALID_CODE',
  CODE_ALREADY_USED = 'CODE_ALREADY_USED',
  SERVER_ERROR = 'SERVER_ERROR'
}

export interface ValidationResult {
  success: boolean;
  error?: PreviewCodeError;
  message?: string;
}

export async function validatePreviewCode(
  code: string, 
  userId: string
): Promise<ValidationResult> {
  try {
    const response = await fetch('/api/preview-codes/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code.trim().toUpperCase(),
        user_id: userId
      })
    });

    const result = await response.json();

    if (result.valid) {
      return { success: true };
    } else {
      return {
        success: false,
        error: result.error_code as PreviewCodeError,
        message: result.message
      };
    }
  } catch (error) {
    return {
      success: false,
      error: PreviewCodeError.SERVER_ERROR,
      message: 'Unable to validate preview code. Please try again.'
    };
  }
}
```

### Step 3: Add Admin Dashboard (Optional)

```jsx
// AdminDashboard.jsx
import React, { useState, useEffect } from 'react';

function AdminDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/preview-codes/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="admin-dashboard">
      <h2>Preview Code Statistics</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Codes</h3>
          <p>{stats.total_codes}</p>
        </div>
        
        <div className="stat-card">
          <h3>Used Codes</h3>
          <p>{stats.used_codes}</p>
        </div>
        
        <div className="stat-card">
          <h3>Remaining</h3>
          <p>{stats.remaining_codes}</p>
        </div>
        
        <div className="stat-card">
          <h3>Usage Rate</h3>
          <p>{stats.usage_rate.toFixed(1)}%</p>
        </div>
      </div>

      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${stats.usage_rate}%` }}
        />
      </div>
    </div>
  );
}
```

---

## 🚀 Integration Checklist

### Frontend Development:
- [ ] Add preview code input field to profile setup
- [ ] Implement real-time validation on blur/change
- [ ] Add visual feedback (loading, success, error states)
- [ ] Prevent form submission without valid code
- [ ] Handle all error cases gracefully
- [ ] Add proper loading states

### Testing:
- [ ] Test with valid codes (use codes from the list above)
- [ ] Test with invalid codes (e.g., "INVALID123")
- [ ] Test with already used codes
- [ ] Test network error scenarios
- [ ] Test form submission flow

### Production:
- [ ] Update API base URL for production
- [ ] Verify CORS is working correctly
- [ ] Test end-to-end user flow
- [ ] Monitor validation attempts and success rates

---

## 🔧 Configuration

### Environment Variables:
```typescript
// config.ts
export const API_CONFIG = {
  baseUrl: process.env.NODE_ENV === 'production' 
    ? 'https://your-function-app.azurewebsites.net/api'
    : 'http://localhost:7071/api'
};
```

### CORS Configuration:
The backend is already configured to accept requests from:
- `http://localhost:3000` (React dev server)
- `http://localhost:5173` (Vite dev server)
- Your production domain

---

## 📞 Support

If you encounter any issues during integration:

1. **Check the browser console** for detailed error messages
2. **Verify the API endpoint URLs** are correct
3. **Ensure the backend is running** (locally or deployed)
4. **Check CORS configuration** if getting cross-origin errors

The backend provides comprehensive logging, so server-side issues can be debugged through the Azure Functions logs.

---

## 🎉 You're Ready!

Your preview code system is **fully implemented and tested**. The frontend integration should be straightforward with the examples above. The system will enforce the 25-user limit automatically and provide clear feedback to users throughout the process.

**Happy coding! 🚀**

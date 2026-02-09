# 🎨 Frontend Implementation Plan — Cookie Authentication UI

## 📋 Overview

Complete guide for implementing cookie authentication UI in the profile page with privacy-focused design.

---

## 🎯 Frontend Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `app/profile/page.tsx` | **NEW** | Full profile page with cookie management |
| `components/Sidebar.tsx` | **UPDATE** | Add Profile link to navigation |
| `lib/api.ts` | **UPDATE** | Add 4 new API methods for cookie CRUD |
| `lib/types.ts` | **UPDATE** | Add cookie-related TypeScript types |
| `globals.css` | **UPDATE** | Add CSS for password-style input masking |

**Total New Lines**: ~550 lines  
**Files Modified**: 4 files  
**Files Created**: 1 file  

---

## 📦 Change #1: Create Profile Page (NEW FILE)

**File**: `frontend/app/profile/page.tsx`

### Features Included:
- ✅ Two-tab authentication selector (UM Library vs My Cookies)
- ✅ Cookie input with show/hide toggle
- ✅ Real-time validation with status indicators
- ✅ Encrypted storage explanation
- ✅ Cookie expiry status display
- ✅ Clear/revoke functionality
- ✅ Step-by-step user instructions
- ✅ Security & privacy notice
- ✅ Responsive design matching existing pages

### Component Structure:
```
ProfilePage
├─ Header (User icon + title)
├─ Lexis Authentication Card
│   ├─ Status Badge (Active/Expired)
│   ├─ Method Selector
│   │   ├─ UM Library (default)
│   │   └─ My Cookies (fast mode)
│   ├─ Cookie Configuration Panel
│   │   ├─ Info Banner (how-to guide)
│   │   ├─ JSON Textarea (masked by default)
│   │   ├─ Show/Hide Toggle
│   │   ├─ Validation Status
│   │   └─ Action Buttons (Validate, Save)
│   └─ Current Status Display
│       ├─ Expiry timestamp
│       └─ Clear button
└─ Privacy Notice Card
```

### Key Implementation Details:

**State Management**:
```typescript
const [authMethod, setAuthMethod] = useState<'um_library' | 'cookies'>('um_library')
const [cookieInput, setCookieInput] = useState('')
const [showCookies, setShowCookies] = useState(false)
const [validationStatus, setValidationStatus] = useState<{
    validated: boolean
    valid: boolean
    message: string
} | null>(null)
```

**API Integration**:
```typescript
// Fetch current status
const { data: cookieStatus, refetch } = useQuery({
    queryKey: ['lexis-cookie-status'],
    queryFn: () => api.getLexisCookieStatus(),
})

// Validate cookies before saving
const validateMutation = useMutation({
    mutationFn: async (cookies: any[]) => {
        return api.validateLexisCookies(cookies)
    },
    onSuccess: (data) => {
        setValidationStatus({
            validated: true,
            valid: data.valid,
            message: data.message
        })
    }
})

// Save validated cookies
const saveMutation = useMutation({
    mutationFn: async (cookies: any[]) => {
        return api.saveLexisCookies(cookies)
    },
    onSuccess: () => {
        refetch()
        setCookieInput('')
    }
})
```

**User Flow**:
1. User pastes cookies from EditThisCookie export
2. Clicks "Validate" → API checks if cookies work
3. If valid, "Save" button enables
4. Click "Save" → Encrypted and stored in DB
5. Status updates to show expiry time
6. All future searches auto-use cookies

---

## 📦 Change #2: Update Sidebar Navigation

**File**: `frontend/components/Sidebar.tsx`

### What Changes:
Add "Profile" link to the ACCOUNT section

### Before:
```typescript
const navigation = [
    {
        section: 'COMMAND',
        items: [
            { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }
        ]
    },
    {
        section: 'OPERATIONS',
        items: [
            { name: 'Matter Intake', href: '/upload', icon: Briefcase },
            { name: 'Pleadings', href: '/drafting', icon: FileText },
            { name: 'Research', href: '/research', icon: Search },
            { name: 'Hearings', href: '/evidence', icon: Calendar },
            { name: 'Doc Chat', href: '/paralegal', icon: Sparkles }
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'All Matters', href: '/matters', icon: Folder },
            { name: 'Pricing', href: '/pricing', icon: CreditCard }
        ]
    }
]
```

### After:
```typescript
import { User } from 'lucide-react' // ADD THIS IMPORT

const navigation = [
    {
        section: 'COMMAND',
        items: [
            { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }
        ]
    },
    {
        section: 'OPERATIONS',
        items: [
            { name: 'Matter Intake', href: '/upload', icon: Briefcase },
            { name: 'Pleadings', href: '/drafting', icon: FileText },
            { name: 'Research', href: '/research', icon: Search },
            { name: 'Hearings', href: '/evidence', icon: Calendar },
            { name: 'Doc Chat', href: '/paralegal', icon: Sparkles }
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'All Matters', href: '/matters', icon: Folder },
            { name: 'Pricing', href: '/pricing', icon: CreditCard }
        ]
    },
    // NEW SECTION
    {
        section: 'ACCOUNT',
        items: [
            { name: 'Profile', href: '/profile', icon: User }
        ]
    }
]
```

**Visual Result**: New "ACCOUNT" section appears at bottom of sidebar with Profile link

---

## 📦 Change #3: Add API Methods

**File**: `frontend/lib/api.ts`

### What Changes:
Add 4 new methods to the exported `api` object

### Add After Line 637 (at end of api object):

```typescript
    // ==========================================
    // User Settings - Lexis Cookie Management
    // ==========================================
    
    /**
     * Get current Lexis cookie authentication status
     * @returns Status object with auth method and expiry
     */
    getLexisCookieStatus: async () => {
        try {
            const response = await apiClient.get('/user/lexis-cookies/status')
            return response.data
        } catch (error) {
            console.error('Error fetching cookie status:', error)
            throw error
        }
    },

    /**
     * Validate Lexis cookies before saving
     * @param cookies - Array of cookie objects from browser export
     * @returns Validation result with valid boolean and message
     */
    validateLexisCookies: async (cookies: any[]) => {
        try {
            const response = await apiClient.post('/user/lexis-cookies/validate', { 
                cookies 
            })
            return response.data
        } catch (error) {
            console.error('Error validating cookies:', error)
            throw error
        }
    },

    /**
     * Save validated cookies to user profile (encrypted)
     * @param cookies - Array of validated cookie objects
     * @returns Success response with expiry timestamp
     */
    saveLexisCookies: async (cookies: any[]) => {
        try {
            const response = await apiClient.post('/user/lexis-cookies/save', { 
                cookies 
            })
            return response.data
        } catch (error) {
            console.error('Error saving cookies:', error)
            throw error
        }
    },

    /**
     * Clear saved cookies and revert to UM Library auth
     * @returns Success confirmation
     */
    clearLexisCookies: async () => {
        try {
            const response = await apiClient.delete('/user/lexis-cookies')
            return response.data
        } catch (error) {
            console.error('Error clearing cookies:', error)
            throw error
        }
    },
```

**Usage Example**:
```typescript
// In profile page component
const { data: status } = useQuery({
    queryKey: ['lexis-cookies'],
    queryFn: () => api.getLexisCookieStatus()
})

const validateMutation = useMutation({
    mutationFn: (cookies) => api.validateLexisCookies(cookies)
})
```

---

## 📦 Change #4: Add TypeScript Types

**File**: `frontend/lib/types.ts`

### What Changes:
Add type definitions for cookie-related API responses

### Add After Line 157 (at end of file):

```typescript
// ==========================================
// Cookie Authentication Types
// ==========================================

/**
 * Lexis cookie structure from browser export
 */
export interface LexisCookie {
    name: string
    value: string
    domain?: string
    path?: string
    httpOnly?: boolean
    secure?: boolean
    expirationDate?: number
}

/**
 * Cookie validation request payload
 */
export interface CookieValidationRequest {
    cookies: LexisCookie[]
}

/**
 * Cookie validation response
 */
export interface CookieValidationResponse {
    valid: boolean
    message: string
    estimated_expiry?: string
}

/**
 * Cookie save response
 */
export interface CookieSaveResponse {
    success: boolean
    message: string
    auth_method: 'um_library' | 'cookies'
    expires_at?: string
}

/**
 * Cookie status response (from /status endpoint)
 */
export interface CookieStatusResponse {
    auth_method: 'um_library' | 'cookies'
    has_cookies: boolean
    expires_at?: string
    is_expired?: boolean
    status: 'active' | 'expired' | 'using_default'
}

/**
 * User authentication method preference
 */
export type AuthMethod = 'um_library' | 'cookies'
```

**Benefits**:
- Full TypeScript autocomplete in VS Code
- Type checking prevents bugs
- Better developer experience

---

## 📦 Change #5: Add CSS for Cookie Masking

**File**: `frontend/app/globals.css`

### What Changes:
Add CSS class for password-style input masking (hides cookie values)

### Add at end of file:

```css
/* ==========================================
 * Cookie Input Security Styling
 * ========================================== */

/**
 * Hide textarea content with dots (like password input)
 * Used for cookie textarea when showCookies = false
 */
.text-security-disc {
    -webkit-text-security: disc;
    -moz-text-security: disc;
    text-security: disc;
}

/* Fallback for browsers without text-security support */
@supports not ((-webkit-text-security: disc) or (-moz-text-security: disc) or (text-security: disc)) {
    .text-security-disc {
        font-family: 'password', monospace;
        letter-spacing: 0.3em;
    }
}
```

**Usage in Profile Page**:
```typescript
<textarea
    className={`... ${!showCookies ? 'text-security-disc' : ''}`}
    value={cookieInput}
    // ... other props
/>
```

**Result**: When user pastes cookies and hide is toggled, text appears as: `●●●●●●●●●●●●●`

---

## 🎨 UI/UX Design Details

### Color Scheme (matches existing design):
- Primary Gold: `var(--gold-primary)` (#D4A853)
- Neon Cyan: `var(--neon-cyan)` (for active states)
- Neon Green: `var(--neon-green)` (for success/fast mode)
- Background: `var(--bg-primary)`, `var(--bg-tertiary)`

### Component States:

**Authentication Method Cards**:
```typescript
// UM Library (default)
border: gray → hover: cyan
speed indicator: "15-20s"

// My Cookies (fast)
border: gray → hover: green
speed badge: "FAST" + "5-8s"
```

**Status Badges**:
```typescript
Active:   ✓ Green badge + "Active"
Expired:  ⚠️ Red badge + "Cookies Expired"
Default:  Gray + "Using UM Library"
```

**Validation States**:
```typescript
Not Validated: Neutral gray
Validating:    Blue with spinner
Valid:         Green with checkmark
Invalid:       Red with X icon
```

### Responsive Breakpoints:
```css
Desktop (lg+):  Full width cards, side-by-side buttons
Tablet (md):    Stacked layout, full-width buttons
Mobile (sm):    Single column, condensed spacing
```

---

## 🔄 User Journey Flow

### Scenario 1: First-Time Setup

```
1. User clicks "Profile" in sidebar
   ↓
2. Sees "UM Library" selected by default
   ↓
3. Clicks "My Cookies" tab
   ↓
4. Reads info banner (how to export cookies)
   ↓
5. Opens Lexis in browser → Logs in → Exports cookies
   ↓
6. Pastes JSON in textarea
   ↓
7. Clicks "Validate" → Spinner shows → Success message
   ↓
8. Clicks "Save" → Success toast → Status updates
   ↓
9. Future searches now use cookies (3x faster)
```

### Scenario 2: Cookie Expired

```
1. User visits profile page
   ↓
2. Sees red badge: "Cookies Expired"
   ↓
3. Status shows expiry timestamp
   ↓
4. User has 2 options:
   a) Update cookies (paste new JSON)
   b) Click "Clear Cookies" (revert to UM flow)
```

### Scenario 3: Revoke Access

```
1. User wants to stop using cookies
   ↓
2. Visits profile page
   ↓
3. Clicks "Clear Cookies" in status section
   ↓
4. Confirmation → Cookies deleted from DB
   ↓
5. Auth method reverts to "UM Library"
   ↓
6. Searches now use default flow
```

---

## 🧪 Frontend Testing Checklist

### Component Rendering
```
[ ] Profile page loads without errors
[ ] Sidebar shows "Profile" link
[ ] Profile link navigates to /profile
[ ] Page matches design system (colors, spacing)
[ ] Responsive on mobile/tablet/desktop
[ ] Icons render correctly (Lucide icons)
```

### State Management
```
[ ] Auth method toggle works
[ ] Cookie input updates on paste
[ ] Show/Hide toggle masks/unmasks text
[ ] Validation status updates correctly
[ ] Error messages display properly
[ ] Success states show as expected
```

### API Integration
```
[ ] getLexisCookieStatus fetches on mount
[ ] validateLexisCookies sends correct payload
[ ] saveLexisCookies saves encrypted data
[ ] clearLexisCookies removes data
[ ] Loading states show during API calls
[ ] Error handling works (try/catch)
```

### User Interactions
```
[ ] Validate button disabled when input empty
[ ] Save button disabled until validation passes
[ ] Clear button shows confirmation
[ ] JSON parsing errors show helpful message
[ ] Expiry timestamp displays correctly
[ ] Status badge reflects real-time state
```

### Security Checks
```
[ ] Cookie values masked by default
[ ] Show toggle works correctly
[ ] No cookies in console.log
[ ] No cookies in Network tab (encrypted)
[ ] Developer tools don't expose raw values
```

---

## 📦 Installation & Dependencies

### Required Packages (already installed):
```json
{
  "@tanstack/react-query": "^5.x",
  "lucide-react": "^0.x",
  "next": "14.x"
}
```

### No New Dependencies Needed! ✅

All required libraries are already in your project.

---

## 🚀 Implementation Steps (Execute in Order)

### Step 1: Add Types (5 min)
```bash
# Edit: frontend/lib/types.ts
# Add cookie-related TypeScript interfaces at end of file
```

### Step 2: Update API Client (10 min)
```bash
# Edit: frontend/lib/api.ts
# Add 4 new methods: getLexisCookieStatus, validate, save, clear
```

### Step 3: Add CSS (2 min)
```bash
# Edit: frontend/app/globals.css
# Add .text-security-disc class for masking
```

### Step 4: Update Sidebar (5 min)
```bash
# Edit: frontend/components/Sidebar.tsx
# Import User icon
# Add ACCOUNT section with Profile link
```

### Step 5: Create Profile Page (30 min)
```bash
# Create: frontend/app/profile/page.tsx
# Copy full component from migration plan
# Test locally: npm run dev → visit /profile
```

### Step 6: Test Integration (20 min)
```bash
# Test all user flows
# Verify API calls in Network tab
# Check responsive design
# Validate error handling
```

**Total Time**: ~1-1.5 hours

---

## 🐛 Common Issues & Solutions

### Issue 1: "Module not found: lucide-react"
```bash
npm install lucide-react
```

### Issue 2: TypeScript errors in profile page
```typescript
// Ensure types are imported
import type { CookieStatusResponse } from '@/lib/types'
```

### Issue 3: API calls fail with 404
```bash
# Backend must be running with new endpoints
# Check: http://localhost:8000/docs
# Verify /user/lexis-cookies routes exist
```

### Issue 4: Cookies not masked
```css
/* Ensure globals.css is imported in layout.tsx */
import './globals.css'
```

### Issue 5: Sidebar doesn't update
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

---

## 📊 File Size Impact

| File | Before | After | Change |
|------|--------|-------|--------|
| `types.ts` | 157 lines | 225 lines | +68 lines |
| `api.ts` | 637 lines | 717 lines | +80 lines |
| `Sidebar.tsx` | 107 lines | 122 lines | +15 lines |
| `globals.css` | ~200 lines | ~220 lines | +20 lines |
| `profile/page.tsx` | 0 lines | 367 lines | **+367 lines** |
| **Total** | - | - | **+550 lines** |

---

## 🎯 Success Criteria

Frontend implementation is complete when:

1. ✅ Profile page renders without errors
2. ✅ Cookie validation shows real-time status
3. ✅ Save button only enables after validation
4. ✅ Cookies are masked by default (security)
5. ✅ Clear button removes saved cookies
6. ✅ Status updates after save/clear
7. ✅ All API calls work correctly
8. ✅ Responsive design works on mobile
9. ✅ Error messages are user-friendly
10. ✅ Design matches existing pages

---

## 📞 Need Help?

| Issue | Solution |
|-------|----------|
| TypeScript errors | Check types.ts import paths |
| API 404 errors | Ensure backend is running with new routes |
| Styling issues | Verify globals.css is imported |
| State bugs | Check React Query cache |
| Build errors | Clear .next folder and rebuild |

---

## 🎉 Final Checklist

```
Frontend Implementation:
[ ] types.ts updated with cookie types
[ ] api.ts has 4 new cookie methods
[ ] globals.css has .text-security-disc
[ ] Sidebar.tsx shows Profile link
[ ] profile/page.tsx created with full UI
[ ] npm run dev works without errors
[ ] /profile route loads correctly
[ ] All user flows tested manually
[ ] No console errors or warnings
[ ] Ready for backend integration
```

---

*Document Version: 1.0*  
*Last Updated: February 3, 2026*  
*Estimated Implementation Time: 1-1.5 hours*

/**
 * ChatterFix Firebase Authentication
 * "Try Before You Buy" - View app without login, auto-create account on first sign-in
 */

// Firebase SDK imports (using CDN)
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import {
    getAuth,
    signInWithPopup,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    GoogleAuthProvider,
    onAuthStateChanged,
    signOut
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// Firebase config for ChatterFix (fredfix project)
const firebaseConfig = {
    apiKey: "AIzaSyAFy3QDpgWBjUa1Qu-FUJTqtYUjx_RH0yU",
    authDomain: "fredfix.firebaseapp.com",
    projectId: "fredfix",
    storageBucket: "fredfix.firebasestorage.app",
    messagingSenderId: "650169261019",
    appId: "1:650169261019:web:chatterfix"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Store current user globally
window.currentUser = null;
window.firebaseAuth = auth;

// Create auth UI elements
function createAuthUI() {
    // Add styles
    const styles = document.createElement('style');
    styles.textContent = `
        .cf-auth-section {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .cf-auth-loading {
            color: rgba(255,255,255,0.6);
            font-size: 0.9rem;
        }
        .cf-btn-login {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .cf-btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .cf-user-menu {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 25px;
            transition: background 0.2s ease;
            position: relative;
        }
        .cf-user-menu:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .cf-user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #667eea;
        }
        .cf-user-name {
            color: white;
            font-weight: 500;
            font-size: 0.9rem;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .cf-user-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: rgba(22, 33, 62, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            min-width: 160px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            z-index: 1001;
            display: none;
        }
        .cf-dropdown-item {
            display: block;
            padding: 12px 16px;
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .cf-dropdown-item:hover {
            color: white;
            background: rgba(255, 255, 255, 0.05);
        }
        .cf-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 2000;
            display: none;
            align-items: center;
            justify-content: center;
        }
        .cf-modal.active {
            display: flex;
        }
        .cf-modal-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
        }
        .cf-modal-content {
            position: relative;
            background: linear-gradient(145deg, rgba(22, 33, 62, 0.98), rgba(10, 10, 10, 0.98));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            max-width: 420px;
            width: 90%;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        }
        .cf-modal-close {
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            color: rgba(255,255,255,0.5);
            font-size: 24px;
            cursor: pointer;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
        }
        .cf-modal-close:hover {
            color: white;
            background: rgba(255, 255, 255, 0.1);
        }
        .cf-modal-title {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            text-align: center;
        }
        .cf-modal-subtitle {
            color: rgba(255,255,255,0.7);
            text-align: center;
            margin-bottom: 30px;
        }
        .cf-auth-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            width: 100%;
            margin-bottom: 12px;
        }
        .cf-google-btn {
            background: white;
            color: #333;
        }
        .cf-google-btn:hover {
            background: #f5f5f5;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .cf-email-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .cf-email-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .cf-auth-divider {
            display: flex;
            align-items: center;
            gap: 16px;
            color: rgba(255,255,255,0.5);
            margin: 16px 0;
        }
        .cf-auth-divider::before,
        .cf-auth-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255, 255, 255, 0.1);
        }
        .cf-form-input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 1rem;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        .cf-form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        .cf-form-input::placeholder {
            color: rgba(255,255,255,0.5);
        }
        .cf-auth-note {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.5);
            text-align: center;
            margin-top: 16px;
        }
        .cf-toast {
            position: fixed;
            top: 100px;
            right: 24px;
            padding: 16px 24px;
            border-radius: 12px;
            z-index: 3000;
            animation: cfSlideIn 0.3s ease;
            color: white;
            font-weight: 500;
        }
        .cf-toast-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        .cf-toast-error { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        .cf-toast-warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
        .cf-toast-info { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
        @keyframes cfSlideIn {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
    `;
    document.head.appendChild(styles);

    // Create auth section HTML
    const authHTML = `
        <div id="cf-auth-section" class="cf-auth-section">
            <div id="cf-auth-loading" class="cf-auth-loading">...</div>
            <div id="cf-auth-logged-out" style="display: none;">
                <button onclick="cfShowLoginModal()" class="cf-btn-login">Sign In</button>
            </div>
            <div id="cf-auth-logged-in" style="display: none;">
                <div class="cf-user-menu" onclick="cfToggleUserMenu()">
                    <img id="cf-user-avatar" src="" alt="User" class="cf-user-avatar">
                    <span id="cf-user-name" class="cf-user-name"></span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    <div id="cf-user-dropdown" class="cf-user-dropdown">
                        <a href="/settings" class="cf-dropdown-item">Settings</a>
                        <div class="cf-dropdown-item" onclick="cfSignOut()">Sign Out</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Create modal HTML
    const modalHTML = `
        <div id="cf-login-modal" class="cf-modal">
            <div class="cf-modal-backdrop" onclick="cfHideLoginModal()"></div>
            <div class="cf-modal-content">
                <button class="cf-modal-close" onclick="cfHideLoginModal()">&times;</button>
                <h2 class="cf-modal-title">Welcome to ChatterFix</h2>
                <p class="cf-modal-subtitle">Sign in to save your data and access all features</p>

                <button onclick="cfSignInWithGoogle()" class="cf-auth-btn cf-google-btn">
                    <svg viewBox="0 0 24 24" width="20" height="20">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                </button>

                <div class="cf-auth-divider"><span>or</span></div>

                <form id="cf-email-auth-form" onsubmit="cfHandleEmailAuth(event)">
                    <input type="email" id="cf-auth-email" placeholder="Email address" class="cf-form-input" required>
                    <input type="password" id="cf-auth-password" placeholder="Password" class="cf-form-input" required>
                    <button type="submit" class="cf-auth-btn cf-email-btn">Sign In / Sign Up</button>
                </form>

                <p class="cf-auth-note">
                    No account? We'll create one automatically when you sign in.
                </p>
            </div>
        </div>
    `;

    // Inject into page
    const header = document.querySelector('.header') || document.querySelector('header') || document.querySelector('.navbar');
    if (header) {
        const authContainer = document.createElement('div');
        authContainer.innerHTML = authHTML;
        authContainer.style.cssText = 'position: absolute; right: 2rem; top: 50%; transform: translateY(-50%);';
        header.style.position = 'relative';
        header.appendChild(authContainer);
    }

    // Add modal to body
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
}

// Toast notification
function cfShowToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `cf-toast cf-toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
window.cfShowToast = cfShowToast;

// Auth state observer
onAuthStateChanged(auth, async (user) => {
    const loadingEl = document.getElementById('cf-auth-loading');
    const loggedOutEl = document.getElementById('cf-auth-logged-out');
    const loggedInEl = document.getElementById('cf-auth-logged-in');

    if (!loadingEl) return; // UI not created yet

    if (user) {
        try {
            const idToken = await user.getIdToken();
            const response = await fetch('/api/auth/verify-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_token: idToken })
            });

            if (response.ok) {
                const data = await response.json();
                window.currentUser = data.user;

                document.getElementById('cf-user-avatar').src = user.photoURL ||
                    `https://ui-avatars.com/api/?name=${encodeURIComponent(data.user.display_name)}&background=667eea&color=fff`;
                document.getElementById('cf-user-name').textContent = data.user.display_name || user.email.split('@')[0];

                loadingEl.style.display = 'none';
                loggedOutEl.style.display = 'none';
                loggedInEl.style.display = 'block';

                if (data.user.is_new_user) {
                    cfShowToast('Welcome to ChatterFix! Your account has been created.', 'success');
                }
                console.log('✅ User authenticated:', data.user.email);
            } else {
                throw new Error('Backend verification failed');
            }
        } catch (error) {
            console.error('Auth verification error:', error);
            document.getElementById('cf-user-avatar').src = user.photoURL ||
                `https://ui-avatars.com/api/?name=${encodeURIComponent(user.email)}&background=667eea&color=fff`;
            document.getElementById('cf-user-name').textContent = user.displayName || user.email.split('@')[0];

            loadingEl.style.display = 'none';
            loggedOutEl.style.display = 'none';
            loggedInEl.style.display = 'block';
        }
    } else {
        window.currentUser = null;
        loadingEl.style.display = 'none';
        loggedOutEl.style.display = 'block';
        loggedInEl.style.display = 'none';
        console.log('👤 User signed out');
    }
});

// Sign in with Google
window.cfSignInWithGoogle = async function() {
    try {
        await signInWithPopup(auth, googleProvider);
        cfHideLoginModal();
        console.log('✅ Google sign-in successful');
    } catch (error) {
        console.error('Google sign-in error:', error);
        if (error.code !== 'auth/popup-closed-by-user') {
            cfShowToast('Sign in failed. Please try again.', 'error');
        }
    }
};

// Handle email/password auth
window.cfHandleEmailAuth = async function(event) {
    event.preventDefault();
    const email = document.getElementById('cf-auth-email').value;
    const password = document.getElementById('cf-auth-password').value;

    try {
        await signInWithEmailAndPassword(auth, email, password);
        cfHideLoginModal();
        console.log('✅ Email sign-in successful');
    } catch (signInError) {
        if (signInError.code === 'auth/user-not-found' || signInError.code === 'auth/invalid-credential') {
            try {
                await createUserWithEmailAndPassword(auth, email, password);
                cfHideLoginModal();
                console.log('✅ Account created successfully');
            } catch (createError) {
                console.error('Account creation error:', createError);
                if (createError.code === 'auth/weak-password') {
                    cfShowToast('Password should be at least 6 characters.', 'warning');
                } else if (createError.code === 'auth/email-already-in-use') {
                    cfShowToast('Incorrect password. Please try again.', 'error');
                } else {
                    cfShowToast('Sign up failed. Please try again.', 'error');
                }
            }
        } else if (signInError.code === 'auth/wrong-password') {
            cfShowToast('Incorrect password. Please try again.', 'error');
        } else {
            console.error('Sign in error:', signInError);
            cfShowToast('Sign in failed. Please try again.', 'error');
        }
    }
};

// Sign out
window.cfSignOut = async function() {
    try {
        await signOut(auth);
        cfShowToast('Signed out successfully.', 'info');
    } catch (error) {
        console.error('Sign out error:', error);
    }
};

// Modal functions
window.cfShowLoginModal = function() {
    document.getElementById('cf-login-modal').classList.add('active');
};

window.cfHideLoginModal = function() {
    document.getElementById('cf-login-modal').classList.remove('active');
    document.getElementById('cf-auth-email').value = '';
    document.getElementById('cf-auth-password').value = '';
};

// User menu toggle
window.cfToggleUserMenu = function() {
    const dropdown = document.getElementById('cf-user-dropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
};

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.cf-user-menu');
    const dropdown = document.getElementById('cf-user-dropdown');
    if (userMenu && dropdown && !userMenu.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cfHideLoginModal();
    }
});

// Initialize auth UI when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createAuthUI);
} else {
    createAuthUI();
}

console.log('🔥 ChatterFix Firebase Auth loaded - Try Before You Buy enabled');

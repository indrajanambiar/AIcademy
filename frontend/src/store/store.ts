import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
    is_admin: boolean;
}

interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    setAuth: (user: User, accessToken: string, refreshToken: string) => void;
    clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            setAuth: (user, accessToken, refreshToken) => {
                localStorage.setItem('access_token', accessToken);
                localStorage.setItem('refresh_token', refreshToken);
                set({
                    user,
                    accessToken,
                    refreshToken,
                    isAuthenticated: true,
                });
            },
            clearAuth: () => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                });
            },
        }),
        {
            name: 'auth-storage',
        }
    )
);

interface ChatMessage {
    id: string;
    message: string;
    reply: string;
    intent?: string;
    confidence?: number;
    timestamp: string;
    isUser: boolean;
}

interface ChatState {
    messages: ChatMessage[];
    isLoading: boolean;
    addMessage: (message: ChatMessage) => void;
    setLoading: (loading: boolean) => void;
    clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    isLoading: false,
    addMessage: (message) =>
        set((state) => ({
            messages: [...state.messages, message],
        })),
    setLoading: (loading) => set({ isLoading: loading }),
    clearMessages: () => set({ messages: [] }),
}));

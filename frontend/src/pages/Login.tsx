import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Lock, Loader2, Sparkles, GraduationCap } from 'lucide-react';
import { authAPI } from '../services/api';
import { useAuthStore } from '../store/store';

const Login: React.FC = () => {
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const loginResponse = await authAPI.login(username, password);
            const { access_token, refresh_token } = loginResponse.data;

            // Set token in localStorage so the interceptor can pick it up for the /me request
            localStorage.setItem('access_token', access_token);

            const userResponse = await authAPI.me();
            const user = userResponse.data;

            setAuth(user, access_token, refresh_token);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-dark-950 via-dark-900 to-primary-950">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl animate-pulse-slow animation-delay-2000" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="glass-card">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: 'spring', delay: 0.2 }}
                            className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-primary-500 to-primary-600 mb-4"
                        >
                            <GraduationCap className="w-8 h-8 text-white" />
                        </motion.div>
                        <h1 className="text-3xl font-display font-bold gradient-text mb-2">
                            Welcome Back! 👋
                        </h1>
                        <p className="text-dark-300">
                            An academy powered by AI — smart learning for the future
                        </p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                            >
                                {error}
                            </motion.div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-dark-200 mb-2">
                                Username
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-400" />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="input w-full pl-10"
                                    placeholder="Enter your username"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-dark-200 mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-400" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input w-full pl-10"
                                    placeholder="Enter your password"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn btn-primary w-full flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-6 text-center text-dark-300">
                        Don't have an account?{' '}
                        <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium">
                            Create one
                        </Link>
                    </div>
                </div>

                {/* Demo credentials hint */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.8 }}
                    className="mt-4 text-center text-dark-400 text-sm"
                >
                    <Sparkles className="inline w-4 h-4 mr-1" />
                    First time? Create an account to get started
                </motion.div>
            </motion.div>
        </div>
    );
};

export default Login;

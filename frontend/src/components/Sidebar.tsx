import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard,
    BookOpen,
    MessageSquare,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    User,
    Sparkles
} from 'lucide-react';
import { useAuthStore } from '../store/store';

interface SidebarProps {
    children: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ children }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const navigate = useNavigate();
    const { user, clearAuth } = useAuthStore();

    const handleLogout = () => {
        clearAuth();
        navigate('/login');
    };

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
        { icon: BookOpen, label: 'Courses', path: '/courses' },
        { icon: MessageSquare, label: 'AI Tutor', path: '/chat' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    return (
        <div className="flex min-h-screen bg-dark-950">
            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: isCollapsed ? 80 : 280 }}
                className="relative h-screen sticky top-0 flex flex-col border-r border-white/5 bg-dark-900/50 backdrop-blur-xl z-20"
            >
                {/* Toggle Button */}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="absolute -right-3 top-8 bg-primary-500 rounded-full p-1 text-white shadow-lg hover:bg-primary-600 transition-colors"
                >
                    {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>

                {/* Logo */}
                <div className="p-6 flex items-center gap-3 overflow-hidden">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center flex-shrink-0">
                        <Sparkles size={18} className="text-white" />
                    </div>
                    <AnimatePresence>
                        {!isCollapsed && (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="font-display font-bold text-lg whitespace-nowrap"
                            >
                                Aicademy
                            </motion.span>
                        )}
                    </AnimatePresence>
                </div>

                {/* User Profile Summary */}
                <div className={`px-4 mb-6 ${isCollapsed ? 'items-center' : ''} flex flex-col`}>
                    <div className={`glass-card p-3 flex items-center gap-3 ${isCollapsed ? 'justify-center p-2' : ''} bg-white/5 border-none`}>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-purple-500 p-[2px] flex-shrink-0">
                            <div className="w-full h-full rounded-full bg-dark-900 flex items-center justify-center overflow-hidden">
                                {user?.full_name ? (
                                    <span className="font-bold text-xs">
                                        {user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                                    </span>
                                ) : (
                                    <User size={16} />
                                )}
                            </div>
                        </div>

                        {!isCollapsed && (
                            <div className="overflow-hidden">
                                <p className="text-sm font-medium truncate">{user?.full_name || user?.username}</p>
                                <p className="text-xs text-gray-400 truncate">Free Plan</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 space-y-2 overflow-y-auto custom-scrollbar">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => `
                                flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group
                                ${isActive
                                    ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }
                                ${isCollapsed ? 'justify-center' : ''}
                            `}
                        >
                            <item.icon size={20} className={isCollapsed ? '' : 'flex-shrink-0'} />
                            {!isCollapsed && (
                                <span className="font-medium truncate">{item.label}</span>
                            )}

                            {/* Tooltip for collapsed state */}
                            {isCollapsed && (
                                <div className="absolute left-full ml-2 px-2 py-1 bg-dark-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-white/10">
                                    {item.label}
                                </div>
                            )}
                        </NavLink>
                    ))}
                </nav>

                {/* Footer Actions */}
                <div className="p-4 border-t border-white/5">
                    <button
                        onClick={handleLogout}
                        className={`
                            flex items-center gap-3 w-full px-3 py-3 rounded-xl text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200
                            ${isCollapsed ? 'justify-center' : ''}
                        `}
                    >
                        <LogOut size={20} />
                        {!isCollapsed && <span className="font-medium">Logout</span>}
                    </button>
                </div>
            </motion.aside>

            {/* Main Content */}
            <main className="flex-1 overflow-x-hidden">
                {children}
            </main>
        </div>
    );
};

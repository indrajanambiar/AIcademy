import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    User,
    Bot,
    Loader2,
    Sparkles,
    LogOut,
    BookOpen,
    TrendingUp,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { conversationAPI, coursesAPI } from '../services/api';
import { useAuthStore } from '../store/store';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { InteractiveQuiz } from '../components/InteractiveQuiz';
import { isQuizMessage, parseQuizFromMessage } from '../utils/quizParser';
import { InteractiveRoadmap } from '../components/InteractiveRoadmap';
import { isRoadmapMessage, parseRoadmapFromMessage } from '../utils/roadmapParser';

interface Message {
    id: string;
    content: string;
    isUser: boolean;
    timestamp: Date;
    intent?: string;
    confidence?: number;
}

const Chat: React.FC = () => {
    const navigate = useNavigate();
    const { user, clearAuth } = useAuthStore();
    const [searchParams] = useSearchParams();
    const courseId = searchParams.get('courseId');
    const [messages, setMessages] = useState<Message[]>([]);

    useEffect(() => {
        const fetchCourseDetails = async () => {
            if (messages.length > 0) return; // Don't reset if messages exist

            if (courseId) {
                try {
                    const response = await coursesAPI.getMyCourseDetails(courseId);
                    const { course, progress } = response.data;

                    let welcomeMsg = `Hello! I am **Bindu Miss**, your teacher for **${course.title}**. 👩‍🏫`;

                    if (progress && (progress.status === 'in_progress' || progress.status === 'paused')) {
                        const currentModuleIdx = progress.current_module || 0;
                        const moduleTitle = course.syllabus?.modules?.[currentModuleIdx]?.title || `Module ${currentModuleIdx + 1}`;
                        welcomeMsg += `\n\nWe are currently in **${moduleTitle}**. Ready to resume where we left off?`;
                    } else {
                        welcomeMsg += `\n\nReady to start your learning journey?`;
                    }

                    setMessages([{
                        id: 'welcome',
                        content: welcomeMsg,
                        isUser: false,
                        timestamp: new Date(),
                    }]);
                } catch (error) {
                    console.error("Failed to fetch course details", error);
                    setMessages([{
                        id: 'welcome',
                        content: `Hello! I'm your AI Learning Coach for **${courseId}** and my name is Bindu and you can call me Bindu Miss. \n\nReady to continue your lesson?`,
                        isUser: false,
                        timestamp: new Date(),
                    }]);
                }
            } else {
                setMessages([{
                    id: 'welcome',
                    content: "Hello! I'm your AI Learning Coach, Bindu — and you can call me Bindu Miss.😊\n\nWhat topic would you like to learn today?",
                    isUser: false,
                    timestamp: new Date(),
                }]);
            }
        };

        fetchCourseDetails();
    }, [courseId]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (override?: string | any) => {
        const messageToSend = typeof override === 'string' ? override : input;

        if (!messageToSend.trim() || loading) return;

        // Regex to detect quiz answers like "1A 2B", "1. A 2. B", "1A, 2B", etc.
        const isQuizAnswer = /^(\d+[\.\:\)\s]*[A-D][\s,]*)+$/i.test(messageToSend.trim());

        // Only show user message if it's NOT a quiz answer string
        if (!isQuizAnswer) {
            const userMessage: Message = {
                id: Date.now().toString(),
                content: messageToSend,
                isUser: true,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);
        }

        // Clear input only if we sent from input
        if (typeof override !== 'string') {
            setInput('');
        }
        setLoading(true);

        try {
            const context = courseId ? { course_id: courseId } : undefined;
            const response = await conversationAPI.chat(messageToSend, context);
            const { reply, intent, confidence } = response.data;

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: reply,
                isUser: false,
                timestamp: new Date(),
                intent,
                confidence,
            };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: "I apologize, but I encountered an error. Please try again.",
                isUser: false,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleLogout = () => {
        clearAuth();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-primary-950 flex flex-col">
            {/* Header */}
            <header className="glass border-b border-white/10 px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-2 rounded-full hover:bg-white/10 transition-colors mr-2"
                            title="Go to Home"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-home"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
                        </button>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-primary-600 flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="font-display font-bold text-lg gradient-text">AI Learning Coach</h1>
                            <p className="text-xs text-dark-400">Powered by LangGraph & LLM</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-dark-200">{user?.username}</p>
                            <p className="text-xs text-dark-400">{user?.email}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="btn btn-secondary flex items-center gap-2 text-sm"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="hidden sm:inline">Logout</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    <AnimatePresence>
                        {messages.map((message) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                                className={`flex items-start gap-3 ${message.isUser ? 'flex-row-reverse' : ''
                                    }`}
                            >
                                {/* Avatar */}
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${message.isUser
                                        ? 'bg-primary-600'
                                        : 'bg-gradient-to-r from-primary-500 to-primary-600'
                                        }`}
                                >
                                    {message.isUser ? (
                                        <User className="w-5 h-5 text-white" />
                                    ) : (
                                        <Bot className="w-5 h-5 text-white" />
                                    )}
                                </div>

                                {/* Message bubble */}
                                <div
                                    className={`glass-card max-w-2xl ${message.isUser ? 'bg-primary-600/20' : ''
                                        }`}
                                >
                                    {/* Check if this is a quiz message */}
                                    {!message.isUser && isQuizMessage(message.content) ? (
                                        <div>
                                            <div className="prose prose-invert prose-sm max-w-none mb-4">
                                                <ReactMarkdown>
                                                    {message.content.split('**Question 1**')[0]}
                                                </ReactMarkdown>
                                            </div>
                                            <InteractiveQuiz
                                                quiz={parseQuizFromMessage(message.content)!}
                                                onSubmit={(answers) => {
                                                    handleSend(answers);
                                                }}
                                            />
                                        </div>
                                    ) : !message.isUser && isRoadmapMessage(message.content) ? (
                                        <div>
                                            <InteractiveRoadmap
                                                {...parseRoadmapFromMessage(message.content)!}
                                            />
                                        </div>
                                    ) : (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown>{message.content}</ReactMarkdown>
                                        </div>
                                    )}

                                    {/* Metadata */}
                                    {!message.isUser && message.confidence !== undefined && (
                                        <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-4 text-xs text-dark-400">
                                            {message.intent && (
                                                <span className="flex items-center gap-1">
                                                    <BookOpen className="w-3 h-3" />
                                                    {message.intent}
                                                </span>
                                            )}
                                            {message.confidence && (
                                                <span className="flex items-center gap-1">
                                                    <TrendingUp className="w-3 h-3" />
                                                    {Math.round(message.confidence)}% confidence
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {loading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center gap-3"
                        >
                            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-primary-600 flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div className="glass-card">
                                <div className="flex items-center gap-2 text-dark-300">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Thinking...</span>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input area */}
            <div className="glass border-t border-white/10 px-4 py-4">
                <div className="max-w-4xl mx-auto">
                    <div className="flex items-end gap-2">
                        <div className="flex-1 glass rounded-xl p-1">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Ask me anything about learning..."
                                className="w-full bg-transparent px-3 py-2 outline-none resize-none max-h-32"
                                rows={1}
                                disabled={loading}
                            />
                        </div>
                        <button
                            onClick={() => handleSend()}
                            disabled={!input.trim() || loading}
                            className="btn btn-primary h-12 w-12 p-0 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </div>

                    {/* Quick actions */}
                    <div className="mt-3 flex flex-wrap gap-2">
                        {['Create a roadmap', 'Quiz me', 'Explain concepts'].map((action) => (
                            <button
                                key={action}
                                onClick={() => setInput(action)}
                                className="text-xs px-3 py-1.5 glass rounded-full hover:bg-white/10 transition-colors text-dark-300"
                            >
                                {action}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chat;

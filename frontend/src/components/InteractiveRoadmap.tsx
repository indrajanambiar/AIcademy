import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Book,
    Code,
    Trophy,
    Star,
    CheckCircle2,
    Lock,
    Flame,
    Target,
    Lightbulb
} from 'lucide-react';

interface Week {
    week: number;
    title: string;
    goal: string;
    topics: string[];
    exercises: string[];
    unlocked: boolean;
    completed: boolean;
}

interface RoadmapProps {
    title: string;
    level: string;
    weeks: Week[];
}

export function InteractiveRoadmap({ title, level, weeks }: RoadmapProps) {
    const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
    const [completedWeeks, setCompletedWeeks] = useState<Set<number>>(new Set());

    const toggleComplete = (weekNum: number) => {
        const newCompleted = new Set(completedWeeks);
        if (newCompleted.has(weekNum)) {
            newCompleted.delete(weekNum);
        } else {
            newCompleted.add(weekNum);
        }
        setCompletedWeeks(newCompleted);
    };

    const getLevelColor = () => {
        switch (level.toLowerCase()) {
            case 'beginner': return 'from-green-400 to-emerald-600';
            case 'intermediate': return 'from-yellow-400 to-orange-600';
            case 'advanced': return 'from-red-400 to-pink-600';
            default: return 'from-blue-400 to-purple-600';
        }
    };

    const getWeekIcon = (weekNum: number) => {
        const icons = [Book, Code, Lightbulb, Trophy];
        const Icon = icons[(weekNum - 1) % icons.length];
        return Icon;
    };

    return (
        <div className="roadmap-container my-6">
            {/* Hero Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`bg-gradient-to-r ${getLevelColor()} rounded-2xl p-8 text-white shadow-2xl mb-8`}
            >
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <Star className="w-8 h-8 animate-pulse" />
                            <h2 className="text-3xl font-bold">{title}</h2>
                        </div>
                        <p className="text-lg opacity-90 flex items-center gap-2">
                            <Flame className="w-5 h-5" />
                            {level} Level Journey
                        </p>
                    </div>
                    <div className="text-center">
                        <div className="text-5xl font-bold">
                            {completedWeeks.size}/{weeks.length}
                        </div>
                        <p className="text-sm opacity-90">Weeks Complete</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-6 bg-white/20 rounded-full h-4 overflow-hidden backdrop-blur-sm">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(completedWeeks.size / weeks.length) * 100}%` }}
                        className="h-full bg-white rounded-full shadow-lg"
                        transition={{ duration: 0.5 }}
                    />
                </div>
            </motion.div>

            {/* Skill Tree Path */}
            <div className="relative">
                {/* Connecting Lines */}
                <svg className="absolute top-0 left-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                    {weeks.map((_, index) => {
                        if (index === weeks.length - 1) return null;
                        const y1 = 120 + (index * 200);
                        const y2 = 120 + ((index + 1) * 200);
                        const x1 = index % 2 === 0 ? '25%' : '75%';
                        const x2 = (index + 1) % 2 === 0 ? '25%' : '75%';

                        return (
                            <motion.line
                                key={index}
                                x1={x1}
                                y1={y1}
                                x2={x2}
                                y2={y2}
                                stroke="url(#gradient)"
                                strokeWidth="3"
                                strokeDasharray="5,5"
                                initial={{ pathLength: 0 }}
                                animate={{ pathLength: 1 }}
                                transition={{ duration: 1, delay: index * 0.2 }}
                            />
                        );
                    })}
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.5" />
                            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.5" />
                        </linearGradient>
                    </defs>
                </svg>

                {/* Week Nodes */}
                <div className="space-y-12 relative" style={{ zIndex: 1 }}>
                    {weeks.map((week, index) => {
                        const Icon = getWeekIcon(week.week);
                        const isCompleted = completedWeeks.has(week.week);
                        const isSelected = selectedWeek === week.week;
                        const isLeft = index % 2 === 0;

                        return (
                            <motion.div
                                key={week.week}
                                initial={{ opacity: 0, x: isLeft ? -100 : 100 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.2 }}
                                className={`flex items-start gap-6 ${isLeft ? 'flex-row' : 'flex-row-reverse'}`}
                            >
                                {/* Week Node */}
                                <div className={`flex-1 ${isLeft ? 'text-right' : 'text-left'}`}>
                                    <motion.div
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => setSelectedWeek(isSelected ? null : week.week)}
                                        className={`
                                            cursor-pointer bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl
                                            border-4 transition-all duration-300
                                            ${isCompleted ? 'border-green-500' : 'border-gray-200 dark:border-gray-700'}
                                            ${isSelected ? 'ring-4 ring-blue-400' : ''}
                                            hover:shadow-2xl
                                        `}
                                    >
                                        <div className="flex items-center gap-4 mb-3">
                                            {!isLeft && <div className="flex-1" />}
                                            <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${getLevelColor()} flex items-center justify-center`}>
                                                {isCompleted ? (
                                                    <CheckCircle2 className="w-8 h-8 text-white" />
                                                ) : (
                                                    <Icon className="w-8 h-8 text-white" />
                                                )}
                                            </div>
                                            {isLeft && <div className="flex-1" />}
                                        </div>

                                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                                            Week {week.week}
                                        </h3>
                                        <p className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">
                                            {week.title}
                                        </p>

                                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                                            <Target className="w-4 h-4" />
                                            <span className="font-medium">{week.goal}</span>
                                        </div>

                                        {/* Expandable Content */}
                                        {isSelected && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
                                            >
                                                {/* Topics */}
                                                <div className="mb-4">
                                                    <h4 className="font-bold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
                                                        <Book className="w-4 h-4" />
                                                        Topics
                                                    </h4>
                                                    <ul className="space-y-1">
                                                        {week.topics.map((topic, i) => (
                                                            <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                                                                <span className="text-blue-500">•</span>
                                                                <span>{topic}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>

                                                {/* Exercises */}
                                                <div className="mb-4">
                                                    <h4 className="font-bold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
                                                        <Code className="w-4 h-4" />
                                                        Exercises
                                                    </h4>
                                                    <ul className="space-y-1">
                                                        {week.exercises.map((exercise, i) => (
                                                            <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                                                                <span className="text-purple-500">→</span>
                                                                <span>{exercise}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>

                                                {/* Mark Complete Button */}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        toggleComplete(week.week);
                                                    }}
                                                    className={`
                                                        w-full py-2 px-4 rounded-lg font-bold transition-all
                                                        ${isCompleted
                                                            ? 'bg-green-500 text-white hover:bg-green-600'
                                                            : 'bg-blue-500 text-white hover:bg-blue-600'
                                                        }
                                                    `}
                                                >
                                                    {isCompleted ? '✓ Completed' : 'Mark as Complete'}
                                                </button>
                                            </motion.div>
                                        )}
                                    </motion.div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Completion Celebration */}
                {completedWeeks.size === weeks.length && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="mt-12 text-center bg-gradient-to-r from-yellow-400 to-orange-500 rounded-2xl p-8 text-white shadow-2xl"
                    >
                        <Trophy className="w-16 h-16 mx-auto mb-4 animate-bounce" />
                        <h3 className="text-3xl font-bold mb-2">🎉 Roadmap Complete!</h3>
                        <p className="text-lg">You've finished all weeks! You're awesome! 🌟</p>
                    </motion.div>
                )}
            </div>
        </div>
    );
}

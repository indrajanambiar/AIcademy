import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { coursesAPI } from '../services/api';

import { Sidebar } from '../components/Sidebar';
import {
    BookOpen,
    Trophy,
    Activity,
    Clock,
    ArrowRight
} from 'lucide-react';

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const { data: enrolledCourses, isLoading } = useQuery({
        queryKey: ['enrolled-courses'],
        queryFn: coursesAPI.getMyCourses,
    });

    const [activeCourseId, setActiveCourseId] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (enrolledCourses?.data?.length > 0 && !activeCourseId) {
            // Find first in-progress course, or just the first one
            const inProgress = enrolledCourses?.data?.find((c: any) => c.status === 'in_progress');
            setActiveCourseId(inProgress ? inProgress.course_id : enrolledCourses?.data?.[0]?.course_id);
        }
    }, [enrolledCourses, activeCourseId]);

    const { data: courseDetails } = useQuery({
        queryKey: ['course-details', activeCourseId],
        queryFn: () => coursesAPI.getMyCourseDetails(activeCourseId!),
        enabled: !!activeCourseId,
    });

    const quizResults = courseDetails?.data?.quiz_results || [];
    const totalQuizzes = quizResults.length;

    if (isLoading) {
        return (
            <div className="min-h-screen bg-dark-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <Sidebar>
            <div className="p-4 md:p-8">
                {/* Header */}
                <header className="mb-8">
                    <h1 className="text-3xl font-bold font-outfit mb-2">
                        Dashboard
                    </h1>
                    <p className="text-gray-400">Track your progress and manage your learning</p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    {/* Main Content Area - Now takes full width or larger share */}
                    <div className="lg:col-span-3 space-y-8">
                        {/* Stats Overview */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="glass-card flex items-center gap-4 p-4">
                                <div className="p-3 rounded-xl bg-blue-500/20 text-blue-400">
                                    <BookOpen size={24} />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-xs uppercase tracking-wider">Enrolled</p>
                                    <p className="text-2xl font-bold">{enrolledCourses?.data?.length || 0}</p>
                                </div>
                            </div>
                            <div className="glass-card flex items-center gap-4 p-4">
                                <div className="p-3 rounded-xl bg-green-500/20 text-green-400">
                                    <Trophy size={24} />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-xs uppercase tracking-wider">Completed</p>
                                    <p className="text-2xl font-bold">
                                        {enrolledCourses?.data?.filter((c: any) => c.status === 'completed').length || 0}
                                    </p>
                                </div>
                            </div>
                            <div className="glass-card flex items-center gap-4 p-4">
                                <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400">
                                    <Activity size={24} />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-xs uppercase tracking-wider">Quizzes Taken</p>
                                    <p className="text-2xl font-bold">{totalQuizzes}</p>
                                </div>
                            </div>
                        </div>

                        {/* Recent Performance */}
                        {quizResults.length > 0 && (
                            <div className="glass-card p-6">
                                <h2 className="text-xl font-bold font-outfit mb-4 flex items-center gap-2">
                                    <Trophy className="text-yellow-500" size={20} />
                                    Learning Log
                                </h2>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="text-gray-400 text-sm border-b border-white/10">
                                                <th className="py-3 px-4">Topic / Module</th>
                                                <th className="py-3 px-4">Score</th>
                                                <th className="py-3 px-4">Status</th>
                                                <th className="py-3 px-4">Date</th>
                                            </tr>
                                        </thead>
                                        <tbody className="text-sm">
                                            {quizResults.map((result: any) => (
                                                <tr key={result.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                    <td className="py-3 px-4 font-medium">
                                                        {result.topic || `Module ${result.week}`}
                                                    </td>
                                                    <td className="py-3 px-4">
                                                        <span className={`font-bold ${result.score >= 80 ? 'text-green-400' :
                                                            result.score >= 60 ? 'text-yellow-400' : 'text-red-400'
                                                            }`}>
                                                            {Math.round(result.score)}%
                                                        </span>
                                                        <span className="text-gray-500 text-xs ml-2">
                                                            ({result.correct_answers}/{result.total_questions})
                                                        </span>
                                                    </td>
                                                    <td className="py-3 px-4">
                                                        {result.score >= 70 ? (
                                                            <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-300 text-xs">Passed</span>
                                                        ) : (
                                                            <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-300 text-xs">Retake</span>
                                                        )}
                                                    </td>
                                                    <td className="py-3 px-4 text-gray-400">
                                                        {new Date(result.taken_at).toLocaleDateString()}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Enrolled Courses */}
                        <div>
                            <h2 className="text-2xl font-bold font-outfit mb-6 flex items-center gap-2">
                                <Clock className="text-primary-500" />
                                Continue Learning
                            </h2>

                            {enrolledCourses?.data?.length === 0 ? (
                                <div className="glass-card text-center py-12">
                                    <div className="mb-4 text-gray-400">
                                        <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="text-xl">You haven't enrolled in any courses yet.</p>
                                    </div>
                                    <button
                                        onClick={() => navigate('/courses')}
                                        className="btn btn-primary"
                                    >
                                        Explore Courses
                                    </button>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {enrolledCourses?.data?.map((course: any) => (
                                        <div key={course.id} className="glass-card group hover:border-primary-500/30 transition-all duration-300 flex flex-col">
                                            <div className="flex justify-between items-start mb-4">
                                                <div className="px-3 py-1 rounded-full text-xs font-medium bg-primary-500/20 text-primary-300 border border-primary-500/20">
                                                    {course.skill_level}
                                                </div>
                                                <div className={`px-3 py-1 rounded-full text-xs font-medium border ${course.status === 'completed'
                                                    ? 'bg-green-500/20 text-green-300 border-green-500/20'
                                                    : 'bg-yellow-500/20 text-yellow-300 border-yellow-500/20'
                                                    }`}>
                                                    {course.status.replace('_', ' ')}
                                                </div>
                                            </div>

                                            <h3 className="text-xl font-bold mb-2 group-hover:text-primary-400 transition-colors">
                                                {course.course_title || course.course_id}
                                            </h3>

                                            <div className="mb-4">
                                                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Current Progress</div>
                                                <div className="text-sm font-medium text-white">
                                                    Module {course.current_module !== undefined ? course.current_module + 1 : 1}
                                                    <span className="text-gray-500 mx-2">•</span>
                                                    Topic {course.current_topic !== undefined ? course.current_topic + 1 : 1}
                                                </div>
                                            </div>

                                            <div className="mb-6 flex-grow">
                                                <div className="flex justify-between text-sm text-gray-400 mb-2">
                                                    <span>Progress</span>
                                                    <span>{Math.round(course.progress * 100)}%</span>
                                                </div>
                                                <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all duration-500"
                                                        style={{ width: `${course.progress * 100}%` }}
                                                    />
                                                </div>
                                            </div>

                                            <div className="flex justify-between items-center pt-4 border-t border-white/5 mt-auto">
                                                <div className="text-sm text-gray-400">
                                                    <span className="block text-xs uppercase tracking-wider opacity-60">Last Activity</span>
                                                    <span className="font-medium text-white">Today</span>
                                                </div>
                                                <button
                                                    onClick={() => navigate(`/chat?courseId=${course.course_id}`)}
                                                    className="btn glass py-2 px-4 text-sm hover:bg-primary-500 hover:text-white flex items-center gap-2 group/btn"
                                                >
                                                    Continue
                                                    <ArrowRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </Sidebar>
    );
};

export default Dashboard;

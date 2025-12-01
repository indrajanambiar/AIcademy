import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { courseDiscoveryAPI, coursesAPI } from '../services/api';
import { Sidebar } from '../components/Sidebar';
import {
    BookOpen,
    Loader2,
    GraduationCap,
    List,
    X,
    CheckCircle
} from 'lucide-react';

interface Course {
    name: string;
    display_name: string;
    path: string;
    pdf_count: number;
    pdf_files: string[];
    total_size_mb: number;
}

const CourseDiscovery: React.FC = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [selectedCourseForSyllabus, setSelectedCourseForSyllabus] = useState<string | null>(null);
    const [syllabusContent, setSyllabusContent] = useState<any | null>(null);
    const [isGeneratingSyllabus, setIsGeneratingSyllabus] = useState(false);

    // Fetch available courses
    const { data: discoveryData, isLoading: isLoadingCourses } = useQuery({
        queryKey: ['discovery-courses'],
        queryFn: courseDiscoveryAPI.discover,
    });

    // Fetch enrolled courses to check status
    const { data: enrolledCourses } = useQuery({
        queryKey: ['enrolled-courses'],
        queryFn: coursesAPI.getMyCourses,
    });

    // Enroll mutation
    const enrollMutation = useMutation({
        mutationFn: (courseId: string) => coursesAPI.enroll(courseId, {
            course_id: courseId,
            skill_level: 'beginner',
            duration_days: 30
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['enrolled-courses'] });
            navigate('/dashboard');
        },
        onError: (error: any) => {
            alert('Failed to enroll: ' + (error.response?.data?.detail || error.message));
        }
    });

    const handleViewSyllabus = async (courseName: string) => {
        setSelectedCourseForSyllabus(courseName);
        setSyllabusContent(null);
        setIsGeneratingSyllabus(true);

        try {
            // Use the dedicated lightweight endpoint for syllabus only
            const response = await courseDiscoveryAPI.generateSyllabus(courseName, 'beginner');
            setSyllabusContent(response.data.syllabus);
        } catch (error: any) {
            setSyllabusContent('Failed to load syllabus. Please try again later.');
            console.error('Syllabus generation failed:', error);
        } finally {
            setIsGeneratingSyllabus(false);
        }
    };

    const isEnrolled = (courseName: string) => {
        return enrolledCourses?.data?.some((c: any) => c.course_id === courseName);
    };

    if (isLoadingCourses) {
        return (
            <div className="min-h-screen bg-dark-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <Sidebar>
            <div className="p-4 md:p-8 min-h-screen">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold font-outfit mb-2 text-white">
                        Explore Courses
                    </h1>
                    <p className="text-gray-400">Discover new skills and expand your knowledge</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {discoveryData?.data?.courses?.map((course: Course) => {
                        const enrolled = isEnrolled(course.name);

                        return (
                            <div key={course.name} className="glass-card flex flex-col h-full group hover:border-primary-500/30 transition-all duration-300">
                                <div className="h-32 bg-gradient-to-br from-primary-900/50 to-dark-800 rounded-t-xl flex items-center justify-center relative overflow-hidden">
                                    <div className="absolute inset-0 bg-grid-white/[0.05] bg-[length:16px_16px]"></div>
                                    <BookOpen size={48} className="text-primary-500/50 group-hover:scale-110 transition-transform duration-500" />
                                    {enrolled && (
                                        <div className="absolute top-3 right-3 bg-green-500/20 text-green-400 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1 border border-green-500/20">
                                            <CheckCircle size={12} />
                                            ENROLLED
                                        </div>
                                    )}
                                </div>

                                <div className="p-6 flex-grow flex flex-col">
                                    <h3 className="text-xl font-bold mb-2 text-white group-hover:text-primary-400 transition-colors">
                                        {course.display_name}
                                    </h3>
                                    <p className="text-sm text-gray-400 mb-6">
                                        {course.pdf_count} Modules • {course.total_size_mb.toFixed(1)} MB
                                    </p>

                                    <div className="mt-auto space-y-3">
                                        {enrolled ? (
                                            <button
                                                onClick={() => navigate(`/chat?courseId=${course.name}`)}
                                                className="w-full btn btn-primary flex items-center justify-center gap-2"
                                            >
                                                <GraduationCap size={18} />
                                                Continue Learning
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => enrollMutation.mutate(course.name)}
                                                disabled={enrollMutation.isPending}
                                                className="w-full btn btn-primary flex items-center justify-center gap-2"
                                            >
                                                {enrollMutation.isPending ? (
                                                    <Loader2 size={18} className="animate-spin" />
                                                ) : (
                                                    <GraduationCap size={18} />
                                                )}
                                                Enroll for Free
                                            </button>
                                        )}

                                        <button
                                            onClick={() => handleViewSyllabus(course.name)}
                                            className="w-full btn glass flex items-center justify-center gap-2 hover:bg-white/10"
                                        >
                                            <List size={18} />
                                            View Syllabus
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Syllabus Modal */}
                {selectedCourseForSyllabus && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                        <div className="bg-dark-900 border border-white/10 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
                            <div className="flex justify-between items-center p-6 border-b border-white/10">
                                <h2 className="text-xl font-bold text-white">Course Syllabus</h2>
                                <button
                                    onClick={() => setSelectedCourseForSyllabus(null)}
                                    className="text-gray-400 hover:text-white transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="p-6 overflow-y-auto custom-scrollbar flex-grow">
                                {isGeneratingSyllabus ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                                        <Loader2 size={48} className="animate-spin mb-4 text-primary-500" />
                                        <p>Loading syllabus...</p>
                                    </div>
                                ) : (
                                    <div className="prose prose-invert max-w-none">
                                        {typeof syllabusContent === 'string' ? (
                                            <pre className="whitespace-pre-wrap font-sans text-gray-300 text-sm leading-relaxed">
                                                {syllabusContent}
                                            </pre>
                                        ) : (
                                            <div className="space-y-6">
                                                <div className="mb-4">
                                                    <h3 className="text-2xl font-bold text-primary-400">{(syllabusContent as any)?.title}</h3>
                                                    <p className="text-gray-400 mt-2">{(syllabusContent as any)?.description}</p>
                                                </div>

                                                <div className="space-y-4">
                                                    {(syllabusContent as any)?.modules?.map((module: any, idx: number) => (
                                                        <div key={idx} className="bg-white/5 rounded-xl p-4 border border-white/10">
                                                            <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                                                                <span className="bg-primary-500/20 text-primary-400 text-xs px-2 py-1 rounded">Module {idx + 1}</span>
                                                                {module.title}
                                                            </h4>
                                                            <p className="text-sm text-gray-400 mb-3">{module.description}</p>
                                                            <ul className="space-y-1">
                                                                {module.topics?.map((topic: string, tIdx: number) => (
                                                                    <li key={tIdx} className="text-sm text-gray-300 flex items-start gap-2">
                                                                        <span className="text-primary-500 mt-1">•</span>
                                                                        {topic}
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div className="p-6 border-t border-white/10 flex justify-end">
                                <button
                                    onClick={() => setSelectedCourseForSyllabus(null)}
                                    className="btn glass"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Sidebar>
    );
};

export default CourseDiscovery;

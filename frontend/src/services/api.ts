import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            // Clear tokens and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;

// Auth API
export const authAPI = {
    register: (data: { username: string; email: string; password: string }) =>
        api.post('/auth/register', data),
    login: (username: string, password: string) =>
        api.post('/auth/login', new URLSearchParams({ username, password }), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }),
    me: () => api.get('/auth/me'),
    refresh: (refreshToken: string) => api.post('/auth/refresh', { refresh_token: refreshToken }),
};

// Conversation API
export const conversationAPI = {
    chat: (message: string, context?: any) =>
        api.post('/conversation/chat', { message, context }),
    getHistory: (limit = 50, offset = 0) =>
        api.get(`/conversation/history?limit=${limit}&offset=${offset}`),
    provideFeedback: (conversationId: string, rating: number, feedback?: string) =>
        api.post(`/conversation/feedback/${conversationId}`, { rating, feedback }),
};

// Courses API
export const coursesAPI = {
    list: () => api.get('/courses/'),
    get: (id: string) => api.get(`/courses/${id}`),
    enroll: (courseId: string, data: any) => api.post(`/courses/${courseId}/enroll`, data),
    getMyCourses: () => api.get('/courses/my/enrolled'),
    getMyCourseDetails: (courseIdentifier: string) => api.get(`/courses/my/details/${courseIdentifier}`),
    start: (courseId: string) => api.post(`/courses/${courseId}/start`),
};

// Upload API
export const uploadAPI = {
    uploadDocument: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/upload/document', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    getStats: () => api.get('/upload/stats'),
};

// Admin API
export const adminAPI = {
    getStats: () => api.get('/admin/stats'),
    getMissingKnowledge: (statusFilter?: string, skip = 0, limit = 100) =>
        api.get('/admin/knowledge/missing', { params: { status_filter: statusFilter, skip, limit } }),
    resolveMissingKnowledge: (itemId: string, resolution: string, adminNotes?: string) =>
        api.post(`/admin/knowledge/missing/${itemId}/resolve`, { resolution, admin_notes: adminNotes }),
    listUsers: (skip = 0, limit = 100) =>
        api.get('/admin/users', { params: { skip, limit } }),
};

// Course Discovery API
export const courseDiscoveryAPI = {
    discover: () => api.get('/course-discovery/discover'),
    processCourse: (courseName: string, maxPdfs?: number, maxPagesPerPdf?: number) =>
        api.post('/course-discovery/process', {
            course_name: courseName,
            max_pdfs: maxPdfs,
            max_pages_per_pdf: maxPagesPerPdf
        }),
    generateAllMaterials: (courseName: string, skillLevel = 'beginner', durationDays = 30) =>
        api.post('/course-discovery/generate-all', {
            course_name: courseName,
            skill_level: skillLevel,
            duration_days: durationDays
        }),
    generateSyllabus: (courseName: string, skillLevel: string) =>
        api.post('/course-discovery/generate-syllabus', { course_name: courseName, skill_level: skillLevel }),
    explainConcept: (courseName: string, concept: string) =>
        api.post('/course-discovery/explain', {
            course_name: courseName,
            concept
        }),
    processAllCourses: (maxPdfsPerCourse?: number, maxPagesPerPdf?: number) =>
        api.post('/course-discovery/process-all', {
            max_pdfs_per_course: maxPdfsPerCourse,
            max_pages_per_pdf: maxPagesPerPdf
        }),
};

// Assessment API
export const assessmentAPI = {
    generateDiagnosticQuiz: (subject: string, topic?: string) =>
        api.post('/assessment/diagnostic-quiz', { subject, topic }),

    evaluateQuiz: (subject: string, quizQuestions: any[], userAnswers: string[]) =>
        api.post('/assessment/evaluate', {
            subject,
            quiz_questions: quizQuestions,
            user_answers: userAnswers
        }),

    generatePersonalizedPlan: (subject: string, skillLevel: string, evaluationResults: any, durationDays: number) =>
        api.post('/assessment/personalized-plan', {
            subject,
            skill_level: skillLevel,
            evaluation_results: evaluationResults,
            duration_days: durationDays
        }),
};

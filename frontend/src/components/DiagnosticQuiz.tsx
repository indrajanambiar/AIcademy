import React, { useState } from 'react';
import { assessmentAPI } from '../services/api';
import { BookOpen, CheckCircle, AlertCircle, Award, ArrowRight } from 'lucide-react';

interface DiagnosticQuizProps {
    subject: string;
    onComplete: (skillLevel: string, studyPlan: any) => void;
    onCancel: () => void;
}

const DiagnosticQuiz: React.FC<DiagnosticQuizProps> = ({ subject, onComplete, onCancel }) => {
    const [step, setStep] = useState<'start' | 'loading_quiz' | 'quiz' | 'evaluating' | 'results' | 'generating_plan'>('start');
    const [quiz, setQuiz] = useState<any>(null);
    const [answers, setAnswers] = useState<string[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [evaluation, setEvaluation] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const startQuiz = async () => {
        setStep('loading_quiz');
        setError(null);
        try {
            const response = await assessmentAPI.generateDiagnosticQuiz(subject);
            setQuiz(response.data);
            setAnswers(new Array(response.data.questions.length).fill(''));
            setStep('quiz');
        } catch (err) {
            console.error(err);
            setError('Failed to generate quiz. Please try again.');
            setStep('start');
        }
    };

    const handleAnswerSelect = (option: string) => {
        const newAnswers = [...answers];
        newAnswers[currentQuestionIndex] = option;
        setAnswers(newAnswers);
    };

    const nextQuestion = () => {
        if (currentQuestionIndex < quiz.questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        } else {
            submitQuiz();
        }
    };

    const submitQuiz = async () => {
        setStep('evaluating');
        try {
            const response = await assessmentAPI.evaluateQuiz(subject, quiz.questions, answers);
            setEvaluation(response.data);
            setStep('results');
        } catch (err) {
            console.error(err);
            setError('Failed to evaluate quiz.');
            setStep('quiz');
        }
    };

    const generatePlan = async () => {
        setStep('generating_plan');
        try {
            const response = await assessmentAPI.generatePersonalizedPlan(
                subject,
                evaluation.skill_level,
                evaluation,
                30 // Default duration
            );
            onComplete(evaluation.skill_level, response.data);
        } catch (err) {
            console.error(err);
            setError('Failed to generate study plan.');
            setStep('results');
        }
    };

    if (step === 'start') {
        return (
            <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
                <div className="text-center mb-8">
                    <div className="bg-blue-100 p-4 rounded-full w-20 h-20 mx-auto flex items-center justify-center mb-4">
                        <Award className="w-10 h-10 text-blue-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Diagnostic Assessment</h2>
                    <p className="text-gray-600">
                        Let's evaluate your {subject} skills to create a personalized learning path.
                    </p>
                </div>

                <div className="space-y-4 mb-8">
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <div className="bg-blue-100 p-2 rounded-full">
                            <CheckCircle className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900">5 Adaptive Questions</h4>
                            <p className="text-sm text-gray-600">Mix of beginner, intermediate, and advanced topics.</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <div className="bg-purple-100 p-2 rounded-full">
                            <BookOpen className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900">Personalized Plan</h4>
                            <p className="text-sm text-gray-600">Get a roadmap tailored to your strengths and weaknesses.</p>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}

                <div className="flex gap-4">
                    <button
                        onClick={onCancel}
                        className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
                    >
                        Skip Assessment
                    </button>
                    <button
                        onClick={startQuiz}
                        className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center justify-center gap-2"
                    >
                        Start Quiz <ArrowRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        );
    }

    if (step === 'loading_quiz' || step === 'evaluating' || step === 'generating_plan') {
        return (
            <div className="bg-white p-12 rounded-xl shadow-lg max-w-2xl mx-auto text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-6"></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {step === 'loading_quiz' && 'Generating your adaptive quiz...'}
                    {step === 'evaluating' && 'Analyzing your performance...'}
                    {step === 'generating_plan' && 'Creating your personalized study plan...'}
                </h3>
                <p className="text-gray-500">
                    Using RAG to fetch relevant content from your PDFs...
                </p>
            </div>
        );
    }

    if (step === 'quiz' && quiz) {
        const question = quiz.questions[currentQuestionIndex];
        return (
            <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <span className="text-sm font-medium text-gray-500">
                        Question {currentQuestionIndex + 1} of {quiz.questions.length}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${question.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                        question.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                        }`}>
                        {question.difficulty.toUpperCase()}
                    </span>
                </div>

                <h3 className="text-xl font-semibold text-gray-900 mb-6">
                    {question.question}
                </h3>

                <div className="space-y-3 mb-8">
                    {Object.entries(question.options).map(([key, value]: [string, any]) => (
                        <button
                            key={key}
                            onClick={() => handleAnswerSelect(key)}
                            className={`w-full text-left p-4 rounded-lg border transition-all ${answers[currentQuestionIndex] === key
                                ? 'border-blue-600 bg-blue-50 text-blue-700'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                                }`}
                        >
                            <span className="font-semibold mr-2">{key}.</span> {value}
                        </button>
                    ))}
                </div>

                <div className="flex justify-end">
                    <button
                        onClick={nextQuestion}
                        disabled={!answers[currentQuestionIndex]}
                        className={`px-6 py-3 rounded-lg font-medium flex items-center gap-2 ${answers[currentQuestionIndex]
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            }`}
                    >
                        {currentQuestionIndex === quiz.questions.length - 1 ? 'Submit Results' : 'Next Question'}
                        <ArrowRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        );
    }

    if (step === 'results' && evaluation) {
        return (
            <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
                <div className="text-center mb-8">
                    <div className="bg-green-100 p-4 rounded-full w-20 h-20 mx-auto flex items-center justify-center mb-4">
                        <Award className="w-10 h-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Assessment Complete!</h2>
                    <p className="text-gray-600">
                        You scored {evaluation.score_percentage}% ({evaluation.total_correct}/{evaluation.total_questions})
                    </p>
                </div>

                <div className="bg-blue-50 p-6 rounded-xl mb-8 border border-blue-100">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">Your Level: {evaluation.skill_level.toUpperCase()}</h3>
                    <p className="text-blue-800 mb-4">{evaluation.level_description}</p>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="font-medium text-blue-900">Strengths:</span>
                            <ul className="list-disc list-inside text-blue-800 mt-1">
                                {evaluation.strengths.map((s: string, i: number) => (
                                    <li key={i}>{s}</li>
                                ))}
                            </ul>
                        </div>
                        <div>
                            <span className="font-medium text-blue-900">Focus Areas:</span>
                            <ul className="list-disc list-inside text-blue-800 mt-1">
                                {evaluation.areas_for_improvement.map((w: string, i: number) => (
                                    <li key={i}>{w}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>

                <button
                    onClick={generatePlan}
                    className="w-full px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all"
                >
                    <BookOpen className="w-5 h-5" />
                    Generate Personalized Study Plan
                </button>
            </div>
        );
    }

    return null;
};

export default DiagnosticQuiz;

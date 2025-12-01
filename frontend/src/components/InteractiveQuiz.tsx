import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle } from 'lucide-react';

interface QuizOption {
    [key: string]: string;
}

interface QuizQuestion {
    id: number;
    difficulty: string;
    question: string;
    options: QuizOption;
    correct_answer: string;
}

interface QuizData {
    questions: QuizQuestion[];
}

interface InteractiveQuizProps {
    quiz: QuizData;
    onSubmit: (answers: string) => void;
}

export function InteractiveQuiz({ quiz, onSubmit }: InteractiveQuizProps) {
    const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: string }>({});
    const [showResults, setShowResults] = useState(false);
    const [evaluation, setEvaluation] = useState<{
        correct: number;
        total: number;
        level: string;
        correctAnswers: { [key: number]: string };
    } | null>(null);

    const handleSelectOption = (questionId: number, option: string) => {
        if (showResults) return; // Disable after submission
        setSelectedAnswers(prev => ({
            ...prev,
            [questionId]: option
        }));
    };

    const evaluateAnswers = () => {
        const correctAnswers: { [key: number]: string } = {};
        let correct = 0;

        quiz.questions.forEach(q => {
            correctAnswers[q.id] = q.correct_answer || 'A'; // Fallback
            if (selectedAnswers[q.id] === correctAnswers[q.id]) {
                correct++;
            }
        });

        // Determine level based on score
        let level = 'Beginner';
        if (correct === 5) level = 'Advanced';
        else if (correct >= 3) level = 'Intermediate';
        else level = 'Beginner';

        return { correct, total: quiz.questions.length, level, correctAnswers };
    };

    const handleSubmit = () => {
        const results = evaluateAnswers();
        setEvaluation(results);
        setShowResults(true);

        // Construct answer string for backend (e.g., "1A 2B 3C 4D 5A")
        const answerString = Object.entries(selectedAnswers)
            .map(([id, ans]) => `${id}${ans}`)
            .join(' ');

        // Send to backend via chat so it can record the score
        onSubmit(answerString);
    };

    const allQuestionsAnswered = quiz.questions.every(q => selectedAnswers[q.id]);

    const getDifficultyColor = (difficulty: string) => {
        switch (difficulty.toLowerCase()) {
            case 'beginner': return 'bg-green-500';
            case 'intermediate': return 'bg-yellow-500';
            case 'advanced': return 'bg-red-500';
            default: return 'bg-gray-500';
        }
    };

    return (
        <div className="quiz-container space-y-6 my-4">
            {/* Results Banner */}
            {showResults && evaluation && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white shadow-xl"
                >
                    <div className="text-center">
                        <h3 className="text-2xl font-bold mb-2">Quiz Complete! 🎉</h3>
                        <div className="flex justify-center items-center gap-4 mb-4">
                            <div className="text-5xl font-bold">
                                {evaluation.correct}/{evaluation.total}
                            </div>
                            <div className="text-xl bg-white/20 px-4 py-2 rounded-full">
                                {evaluation.correct * 20} Points
                            </div>
                        </div>

                        <div className="flex justify-center gap-1 mb-4 text-2xl">
                            {[...Array(5)].map((_, i) => (
                                <span key={i} className={i < evaluation.correct ? "opacity-100" : "opacity-30"}>
                                    ⭐
                                </span>
                            ))}
                        </div>

                        <p className="text-lg mb-3">
                            {evaluation.correct === 5 && "Perfect score! Outstanding!"}
                            {evaluation.correct === 4 && "Excellent work!"}
                            {evaluation.correct === 3 && "Good job!"}
                            {evaluation.correct <= 2 && "Keep practicing!"}
                        </p>
                    </div>
                </motion.div>
            )}

            {quiz.questions.map((question, index) => {
                const isCorrect = showResults && selectedAnswers[question.id] === evaluation?.correctAnswers[question.id];
                const isWrong = showResults && selectedAnswers[question.id] !== evaluation?.correctAnswers[question.id];

                return (
                    <motion.div
                        key={question.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`question-card bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg border-2 ${isCorrect ? 'border-green-500' : isWrong ? 'border-red-500' : 'border-gray-200 dark:border-gray-700'
                            }`}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-lg font-bold text-gray-700 dark:text-gray-300">
                                Q{question.id}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${getDifficultyColor(question.difficulty)}`}>
                                {question.difficulty}
                            </span>
                            {showResults && (
                                <span className={`ml-auto text-lg font-bold ${isCorrect ? 'text-green-500' : 'text-red-500'}`}>
                                    {isCorrect ? '✓ Correct' : '✗ Incorrect'}
                                </span>
                            )}
                        </div>

                        <p className="text-gray-900 dark:text-gray-100 font-medium mb-4">
                            {question.question}
                        </p>

                        <div className="options space-y-2">
                            {Object.entries(question.options).map(([key, value]) => {
                                const isSelected = selectedAnswers[question.id] === key;
                                const isCorrectAnswer = showResults && key === evaluation?.correctAnswers[question.id];
                                const isWrongSelection = showResults && isSelected && !isCorrectAnswer;

                                return (
                                    <button
                                        key={key}
                                        onClick={() => handleSelectOption(question.id, key)}
                                        disabled={showResults}
                                        className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 flex items-center gap-3 ${isCorrectAnswer
                                            ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                                            : isWrongSelection
                                                ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                                                : isSelected
                                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                                    : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                            } ${showResults ? 'cursor-default' : 'cursor-pointer'}`}
                                    >
                                        {isCorrectAnswer ? (
                                            <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                                        ) : isWrongSelection ? (
                                            <span className="w-5 h-5 text-red-500 flex-shrink-0">✗</span>
                                        ) : isSelected ? (
                                            <CheckCircle2 className="w-5 h-5 text-blue-500 flex-shrink-0" />
                                        ) : (
                                            <Circle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                        )}
                                        <span className="font-semibold text-blue-600 dark:text-blue-400 mr-2">
                                            {key})
                                        </span>
                                        <span className={`${isCorrectAnswer ? 'text-green-700 dark:text-green-300 font-bold' :
                                            isWrongSelection ? 'text-red-700 dark:text-red-300' :
                                                isSelected ? 'text-blue-700 dark:text-blue-300 font-medium' :
                                                    'text-gray-700 dark:text-gray-300'
                                            }`}>
                                            {value}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </motion.div>
                );
            })}

            {!showResults && (
                <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: quiz.questions.length * 0.1 + 0.2 }}
                    onClick={handleSubmit}
                    disabled={!allQuestionsAnswered}
                    className={`w-full py-4 rounded-lg font-bold text-white transition-all duration-200 ${allQuestionsAnswered
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl'
                        : 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
                        }`}
                >
                    {allQuestionsAnswered ? (
                        'Submit Answers'
                    ) : (
                        `Answer all questions (${Object.keys(selectedAnswers).length}/${quiz.questions.length})`
                    )}
                </motion.button>
            )}
        </div>
    );
}

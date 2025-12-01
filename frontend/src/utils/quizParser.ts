/**
 * Utility to parse quiz questions from chat message markdown text
 */

export interface QuizQuestion {
    id: number;
    difficulty: string;
    question: string;
    options: { [key: string]: string };
    correct_answer: string;
}

export interface ParsedQuiz {
    questions: QuizQuestion[];
}

/**
 * Detects if a message contains a quiz
 */
export function isQuizMessage(content: string): boolean {
    return content.includes('```json_quiz') || (
        content.includes('Question 1') &&
        content.includes('Question 5') &&
        content.includes('Reply with your answers')
    );
}

/**
 * Parses quiz questions from markdown text
 * Format expected:
 * **Question 1** (Beginner):
 * What is Python?
 * A) Option A
 * B) Option B
 * ...
 * OR
 * ```json_quiz
 * { "questions": [...] }
 * ```
 */
export function parseQuizFromMessage(content: string): ParsedQuiz | null {
    try {
        // 1. Try parsing JSON block
        const jsonMatch = content.match(/```json_quiz\n([\s\S]*?)\n```/);
        if (jsonMatch) {
            try {
                const parsed = JSON.parse(jsonMatch[1]);
                if (parsed && parsed.questions && Array.isArray(parsed.questions)) {
                    return parsed;
                }
            } catch (e) {
                console.error("Failed to parse quiz JSON", e);
            }
        }

        // 2. Fallback to regex parsing
        const questions: QuizQuestion[] = [];

        // Split by question markers
        const questionBlocks = content.split(/\*\*Question \d+\*\*/g).slice(1);

        questionBlocks.forEach((block, index) => {
            const questionId = index + 1;

            // Extract difficulty
            const difficultyMatch = block.match(/\((\w+)\)/);
            const difficulty = difficultyMatch ? difficultyMatch[1] : 'unknown';

            // Extract question text (everything before first option)
            const questionMatch = block.match(/:\s*\n([^\n]+)\n/);
            const question = questionMatch ? questionMatch[1].trim() : '';

            // Extract options
            const options: { [key: string]: string } = {};
            const optionMatches = block.matchAll(/([A-D])\)\s*([^\n]+)/g);

            for (const match of optionMatches) {
                const [, key, value] = match;
                options[key] = value.trim();
            }

            if (question && Object.keys(options).length > 0) {
                questions.push({
                    id: questionId,
                    difficulty,
                    question,
                    options,
                    correct_answer: 'A'  // Default, will be provided by backend
                });
            }
        });

        return questions.length === 5 ? { questions } : null;
    } catch (error) {
        console.error('Failed to parse quiz:', error);
        return null;
    }
}

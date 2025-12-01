/**
 * Utility to parse roadmap from chat message markdown text
 */

export interface RoadmapWeek {
    week: number;
    title: string;
    goal: string;
    topics: string[];
    exercises: string[];
    unlocked: boolean;
    completed: boolean;
}

export interface ParsedRoadmap {
    title: string;
    level: string;
    weeks: RoadmapWeek[];
}

/**
 * Detects if a message contains a roadmap
 */
export function isRoadmapMessage(content: string): boolean {
    return content.includes('Learning Roadmap') ||
        (content.includes('Week 1:') && content.includes('Week 2:'));
}

/**
 * Parses roadmap from markdown text
 */
export function parseRoadmapFromMessage(content: string): ParsedRoadmap | null {
    try {
        // Extract title and level
        const titleMatch = content.match(/Learning Roadmap:\s*(.+?)(?:\n|$)/i);
        const title = titleMatch ? titleMatch[1].trim() : 'Learning Roadmap';

        const levelMatch = content.match(/(Beginner|Intermediate|Advanced)\s*Level/i);
        const level = levelMatch ? levelMatch[1] : 'Beginner';

        const weeks: RoadmapWeek[] = [];

        // Split by week headers
        const weekSections = content.split(/Week \d+:/g).slice(1);
        const weekNumbers = content.match(/Week (\d+):/g);

        weekSections.forEach((section, index) => {
            // Extract week number
            const weekNum = weekNumbers && weekNumbers[index]
                ? parseInt(weekNumbers[index].match(/\d+/)?.[0] || '1')
                : index + 1;

            // Extract title (first line after week number)
            const lines = section.trim().split('\n');
            const weekTitle = lines[0]?.replace(/Week \d+:\s*/i, '').trim() || 'Week ' + weekNum;

            // Extract goal
            const goalMatch = section.match(/🎯\s*Goal:\s*(.+?)(?:\n|$)/i);
            const goal = goalMatch ? goalMatch[1].trim() : '';

            // Extract topics
            const topicsSection = section.match(/📚\s*Topics?:\s*([\s\S]+?)(?:\n💻|$)/i);
            const topics: string[] = [];
            if (topicsSection) {
                const topicLines = topicsSection[1].split('\n');
                topicLines.forEach(line => {
                    const cleaned = line.replace(/^[•\-\*]\s*/, '').trim();
                    if (cleaned && !cleaned.startsWith('📚') && !cleaned.startsWith('💻')) {
                        topics.push(cleaned);
                    }
                });
            }

            // Extract exercises
            const exercisesSection = section.match(/💻\s*Exercises?:\s*([\s\S]+?)(?:\nWeek|$)/i);
            const exercises: string[] = [];
            if (exercisesSection) {
                const exerciseLines = exercisesSection[1].split('\n');
                exerciseLines.forEach(line => {
                    const cleaned = line.replace(/^[•\-\*]\s*/, '').trim();
                    if (cleaned && !cleaned.startsWith('📚') && !cleaned.startsWith('💻') && !cleaned.startsWith('💪')) {
                        exercises.push(cleaned);
                    }
                });
            }

            if (weekTitle && topics.length > 0) {
                weeks.push({
                    week: weekNum,
                    title: weekTitle,
                    goal: goal || 'Complete this week',
                    topics,
                    exercises,
                    unlocked: true,
                    completed: false
                });
            }
        });

        return weeks.length > 0 ? { title, level, weeks } : null;
    } catch (error) {
        console.error('Failed to parse roadmap:', error);
        return null;
    }
}

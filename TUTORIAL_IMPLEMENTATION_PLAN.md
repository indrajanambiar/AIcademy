# 🎓 AI Tutor - Interactive Tutorial System Implementation Plan

## 📋 Overview
Add interactive tutorial mode to the roadmap where users can:
1. Start/Resume/Stop tutorials for each week
2. Complete lessons with embedded quizzes
3. Track progress and mark weeks as complete
4. Visual progress indicators on roadmap

## 🏗️ Architecture

### Frontend Components

#### 1. **TutorialControls.tsx** (New Component)
```tsx
interface TutorialControlsProps {
    weekNumber: number;
    isCompleted: boolean;
    inProgress: boolean;
    onStart: () => void;
    onResume: () => void;
    onStop: () => void;
}

// Buttons:
// - "▶️ Start Tutorial" (green) - when not started
// - "⏸️ Pause" (yellow) - when in progress
// - "▶️ Resume" (blue) - when paused
// - "🏁 Complete" (green checkmark) - when finished
```

#### 2. **TutorialModal.tsx** (New Component)
Full-screen modal for tutorial content:
```tsx
interface TutorialModalProps {
    week: RoadmapWeek;
    onClose: () => void;
    onComplete: () => void;
}

// Features:
// - Step-by-step lesson navigation
// - Embedded quiz for each topic
// - Progress bar (e.g., "Topic 2/4")
// - Video/text content sections
// - Code playground integration
```

#### 3. **LessonQuiz.tsx** (Mini Quiz Component)
Smaller quizzes embedded in tutorials:
```tsx
interface LessonQuizProps {
    topic: string;
    questions: QuizQuestion[];  // 2-3 questions per topic
    onPass: (score: number) => void;
}

// Must pass (60%+) to unlock next topic
```

### Backend Endpoints

#### New API Routes
```python
# backend/app/api/tutorial.py

@router.post("/api/tutorial/start")
async def start_tutorial(week_num: int, topic: str):
    """Start a tutorial for a specific week/topic"""
    # Generate lesson content from RAG
    # Return structured lesson data

@router.post("/api/tutorial/quiz")
async def generate_lesson_quiz(topic: str, difficulty: str):
    """Generate mini-quiz for a lesson topic"""
    # 2-3 questions focused on the topic
    # Return quiz JSON

@router.post("/api/tutorial/complete")
async def complete_tutorial(week_num: int, score: float):
    """Mark tutorial as complete and update roadmap"""
    # Save progress to database
    # Update user's roadmap completion status
```

#### Database Schema Updates
```sql
-- Add tutorial_progress table
CREATE TABLE tutorial_progress (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    topic STRING,
    week_number INT,
    status STRING,  -- 'not_started', 'in_progress', 'paused', 'completed'
    score FLOAT,
    current_step INT,
    total_steps INT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### State Management

#### Tutorial State (Frontend)
```typescript
interface TutorialState {
    activeWeek: number | null;
    currentStep: number;
    totalSteps: number;
    passedQuizzes: Set<string>;  // Set of passed topic names
    weekProgress: Map<number, {
        status: 'not_started' | 'in_progress' | 'completed';
        score: number;
        completedTopics: string[];
    }>;
}
```

## 🎮 User Flow

### 1. Starting a Tutorial
```
User clicks "▶️ Start Tutorial" on Week 1 node
    ↓
Modal opens with Week 1 content
    ↓
Shows: "Topic 1: Variables and Data Types"
    ↓
Text explanation + code examples
    ↓
Mini quiz (2-3 questions)
    ↓
Score ≥ 60%? → Unlock Topic 2
Score < 60%? → Review and retry
```

### 2. Tutorial Modal Structure
```
┌─────────────────────────────────────┐
│ Week 1: Python Basics  [X Close]   │
├─────────────────────────────────────┤
│ Progress: ████░░░░ 2/4 Topics       │
├─────────────────────────────────────┤
│                                     │
│ 📖 Topic: Variables                 │
│                                     │
│ [Lesson content here...]            │
│                                     │
│ 💻 Code Example:                    │
│ ┌─────────────────────────────────┐ │
│ │ x = 10                         │ │
│ │ print(x)                       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ❓ Quick Quiz (Pass to continue)    │
│                                     │
│ Q1: What is a variable?             │
│ [A] A storage location              │
│ [B] A function                      │
│ ...                                 │
│                                     │
│ [Submit Answers]                    │
│                                     │
├─────────────────────────────────────┤
│ [← Previous] [Next →] [Pause] [✓]  │
└─────────────────────────────────────┘
```

### 3. Completion Flow
```
User completes all topics in Week 1
    ↓
Final quiz (5 questions covering all topics)
    ↓
Score ≥ 70%? 
    ├─ YES → Mark week as complete ✓
    │         Update roadmap visual (green checkmark)
    │         Unlock Week 2
    │         Show celebration modal
    └─ NO → Allow retry or continue to next week
```

## 🎨 Visual Enhancements

### Roadmap Updates
```tsx
// Add to each week node:

1. Progress Ring
   ┌────────┐
   │   2/4  │  ← Topics completed
   └────────┘

2. Status Badge
   - 🔒 Locked (previous week incomplete)
   - 📚 Not Started
   - 📖 In Progress (yellow pulse)
   - ✅ Completed (green glow)

3. Tutorial Controls (below node)
   [▶️ Start] [⏸️ Pause] [▶️ Resume]
```

### Completion Animations
- Confetti when week completed
- Level-up animation
- XP/Points earned display
- Achievement badges

## 📝 Implementation Steps

### Phase 1: Basic Tutorial Flow (Priority High)
1. ✅ Add tutorial buttons to roadmap nodes
2. ✅ Create TutorialModal component
3. ✅ Implement lesson content display
4. ✅ Add mini quiz component
5. ✅ Basic progress tracking (localStorage)

### Phase 2: Backend Integration (Priority High)
1. Create tutorial API endpoints
2. Generate lesson content from RAG
3. Create lesson quiz generation
4. Add database schema for progress
5. Save/load progress from backend

### Phase 3: Advanced Features (Priority Medium)
1. Code playground integration
2. Video content support
3. Gamification (XP, badges, streaks)
4. Social features (leaderboards)
5. Mobile responsive design

### Phase 4: Polish (Priority Low)
1. Animations and transitions
2. Sound effects
3. Dark mode optimization
4. Accessibility improvements
5. Performance optimization

## 🚀 Quick Start Implementation

### Minimal Viable Tutorial (1-2 hours)
```tsx
// Add to InteractiveRoadmap.tsx

const [activeTutorial, setActiveTutorial] = useState<number | null>(null);

// In each week node:
<button onClick={() => setActiveTutorial(week.week)}>
    ▶️ Start Tutorial
</button>

// Modal
{activeTutorial && (
    <TutorialModal
        week={weeks[activeTutorial - 1]}
        onClose={() => setActiveTutorial(null)}
        onComplete={(score) => {
            toggleComplete(activeTutorial);
            setActiveTutorial(null);
        }}
    />
)}
```

## 📊 Success Metrics
- % of users who start tutorials
- Average completion rate per week
- Average quiz scores
- Time spent in tutorial mode
- Roadmap completion rate

## 🔮 Future Enhancements
- AI-powered personalized hints
- Peer discussion forums
- Live coding challenges
- Certificate generation
- Integration with external coding platforms

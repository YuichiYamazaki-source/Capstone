---
name: project_future_ux_improvements
description: Planned UX improvements - detailed user input and chat-based profile learning
type: project
---

Two future improvements approved by user (2026-03-17):

1. **Detailed user input for Analysis**: My Learning page data is what users reference, but actual data comes from MongoDB via LLM. Users should be able to input more structured data (experience years, current role, detailed skills with proficiency levels) to improve analysis quality.
   **Why:** Current profile data (skills list + motivation) is too sparse for high-quality analysis.
   **How to apply:** Extend user profile schema in MongoDB and onboarding flow.

2. **Chat-based profile learning**: Extract user characteristics (skills, interests, goals) from Explore chat conversations and save to MongoDB profile automatically.
   **Why:** Users reveal preferences/skills naturally in conversation that they may not explicitly set in profile.
   **How to apply:** Add post-processing to chat endpoint that extracts and stores user traits from conversation context.

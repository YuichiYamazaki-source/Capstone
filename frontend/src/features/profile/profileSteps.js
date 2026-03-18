/**
 * Shared step definitions for onboarding and profile editing wizards.
 * The "skills" step uses API-driven autocomplete instead of static options.
 * After skill selection, a "skill_levels" step lets users rate each skill.
 */

export const SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"];

const PROFILE_STEPS = [
  {
    title: "What skills do you already have?",
    subtitle: "Search and select from available skills, or add your own.",
    key: "skills",
    multi: true,
    autocomplete: true,
    options: [],
  },
  {
    title: "Rate your skill levels",
    subtitle: "Set your proficiency level for each skill you selected.",
    key: "skill_levels",
    type: "skill_levels",
  },
  {
    title: "What brings you here?",
    subtitle: "Understanding your motivation helps us recommend better.",
    key: "motivation",
    multi: false,
    options: [
      "Career Change",
      "Skill Up at Current Job",
      "Hobby / Personal Interest",
      "Academic / Certification",
    ],
  },
  {
    title: "How deep do you want to go?",
    subtitle: "This helps us calibrate the scope of recommendations.",
    key: "learning_scope",
    multi: false,
    options: [
      "Single Course",
      "A Few Related Courses",
      "Full Learning Path",
      "Not Sure Yet",
    ],
  },
  {
    title: "How do you learn best?",
    subtitle: "We'll match your style with the right courses.",
    key: "learning_style",
    multi: false,
    options: [
      "Video Lectures",
      "Hands-on Projects",
      "Reading / Articles",
      "Interactive Exercises",
    ],
  },
  {
    title: "What areas interest you?",
    subtitle: "Select topics you'd like to explore.",
    key: "interest_areas",
    multi: true,
    options: [
      "Web Development",
      "Data Science",
      "Artificial Intelligence",
      "Cloud & DevOps",
      "Cybersecurity",
      "Mobile Development",
      "Business & Management",
      "Design & UX",
    ],
  },
];

export default PROFILE_STEPS;

# Job Matcher AI

PROJECT MASTER INSTRUCTION

Build a web-based project named:

AI-Based Resume Analyzer and Job Matching System

PROJECT TYPE

This is a BCA-level Minor Project.

The project must be a genuine working AI/ML + NLP based application, not a static demo or hardcoded-result application.

MAIN OBJECTIVE

The system should allow a user to:

Upload a resume in PDF format.

Extract text from the resume.

Clean and preprocess the extracted text.

Identify skills and keywords from the resume.

Enter or provide a Job Description.

Analyze the Job Description.

Compare the resume with the Job Description.

Calculate a meaningful matching score.

Display matched skills.

Display missing skills.

Generate basic intelligent improvement recommendations.

Save analysis history for the user.

Allow the user to view previous analyses.

FIXED TECHNOLOGY STACK

Do not randomly change or add technologies.

Target stack:

Frontend:

HTML

CSS

JavaScript

Bootstrap

Backend:

Python

Flask

PDF Processing:

PyMuPDF

NLP:

Python NLP techniques

Text preprocessing

Tokenization

Stop-word removal

Keyword extraction

Skill extraction

Machine Learning:

scikit-learn

TF-IDF

Cosine Similarity

Data Processing:

pandas

NumPy

Database:

SQLite

Charts:

Chart.js only if genuinely useful.

Development:

VS Code

Git

GitHub

IMPORTANT ARCHITECTURE RULE

The final application should use Python + Flask as the backend.

Do not replace the backend with another framework.

Do not introduce unnecessary technologies.

Do not add external AI APIs such as OpenAI, Gemini, Claude, etc. unless explicitly requested later.

The AI/ML functionality must be implemented locally using NLP techniques and scikit-learn.

DEVELOPMENT METHOD

Build the application incrementally.

DO NOT generate the entire application at once.

Implement only the current milestone/task.

After each milestone:

Run the application.

Test the implemented functionality.

Fix discovered issues.

Verify that previously working functionality still works.

Only then continue to the next milestone.

CODE SAFETY RULES

Before modifying code:

Understand the existing project structure.

Reuse existing components where possible.

Do not rewrite working modules unnecessarily.

Do not modify unrelated features.

Make the smallest necessary changes.

Preserve existing functionality.

Keep code modular and maintainable.

Avoid duplicated code.

UI RULES

Create a clean, modern, professional and responsive UI.

Use Bootstrap where appropriate.

The interface should look like a real student/job-seeker application rather than a basic HTML demo.

Use:

Responsive navbar/sidebar

Cards

Tables

Forms

Progress indicators

Score displays

Loading states

Empty states

Success messages

Error messages

Do not sacrifice functionality for visual effects.

ERROR HANDLING

Every important operation should handle errors properly.

Examples:

Invalid PDF

Corrupted PDF

Empty PDF

PDF with no extractable text

Missing Job Description

Empty input

Invalid input

Database error

Analysis failure

Unexpected server error

Never show a blank page or raw Python traceback to the user.

SECURITY BASICS

Implement basic security appropriate for a student project:

Validate uploaded files.

Restrict resume uploads to PDF.

Use safe filenames.

Do not expose sensitive configuration.

Do not expose passwords or secret keys in frontend code.

Protect user-specific data.

Prevent unauthorized access to user pages.

Validate form inputs.

AI/ML REQUIREMENT

The matching system must not simply return hardcoded scores.

The score must be calculated from the actual resume and actual Job Description.

Use:

Resume Text
+
Job Description
↓
Text preprocessing
↓
TF-IDF
↓
Cosine Similarity
↓
Skill comparison
↓
Matching score

Also identify:

Matched skills

Missing skills

Recommendations

The system should use a predefined skill dataset/list initially.

Initial skills can include:

Python
Java
C++
JavaScript
HTML
CSS
SQL
MySQL
Flask
Django
Git
GitHub
React
Node.js
PHP
and other common technical skills.

MATCHING SYSTEM

Use both:

Text similarity

Skill matching

The final score should be deterministic and explainable.

Do not generate random scores.

Do not generate fake AI results.

Display enough information so the user can understand why the score was obtained.

DATABASE

Use SQLite.

The basic conceptual relationships are:

users
↓
resumes
↓
analyses

Users should only be able to access their own resume and analysis history.

CURRENT DEVELOPMENT RULE

Start only with the milestone explicitly requested by me.

Do not implement future milestones automatically.

At the end of each task, tell me:

What was implemented.

Which files were created/modified.

How to run/test it.

What should be tested before proceeding.

Any known limitation.

Do not dump unrelated code.

PROJECT QUALITY

The final result should be:

Fully runnable locally.

Modular.

Understandable for a BCA student.

Suitable for academic demonstration.

Suitable for GitHub.

Ready for future expansion into a larger AI Career/Job Recommendation platform.

Do not over-engineer the Minor Project.

WAIT FOR MY MILESTONE INSTRUCTION.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/65b062dc-aa9b-477f-b713-29b8e6792962).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

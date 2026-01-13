"""Prompt templates for LLM analysis."""

EMAIL_ANALYSIS_PROMPT = """Analyze this email and extract job application information.

EMAIL DETAILS:
Subject: {subject}
From: {sender}
Body: {body}

{thread_context}

TASK:
1. Determine if this is a REAL job application email (not marketplace, newsletter, or promotional)
2. Extract company name, position title, and application status
3. Provide reasoning for your classification

CRITICAL - POSITION EXTRACTION:
The position title is ESSENTIAL. Try VERY HARD to extract it. Look in these locations:
1. Subject line (e.g., "Re: Software Engineer Application")
2. Body text (e.g., "regarding your application for Data Scientist")
3. Email signatures or footers (e.g., "Talent Team - ML Engineer Role")
4. Reference to "the [Position] role" or "this position"
5. Any mention of job title in context of "your application"
6. **THREAD CONTEXT above** - If this email is part of a conversation thread and the context shows company/position from earlier emails, USE THAT INFORMATION

Return null ONLY if there is absolutely NO indication of the position anywhere in the email OR thread context.
Even vague titles like "Graduate Program" or "Engineering Role" are better than null.

IMPORTANT RULES:
- If email is about a product/template (e.g., "template", "marketplace", "download"), mark as NOT job-related
- If email contains pricing, ratings, or promotional content, mark as NOT job-related
- Company name should be the ACTUAL employer, not the ATS platform (e.g., "Apple" not "Lever")
- Position must be a real job title, not phrases like "Your Interest In..."
- For German emails, extract information the same way as English

STATUS CLASSIFICATION:
- "Applied": Initial application submission
- "Application Received": Confirmation that application was received
- "Interview Scheduled": Interview invitation or scheduling
- "Assessment Sent": Coding challenge, take-home assignment
- "Offer Received": Job offer extended
- "Rejected": Application declined or position filled

OUTPUT FORMAT (JSON):
{{
  "is_job_related": true/false,
  "confidence": 0.0-1.0,
  "company": "Company Name" or null,
  "position": "Job Title" or null,
  "status": "Status from list above" or null,
  "reasoning": "Brief explanation of classification"
}}

EXAMPLES:

Example 1 (Confirmation - Clear):
Subject: Your application to Apple
Body: Thank you for applying to the Senior Software Engineer position at Apple. We have received your application...
Output: {{"is_job_related": true, "confidence": 0.95, "company": "Apple", "position": "Senior Software Engineer", "status": "Application Received", "reasoning": "Confirmation email from Apple about software engineer application"}}

Example 2 (Confirmation - Subtle):
Subject: Application Confirmation
Body: Thank you for your interest. Your application has been successfully submitted and is being reviewed.
Output: {{"is_job_related": true, "confidence": 0.85, "company": null, "position": null, "status": "Application Received", "reasoning": "Generic confirmation email confirming application submission"}}

Example 3 (Confirmation - German):
Subject: Bewerbung eingegangen
Body: Vielen Dank für Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten...
Output: {{"is_job_related": true, "confidence": 0.90, "company": null, "position": null, "status": "Application Received", "reasoning": "German confirmation email for received application"}}

Example 4 (Position in Subject):
Subject: Trainee AI Engineer (d/f/m/x) - Application Confirmation
Body: Thank you for your application. We have received your documents and will review them carefully.
Output: {{"is_job_related": true, "confidence": 0.95, "company": null, "position": "Trainee AI Engineer", "status": "Application Received", "reasoning": "Confirmation email with position extracted from subject line"}}

Example 5 (Marketplace Email - NOT JOB):
Subject: You've downloaded Job Application Tracker
Body: Thanks for downloading... Check out these templates... Price: $9.99
Output: {{"is_job_related": false, "confidence": 0.98, "company": null, "position": null, "status": null, "reasoning": "Notion marketplace email about template product, not actual job application"}}

Example 6 (Rejection):
Subject: Update on your application
Body: Thank you for your interest. Unfortunately, we have decided to proceed with other candidates...
Output: {{"is_job_related": true, "confidence": 0.92, "company": null, "position": null, "status": "Rejected", "reasoning": "Rejection email with clear decline language"}}

Example 7 (Interview Invitation):
Subject: Next steps - Interview
Body: We'd love to schedule a phone screen to discuss the role further...
Output: {{"is_job_related": true, "confidence": 0.94, "company": null, "position": null, "status": "Interview Scheduled", "reasoning": "Interview invitation email"}}

Example 8 (Rejection - Position in Subject):
Subject: Re: Senior Data Scientist Application
Body: Thank you for your interest. Unfortunately, we have decided to move forward with other candidates...
Output: {{"is_job_related": true, "confidence": 0.95, "company": null, "position": "Senior Data Scientist", "status": "Rejected", "reasoning": "Rejection email with position extracted from subject line"}}

Example 9 (Update - Position in Body):
Subject: Application Update
Body: We wanted to update you regarding your application for the Machine Learning Engineer position. We are still reviewing...
Output: {{"is_job_related": true, "confidence": 0.93, "company": null, "position": "Machine Learning Engineer", "status": "Application Received", "reasoning": "Status update email with position mentioned in body text"}}

Example 10 (Assessment - Position Reference):
Subject: Next Steps
Body: Please complete this assessment for the Graduate Program role...
Output: {{"is_job_related": true, "confidence": 0.92, "company": null, "position": "Graduate Program", "status": "Assessment Sent", "reasoning": "Assessment email with position mentioned as 'Graduate Program role'"}}

Now analyze the email above and provide JSON output:
"""

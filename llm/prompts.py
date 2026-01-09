"""Prompt templates for LLM analysis."""

EMAIL_ANALYSIS_PROMPT = """Analyze this email and extract job application information.

EMAIL DETAILS:
Subject: {subject}
From: {sender}
Body: {body}

TASK:
1. Determine if this is a REAL job application email (not marketplace, newsletter, or promotional)
2. Extract company name, position title, and application status
3. Provide reasoning for your classification

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

Example 1 (Real Job Email):
Subject: Your application to Apple
Body: Thank you for applying to the Senior Software Engineer position at Apple. We have received your application...
Output: {{"is_job_related": true, "confidence": 0.95, "company": "Apple", "position": "Senior Software Engineer", "status": "Application Received", "reasoning": "Confirmation email from Apple about software engineer application"}}

Example 2 (Marketplace Email - NOT JOB):
Subject: You've downloaded Job Application Tracker
Body: Thanks for downloading... Check out these templates... Price: $9.99
Output: {{"is_job_related": false, "confidence": 0.98, "company": null, "position": null, "status": null, "reasoning": "Notion marketplace email about template product, not actual job application"}}

Example 3 (Rejection):
Subject: Update on your application
Body: Thank you for your interest. Unfortunately, we have decided to proceed with other candidates...
Output: {{"is_job_related": true, "confidence": 0.92, "company": null, "position": null, "status": "Rejected", "reasoning": "Rejection email with clear decline language"}}

Now analyze the email above and provide JSON output:
"""

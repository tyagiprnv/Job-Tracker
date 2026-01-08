"""Keyword patterns and detection rules for job emails (English + German)."""

import re

# Known Application Tracking System (ATS) domains
ATS_DOMAINS = [
    "lever.co",
    "greenhouse.io",
    "workday.com",
    "icims.com",
    "smartrecruiters.com",
    "myworkdayjobs.com",
    "ultipro.com",
    "taleo.net",
    "jobvite.com",
    "applytojob.com",
    "breezy.hr",
    "recruitee.com",
    # German ATS platforms
    "bewerbung-online.com",
    "stellenanzeigen.de",
    "personio.de",
]

# Recruiting email patterns (regex)
RECRUITING_PATTERNS = [
    r"recruiting@",
    r"talent@",
    r"careers@",
    r"jobs@",
    r"hiring@",
    r"hr@",
    r"noreply@.*jobs",
    r"noreply@.*careers",
    # German patterns
    r"bewerbung@",
    r"karriere@",
    r"personal@",
]

# Compile regex patterns for efficiency
RECRUITING_REGEX = re.compile("|".join(RECRUITING_PATTERNS), re.IGNORECASE)

# Status classification keywords (English + German)
STATUS_KEYWORDS = {
    "APPLICATION_RECEIVED": [
        # English
        "received your application",
        "application submitted",
        "thank you for applying",
        "application confirmed",
        "successfully applied",
        "we have received your application",
        # German
        "bewerbung eingegangen",
        "bewerbung erhalten",
        "vielen dank für ihre bewerbung",
        "haben ihre bewerbung erhalten",
        "bewerbung ist bei uns eingegangen",
        "erfolgreich beworben",
    ],
    "INTERVIEW_SCHEDULED": [
        # English
        "schedule an interview",
        "interview invitation",
        "phone screen",
        "meet with",
        "next steps",
        "interview opportunity",
        "schedule a call",
        "invite you to interview",
        # German
        "gespräch vereinbaren",
        "einladung zum gespräch",
        "telefoninterview",
        "vorstellungsgespräch",
        "nächste schritte",
        "kennenlerngespräch",
        "laden sie ein",
    ],
    "REJECTED": [
        # English
        "not moving forward",
        "other candidates",
        "regret to inform",
        "not selected",
        "decided to proceed",
        "unfortunately",
        "will not be moving forward",
        "chosen to pursue",
        "other applicants",
        # German
        "absage",
        "können wir ihnen leider nicht zusagen",
        "andere kandidaten",
        "nicht berücksichtigen",
        "leider müssen wir",
        "haben uns für andere",
        "bedauerlicherweise",
    ],
    "OFFER": [
        # English
        "offer letter",
        "excited to offer",
        "compensation package",
        "extend an offer",
        "pleased to offer",
        "offer of employment",
        "congratulations",
        # German
        "vertragsangebot",
        "arbeitsvertrag",
        "zusage",
        "freuen uns ihnen",
        "angebot zu unterbreiten",
        "gratulation",
    ],
    "ASSESSMENT": [
        # English
        "coding challenge",
        "take-home",
        "assessment",
        "technical test",
        "assignment",
        "complete the following",
        # German
        "programmieraufgabe",
        "testaufgabe",
        "technische aufgabe",
        "übung",
    ],
}

# Detection keywords for identifying job emails (weighted scoring)
DETECTION_KEYWORDS = {
    "HIGH_CONFIDENCE": [
        # English
        "job application",
        "position you applied",
        "your application for",
        "application status",
        "application for the",
        # German
        "ihre bewerbung",
        "ihre anfrage",
        "bewerbungsprozess",
        "bewerbungsstatus",
        "bewerbung für",
    ],
    "MEDIUM_CONFIDENCE": [
        # English
        "interview",
        "candidate",
        "recruiting team",
        "hiring manager",
        "applicant",
        "recruitment",
        # German
        "kandidat",
        "recruiting",
        "personalabteilung",
        "einstellungsprozess",
        "bewerber",
        "personalmanager",
    ],
    "LOW_CONFIDENCE": [
        # English
        "opportunity",
        "role",
        "team",
        "resume",
        "cv",
        "position",
        # German
        "stelle",
        "position",
        "team",
        "lebenslauf",
        "gelegenheit",
    ],
}

# Exclusion patterns (newsletters, job alerts, etc.)
EXCLUSION_PATTERNS = [
    # English
    "job alert",
    "recommended jobs",
    "jobs you might like",
    "newsletter",
    "digest",
    "career tips",
    "unsubscribe",
    "job recommendations",
    "new jobs matching",
    # German
    "jobalarm",
    "stellenanzeigen die zu ihnen passen",
    "newsletter",
    "abmelden",
    "job-empfehlungen",
]

# Common job platforms (not direct applications)
JOB_BOARD_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "stepstone.de",
    "xing.com",
]

# Company name extraction patterns (words to remove for normalization)
COMPANY_SUFFIXES = [
    "inc",
    "inc.",
    "llc",
    "llc.",
    "ltd",
    "ltd.",
    "gmbh",
    "ag",
    "corp",
    "corp.",
    "corporation",
    "company",
    "co.",
]

# Position title keywords (helps identify position in text)
POSITION_INDICATORS = [
    # English
    "position of",
    "role of",
    "position:",
    "role:",
    "title:",
    "for the",
    "as a",
    "as an",
    # German
    "stelle als",
    "position als",
    "als",
    "für die stelle",
]

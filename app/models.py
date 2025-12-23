"""
Data Models for Youth Workshop Activity Generator

Pydantic models for activity details and reports.
"""

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# Set up logging
logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of activities"""
    RELIGIOUS_HOLIDAY = "religious_holiday"
    VALUES_EDUCATION = "values_education"
    STORY_SESSION = "story_session"
    DISCUSSION = "discussion"
    GAME_BASED = "game_based"
    COMBINED = "combined"


class AgeGroup(str, Enum):
    """Target age groups"""
    MIDDLE = "middle"  # 10-13
    TEEN = "teen"  # 14-16
    # No younger children support as per new requirements


class ActivityDetails(BaseModel):
    """Activity details collected from user"""
    
    # Required fields
    activity_type: ActivityType = Field(
        ...,
        description="Type of activity (religious_holiday, values_education, story_session, discussion, game_based, combined)"
    )
    age_group: AgeGroup = Field(
        ...,
        description="Target age group (young: 6-9, middle: 10-13, teen: 14-17, mixed)"
    )
    duration_minutes: int = Field(
        40,
        ge=30,
        le=60,
        description="Duration of activity in minutes (30-60 minutes)"
    )
    main_topic: str = Field(
        ...,
        description="Main topic of the activity in Hebrew (e.g., 'חג הסיגד')"
    )
    main_values: List[str] = Field(
        ...,
        min_length=1,
        description="List of main values/themes in Hebrew (e.g., ['אמונה', 'געגוע לירושלים'])"
    )
    
    # Optional fields
    specific_story_preference: Optional[str] = Field(
        None,
        description="Preferred story title or theme if user has a specific preference"
    )
    opening_activity_preference: Optional[str] = Field(
        None,
        description="Preferred opening activity type (e.g., 'game', 'icebreaker', 'story')"
    )
    closing_message_theme: Optional[str] = Field(
        None,
        description="Theme for closing message if user has a preference"
    )
    number_of_participants: Optional[int] = Field(
        None,
        ge=1,
        description="Expected number of participants"
    )
    location_type: Optional[str] = Field(
        None,
        description="Location type (indoors, outdoors, mixed)"
    )
    materials_available: Optional[List[str]] = Field(
        None,
        description="List of materials available for the activity"
    )
    
    # Additional request/comments
    additional_requirements: Optional[str] = Field(
        None,
        description="Additional requirements or special requests"
    )
    special_notes: Optional[str] = Field(
        None,
        description="Special notes or comments"
    )
    explicit_central_message: Optional[str] = Field(
        None,
        description="Explicit central message provided by the user in the prompt. If provided, this MUST be used as the central message. Should be concrete and specific, not generic."
    )
    
    @field_validator('main_topic')
    @classmethod
    def validate_main_topic(cls, v: str) -> str:
        """Validate main topic is not empty"""
        if not v or not v.strip():
            raise ValueError("Main topic cannot be empty")
        return v.strip()
    
    @field_validator('main_values')
    @classmethod
    def validate_main_values(cls, v: List[str]) -> List[str]:
        """Validate main values list"""
        if not v:
            raise ValueError("At least one main value is required")
        # Filter out empty values
        filtered = [val.strip() for val in v if val and val.strip()]
        if not filtered:
            raise ValueError("At least one non-empty main value is required")
        return filtered
    
    class Config:
        """Pydantic configuration"""
        # Removed json_schema_extra to avoid set serialization issues
        pass


class StoryReference(BaseModel):
    """Reference to a story from agadah.org.il"""
    
    title: str = Field(..., description="Story title in Hebrew")
    url: str = Field(..., description="URL to the story on agadah.org.il - MUST be the exact 'link' field from WordPress search tool results, NEVER construct URLs yourself")
    content: Optional[str] = Field(
        None, 
        description="The actual story content fetched from the URL - this is CRITICAL for creating specific discussion questions and activities based on the story"
    )
    category: Optional[str] = Field(None, description="Story category if available")
    tags: Optional[List[str]] = Field(None, description="Story tags if available")
    relevance_reason: Optional[str] = Field(
        None,
        description="Explanation of why this story is relevant to the activity - must reference specific details from the content"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format and ensure it's a real URL from agadah.org.il"""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        # Ensure it's from agadah.org.il domain
        if "agadah.org.il" not in v:
            raise ValueError(f"URL must be from agadah.org.il domain, got: {v}")
        # Warn if URL looks constructed (contains /story/ followed by topic name)
        # Common patterns: /story/sukkot, /story/סוכות, /story/sigd, etc.
        import re
        # Check for suspicious patterns that suggest constructed URLs
        suspicious_patterns = [
            r'/story/[a-z]+$',  # /story/sukkot, /story/sigd (English)
            r'/story/[\u0590-\u05FF]+$',  # /story/סוכות, /story/סיגד (Hebrew)
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                # This might be a constructed URL - log warning
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ SUSPICIOUS URL PATTERN DETECTED - may be constructed: {v}")
                logger.warning(f"   This URL looks like it was constructed rather than from WordPress API")
                logger.warning(f"   Please ensure you're using the exact 'link' field from search results")
        return v
    
    class Config:
        """Pydantic configuration"""
        pass


class StoryProcessing(BaseModel):
    """Story processing component with guiding questions and connection to activity topic"""
    
    guiding_questions: List[str] = Field(
        ...,
        min_length=3,
        description="List of guiding questions in Hebrew to discuss the story and connect it to the activity topic and central message"
    )
    connection_to_topic: str = Field(
        ...,
        description="Explanation in Hebrew of how the story connects to the main activity topic, values, and central message"
    )
    discussion_instructions: str = Field(
        ...,
        description="Brief instructions in Hebrew for facilitating the discussion"
    )
    
    class Config:
        """Pydantic configuration"""
        pass


class ActivitySection(BaseModel):
    """A section of the activity plan"""
    
    section_name: str = Field(
        ...,
        description="Name of the section in Hebrew (e.g., 'סיפור', 'עיבוד הסיפור', 'משחק')"
    )
    section_type: str = Field(
        ...,
        description="Type of section (story, story_processing, game, activity). Must include story, story_processing, and one interactive element (game/activity)"
    )
    description: str = Field(
        ...,
        description="Brief description of the section in Hebrew (keep it concise - 1-2 sentences)"
    )
    duration_minutes: int = Field(
        ...,
        ge=1,
        description="Duration of this section in minutes"
    )
    materials_needed: Optional[List[str]] = Field(
        None,
        description="List of materials needed for this section"
    )
    instructions: str = Field(
        ...,
        description="Step-by-step instructions in Hebrew (keep concise and clear)"
    )
    discussion_questions: Optional[List[str]] = Field(
        None,
        description="Discussion questions for this section if applicable (deprecated - use story_processing instead)"
    )
    story_reference: Optional[StoryReference] = Field(
        None,
        description="Reference to story used in this section if applicable"
    )
    story_processing: Optional[StoryProcessing] = Field(
        None,
        description="Story processing component with guiding questions and connection to topic. Required if section_type is 'story_processing'"
    )
    
    @field_validator('section_name', 'description', 'instructions')
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        """Validate string fields are not empty"""
        if not v or not v.strip():
            field_name = info.field_name
            raise ValueError(f"{field_name} cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration"""
        pass


class ActivityReport(BaseModel):
    """Final activity report"""
    
    title: str = Field(
        ...,
        description="Title of the activity in Hebrew (e.g., 'פעילות לכבוד הסיגד')"
    )
    central_message: str = Field(
        ...,
        description="""The central message or theme that ALL sections must follow. This is the unifying thread that connects the story, story processing, and game.
        
        CRITICAL REQUIREMENTS:
        - Must be CONCRETE and SPECIFIC, not generic
        - Must be a complete sentence that clearly states the message
        - Should reference specific concepts, values, or ideas
        - Must be directly related to the activity topic and values
        
        GOOD EXAMPLES (concrete and specific):
        - "אמונה בהשגחה עליונה וגעגוע לירושלים ככוח מניע בחיי העם היהודי"
        - "שלום וסובלנות כבסיס לדיאלוג בין אנשים עם דעות שונות"
        - "מסירות נפש למען העם היהודי גם במחיר אישי גבוה"
        - "אהבת חינם ככוח שמאפשר אחדות גם בעת מחלוקת"
        
        BAD EXAMPLES (too generic):
        - "חשוב להיות טוב" (too vague)
        - "אמונה" (not a complete message)
        - "ערכים חשובים" (too general)
        
        If explicit_central_message was provided in activity_details, use that. Otherwise, derive from stories found in research."""
    )
    summary: str = Field(
        ...,
        description="Brief summary sentence in Hebrew explaining what the activity is about and the order of sections (e.g., 'פעילות על [נושא] הכוללת סיפור, עיבוד שלו, ומשחק')"
    )
    activity_details: ActivityDetails = Field(
        ...,
        description="Original activity details"
    )
    sections: List[ActivitySection] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="List of exactly 3 activity sections in order: story, story_processing, and game/activity. ALL sections MUST connect to and reinforce the central_message."
    )
    total_duration_minutes: int = Field(
        ...,
        ge=1,
        description="Total duration of the activity in minutes"
    )
    story_references: List[StoryReference] = Field(
        default_factory=list,  # Can be empty if no suitable stories found
        description="All story references used in the activity. Can be empty list if no stories were found."
    )
    preparation_notes: Optional[str] = Field(
        None,
        description="Notes for preparation before the activity"
    )
    adaptation_notes: Optional[str] = Field(
        None,
        description="Notes on how to adapt the activity for different situations"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @field_validator('sections')
    @classmethod
    def validate_sections(cls, v: List[ActivitySection]) -> List[ActivitySection]:
        """Validate sections list"""
        if not v:
            raise ValueError("At least one section is required")
        return v
    
    @field_validator('total_duration_minutes')
    @classmethod
    def validate_total_duration(cls, v: int) -> int:
        """Validate total duration is positive"""
        if v < 1:
            raise ValueError("Total duration must be at least 1 minute")
        return v
    
    def model_post_init(self, __context):
        """Validate after model initialization"""
        # Check if total duration approximately matches sum of sections
        section_total = sum(section.duration_minutes for section in self.sections)
        if abs(self.total_duration_minutes - section_total) > 5:  # Allow 5 minute tolerance
            logger.warning(
                f"Total duration ({self.total_duration_minutes}) doesn't match "
                f"sum of sections ({section_total}). This is allowed but may indicate an error."
            )
    
    class Config:
        """Pydantic configuration"""
        pass


class SafetyReport(BaseModel):
    """Report from Content Safety Officer"""
    is_safe: bool = Field(..., description="Whether the activity is safe and appropriate")
    safety_score: int = Field(..., ge=1, le=10, description="Safety score 1-10")
    issues: List[str] = Field(default_factory=list, description="List of safety issues found")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    
    class Config:
        """Pydantic configuration"""
        pass


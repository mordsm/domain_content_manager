from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ContentCaptureRequest(BaseModel):
    title: Optional[str] = None
    content_text: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "note"  # video, podcast, article, image, voice, note, infographic
    original_media_url: Optional[str] = None
    workspace_id: Optional[str] = "default_ws"
    owner_id: Optional[str] = "default_owner"
    primary_domain: Optional[str] = "general"
    domains: List[str] = Field(default_factory=list)
    sub_topics: List[str] = Field(default_factory=list)
    custom_tags: List[str] = Field(default_factory=list)

class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    primary_domain: Optional[str] = None
    domains: Optional[List[str]] = None
    sub_topics: Optional[List[str]] = None
    custom_tags: Optional[List[str]] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None

class ContentEnrichRequest(BaseModel):
    record_id: str
    primary_domain: str
    domains: List[str] = Field(default_factory=list)
    sub_topics: List[str] = Field(default_factory=list)
    custom_tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    why_saved: Optional[str] = None
    personal_rating: Optional[int] = None
    reliability_layer: str = "personal"  # research, traditional, personal, doubt
    risk_level: str = "none"  # none, low, medium, high
    seasonality: Optional[str] = None
    domain_specific_data: Dict[str, Any] = Field(default_factory=dict)
    related_record_ids: List[str] = Field(default_factory=list)
    relation_type: str = "related"  # summary_of, derived_from, infographic_of, related

class ContentRecordResponse(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    title: str
    source_url: Optional[str]
    source_type: str
    capture_date: str
    status: str
    summary: Optional[str]
    keywords: List[str]
    primary_domain: str
    domains: List[str]
    sub_topics: List[str] = Field(default_factory=list)
    custom_tags: List[str] = Field(default_factory=list)
    reliability_layer: str
    risk_level: str
    is_cross_domain: bool
    seasonality: Optional[str]
    created_at: str

class CookPilotRequest(BaseModel):
    workspace_id: Optional[str] = "default_ws"
    owner_id: Optional[str] = "default_owner"
    goal: str = Field(default="cook_with_what_i_have")
    available_ingredients: List[str] = Field(default_factory=list)
    avoid_ingredients: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    servings: Optional[int] = None
    max_minutes: Optional[int] = None
    voice_input: Optional[str] = None
    current_step: int = 1
    command: Optional[str] = None
    include_saved_sources: bool = True

class CookPilotResponse(BaseModel):
    title: str
    matched_records: List[Dict[str, Any]]
    suggested_plan: List[str]
    next_action: str
    current_step: int
    total_steps: int
    is_complete: bool
    estimated_total_minutes: Optional[int]
    step_timer_minutes: Optional[int]
    checkpoints: List[str]
    suitability_score: int
    suitability_notes: List[str]
    pantry_readiness: Dict[str, Any]
    substitutions: List[Dict[str, Any]]
    prep_checklist: List[str]
    safety_alerts: List[str]
    serving_adjustments: List[str]
    cleanup_plan: List[str]
    cooking_method: str
    flavor_profile: List[str]
    time_budget: Dict[str, Any]
    leftover_guidance: List[str]
    plating_suggestion: Optional[str]
    confidence: Dict[str, Any]
    suggested_commands: List[str]
    allergen_flags: List[Dict[str, str]]
    nutrition_focus: Dict[str, Any]
    batch_plan: Dict[str, Any]
    heat_level: str
    doneness_cues: List[str]
    rescue_tips: List[str]
    mise_en_place: Dict[str, List[str]]
    difficulty: Dict[str, Any]
    active_attention: Dict[str, Any]
    parallel_tasks: List[str]
    sensory_cues: List[str]
    cookware_plan: Dict[str, Any]
    cost_estimate: Dict[str, Any]
    seasonality_hint: Dict[str, Any]
    generated_note_title: str
    learning_prompts: List[str]
    branch_suggestions: List[Dict[str, str]]
    source_gaps: List[str]
    personalization_hints: List[str]
    risk_review: Dict[str, Any]
    stop_or_continue: Dict[str, str]
    step_history: List[Dict[str, Any]]
    progress_percent: int
    timer_schedule: List[Dict[str, Any]]
    voice_checkpoint: str
    session_tags: List[str]
    obsidian_links: List[str]
    next_session_seed: Dict[str, Any]
    hydration_plan: List[str]
    holding_plan: Dict[str, str]
    reheating_plan: List[str]
    storage_label: Dict[str, str]
    shopping_priority: List[Dict[str, str]]
    cleanup_effort: Dict[str, Any]
    serving_window: Dict[str, str]
    ingredient_roles: List[Dict[str, str]]
    texture_targets: List[str]
    flavor_adjustment_ladder: List[str]
    waste_reduction_plan: List[str]
    plating_variations: List[str]
    confidence_drivers: Dict[str, Any]
    interruption_recovery: Dict[str, str]
    quality_gate: Dict[str, Any]
    constraint_summary: Dict[str, Any]
    assumption_log: List[str]
    missing_info_questions: List[str]
    adaptation_notes: List[str]
    rehearse_script: str
    final_checklist: List[str]
    aroma_notes: List[str]
    table_setup: Dict[str, Any]
    pairing_suggestions: List[str]
    portioning_plan: Dict[str, Any]
    feedback_metrics: List[Dict[str, str]]
    success_criteria: List[str]
    provenance_summary: Dict[str, Any]
    preheat_plan: Dict[str, str]
    seasoning_strategy: List[str]
    allergen_safe_serving: Dict[str, Any]
    kid_friendly_adjustment: List[str]
    make_ahead_window: Dict[str, str]
    emergency_fallback: Dict[str, str]
    voice_command_map: Dict[str, str]
    equipment_safety_check: Dict[str, Any]
    timing_buffer_plan: Dict[str, Any]
    serving_temperature: Dict[str, str]
    garnish_plan: List[str]
    salt_acid_balance: Dict[str, Any]
    leftover_label_details: Dict[str, str]
    cleanup_reset_cue: Dict[str, str]
    portion_scaling_notes: Dict[str, Any]
    prep_order: List[str]
    heat_recovery_plan: Dict[str, str]
    doneness_verification: Dict[str, Any]
    serving_sequence: List[str]
    voice_summary_card: Dict[str, str]
    post_cook_review_prompt: Dict[str, str]
    allergen_cross_contact_plan: Dict[str, Any]
    cook_mode: Dict[str, str]
    shopping_trip_plan: Dict[str, Any]
    sensory_stop_signals: List[str]
    plating_timing_plan: Dict[str, str]
    leftover_risk_flags: List[str]
    voice_recovery_prompts: List[str]
    prep_risk_order: List[str]
    appliance_load_plan: Dict[str, str]
    taste_calibration: Dict[str, Any]
    serving_role_assignments: Dict[str, Any]
    confidence_recheck: Dict[str, Any]
    cleanup_timeline: Dict[str, Any]
    next_cook_memory_patch: Dict[str, Any]
    timing_pressure_flags: Dict[str, Any]
    substitution_confidence: Dict[str, Any]
    nutrition_balance_check: Dict[str, Any]
    heat_zone_plan: Dict[str, str]
    source_review_queue: List[Dict[str, str]]
    interruption_safety_check: Dict[str, str]
    voice_handoff_brief: Dict[str, Any]
    serving_risk_window: Dict[str, str]
    batch_hold_strategy: Dict[str, str]
    flavor_memory_delta: Dict[str, Any]
    tool_cleanup_order: List[str]
    ingredient_cut_size_plan: Dict[str, Any]
    doneness_escalation_path: List[str]
    voice_timer_brief: Dict[str, Any]
    equipment_gaps: List[str]
    dietary_conflicts: List[str]
    source_trace: List[Dict[str, Any]]
    save_candidate: Dict[str, Any]
    shopping_list: List[str]
    ingredient_gaps: List[str]
    cautions: List[str]
    voice_feedback: str

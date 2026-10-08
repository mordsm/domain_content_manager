from fastapi.testclient import TestClient

from app.api.main import app
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.cook_pilot import cook_pilot_engine


def test_cook_pilot_matches_saved_culinary_record():
    init_db()
    record = capture_engine.capture_text_or_url(
        title="Carrot Ginger Soup",
        content_text="Carrot soup with ginger, coconut milk, onion, and turmeric.",
        primary_domain="culinary",
        workspace_id="kitchen_ws",
        owner_id="cook_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="kitchen_ws",
        owner_id="cook_owner",
        available_ingredients=["carrot", "ginger"],
        equipment=["pot"],
        servings=2,
        max_minutes=40,
    )

    assert result["matched_records"][0]["record_id"] == record.id
    assert result["matched_records"][0]["matched_ingredients"] == ["carrot", "ginger"]
    assert result["matched_records"][0]["match_reason"] == "ingredient_overlap"
    assert "onion" in result["shopping_list"]
    assert result["next_action"] == result["suggested_plan"][0]
    assert result["current_step"] == 1
    assert result["total_steps"] == len(result["suggested_plan"])
    assert result["is_complete"] is False
    assert result["estimated_total_minutes"] == 40
    assert result["step_timer_minutes"] == 1
    assert result["checkpoints"]
    assert result["suitability_score"] > 0
    assert result["suitability_notes"]
    assert result["pantry_readiness"]["status"] in {"ready", "mostly_ready", "needs_adjustment"}
    assert "Wash, trim, and cut carrots into even pieces." in result["prep_checklist"]
    assert result["serving_adjustments"] == ["Portion ingredients for 2 servings before cooking starts."]
    assert result["cleanup_plan"]
    assert result["cooking_method"] == "simmer"
    assert "sweet" in result["flavor_profile"]
    assert result["time_budget"]["status"] == "comfortable"
    assert result["confidence"]["band"] in {"medium", "high"}
    assert "next" in result["suggested_commands"]
    assert {"allergen": "tree_nut", "ingredient": "coconut milk", "note": "Review if serving someone with this allergy or sensitivity."} in result["allergen_flags"]
    assert "vegetable" in result["nutrition_focus"]["groups"]
    assert result["batch_plan"]["mode"] == "make_ahead_friendly"
    assert result["heat_level"] == "medium until bubbling, then low"
    assert result["doneness_cues"]
    assert result["rescue_tips"]
    assert "carrot" in result["mise_en_place"]["prep_first"]
    assert result["difficulty"]["level"] in {"easy", "medium"}
    assert result["active_attention"]["level"] == "medium"
    assert "set serving bowls or storage containers" in result["parallel_tasks"]
    assert "bubbles are gentle and regular" in result["sensory_cues"]
    assert result["cookware_plan"]["primary"] == "pot"
    assert result["cost_estimate"]["band"] in {"medium", "high"}
    assert "winter" in result["seasonality_hint"]["seasons"]
    assert result["generated_note_title"] == "Carrot Ginger Simmer Cook Session"
    assert result["learning_prompts"]
    assert any(branch["title"] == "Soup or stew version" for branch in result["branch_suggestions"])
    assert result["source_gaps"] == []
    assert result["risk_review"]["level"] == "medium"
    assert result["stop_or_continue"]["decision"] == "continue_with_caution"
    assert result["step_history"][0]["status"] == "active"
    assert result["progress_percent"] == 0
    assert result["timer_schedule"][0]["step"] == 1
    assert "Set a 1 minute timer." in result["voice_checkpoint"]
    assert "method_simmer" in result["session_tags"]
    assert f"[[{record.title}]]" in result["obsidian_links"]
    assert result["next_session_seed"]["from_note"] == result["generated_note_title"]
    assert "Keep a small cup of water or stock nearby for texture control." in result["hydration_plan"]
    assert result["holding_plan"]["mode"] == "short_hold_ok"
    assert result["reheating_plan"][0] == "Reheat gently with a splash of water or stock."
    assert result["storage_label"]["label"] == "Carrot Ginger Simmer"
    assert any(item["item"] == "safety check" for item in result["shopping_priority"])
    assert result["cleanup_effort"]["level"] in {"low", "medium"}
    assert result["serving_window"]["window"] == "serve_within_15_minutes"
    assert result["source_trace"][0]["record_id"] == record.id
    assert result["save_candidate"]["primary_domain"] == "culinary"
    assert record.id in result["save_candidate"]["related_record_ids"]
    assert any("40 minutes" in step for step in result["suggested_plan"])
    assert "Cook Pilot" in result["voice_feedback"]


def test_cook_pilot_api_returns_plan():
    init_db()
    capture_engine.capture_text_or_url(
        title="Apple Chips",
        content_text="Thin apple slices baked with cinnamon.",
        primary_domain="culinary",
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/cook-pilot/plan",
        json={
            "available_ingredients": ["apple", "cinnamon"],
            "avoid_ingredients": ["peanut"],
            "max_minutes": 30,
            "voice_input": "make a quick snack",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_records"]
    assert payload["suggested_plan"]
    assert payload["next_action"]
    assert payload["current_step"] == 1
    assert payload["estimated_total_minutes"] == 30
    assert "suitability_score" in payload
    assert "equipment_gaps" in payload
    assert "dietary_conflicts" in payload
    assert "pantry_readiness" in payload
    assert "substitutions" in payload
    assert "prep_checklist" in payload
    assert "safety_alerts" in payload
    assert "serving_adjustments" in payload
    assert "cleanup_plan" in payload
    assert "cooking_method" in payload
    assert "flavor_profile" in payload
    assert "time_budget" in payload
    assert "leftover_guidance" in payload
    assert "plating_suggestion" in payload
    assert "confidence" in payload
    assert "suggested_commands" in payload
    assert "allergen_flags" in payload
    assert "nutrition_focus" in payload
    assert "batch_plan" in payload
    assert "heat_level" in payload
    assert "doneness_cues" in payload
    assert "rescue_tips" in payload
    assert "mise_en_place" in payload
    assert "difficulty" in payload
    assert "active_attention" in payload
    assert "parallel_tasks" in payload
    assert "sensory_cues" in payload
    assert "cookware_plan" in payload
    assert "cost_estimate" in payload
    assert "seasonality_hint" in payload
    assert "generated_note_title" in payload
    assert "learning_prompts" in payload
    assert "branch_suggestions" in payload
    assert "source_gaps" in payload
    assert "personalization_hints" in payload
    assert "risk_review" in payload
    assert "stop_or_continue" in payload
    assert "step_history" in payload
    assert "progress_percent" in payload
    assert "timer_schedule" in payload
    assert "voice_checkpoint" in payload
    assert "session_tags" in payload
    assert "obsidian_links" in payload
    assert "next_session_seed" in payload
    assert "hydration_plan" in payload
    assert "holding_plan" in payload
    assert "reheating_plan" in payload
    assert "storage_label" in payload
    assert "shopping_priority" in payload
    assert "cleanup_effort" in payload
    assert "serving_window" in payload
    assert "ingredient_roles" in payload
    assert "texture_targets" in payload
    assert "flavor_adjustment_ladder" in payload
    assert "waste_reduction_plan" in payload
    assert "plating_variations" in payload
    assert "confidence_drivers" in payload
    assert "interruption_recovery" in payload
    assert "quality_gate" in payload
    assert "constraint_summary" in payload
    assert "assumption_log" in payload
    assert "missing_info_questions" in payload
    assert "adaptation_notes" in payload
    assert "rehearse_script" in payload
    assert "final_checklist" in payload
    assert "aroma_notes" in payload
    assert "table_setup" in payload
    assert "pairing_suggestions" in payload
    assert "portioning_plan" in payload
    assert "feedback_metrics" in payload
    assert "success_criteria" in payload
    assert "provenance_summary" in payload
    assert "source_trace" in payload
    assert "save_candidate" in payload
    assert payload["voice_feedback"]


def test_cook_pilot_extracts_ingredients_from_voice_prompt():
    init_db()
    capture_engine.capture_text_or_url(
        title="Tomato Rice",
        content_text="Tomato rice with garlic and onion.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        voice_input="I have tomato and rice, make something fast",
        max_minutes=20,
    )

    assert result["matched_records"][0]["matched_ingredients"] == ["rice", "tomato"]
    assert "garlic" in result["shopping_list"]


def test_cook_pilot_adds_substitution_step_for_avoided_ingredients():
    init_db()
    capture_engine.capture_text_or_url(
        title="Coconut Ginger Soup",
        content_text="Soup with carrot, ginger, coconut milk, and onion.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["carrot", "ginger"],
        avoid_ingredients=["coconut milk"],
    )

    assert result["matched_records"][0]["avoided_ingredients"] == ["coconut milk"]
    assert any("Remove or substitute" in step for step in result["suggested_plan"])


def test_cook_pilot_advances_hands_free_step_commands():
    init_db()
    capture_engine.capture_text_or_url(
        title="Garlic Tomato Rice",
        content_text="Tomato rice with garlic, onion, and salt.",
        primary_domain="culinary",
    )

    first = cook_pilot_engine.plan_next_cook(
        available_ingredients=["tomato", "rice"],
    )
    second = cook_pilot_engine.plan_next_cook(
        available_ingredients=["tomato", "rice"],
        current_step=first["current_step"],
        command="go to the next step",
    )
    repeated = cook_pilot_engine.plan_next_cook(
        available_ingredients=["tomato", "rice"],
        current_step=second["current_step"],
        command="repeat",
    )

    assert second["current_step"] == 2
    assert second["next_action"] == second["suggested_plan"][1]
    assert repeated["current_step"] == second["current_step"]
    assert repeated["next_action"] == second["next_action"]
    assert second["step_timer_minutes"]


def test_cook_pilot_can_stop_session():
    init_db()
    capture_engine.capture_text_or_url(
        title="Quick Eggs",
        content_text="Eggs with salt and pepper.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["egg"],
        command="stop",
    )

    assert result["is_complete"] is True
    assert result["current_step"] == result["total_steps"]
    assert result["next_action"] == "Cooking session is complete."
    assert result["step_timer_minutes"] is None
    assert result["checkpoints"] == ["Serve, store leftovers safely, and save any useful adjustment notes."]


def test_cook_pilot_can_move_back_with_voice_phrase():
    init_db()
    capture_engine.capture_text_or_url(
        title="Bean Tomato Pot",
        content_text="Beans with tomato, onion, garlic, and salt.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["beans", "tomato"],
        current_step=3,
        command="previous step please",
    )

    assert result["current_step"] == 2
    assert result["next_action"] == result["suggested_plan"][1]


def test_cook_pilot_estimates_time_without_max_minutes():
    init_db()
    capture_engine.capture_text_or_url(
        title="Lentil Soup",
        content_text="Lentils with carrot, onion, garlic, and turmeric.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["lentils", "carrot"],
    )

    assert result["estimated_total_minutes"] >= 10
    assert result["step_timer_minutes"] is not None


def test_cook_pilot_reports_equipment_gap_and_adjusts_plan():
    init_db()
    capture_engine.capture_text_or_url(
        title="Baked Apple Chips",
        content_text="Thin apple slices baked with cinnamon.",
        primary_domain="culinary",
    )

    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["apple", "cinnamon"],
        equipment=["knife"],
    )

    assert result["equipment_gaps"] == ["oven"]
    assert any("equipment may be missing" in step for step in result["suggested_plan"])
    assert result["suitability_score"] < 100


def test_cook_pilot_reports_dietary_conflict_and_adjusts_plan():
    init_db()
    capture_engine.capture_text_or_url(
        title="Cheese Eggs",
        content_text="Eggs with cheese, salt, and pepper.",
        primary_domain="culinary",
        workspace_id="diet_ws",
        owner_id="diet_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="diet_ws",
        owner_id="diet_owner",
        available_ingredients=["egg"],
        dietary_preferences=["vegan"],
    )

    assert "vegan conflict: cheese" in result["dietary_conflicts"]
    assert "vegan conflict: egg" in result["dietary_conflicts"]
    assert any("Resolve dietary conflicts" in step for step in result["suggested_plan"])
    assert any("Dietary conflicts need review" in note for note in result["suitability_notes"])


def test_cook_pilot_save_candidate_contains_plan_and_source_trace():
    init_db()
    record = capture_engine.capture_text_or_url(
        title="Pepper Tomato Pan",
        content_text="Tomato and pepper saute in a pan with garlic.",
        primary_domain="culinary",
        workspace_id="save_ws",
        owner_id="save_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="save_ws",
        owner_id="save_owner",
        available_ingredients=["tomato", "pepper"],
    )

    save_candidate = result["save_candidate"]
    assert save_candidate["source_type"] == "note"
    assert save_candidate["relation_type"] == "derived_from"
    assert save_candidate["related_record_ids"] == [record.id]
    assert "Plan:" in save_candidate["content_text"]
    assert "Source trace:" in save_candidate["content_text"]
    assert record.id in save_candidate["content_text"]
    assert any("source trace" in step.lower() for step in result["suggested_plan"])


def test_cook_pilot_source_trace_is_empty_without_saved_sources():
    result = cook_pilot_engine.plan_next_cook(
        available_ingredients=["tomato"],
        include_saved_sources=False,
    )

    assert result["source_trace"] == []
    assert result["save_candidate"]["related_record_ids"] == []
    assert "cook_pilot" in result["save_candidate"]["custom_tags"]
    assert "needs_source_review" in result["save_candidate"]["custom_tags"]
    assert "saved_sources_skipped" in result["source_gaps"]
    assert "no_culinary_source_trace" in result["source_gaps"]


def test_cook_pilot_builds_kitchen_flow_helpers():
    init_db()
    capture_engine.capture_text_or_url(
        title="Chicken Rice Pan",
        content_text="Chicken and rice saute in a pan with garlic and onion.",
        primary_domain="culinary",
        workspace_id="flow_ws",
        owner_id="flow_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="flow_ws",
        owner_id="flow_owner",
        available_ingredients=["chicken", "rice"],
        avoid_ingredients=["garlic"],
        equipment=["pan"],
        servings=6,
    )

    assert result["pantry_readiness"]["status"] in {"mostly_ready", "needs_adjustment"}
    assert {"ingredient": "garlic", "options": ["onion", "ginger"]} in result["substitutions"]
    assert "Rinse rice until the water runs mostly clear." in result["prep_checklist"]
    assert any("Cook chicken fully" in alert for alert in result["safety_alerts"])
    assert result["serving_adjustments"] == [
        "Use a larger pot or pan and add seasoning in stages for an even batch."
    ]
    assert "Wipe oil splatter after the pan cools." in result["cleanup_plan"]
    assert result["cooking_method"] == "pan_cook"
    assert result["time_budget"]["status"] == "unbounded"
    assert "Cool rice leftovers quickly in a shallow container." in result["leftover_guidance"]
    assert result["plating_suggestion"] == "Plate immediately and keep any crisp edges facing up."
    assert result["batch_plan"]["mode"] == "large_batch"
    assert result["heat_level"] == "medium-high then medium"
    assert "Chicken is fully cooked with no pink center." in result["doneness_cues"]
    assert any("pan gets too dry" in tip for tip in result["rescue_tips"])
    assert result["mise_en_place"]["tools_ready"] == ["pan", "knife", "cutting board"]
    assert result["difficulty"]["level"] == "easy"
    assert result["active_attention"]["level"] == "high"
    assert "clear used prep tools" in result["parallel_tasks"]
    assert "sizzling is steady, not smoky" in result["sensory_cues"]
    assert result["cookware_plan"]["primary"] == "pan"
    assert result["cost_estimate"]["drivers"] == ["chicken"]
    assert result["risk_review"]["level"] == "high"
    assert result["stop_or_continue"]["decision"] == "review_before_cooking"
    assert "risk_high" in result["session_tags"]
    assert result["next_session_seed"]["last_decision"] == "review_before_cooking"
    assert result["holding_plan"]["mode"] == "serve_promptly"
    assert result["serving_window"]["window"] == "serve_or_store_within_30_minutes"
    assert any("Choose substitutions" in step for step in result["suggested_plan"])
    assert any("Safety check" in step for step in result["suggested_plan"])
    assert "Prep checklist:" in result["save_candidate"]["content_text"]
    assert "Safety alerts:" in result["save_candidate"]["content_text"]
    assert "Cleanup plan:" in result["save_candidate"]["content_text"]
    assert "Doneness cues:" in result["save_candidate"]["content_text"]
    assert "Rescue tips:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_pilot_brain_outputs_for_tight_timing():
    init_db()
    capture_engine.capture_text_or_url(
        title="Baked Apple Cinnamon",
        content_text="Baked apple with cinnamon and lemon.",
        primary_domain="culinary",
        workspace_id="brain_ws",
        owner_id="brain_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="brain_ws",
        owner_id="brain_owner",
        available_ingredients=["apple", "cinnamon"],
        equipment=["oven"],
        servings=1,
        max_minutes=12,
    )

    assert result["cooking_method"] == "bake"
    assert result["time_budget"]["status"] == "tight"
    assert result["time_budget"]["target_minutes"] == 12
    assert result["flavor_profile"][:2] == ["sweet", "warm"]
    assert result["plating_suggestion"] == "Let it cool briefly, then serve on a dry plate to keep texture crisp."
    assert result["confidence"]["reason"]
    assert result["suggested_commands"] == ["next", "repeat", "stop"]
    assert result["allergen_flags"] == []
    assert result["nutrition_focus"]["groups"] == ["fruit"]
    assert result["batch_plan"]["mode"] == "quick_batch"
    assert result["heat_level"] == "steady oven heat"
    assert "Edges are set or lightly browned." in result["doneness_cues"]
    assert any("timing slips" in tip for tip in result["rescue_tips"])
    assert result["mise_en_place"]["hold_back"] == []
    assert result["difficulty"]["level"] == "medium"
    assert result["active_attention"]["level"] == "medium"
    assert "smells warm and lightly toasted" in result["sensory_cues"]
    assert result["cookware_plan"]["primary"] == "oven tray"
    assert result["cost_estimate"]["band"] == "low"
    assert set(result["seasonality_hint"]["seasons"]) == {"autumn", "winter"}
    assert any("Time budget is tight" in step for step in result["suggested_plan"])
    assert any("Use the main method: bake." in step for step in result["suggested_plan"])
    assert any("Set heat level: steady oven heat." in step for step in result["suggested_plan"])
    assert any("Doneness cues:" in step for step in result["suggested_plan"])
    assert any("Rescue plan:" in step for step in result["suggested_plan"])
    assert "Cook Pilot confidence:" in result["save_candidate"]["content_text"]
    assert "Flavor profile: sweet, warm, acidic" in result["save_candidate"]["content_text"]
    assert "Plating:" in result["save_candidate"]["content_text"]
    assert "Difficulty:" in result["save_candidate"]["content_text"]
    assert "Sensory cues:" in result["save_candidate"]["content_text"]
    assert "Parallel tasks:" in result["save_candidate"]["content_text"]
    assert result["save_candidate"]["title"] == result["generated_note_title"]
    assert "Learning prompts:" in result["save_candidate"]["content_text"]
    assert "Timer schedule:" in result["save_candidate"]["content_text"]
    assert "Step history:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_control_outputs_for_allergens_and_balance():
    init_db()
    capture_engine.capture_text_or_url(
        title="Cheese Egg Toast",
        content_text="Bread with cheese, egg, tomato, salt, and pepper.",
        primary_domain="culinary",
        workspace_id="control_ws",
        owner_id="control_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="control_ws",
        owner_id="control_owner",
        available_ingredients=["bread", "egg", "tomato", "salt"],
        equipment=["pan"],
        max_minutes=10,
    )

    assert result["allergen_flags"][:3] == [
        {"allergen": "gluten", "ingredient": "bread", "note": "Review if serving someone with this allergy or sensitivity."},
        {"allergen": "dairy", "ingredient": "cheese", "note": "Review if serving someone with this allergy or sensitivity."},
        {"allergen": "egg", "ingredient": "egg", "note": "Review if serving someone with this allergy or sensitivity."},
    ]
    assert "protein" in result["nutrition_focus"]["groups"]
    assert "starch" in result["nutrition_focus"]["groups"]
    assert result["batch_plan"]["mode"] == "quick_batch"
    assert result["heat_level"] in {"focused medium-high", "medium-high then medium"}
    assert "Eggs are set to the intended texture." in result["doneness_cues"]
    assert result["mise_en_place"]["hold_back"] == ["salt"]
    assert result["difficulty"]["score"] >= 1
    assert result["cost_estimate"]["band"] in {"medium", "high"}
    assert "summer" in result["seasonality_hint"]["seasons"]
    assert result["risk_review"]["level"] == "high"
    assert result["stop_or_continue"]["decision"] == "review_before_cooking"
    assert "Allergen flags:" in result["save_candidate"]["content_text"]
    assert "Nutrition focus:" in result["save_candidate"]["content_text"]
    assert "Mise en place:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_session_management_outputs():
    init_db()
    capture_engine.capture_text_or_url(
        title="Mushroom Tomato Skillet",
        content_text="Mushroom and tomato saute with onion, lemon, salt, and pepper.",
        primary_domain="culinary",
        workspace_id="session_ws",
        owner_id="session_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="session_ws",
        owner_id="session_owner",
        available_ingredients=["mushroom", "tomato", "lemon", "salt"],
        equipment=["pan"],
        max_minutes=25,
    )

    assert result["cooking_method"] == "pan_cook"
    assert result["difficulty"]["level"] == "easy"
    assert result["active_attention"]["level"] == "high"
    assert result["parallel_tasks"] == ["finish small prep tasks", "clear used prep tools"]
    assert "sizzling is steady, not smoky" in result["sensory_cues"]
    assert "sharpness smells fresh, not harsh" in result["sensory_cues"]
    assert result["cookware_plan"] == {
        "primary": "pan",
        "alternatives": ["wide pot"],
        "missing": [],
    }
    assert result["cost_estimate"]["band"] == "medium"
    assert set(result["seasonality_hint"]["seasons"]) == {"autumn", "summer"}
    assert result["generated_note_title"] == "Mushroom Tomato Lemon Pan Cook Cook Session"
    assert any(branch["title"] == "Sauce version" for branch in result["branch_suggestions"])
    assert any(branch["title"] == "Softer flavor variant" for branch in result["branch_suggestions"])
    assert result["risk_review"]["requires_review"] is True
    assert result["stop_or_continue"]["decision"] == "review_before_cooking"
    assert "[[Mushroom Tomato Skillet]]" in result["obsidian_links"]
    assert "[[Cook Pilot/Sauce version]]" in result["obsidian_links"]
    assert any("Cookware setup: use pan." in step for step in result["suggested_plan"])
    assert any("Stay close to the cooktop" in step for step in result["suggested_plan"])
    assert any("Sensory cues:" in step for step in result["suggested_plan"])
    assert "Cookware plan:" in result["save_candidate"]["content_text"]
    assert "Seasonality:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_memory_and_review_outputs():
    result = cook_pilot_engine.plan_next_cook(
        goal="quick_snack",
        available_ingredients=["apple", "cinnamon"],
        voice_input="make a quick snack",
        include_saved_sources=False,
    )

    assert result["generated_note_title"] == "Apple Cinnamon Flexible Cook Session"
    assert "User prefers speed for this session." in result["personalization_hints"]
    assert "User framed this as a snack." in result["personalization_hints"]
    assert "saved_sources_skipped" in result["source_gaps"]
    assert "no_culinary_source_trace" in result["source_gaps"]
    assert result["risk_review"] == {
        "level": "low",
        "issues": [],
        "requires_review": False,
    }
    assert result["stop_or_continue"]["decision"] == "continue_with_caution"
    assert result["learning_prompts"][:2] == [
        "What adjustment improved the dish most?",
        "What should be repeated next time?",
    ]
    assert result["branch_suggestions"][0]["title"] == "Fast weekday version"
    assert "Generated note title:" in result["save_candidate"]["content_text"]
    assert "Source gaps:" in result["save_candidate"]["content_text"]
    assert "Personalization hints:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_execution_tracking_outputs():
    init_db()
    capture_engine.capture_text_or_url(
        title="Tomato Rice",
        content_text="Tomato rice with garlic and onion.",
        primary_domain="culinary",
        workspace_id="tracking_ws",
        owner_id="tracking_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="tracking_ws",
        owner_id="tracking_owner",
        available_ingredients=["tomato", "rice"],
        current_step=3,
        command="next",
        max_minutes=20,
    )

    assert result["current_step"] == 4
    assert result["progress_percent"] > 0
    assert result["step_history"][0]["status"] == "complete"
    assert result["step_history"][3]["status"] == "active"
    assert len(result["timer_schedule"]) == result["total_steps"]
    assert result["timer_schedule"][0]["cumulative_minutes"] >= result["timer_schedule"][0]["minutes"]
    assert result["voice_checkpoint"].startswith(result["next_action"])
    assert "method_simmer" in result["session_tags"]
    assert result["obsidian_links"][0] == "[[Tomato Rice]]"
    assert result["next_session_seed"]["review_prompt"] == "What adjustment improved the dish most?"
    assert "Voice checkpoint:" in result["save_candidate"]["content_text"]
    assert "Session tags:" in result["save_candidate"]["content_text"]
    assert "Obsidian links:" in result["save_candidate"]["content_text"]
    assert "Next session seed:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_after_cook_logistics_outputs():
    init_db()
    capture_engine.capture_text_or_url(
        title="Bean Lentil Soup",
        content_text="Beans and lentils simmer with carrot, onion, salt, and pepper.",
        primary_domain="culinary",
        workspace_id="logistics_ws",
        owner_id="logistics_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="logistics_ws",
        owner_id="logistics_owner",
        available_ingredients=["beans", "lentils", "carrot"],
        equipment=["pot"],
        servings=5,
        max_minutes=45,
    )

    assert result["cooking_method"] == "simmer"
    assert "Set a water break at the midpoint." in result["hydration_plan"]
    assert result["holding_plan"] == {
        "mode": "short_hold_ok",
        "guidance": "Hold briefly covered and recheck texture before serving.",
    }
    assert result["reheating_plan"] == [
        "Reheat gently with a splash of water or stock.",
        "Stir and check seasoning after reheating.",
    ]
    assert result["storage_label"]["label"] == "Beans Lentils Carrot Simmer"
    assert result["storage_label"]["cooling_priority"] == "normal"
    assert result["shopping_priority"][0]["priority"] == "optional"
    assert result["cleanup_effort"]["first_action"] == "Clear one landing zone for hot cookware."
    assert result["serving_window"]["window"] == "serve_within_15_minutes"
    assert "Hydration plan:" in result["save_candidate"]["content_text"]
    assert "Holding plan:" in result["save_candidate"]["content_text"]
    assert "Reheating plan:" in result["save_candidate"]["content_text"]
    assert "Shopping priority:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_refinement_and_recovery_outputs():
    init_db()
    capture_engine.capture_text_or_url(
        title="Zucchini Tomato Pan",
        content_text="Zucchini and tomato saute with garlic, lemon, salt, and pepper.",
        primary_domain="culinary",
        workspace_id="refine_ws",
        owner_id="refine_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="refine_ws",
        owner_id="refine_owner",
        available_ingredients=["zucchini", "tomato", "garlic", "lemon"],
        equipment=["pan"],
        servings=2,
        current_step=2,
    )

    assert {"ingredient": "zucchini", "role": "produce", "source": "available"} in result["ingredient_roles"]
    assert {"ingredient": "garlic", "role": "seasoning", "source": "available"} in result["ingredient_roles"]
    assert "hot through with intentional browning" in result["texture_targets"]
    assert result["flavor_adjustment_ladder"][0] == "Taste before changing anything."
    assert "Add a savory base note before adding more salt." not in result["flavor_adjustment_ladder"]
    assert "Use zest before juicing if the peel is clean." in result["waste_reduction_plan"]
    assert "Save clean vegetable trimmings for stock if practical." in result["waste_reduction_plan"]
    assert "Plate browned pieces on top so texture stays visible." in result["plating_variations"]
    assert result["confidence_drivers"]["band"] == result["confidence"]["band"]
    assert result["confidence_drivers"]["positive"]
    assert result["interruption_recovery"] == {
        "resume_step": "2",
        "action": "Turn heat down or off before stepping away from the pan.",
    }
    assert "Ingredient roles:" in result["save_candidate"]["content_text"]
    assert "Texture targets:" in result["save_candidate"]["content_text"]
    assert "Flavor adjustment ladder:" in result["save_candidate"]["content_text"]
    assert "Waste reduction:" in result["save_candidate"]["content_text"]
    assert "Plating variations:" in result["save_candidate"]["content_text"]
    assert "Confidence drivers:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_preflight_review_outputs():
    result = cook_pilot_engine.plan_next_cook(
        goal="fast_dinner",
        available_ingredients=["egg", "bread"],
        equipment=["pan"],
        max_minutes=10,
        include_saved_sources=False,
    )

    assert result["quality_gate"]["status"] == "blocked"
    assert "risk_review_required" in result["quality_gate"]["blockers"]
    assert result["constraint_summary"]["time"] == "10 minutes"
    assert result["constraint_summary"]["servings"] == "not specified"
    assert "Saved sources were intentionally skipped." in result["assumption_log"]
    assert "How many servings should this make?" in result["missing_info_questions"]
    assert "Any dietary constraints for the people eating?" in result["missing_info_questions"]
    assert "Cut smaller and simplify optional steps." in result["adaptation_notes"]
    assert "Review risk flags before serving." in result["adaptation_notes"]
    assert result["rehearse_script"].startswith("Cook Pilot: Fast Dinner:")
    assert result["final_checklist"][0] == "Quality gate: blocked."
    assert any("Eggs are set" in item for item in result["final_checklist"])
    assert "Quality gate:" in result["save_candidate"]["content_text"]
    assert "Constraint summary:" in result["save_candidate"]["content_text"]
    assert "Assumptions:" in result["save_candidate"]["content_text"]
    assert "Missing info questions:" in result["save_candidate"]["content_text"]
    assert "Adaptation notes:" in result["save_candidate"]["content_text"]
    assert "Rehearse script:" in result["save_candidate"]["content_text"]
    assert "Final checklist:" in result["save_candidate"]["content_text"]


def test_cook_pilot_adds_serving_experience_and_review_metrics():
    init_db()
    capture_engine.capture_text_or_url(
        title="Apple Cinnamon Bake",
        content_text="Baked apple with cinnamon and lemon.",
        primary_domain="culinary",
        workspace_id="serve_ws",
        owner_id="serve_owner",
    )

    result = cook_pilot_engine.plan_next_cook(
        workspace_id="serve_ws",
        owner_id="serve_owner",
        available_ingredients=["apple", "cinnamon", "lemon"],
        equipment=["oven"],
        servings=3,
        max_minutes=35,
    )

    assert "warm spices should smell fragrant, not scorched" in result["aroma_notes"]
    assert result["table_setup"]["style"] == "family_style"
    assert result["table_setup"]["timing"] == result["serving_window"]["window"]
    assert "Pair with something creamy, starchy, or mild." in result["pairing_suggestions"]
    assert "Pair with something salty or tangy for balance." in result["pairing_suggestions"]
    assert result["portioning_plan"]["servings"] == 3
    assert result["portioning_plan"]["mode"] == result["batch_plan"]["mode"]
    assert result["feedback_metrics"][0]["metric"] == "texture"
    assert any(item["metric"] == "learning" for item in result["feedback_metrics"])
    assert result["success_criteria"][0] in result["doneness_cues"]
    assert result["provenance_summary"]["source_count"] == 1
    assert result["provenance_summary"]["source_titles"] == ["Apple Cinnamon Bake"]
    assert "Aroma notes:" in result["save_candidate"]["content_text"]
    assert "Pairing suggestions:" in result["save_candidate"]["content_text"]
    assert "Portioning plan:" in result["save_candidate"]["content_text"]
    assert "Feedback metrics:" in result["save_candidate"]["content_text"]
    assert "Success criteria:" in result["save_candidate"]["content_text"]

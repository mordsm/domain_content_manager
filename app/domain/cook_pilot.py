from typing import Any

from app.db.models import ContentRecord
from app.domain.retrieval import retrieval_engine
from app.services.tts_service import tts_service


class CookPilotEngine:
    COMMON_INGREDIENTS = [
        "apple",
        "beans",
        "bread",
        "carrot",
        "cheese",
        "chicken",
        "cinnamon",
        "coconut milk",
        "egg",
        "garlic",
        "ginger",
        "lentils",
        "lemon",
        "mushroom",
        "onion",
        "pepper",
        "potato",
        "rice",
        "salt",
        "tomato",
        "turmeric",
        "zucchini",
    ]
    EQUIPMENT_HINTS = {
        "baked": "oven",
        "bake": "oven",
        "soup": "pot",
        "rice": "pot",
        "saute": "pan",
        "fried": "pan",
        "blend": "blender",
        "smoothie": "blender",
    }
    DIETARY_CONFLICTS = {
        "vegan": ["cheese", "chicken", "egg"],
        "vegetarian": ["chicken"],
        "dairy-free": ["cheese", "coconut milk"],
        "gluten-free": ["bread"],
    }
    PREP_HINTS = {
        "apple": "Slice apples evenly so they cook at the same pace.",
        "beans": "Rinse and drain beans before adding them.",
        "carrot": "Wash, trim, and cut carrots into even pieces.",
        "chicken": "Keep chicken separate from ready-to-eat ingredients.",
        "garlic": "Peel and mince garlic before heating the pan.",
        "ginger": "Peel and grate ginger before cooking starts.",
        "lentils": "Rinse lentils until the water runs mostly clear.",
        "mushroom": "Brush mushrooms clean and slice them evenly.",
        "onion": "Dice onion before heating oil.",
        "potato": "Scrub potatoes and cut them into even pieces.",
        "rice": "Rinse rice until the water runs mostly clear.",
        "tomato": "Chop tomatoes and keep their juices for the dish.",
        "zucchini": "Trim zucchini and cut it into even pieces.",
    }
    SUBSTITUTIONS = {
        "bread": ["rice", "potato"],
        "cheese": ["nutritional yeast", "olive oil"],
        "chicken": ["beans", "lentils", "mushroom"],
        "coconut milk": ["vegetable stock", "cream"],
        "egg": ["tofu", "beans"],
        "garlic": ["onion", "ginger"],
        "onion": ["garlic", "leek"],
    }
    SAFETY_CUES = {
        "chicken": "Cook chicken fully and avoid cross-contamination with ready-to-eat food.",
        "egg": "Cook eggs until set unless using pasteurized eggs.",
        "mushroom": "Use only positively identified edible mushrooms from trusted sources.",
        "rice": "Cool leftover rice quickly and refrigerate it promptly.",
    }
    FLAVOR_CUES = {
        "apple": "sweet",
        "carrot": "sweet",
        "cinnamon": "warm",
        "coconut milk": "creamy",
        "garlic": "savory",
        "ginger": "bright",
        "lemon": "acidic",
        "mushroom": "umami",
        "onion": "savory",
        "pepper": "fresh",
        "tomato": "acidic",
        "turmeric": "earthy",
    }
    METHOD_CUES = {
        "bake": "bake",
        "baked": "bake",
        "blend": "blend",
        "fried": "pan_cook",
        "saute": "pan_cook",
        "smoothie": "blend",
        "soup": "simmer",
        "rice": "simmer",
    }
    ALLERGEN_CUES = {
        "bread": "gluten",
        "cheese": "dairy",
        "coconut milk": "tree_nut",
        "egg": "egg",
    }
    NUTRITION_CUES = {
        "apple": "fruit",
        "beans": "plant_protein",
        "bread": "starch",
        "carrot": "vegetable",
        "chicken": "protein",
        "egg": "protein",
        "lentils": "plant_protein",
        "mushroom": "vegetable",
        "onion": "vegetable",
        "potato": "starch",
        "rice": "starch",
        "tomato": "vegetable",
        "zucchini": "vegetable",
    }
    DONENESS_CUES = {
        "bake": ["Edges are set or lightly browned.", "A tester or fork meets the expected tenderness."],
        "blend": ["Texture is smooth enough for the intended dish.", "Taste is balanced after blending."],
        "flexible": ["Main ingredient is tender enough to eat.", "Seasoning tastes balanced before serving."],
        "pan_cook": ["Surface has color without burning.", "Ingredients are hot through and texture is intentional."],
        "simmer": ["Liquid is gently bubbling, not aggressively boiling.", "Dense ingredients are tender all the way through."],
    }
    SEASONAL_CUES = {
        "apple": "autumn",
        "carrot": "winter",
        "cinnamon": "winter",
        "coconut milk": "year_round",
        "lentils": "winter",
        "mushroom": "autumn",
        "tomato": "summer",
        "zucchini": "summer",
    }
    COST_CUES = {
        "beans": 1,
        "bread": 1,
        "carrot": 1,
        "cinnamon": 1,
        "egg": 1,
        "lentils": 1,
        "lemon": 1,
        "onion": 1,
        "pepper": 1,
        "potato": 1,
        "rice": 1,
        "salt": 1,
        "apple": 2,
        "cheese": 2,
        "coconut milk": 2,
        "mushroom": 2,
        "tomato": 2,
        "zucchini": 2,
        "chicken": 3,
    }

    def plan_next_cook(
        self,
        workspace_id: str = "default_ws",
        owner_id: str = "default_owner",
        goal: str = "cook_with_what_i_have",
        available_ingredients: list[str] | None = None,
        avoid_ingredients: list[str] | None = None,
        dietary_preferences: list[str] | None = None,
        equipment: list[str] | None = None,
        servings: int | None = None,
        max_minutes: int | None = None,
        voice_input: str | None = None,
        current_step: int = 1,
        command: str | None = None,
        include_saved_sources: bool = True,
    ) -> dict[str, Any]:
        available_ingredients = self._clean_terms(available_ingredients)
        voice_ingredients = self._ingredients_from_voice(voice_input)
        available_ingredients = self._merge_unique(available_ingredients, voice_ingredients)
        avoid_ingredients = self._clean_terms(avoid_ingredients)
        dietary_preferences = self._clean_terms(dietary_preferences)
        equipment = self._clean_terms(equipment)

        records = retrieval_engine.search(domain="culinary") if include_saved_sources else []
        records = [
            record for record in records
            if record.workspace_id == workspace_id and record.owner_id == owner_id
        ]

        matches = self._rank_records(records, available_ingredients, avoid_ingredients)
        top_matches = matches[:3]
        suggested_plan = self._build_plan(
            goal=goal,
            available_ingredients=available_ingredients,
            avoid_ingredients=avoid_ingredients,
            dietary_preferences=dietary_preferences,
            equipment=equipment,
            servings=servings,
            max_minutes=max_minutes,
            matched_records=top_matches,
            voice_input=voice_input,
        )
        gaps = self._ingredient_gaps(available_ingredients, top_matches)
        shopping_list = self._shopping_list(available_ingredients, top_matches)
        equipment_gaps = self._equipment_gaps(equipment, top_matches)
        dietary_conflicts = self._dietary_conflicts(dietary_preferences, top_matches)
        suitability = self._suitability(top_matches, shopping_list, equipment_gaps, dietary_conflicts)
        pantry_readiness = self._pantry_readiness(
            available_ingredients,
            shopping_list,
            equipment_gaps,
            dietary_conflicts,
        )
        substitutions = self._substitutions(avoid_ingredients, dietary_conflicts, shopping_list)
        prep_checklist = self._prep_checklist(available_ingredients, top_matches)
        safety_alerts = self._safety_alerts(available_ingredients, top_matches)
        serving_adjustments = self._serving_adjustments(servings)
        cleanup_plan = self._cleanup_plan(top_matches, equipment_gaps)
        cooking_method = self._cooking_method(top_matches, goal, voice_input)
        flavor_profile = self._flavor_profile(available_ingredients, top_matches)
        time_budget = self._time_budget(max_minutes, suggested_plan, cooking_method)
        leftover_guidance = self._leftover_guidance(servings, available_ingredients, top_matches)
        plating_suggestion = self._plating_suggestion(cooking_method, flavor_profile)
        source_trace = self._source_trace(top_matches)
        confidence = self._confidence_band(suitability, pantry_readiness, source_trace)
        allergen_flags = self._allergen_flags(available_ingredients, top_matches)
        nutrition_focus = self._nutrition_focus(available_ingredients, top_matches)
        batch_plan = self._batch_plan(servings, max_minutes, cooking_method)
        heat_level = self._heat_level(cooking_method, time_budget)
        doneness_cues = self._doneness_cues(cooking_method, available_ingredients)
        rescue_tips = self._rescue_tips(cooking_method, flavor_profile, time_budget, equipment_gaps)
        mise_en_place = self._mise_en_place(available_ingredients, prep_checklist, equipment)
        difficulty = self._difficulty(cooking_method, time_budget, equipment_gaps, dietary_conflicts)
        active_attention = self._active_attention(cooking_method, difficulty)
        parallel_tasks = self._parallel_tasks(cooking_method, prep_checklist, cleanup_plan, time_budget)
        sensory_cues = self._sensory_cues(cooking_method, flavor_profile)
        cookware_plan = self._cookware_plan(cooking_method, equipment, equipment_gaps)
        cost_estimate = self._cost_estimate(available_ingredients, shopping_list)
        seasonality_hint = self._seasonality_hint(available_ingredients, top_matches)
        generated_note_title = self._generated_note_title(goal, available_ingredients, cooking_method)
        learning_prompts = self._learning_prompts(cooking_method, flavor_profile, confidence)
        branch_suggestions = self._branch_suggestions(cooking_method, dietary_preferences, flavor_profile)
        source_gaps = self._source_gaps(top_matches, include_saved_sources, gaps)
        personalization_hints = self._personalization_hints(voice_input, dietary_preferences, avoid_ingredients)
        risk_review = self._risk_review(safety_alerts, allergen_flags, dietary_conflicts)
        stop_or_continue = self._stop_or_continue(confidence, pantry_readiness, risk_review, source_gaps)
        suggested_plan = self._add_fit_adjustments(
            suggested_plan,
            equipment_gaps,
            dietary_conflicts,
            substitutions,
            prep_checklist,
            safety_alerts,
            serving_adjustments,
            cleanup_plan,
            cooking_method,
            time_budget,
            leftover_guidance,
            plating_suggestion,
            heat_level,
            doneness_cues,
            rescue_tips,
            mise_en_place,
            difficulty,
            active_attention,
            parallel_tasks,
            sensory_cues,
            cookware_plan,
        )
        cautions = self._cautions(avoid_ingredients, top_matches)
        title = self._title(goal, top_matches)
        step_state = self._step_state(suggested_plan, current_step, command)
        next_action = step_state["next_action"]
        estimated_total_minutes = self._estimated_total_minutes(max_minutes, suggested_plan)
        step_timer_minutes = self._step_timer_minutes(next_action, estimated_total_minutes)
        checkpoints = self._checkpoints(next_action, cautions, shopping_list, equipment_gaps, dietary_conflicts)
        step_history = self._step_history(suggested_plan, step_state)
        progress_percent = self._progress_percent(step_state)
        timer_schedule = self._timer_schedule(suggested_plan, estimated_total_minutes)
        voice_checkpoint = self._voice_checkpoint(next_action, checkpoints, step_timer_minutes)
        session_tags = self._session_tags(cooking_method, dietary_preferences, risk_review, source_gaps)
        obsidian_links = self._obsidian_links(source_trace, branch_suggestions)
        next_session_seed = self._next_session_seed(
            generated_note_title,
            branch_suggestions,
            learning_prompts,
            stop_or_continue,
        )
        hydration_plan = self._hydration_plan(cooking_method, heat_level, max_minutes)
        holding_plan = self._holding_plan(cooking_method, risk_review, serving_adjustments)
        reheating_plan = self._reheating_plan(cooking_method, leftover_guidance)
        storage_label = self._storage_label(generated_note_title, risk_review, leftover_guidance)
        shopping_priority = self._shopping_priority(shopping_list, substitutions, risk_review)
        cleanup_effort = self._cleanup_effort(cleanup_plan, cookware_plan, cooking_method)
        serving_window = self._serving_window(cooking_method, risk_review, time_budget)
        ingredient_roles = self._ingredient_roles(available_ingredients, shopping_list, flavor_profile)
        texture_targets = self._texture_targets(cooking_method, available_ingredients)
        flavor_adjustment_ladder = self._flavor_adjustment_ladder(flavor_profile, avoid_ingredients)
        waste_reduction_plan = self._waste_reduction_plan(available_ingredients, shopping_list, cleanup_plan)
        plating_variations = self._plating_variations(cooking_method, servings, plating_suggestion)
        confidence_drivers = self._confidence_drivers(confidence, suitability, source_trace, source_gaps)
        interruption_recovery = self._interruption_recovery(cooking_method, step_state, risk_review)
        quality_gate = self._quality_gate(stop_or_continue, risk_review, pantry_readiness, confidence)
        constraint_summary = self._constraint_summary(
            max_minutes,
            servings,
            dietary_preferences,
            avoid_ingredients,
            equipment_gaps,
        )
        assumption_log = self._assumption_log(include_saved_sources, source_trace, max_minutes, servings)
        missing_info_questions = self._missing_info_questions(
            available_ingredients,
            equipment,
            servings,
            dietary_preferences,
            source_gaps,
        )
        adaptation_notes = self._adaptation_notes(substitutions, equipment_gaps, time_budget, risk_review)
        rehearse_script = self._rehearse_script(title, next_action, stop_or_continue, voice_checkpoint)
        final_checklist = self._final_checklist(quality_gate, doneness_cues, serving_window, storage_label)
        aroma_notes = self._aroma_notes(cooking_method, flavor_profile, sensory_cues)
        table_setup = self._table_setup(servings, serving_window, plating_variations)
        pairing_suggestions = self._pairing_suggestions(cooking_method, flavor_profile, nutrition_focus)
        portioning_plan = self._portioning_plan(servings, batch_plan, leftover_guidance)
        feedback_metrics = self._feedback_metrics(texture_targets, flavor_adjustment_ladder, learning_prompts)
        success_criteria = self._success_criteria(doneness_cues, quality_gate, stop_or_continue)
        provenance_summary = self._provenance_summary(source_trace, source_gaps, confidence_drivers)
        suggested_commands = self._suggested_commands(step_state)
        preheat_plan = self._preheat_plan(cooking_method, cookware_plan, time_budget)
        seasoning_strategy = self._seasoning_strategy(flavor_profile, avoid_ingredients, dietary_preferences)
        allergen_safe_serving = self._allergen_safe_serving(allergen_flags, risk_review, servings)
        kid_friendly_adjustment = self._kid_friendly_adjustment(flavor_profile, heat_level, risk_review)
        make_ahead_window = self._make_ahead_window(cooking_method, leftover_guidance, serving_window)
        emergency_fallback = self._emergency_fallback(
            available_ingredients,
            cooking_method,
            equipment_gaps,
            quality_gate,
        )
        voice_command_map = self._voice_command_map(suggested_commands, step_state)
        equipment_safety_check = self._equipment_safety_check(cookware_plan, equipment_gaps, risk_review)
        timing_buffer_plan = self._timing_buffer_plan(time_budget, estimated_total_minutes, timer_schedule)
        serving_temperature = self._serving_temperature(cooking_method, risk_review, serving_window)
        garnish_plan = self._garnish_plan(flavor_profile, available_ingredients, avoid_ingredients)
        salt_acid_balance = self._salt_acid_balance(flavor_profile, seasoning_strategy)
        leftover_label_details = self._leftover_label_details(storage_label, leftover_guidance, risk_review)
        cleanup_reset_cue = self._cleanup_reset_cue(cleanup_effort, cookware_plan, safety_alerts)
        portion_scaling_notes = self._portion_scaling_notes(servings, portioning_plan, serving_adjustments)
        prep_order = self._prep_order(mise_en_place, prep_checklist, cooking_method)
        heat_recovery_plan = self._heat_recovery_plan(cooking_method, heat_level, rescue_tips)
        doneness_verification = self._doneness_verification(doneness_cues, risk_review, cooking_method)
        serving_sequence = self._serving_sequence(serving_temperature, plating_variations, table_setup)
        voice_summary_card = self._voice_summary_card(title, next_action, timing_buffer_plan, risk_review)
        post_cook_review_prompt = self._post_cook_review_prompt(feedback_metrics, success_criteria, next_session_seed)
        allergen_cross_contact_plan = self._allergen_cross_contact_plan(allergen_flags, dietary_conflicts)
        cook_mode = self._cook_mode(active_attention, time_budget, risk_review)
        shopping_trip_plan = self._shopping_trip_plan(shopping_priority, pantry_readiness, max_minutes)
        sensory_stop_signals = self._sensory_stop_signals(cooking_method, risk_review, sensory_cues)
        plating_timing_plan = self._plating_timing_plan(serving_sequence, serving_window, plating_suggestion)
        leftover_risk_flags = self._leftover_risk_flags(leftover_guidance, risk_review, available_ingredients)
        voice_recovery_prompts = self._voice_recovery_prompts(interruption_recovery, emergency_fallback, quality_gate)
        prep_risk_order = self._prep_risk_order(prep_order, safety_alerts, allergen_cross_contact_plan)
        appliance_load_plan = self._appliance_load_plan(cookware_plan, cooking_method, servings)
        taste_calibration = self._taste_calibration(flavor_profile, salt_acid_balance, seasoning_strategy)
        serving_role_assignments = self._serving_role_assignments(servings, cook_mode, table_setup)
        confidence_recheck = self._confidence_recheck(confidence, quality_gate, stop_or_continue)
        cleanup_timeline = self._cleanup_timeline(cleanup_plan, cleanup_effort, timing_buffer_plan)
        next_cook_memory_patch = self._next_cook_memory_patch(next_session_seed, feedback_metrics, source_gaps)
        timing_pressure_flags = self._timing_pressure_flags(time_budget, active_attention, timing_buffer_plan)
        substitution_confidence = self._substitution_confidence(substitutions, dietary_conflicts, shopping_list)
        nutrition_balance_check = self._nutrition_balance_check(nutrition_focus, ingredient_roles)
        heat_zone_plan = self._heat_zone_plan(cooking_method, heat_level, cookware_plan)
        source_review_queue = self._source_review_queue(source_trace, source_gaps, confidence)
        interruption_safety_check = self._interruption_safety_check(interruption_recovery, risk_review, heat_level)
        voice_handoff_brief = self._voice_handoff_brief(voice_summary_card, voice_recovery_prompts, suggested_commands)
        serving_risk_window = self._serving_risk_window(serving_window, risk_review, leftover_label_details)
        batch_hold_strategy = self._batch_hold_strategy(batch_plan, holding_plan, appliance_load_plan)
        flavor_memory_delta = self._flavor_memory_delta(flavor_profile, taste_calibration, feedback_metrics)
        tool_cleanup_order = self._tool_cleanup_order(cookware_plan, cleanup_timeline, equipment_safety_check)
        ingredient_cut_size_plan = self._ingredient_cut_size_plan(cooking_method, available_ingredients, time_budget)
        doneness_escalation_path = self._doneness_escalation_path(doneness_verification, sensory_stop_signals, heat_recovery_plan)
        voice_timer_brief = self._voice_timer_brief(timer_schedule, step_timer_minutes, timing_pressure_flags)
        save_candidate = self._save_candidate(
            title=title,
            goal=goal,
            available_ingredients=available_ingredients,
            suggested_plan=suggested_plan,
            source_trace=source_trace,
            suitability=suitability,
            cautions=cautions,
            pantry_readiness=pantry_readiness,
            substitutions=substitutions,
            prep_checklist=prep_checklist,
            safety_alerts=safety_alerts,
            cleanup_plan=cleanup_plan,
            cooking_method=cooking_method,
            flavor_profile=flavor_profile,
            time_budget=time_budget,
            leftover_guidance=leftover_guidance,
            plating_suggestion=plating_suggestion,
            confidence=confidence,
            allergen_flags=allergen_flags,
            nutrition_focus=nutrition_focus,
            batch_plan=batch_plan,
            heat_level=heat_level,
            doneness_cues=doneness_cues,
            rescue_tips=rescue_tips,
            mise_en_place=mise_en_place,
            difficulty=difficulty,
            active_attention=active_attention,
            parallel_tasks=parallel_tasks,
            sensory_cues=sensory_cues,
            cookware_plan=cookware_plan,
            cost_estimate=cost_estimate,
            seasonality_hint=seasonality_hint,
            generated_note_title=generated_note_title,
            learning_prompts=learning_prompts,
            branch_suggestions=branch_suggestions,
            source_gaps=source_gaps,
            personalization_hints=personalization_hints,
            risk_review=risk_review,
            stop_or_continue=stop_or_continue,
            step_history=step_history,
            progress_percent=progress_percent,
            timer_schedule=timer_schedule,
            voice_checkpoint=voice_checkpoint,
            session_tags=session_tags,
            obsidian_links=obsidian_links,
            next_session_seed=next_session_seed,
            hydration_plan=hydration_plan,
            holding_plan=holding_plan,
            reheating_plan=reheating_plan,
            storage_label=storage_label,
            shopping_priority=shopping_priority,
            cleanup_effort=cleanup_effort,
            serving_window=serving_window,
            ingredient_roles=ingredient_roles,
            texture_targets=texture_targets,
            flavor_adjustment_ladder=flavor_adjustment_ladder,
            waste_reduction_plan=waste_reduction_plan,
            plating_variations=plating_variations,
            confidence_drivers=confidence_drivers,
            interruption_recovery=interruption_recovery,
            quality_gate=quality_gate,
            constraint_summary=constraint_summary,
            assumption_log=assumption_log,
            missing_info_questions=missing_info_questions,
            adaptation_notes=adaptation_notes,
            rehearse_script=rehearse_script,
            final_checklist=final_checklist,
            aroma_notes=aroma_notes,
            table_setup=table_setup,
            pairing_suggestions=pairing_suggestions,
            portioning_plan=portioning_plan,
            feedback_metrics=feedback_metrics,
            success_criteria=success_criteria,
            provenance_summary=provenance_summary,
            preheat_plan=preheat_plan,
            seasoning_strategy=seasoning_strategy,
            allergen_safe_serving=allergen_safe_serving,
            kid_friendly_adjustment=kid_friendly_adjustment,
            make_ahead_window=make_ahead_window,
            emergency_fallback=emergency_fallback,
            voice_command_map=voice_command_map,
            equipment_safety_check=equipment_safety_check,
            timing_buffer_plan=timing_buffer_plan,
            serving_temperature=serving_temperature,
            garnish_plan=garnish_plan,
            salt_acid_balance=salt_acid_balance,
            leftover_label_details=leftover_label_details,
            cleanup_reset_cue=cleanup_reset_cue,
            portion_scaling_notes=portion_scaling_notes,
            prep_order=prep_order,
            heat_recovery_plan=heat_recovery_plan,
            doneness_verification=doneness_verification,
            serving_sequence=serving_sequence,
            voice_summary_card=voice_summary_card,
            post_cook_review_prompt=post_cook_review_prompt,
            allergen_cross_contact_plan=allergen_cross_contact_plan,
            cook_mode=cook_mode,
            shopping_trip_plan=shopping_trip_plan,
            sensory_stop_signals=sensory_stop_signals,
            plating_timing_plan=plating_timing_plan,
            leftover_risk_flags=leftover_risk_flags,
            voice_recovery_prompts=voice_recovery_prompts,
            prep_risk_order=prep_risk_order,
            appliance_load_plan=appliance_load_plan,
            taste_calibration=taste_calibration,
            serving_role_assignments=serving_role_assignments,
            confidence_recheck=confidence_recheck,
            cleanup_timeline=cleanup_timeline,
            next_cook_memory_patch=next_cook_memory_patch,
            timing_pressure_flags=timing_pressure_flags,
            substitution_confidence=substitution_confidence,
            nutrition_balance_check=nutrition_balance_check,
            heat_zone_plan=heat_zone_plan,
            source_review_queue=source_review_queue,
            interruption_safety_check=interruption_safety_check,
            voice_handoff_brief=voice_handoff_brief,
            serving_risk_window=serving_risk_window,
            batch_hold_strategy=batch_hold_strategy,
            flavor_memory_delta=flavor_memory_delta,
            tool_cleanup_order=tool_cleanup_order,
            ingredient_cut_size_plan=ingredient_cut_size_plan,
            doneness_escalation_path=doneness_escalation_path,
            voice_timer_brief=voice_timer_brief,
        )

        speech = self._voice_text(title, next_action, step_state["is_complete"], cautions)
        voice_res = tts_service.synthesize_speech(speech)

        return {
            "title": title,
            "matched_records": [self._match_payload(match) for match in top_matches],
            "suggested_plan": suggested_plan,
            "next_action": next_action,
            "current_step": step_state["current_step"],
            "total_steps": step_state["total_steps"],
            "is_complete": step_state["is_complete"],
            "estimated_total_minutes": estimated_total_minutes,
            "step_timer_minutes": step_timer_minutes,
            "checkpoints": checkpoints,
            "suitability_score": suitability["score"],
            "suitability_notes": suitability["notes"],
            "pantry_readiness": pantry_readiness,
            "substitutions": substitutions,
            "prep_checklist": prep_checklist,
            "safety_alerts": safety_alerts,
            "serving_adjustments": serving_adjustments,
            "cleanup_plan": cleanup_plan,
            "cooking_method": cooking_method,
            "flavor_profile": flavor_profile,
            "time_budget": time_budget,
            "leftover_guidance": leftover_guidance,
            "plating_suggestion": plating_suggestion,
            "confidence": confidence,
            "suggested_commands": suggested_commands,
            "allergen_flags": allergen_flags,
            "nutrition_focus": nutrition_focus,
            "batch_plan": batch_plan,
            "heat_level": heat_level,
            "doneness_cues": doneness_cues,
            "rescue_tips": rescue_tips,
            "mise_en_place": mise_en_place,
            "difficulty": difficulty,
            "active_attention": active_attention,
            "parallel_tasks": parallel_tasks,
            "sensory_cues": sensory_cues,
            "cookware_plan": cookware_plan,
            "cost_estimate": cost_estimate,
            "seasonality_hint": seasonality_hint,
            "generated_note_title": generated_note_title,
            "learning_prompts": learning_prompts,
            "branch_suggestions": branch_suggestions,
            "source_gaps": source_gaps,
            "personalization_hints": personalization_hints,
            "risk_review": risk_review,
            "stop_or_continue": stop_or_continue,
            "step_history": step_history,
            "progress_percent": progress_percent,
            "timer_schedule": timer_schedule,
            "voice_checkpoint": voice_checkpoint,
            "session_tags": session_tags,
            "obsidian_links": obsidian_links,
            "next_session_seed": next_session_seed,
            "hydration_plan": hydration_plan,
            "holding_plan": holding_plan,
            "reheating_plan": reheating_plan,
            "storage_label": storage_label,
            "shopping_priority": shopping_priority,
            "cleanup_effort": cleanup_effort,
            "serving_window": serving_window,
            "ingredient_roles": ingredient_roles,
            "texture_targets": texture_targets,
            "flavor_adjustment_ladder": flavor_adjustment_ladder,
            "waste_reduction_plan": waste_reduction_plan,
            "plating_variations": plating_variations,
            "confidence_drivers": confidence_drivers,
            "interruption_recovery": interruption_recovery,
            "quality_gate": quality_gate,
            "constraint_summary": constraint_summary,
            "assumption_log": assumption_log,
            "missing_info_questions": missing_info_questions,
            "adaptation_notes": adaptation_notes,
            "rehearse_script": rehearse_script,
            "final_checklist": final_checklist,
            "aroma_notes": aroma_notes,
            "table_setup": table_setup,
            "pairing_suggestions": pairing_suggestions,
            "portioning_plan": portioning_plan,
            "feedback_metrics": feedback_metrics,
            "success_criteria": success_criteria,
            "provenance_summary": provenance_summary,
            "preheat_plan": preheat_plan,
            "seasoning_strategy": seasoning_strategy,
            "allergen_safe_serving": allergen_safe_serving,
            "kid_friendly_adjustment": kid_friendly_adjustment,
            "make_ahead_window": make_ahead_window,
            "emergency_fallback": emergency_fallback,
            "voice_command_map": voice_command_map,
            "equipment_safety_check": equipment_safety_check,
            "timing_buffer_plan": timing_buffer_plan,
            "serving_temperature": serving_temperature,
            "garnish_plan": garnish_plan,
            "salt_acid_balance": salt_acid_balance,
            "leftover_label_details": leftover_label_details,
            "cleanup_reset_cue": cleanup_reset_cue,
            "portion_scaling_notes": portion_scaling_notes,
            "prep_order": prep_order,
            "heat_recovery_plan": heat_recovery_plan,
            "doneness_verification": doneness_verification,
            "serving_sequence": serving_sequence,
            "voice_summary_card": voice_summary_card,
            "post_cook_review_prompt": post_cook_review_prompt,
            "allergen_cross_contact_plan": allergen_cross_contact_plan,
            "cook_mode": cook_mode,
            "shopping_trip_plan": shopping_trip_plan,
            "sensory_stop_signals": sensory_stop_signals,
            "plating_timing_plan": plating_timing_plan,
            "leftover_risk_flags": leftover_risk_flags,
            "voice_recovery_prompts": voice_recovery_prompts,
            "prep_risk_order": prep_risk_order,
            "appliance_load_plan": appliance_load_plan,
            "taste_calibration": taste_calibration,
            "serving_role_assignments": serving_role_assignments,
            "confidence_recheck": confidence_recheck,
            "cleanup_timeline": cleanup_timeline,
            "next_cook_memory_patch": next_cook_memory_patch,
            "timing_pressure_flags": timing_pressure_flags,
            "substitution_confidence": substitution_confidence,
            "nutrition_balance_check": nutrition_balance_check,
            "heat_zone_plan": heat_zone_plan,
            "source_review_queue": source_review_queue,
            "interruption_safety_check": interruption_safety_check,
            "voice_handoff_brief": voice_handoff_brief,
            "serving_risk_window": serving_risk_window,
            "batch_hold_strategy": batch_hold_strategy,
            "flavor_memory_delta": flavor_memory_delta,
            "tool_cleanup_order": tool_cleanup_order,
            "ingredient_cut_size_plan": ingredient_cut_size_plan,
            "doneness_escalation_path": doneness_escalation_path,
            "voice_timer_brief": voice_timer_brief,
            "equipment_gaps": equipment_gaps,
            "dietary_conflicts": dietary_conflicts,
            "source_trace": source_trace,
            "save_candidate": save_candidate,
            "shopping_list": shopping_list,
            "ingredient_gaps": gaps,
            "cautions": cautions,
            "voice_feedback": voice_res["voice_script"],
        }

    def _rank_records(
        self,
        records: list[ContentRecord],
        available_ingredients: list[str],
        avoid_ingredients: list[str],
    ) -> list[dict[str, Any]]:
        ranked = []
        for record in records:
            searchable = self._record_text(record)
            matched = [item for item in available_ingredients if item in searchable]
            avoided = [item for item in avoid_ingredients if item in searchable]
            score = (len(matched) * 3) - (len(avoided) * 5)
            if score > 0 or not available_ingredients:
                ranked.append({
                    "record": record,
                    "score": score,
                    "matched_ingredients": matched,
                    "avoided_ingredients": avoided,
                })

        return sorted(ranked, key=lambda item: item["score"], reverse=True)

    def _build_plan(
        self,
        goal: str,
        available_ingredients: list[str],
        avoid_ingredients: list[str],
        dietary_preferences: list[str],
        equipment: list[str],
        servings: int | None,
        max_minutes: int | None,
        matched_records: list[dict[str, Any]],
        voice_input: str | None,
    ) -> list[str]:
        plan = []
        context = voice_input or goal.replace("_", " ")
        dish_name = self._recipe_name(available_ingredients, matched_records, context)
        method = self._cooking_method(matched_records, goal, voice_input)
        primary = ", ".join(available_ingredients[:4]) if available_ingredients else "your chosen ingredients"
        servings_text = f" for {servings} servings" if servings else ""
        time_text = f" in about {max_minutes} minutes" if max_minutes else ""
        plan.append(f"Recipe: make {dish_name}{servings_text}{time_text}.")

        if available_ingredients:
            plan.append(f"Prep the ingredients: wash, trim, and cut {primary} into even pieces.")
            plan.append(f"Cook the base: {self._recipe_method_step(method, available_ingredients)}")
            plan.append(f"Season and balance: add salt, acid, heat, or fat in small rounds, tasting between changes.")
        else:
            plan.append("Start by choosing 2-3 available base ingredients before committing to a recipe.")

        if matched_records:
            titles = ", ".join(match["record"].title for match in matched_records)
            plan.append(f"Use saved culinary notes as inspiration: {titles}.")
            plan.append("Keep source trace attached if you save this cooking session.")
        else:
            plan.append("No saved culinary note strongly matches yet, so keep this as a flexible improvisation.")

        avoided_hits = sorted({
            ingredient
            for match in matched_records
            for ingredient in match["avoided_ingredients"]
        })
        if avoided_hits:
            plan.append(f"Remove or substitute avoided ingredients before cooking: {', '.join(avoided_hits)}.")
        elif avoid_ingredients:
            plan.append(f"Check labels and sauces for avoided ingredients: {', '.join(avoid_ingredients)}.")

        if dietary_preferences:
            plan.append(f"Keep these preferences visible while adjusting the dish: {', '.join(dietary_preferences)}.")
        if equipment:
            plan.append(f"Prefer equipment already ready in the kitchen: {', '.join(equipment)}.")
        if servings:
            plan.append(f"Scale the dish for {servings} servings before seasoning heavily.")
        if max_minutes:
            plan.append(f"Choose a method that can finish within {max_minutes} minutes.")

        plan.append("Before serving, taste once for salt, acid, heat, and texture, then make one final adjustment.")
        return plan

    def _recipe_name(
        self,
        available_ingredients: list[str],
        matched_records: list[dict[str, Any]],
        context: str,
    ) -> str:
        if matched_records:
            return matched_records[0]["record"].title
        if len(available_ingredients) >= 2:
            return f"{available_ingredients[0].title()} {available_ingredients[1].title()} Skillet"
        if available_ingredients:
            return f"Simple {available_ingredients[0].title()} Plate"
        return context.title()

    def _recipe_method_step(self, method: str, available_ingredients: list[str]) -> str:
        base = ", ".join(available_ingredients[:3]) if available_ingredients else "the base ingredients"
        if method == "simmer":
            return f"simmer {base} with enough water or stock to soften everything without scorching."
        if method == "bake":
            return f"spread {base} on the tray and bake until tender, browned, or fragrant."
        if method == "blend":
            return f"blend {base} until the texture is smooth enough, then adjust thickness."
        if method == "pan_cook":
            return f"saute {base} in a hot pan, stirring until tender and lightly colored."
        return f"cook {base} with the simplest available method until tender and hot through."

    def _ingredient_gaps(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        if not matches:
            return ["saved_recipe_match"]
        if available_ingredients and not matches[0]["matched_ingredients"]:
            return ["strong_ingredient_overlap"]
        return []

    def _shopping_list(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        if not matches:
            return []

        searchable = self._record_text(matches[0]["record"])
        candidate_items = [
            ingredient for ingredient in self.COMMON_INGREDIENTS
            if ingredient in searchable and ingredient not in available_ingredients
        ]
        return candidate_items[:5]

    def _equipment_gaps(
        self,
        equipment: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        if not matches:
            return []

        searchable = self._record_text(matches[0]["record"])
        owned = set(equipment)
        gaps = []
        for cue, required in self.EQUIPMENT_HINTS.items():
            if cue in searchable and required not in owned and required not in gaps:
                gaps.append(required)
        return gaps[:3]

    def _dietary_conflicts(
        self,
        dietary_preferences: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        if not matches:
            return []

        searchable = self._record_text(matches[0]["record"])
        conflicts = []
        for preference in dietary_preferences:
            for ingredient in self.DIETARY_CONFLICTS.get(preference, []):
                if ingredient in searchable:
                    conflicts.append(f"{preference} conflict: {ingredient}")
        return conflicts

    def _suitability(
        self,
        matches: list[dict[str, Any]],
        shopping_list: list[str],
        equipment_gaps: list[str],
        dietary_conflicts: list[str],
    ) -> dict[str, Any]:
        if not matches:
            return {
                "score": 35,
                "notes": ["No saved culinary source matched strongly."],
            }

        score = 70 + min(matches[0]["score"] * 5, 20)
        score -= len(shopping_list) * 3
        score -= len(equipment_gaps) * 8
        score -= len(dietary_conflicts) * 15
        score = max(0, min(score, 100))

        notes = [f"Matched {len(matches[0]['matched_ingredients'])} available ingredients."]
        if shopping_list:
            notes.append(f"{len(shopping_list)} optional missing ingredients identified.")
        if equipment_gaps:
            notes.append(f"Missing likely equipment: {', '.join(equipment_gaps)}.")
        if dietary_conflicts:
            notes.append(f"Dietary conflicts need review: {', '.join(dietary_conflicts)}.")
        return {"score": score, "notes": notes}

    def _cautions(
        self,
        avoid_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        cautions = []
        for match in matches:
            if match["avoided_ingredients"]:
                avoided = ", ".join(match["avoided_ingredients"])
                cautions.append(f"{match['record'].title} mentions avoided ingredients: {avoided}.")
        if avoid_ingredients and not cautions:
            cautions.append(f"Keep avoiding: {', '.join(avoid_ingredients)}.")
        return cautions

    def _add_fit_adjustments(
        self,
        plan: list[str],
        equipment_gaps: list[str],
        dietary_conflicts: list[str],
        substitutions: list[dict[str, Any]],
        prep_checklist: list[str],
        safety_alerts: list[str],
        serving_adjustments: list[str],
        cleanup_plan: list[str],
        cooking_method: str,
        time_budget: dict[str, Any],
        leftover_guidance: list[str],
        plating_suggestion: str | None,
        heat_level: str,
        doneness_cues: list[str],
        rescue_tips: list[str],
        mise_en_place: dict[str, list[str]],
        difficulty: dict[str, Any],
        active_attention: dict[str, Any],
        parallel_tasks: list[str],
        sensory_cues: list[str],
        cookware_plan: dict[str, Any],
    ) -> list[str]:
        adjusted = list(plan)
        insert_at = min(3, len(adjusted))
        if equipment_gaps:
            adjusted.insert(insert_at, f"Adapt the method because this equipment may be missing: {', '.join(equipment_gaps)}.")
            insert_at += 1
        if dietary_conflicts:
            adjusted.insert(insert_at, f"Resolve dietary conflicts before cooking: {', '.join(dietary_conflicts)}.")
            insert_at += 1
        if substitutions:
            substitution_text = "; ".join(
                f"{item['ingredient']} -> {', '.join(item['options'])}" for item in substitutions[:3]
            )
            adjusted.insert(insert_at, f"Choose substitutions before heat goes on: {substitution_text}.")
            insert_at += 1
        if prep_checklist:
            adjusted.insert(insert_at, f"Prep before cooking: {'; '.join(prep_checklist[:3])}.")
            insert_at += 1
        if serving_adjustments:
            adjusted.insert(insert_at, f"Serving scale check: {' '.join(serving_adjustments)}")
            insert_at += 1
        if safety_alerts:
            adjusted.insert(insert_at, f"Safety check: {safety_alerts[0]}")
            insert_at += 1
        if time_budget["status"] == "tight":
            adjusted.insert(insert_at, f"Time budget is tight: {time_budget['guidance']}")
            insert_at += 1
        if cooking_method != "flexible":
            adjusted.insert(insert_at, f"Use the main method: {cooking_method.replace('_', ' ')}.")
            insert_at += 1
        if heat_level != "flexible":
            adjusted.insert(insert_at, f"Set heat level: {heat_level}.")
            insert_at += 1
        if mise_en_place["prep_first"]:
            adjusted.insert(insert_at, f"Mise en place first: {', '.join(mise_en_place['prep_first'][:4])}.")
            insert_at += 1
        if cookware_plan["primary"]:
            adjusted.insert(insert_at, f"Cookware setup: use {cookware_plan['primary']}.")
            insert_at += 1
        if active_attention["level"] == "high":
            adjusted.insert(insert_at, f"Stay close to the cooktop: {active_attention['reason']}")
        if cleanup_plan:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Stage cleanup while cooking: {'; '.join(cleanup_plan[:3])}.")
        if parallel_tasks:
            adjusted.insert(max(len(adjusted) - 1, 0), f"While it cooks: {'; '.join(parallel_tasks[:3])}.")
        if leftover_guidance:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Plan leftovers: {' '.join(leftover_guidance[:2])}")
        if plating_suggestion:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Plate it: {plating_suggestion}")
        if sensory_cues:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Sensory cues: {' '.join(sensory_cues[:2])}")
        if doneness_cues:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Doneness cues: {' '.join(doneness_cues[:2])}")
        if rescue_tips:
            adjusted.insert(max(len(adjusted) - 1, 0), f"Rescue plan: {rescue_tips[0]}")
        if difficulty["level"] == "easy":
            adjusted.insert(max(len(adjusted) - 1, 0), "Keep this simple: avoid adding extra components after the plan is set.")
        return adjusted

    def _pantry_readiness(
        self,
        available_ingredients: list[str],
        shopping_list: list[str],
        equipment_gaps: list[str],
        dietary_conflicts: list[str],
    ) -> dict[str, Any]:
        blockers = []
        if not available_ingredients:
            blockers.append("available_ingredients_unknown")
        blockers.extend(f"missing_equipment:{item}" for item in equipment_gaps)
        blockers.extend(f"dietary_conflict:{item}" for item in dietary_conflicts)

        optional_missing_count = len(shopping_list)
        if blockers:
            status = "needs_adjustment"
        elif optional_missing_count:
            status = "mostly_ready"
        else:
            status = "ready"

        return {
            "status": status,
            "available_count": len(available_ingredients),
            "optional_missing_count": optional_missing_count,
            "blockers": blockers,
        }

    def _substitutions(
        self,
        avoid_ingredients: list[str],
        dietary_conflicts: list[str],
        shopping_list: list[str],
    ) -> list[dict[str, Any]]:
        needed = list(avoid_ingredients)
        for conflict in dietary_conflicts:
            if ": " in conflict:
                needed.append(conflict.split(": ", 1)[1])
        needed.extend(shopping_list[:3])

        substitutions = []
        for ingredient in needed:
            if ingredient in self.SUBSTITUTIONS and ingredient not in [item["ingredient"] for item in substitutions]:
                substitutions.append({
                    "ingredient": ingredient,
                    "options": self.SUBSTITUTIONS[ingredient],
                })
        return substitutions

    def _prep_checklist(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        ingredients = list(available_ingredients)
        if matches:
            ingredients.extend(matches[0]["matched_ingredients"])

        checklist = []
        for ingredient in ingredients:
            hint = self.PREP_HINTS.get(ingredient)
            if hint and hint not in checklist:
                checklist.append(hint)
        return checklist[:6]

    def _safety_alerts(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"

        alerts = []
        for ingredient, alert in self.SAFETY_CUES.items():
            if ingredient in searchable and alert not in alerts:
                alerts.append(alert)
        return alerts

    def _serving_adjustments(self, servings: int | None) -> list[str]:
        if not servings:
            return []
        if servings <= 1:
            return ["Cook a small batch and season lightly until the final taste."]
        if servings >= 6:
            return ["Use a larger pot or pan and add seasoning in stages for an even batch."]
        return [f"Portion ingredients for {servings} servings before cooking starts."]

    def _cleanup_plan(
        self,
        matches: list[dict[str, Any]],
        equipment_gaps: list[str],
    ) -> list[str]:
        cleanup = ["Clear one landing zone for hot cookware."]
        if matches:
            searchable = self._record_text(matches[0]["record"])
            if "pan" in searchable or "saute" in searchable or "fried" in searchable:
                cleanup.append("Wipe oil splatter after the pan cools.")
            if "bake" in searchable or "baked" in searchable:
                cleanup.append("Line or soak the baking tray after use.")
            if "blend" in searchable or "smoothie" in searchable:
                cleanup.append("Rinse the blender jar immediately.")
        if equipment_gaps:
            cleanup.append("Put substitute tools back once the method is adapted.")
        cleanup.append("Label leftovers with date and dish name.")
        return cleanup[:4]

    def _cooking_method(
        self,
        matches: list[dict[str, Any]],
        goal: str,
        voice_input: str | None,
    ) -> str:
        searchable = f"{goal} {voice_input or ''}".lower()
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"
        for cue, method in self.METHOD_CUES.items():
            if cue in searchable:
                return method
        return "flexible"

    def _flavor_profile(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"

        profile = []
        for ingredient, flavor in self.FLAVOR_CUES.items():
            if ingredient in searchable and flavor not in profile:
                profile.append(flavor)
        return profile[:5]

    def _time_budget(
        self,
        max_minutes: int | None,
        plan: list[str],
        cooking_method: str,
    ) -> dict[str, Any]:
        baseline = {
            "bake": 30,
            "blend": 10,
            "flexible": max(15, len(plan) * 4),
            "pan_cook": 20,
            "simmer": 25,
        }.get(cooking_method, 20)
        if max_minutes is None:
            return {
                "status": "unbounded",
                "target_minutes": baseline,
                "guidance": "No hard time limit was set.",
            }
        if max_minutes < baseline:
            return {
                "status": "tight",
                "target_minutes": max_minutes,
                "guidance": "Use smaller cuts, fewer add-ins, and skip nonessential garnish.",
            }
        return {
            "status": "comfortable",
            "target_minutes": max_minutes,
            "guidance": "There is enough time for the selected method.",
        }

    def _leftover_guidance(
        self,
        servings: int | None,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[str]:
        guidance = []
        if servings and servings >= 4:
            guidance.append("Set aside leftovers before the serving dish gets mixed at the table.")
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"
        if "rice" in searchable:
            guidance.append("Cool rice leftovers quickly in a shallow container.")
        if "soup" in searchable or "beans" in searchable or "lentils" in searchable:
            guidance.append("Refrigerate in portions so reheating is easy.")
        return guidance[:3]

    def _plating_suggestion(
        self,
        cooking_method: str,
        flavor_profile: list[str],
    ) -> str | None:
        if cooking_method == "blend":
            return "Serve in a clear cup or bowl and finish with a contrasting topping."
        if cooking_method == "bake":
            return "Let it cool briefly, then serve on a dry plate to keep texture crisp."
        if cooking_method == "simmer":
            return "Serve in a warm bowl and add a bright finish at the end."
        if cooking_method == "pan_cook":
            return "Plate immediately and keep any crisp edges facing up."
        if "acidic" in flavor_profile:
            return "Finish with a small fresh element to balance the acidity."
        return None

    def _confidence_band(
        self,
        suitability: dict[str, Any],
        pantry_readiness: dict[str, Any],
        source_trace: list[dict[str, Any]],
    ) -> dict[str, Any]:
        score = suitability["score"]
        if pantry_readiness["status"] == "needs_adjustment":
            score -= 10
        if source_trace:
            score += 5
        score = max(0, min(score, 100))
        if score >= 80:
            band = "high"
        elif score >= 55:
            band = "medium"
        else:
            band = "low"
        return {
            "band": band,
            "score": score,
            "reason": "Based on saved-source fit, pantry readiness, and missing-item friction.",
        }

    def _suggested_commands(self, step_state: dict[str, Any] | None) -> list[str]:
        if not step_state:
            return ["next", "repeat", "back", "stop"]
        if step_state["is_complete"]:
            return ["save session", "start new cook"]
        commands = ["next", "repeat", "back", "stop"]
        if step_state["current_step"] == 1:
            commands.remove("back")
        return commands

    def _allergen_flags(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"

        flags = []
        for ingredient, allergen in self.ALLERGEN_CUES.items():
            if ingredient in searchable and allergen not in [flag["allergen"] for flag in flags]:
                flags.append({
                    "allergen": allergen,
                    "ingredient": ingredient,
                    "note": "Review if serving someone with this allergy or sensitivity.",
                })
        return flags

    def _nutrition_focus(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"

        groups = []
        for ingredient, group in self.NUTRITION_CUES.items():
            if ingredient in searchable and group not in groups:
                groups.append(group)

        notes = []
        if "protein" not in groups and "plant_protein" not in groups:
            notes.append("Protein may be light; add beans, lentils, egg, chicken, or another protein if needed.")
        if "vegetable" not in groups and "fruit" not in groups:
            notes.append("Fresh produce may be light; add a vegetable, fruit, or herb if available.")
        if "starch" not in groups:
            notes.append("Add rice, potato, bread, or another starch if this needs to be more filling.")

        return {
            "groups": groups,
            "notes": notes,
        }

    def _batch_plan(
        self,
        servings: int | None,
        max_minutes: int | None,
        cooking_method: str,
    ) -> dict[str, Any]:
        if servings and servings >= 6:
            mode = "large_batch"
            guidance = "Cook in a wide vessel or split into batches so texture stays controlled."
        elif max_minutes and max_minutes <= 15:
            mode = "quick_batch"
            guidance = "Keep the batch small and avoid slow components."
        elif cooking_method in {"simmer", "bake"}:
            mode = "make_ahead_friendly"
            guidance = "This can tolerate a little holding time after cooking."
        else:
            mode = "single_service"
            guidance = "Best served soon after cooking."
        return {
            "mode": mode,
            "guidance": guidance,
        }

    def _heat_level(
        self,
        cooking_method: str,
        time_budget: dict[str, Any],
    ) -> str:
        if cooking_method == "bake":
            return "steady oven heat"
        if cooking_method == "blend":
            return "no heat"
        if cooking_method == "pan_cook":
            return "medium-high then medium"
        if cooking_method == "simmer":
            return "medium until bubbling, then low"
        if time_budget["status"] == "tight":
            return "focused medium-high"
        return "flexible"

    def _doneness_cues(
        self,
        cooking_method: str,
        available_ingredients: list[str],
    ) -> list[str]:
        cues = list(self.DONENESS_CUES.get(cooking_method, self.DONENESS_CUES["flexible"]))
        if "chicken" in available_ingredients:
            cues.insert(0, "Chicken is fully cooked with no pink center.")
        if "egg" in available_ingredients:
            cues.insert(0, "Eggs are set to the intended texture.")
        return cues[:4]

    def _rescue_tips(
        self,
        cooking_method: str,
        flavor_profile: list[str],
        time_budget: dict[str, Any],
        equipment_gaps: list[str],
    ) -> list[str]:
        tips = []
        if time_budget["status"] == "tight":
            tips.append("If timing slips, reduce the ingredient size or serve as a simpler version.")
        if equipment_gaps:
            tips.append(f"If missing equipment blocks the method, switch to available tools before heating: {', '.join(equipment_gaps)}.")
        if "acidic" in flavor_profile:
            tips.append("If it tastes sharp, add a little fat, sweetness, or starch.")
        if "sweet" in flavor_profile:
            tips.append("If it tastes too sweet, add salt, acid, or a savory element.")
        if cooking_method == "pan_cook":
            tips.append("If the pan gets too dry, lower heat and add a splash of water or oil.")
        if cooking_method == "simmer":
            tips.append("If it gets too thick, loosen gradually with hot water or stock.")
        return tips[:4]

    def _mise_en_place(
        self,
        available_ingredients: list[str],
        prep_checklist: list[str],
        equipment: list[str],
    ) -> dict[str, list[str]]:
        prep_first = []
        for ingredient in available_ingredients:
            if ingredient not in prep_first:
                prep_first.append(ingredient)
        tools_ready = list(equipment)
        if prep_checklist and "knife" not in tools_ready:
            tools_ready.append("knife")
        if prep_checklist and "cutting board" not in tools_ready:
            tools_ready.append("cutting board")
        hold_back = [item for item in available_ingredients if item in {"lemon", "salt", "pepper"}]
        return {
            "prep_first": prep_first[:6],
            "tools_ready": tools_ready[:6],
            "hold_back": hold_back[:4],
        }

    def _difficulty(
        self,
        cooking_method: str,
        time_budget: dict[str, Any],
        equipment_gaps: list[str],
        dietary_conflicts: list[str],
    ) -> dict[str, Any]:
        score = 1
        reasons = []
        if cooking_method in {"bake", "simmer"}:
            score += 1
            reasons.append(f"{cooking_method} needs timing control")
        if time_budget["status"] == "tight":
            score += 1
            reasons.append("tight time budget")
        if equipment_gaps:
            score += 1
            reasons.append("missing equipment")
        if dietary_conflicts:
            score += 1
            reasons.append("dietary conflict")
        level = "easy" if score <= 2 else "medium" if score <= 4 else "hard"
        return {
            "level": level,
            "score": score,
            "reasons": reasons,
        }

    def _active_attention(
        self,
        cooking_method: str,
        difficulty: dict[str, Any],
    ) -> dict[str, Any]:
        if cooking_method == "pan_cook":
            return {
                "level": "high",
                "reason": "pan cooking changes quickly and needs frequent stirring or turning.",
            }
        if difficulty["level"] == "hard":
            return {
                "level": "high",
                "reason": "several constraints need active monitoring.",
            }
        if cooking_method in {"bake", "simmer"}:
            return {
                "level": "medium",
                "reason": "check progress at intervals instead of constantly stirring.",
            }
        return {
            "level": "low",
            "reason": "few active cooking risks are detected.",
        }

    def _parallel_tasks(
        self,
        cooking_method: str,
        prep_checklist: list[str],
        cleanup_plan: list[str],
        time_budget: dict[str, Any],
    ) -> list[str]:
        tasks = []
        if time_budget["status"] != "tight" and prep_checklist:
            tasks.append("finish small prep tasks")
        if cooking_method in {"bake", "simmer"}:
            tasks.append("set serving bowls or storage containers")
        if cleanup_plan:
            tasks.append("clear used prep tools")
        return tasks[:4]

    def _sensory_cues(
        self,
        cooking_method: str,
        flavor_profile: list[str],
    ) -> list[str]:
        cues = []
        if cooking_method == "bake":
            cues.append("smells warm and lightly toasted")
        elif cooking_method == "pan_cook":
            cues.append("sizzling is steady, not smoky")
        elif cooking_method == "simmer":
            cues.append("bubbles are gentle and regular")
        elif cooking_method == "blend":
            cues.append("sound becomes smoother and less choppy")
        if "savory" in flavor_profile:
            cues.append("aroma turns rounded and cooked, not raw")
        if "acidic" in flavor_profile:
            cues.append("sharpness smells fresh, not harsh")
        return cues[:4]

    def _cookware_plan(
        self,
        cooking_method: str,
        equipment: list[str],
        equipment_gaps: list[str],
    ) -> dict[str, Any]:
        default_primary = {
            "bake": "oven tray",
            "blend": "blender jar",
            "pan_cook": "pan",
            "simmer": "pot",
        }.get(cooking_method)
        primary = default_primary
        if default_primary and default_primary in equipment:
            primary = default_primary
        elif cooking_method == "bake" and "oven" in equipment:
            primary = "oven tray"
        elif equipment:
            primary = equipment[0]
        alternatives = []
        if equipment_gaps:
            alternatives.append("adapt method to available tools")
        if cooking_method == "pan_cook":
            alternatives.append("wide pot")
        if cooking_method == "simmer":
            alternatives.append("deep pan")
        return {
            "primary": primary,
            "alternatives": alternatives[:3],
            "missing": equipment_gaps,
        }

    def _cost_estimate(
        self,
        available_ingredients: list[str],
        shopping_list: list[str],
    ) -> dict[str, Any]:
        scored_items = available_ingredients + shopping_list
        score = sum(self.COST_CUES.get(item, 2) for item in scored_items)
        if score <= 5:
            band = "low"
        elif score <= 10:
            band = "medium"
        else:
            band = "high"
        return {
            "band": band,
            "score": score,
            "drivers": [item for item in scored_items if self.COST_CUES.get(item, 2) >= 3],
        }

    def _seasonality_hint(
        self,
        available_ingredients: list[str],
        matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        searchable = " ".join(available_ingredients)
        if matches:
            searchable = f"{searchable} {self._record_text(matches[0]['record'])}"
        seasons = []
        for ingredient, season in self.SEASONAL_CUES.items():
            if ingredient in searchable and season not in seasons:
                seasons.append(season)
        return {
            "seasons": seasons,
            "note": "Seasonality is a cooking cue, not a freshness guarantee." if seasons else "No strong seasonality cue detected.",
        }

    def _generated_note_title(
        self,
        goal: str,
        available_ingredients: list[str],
        cooking_method: str,
    ) -> str:
        if available_ingredients:
            ingredient_text = " ".join(item.title() for item in available_ingredients[:3])
        else:
            ingredient_text = goal.replace("_", " ").title()
        method_text = cooking_method.replace("_", " ").title()
        return f"{ingredient_text} {method_text} Cook Session"

    def _learning_prompts(
        self,
        cooking_method: str,
        flavor_profile: list[str],
        confidence: dict[str, Any],
    ) -> list[str]:
        prompts = [
            "What adjustment improved the dish most?",
            "What should be repeated next time?",
        ]
        if cooking_method != "flexible":
            prompts.append(f"Did the {cooking_method.replace('_', ' ')} method fit the ingredients?")
        if flavor_profile:
            prompts.append(f"Was the {flavor_profile[0]} profile balanced?")
        if confidence["band"] == "low":
            prompts.append("What missing source or ingredient would raise confidence?")
        return prompts[:5]

    def _branch_suggestions(
        self,
        cooking_method: str,
        dietary_preferences: list[str],
        flavor_profile: list[str],
    ) -> list[dict[str, str]]:
        branches = []
        if cooking_method == "pan_cook":
            branches.append({"title": "Sauce version", "reason": "Pan dishes can branch into a saucier variation quickly."})
        if cooking_method == "simmer":
            branches.append({"title": "Soup or stew version", "reason": "Simmered dishes often scale into a deeper batch."})
        if "vegan" in dietary_preferences:
            branches.append({"title": "Fully vegan variant", "reason": "Keep substitutions and protein choices explicit."})
        if "acidic" in flavor_profile:
            branches.append({"title": "Softer flavor variant", "reason": "Acidic dishes may benefit from creamy or starchy balance."})
        if not branches:
            branches.append({"title": "Fast weekday version", "reason": "Keep the successful base and reduce steps."})
        return branches[:4]

    def _source_gaps(
        self,
        matches: list[dict[str, Any]],
        include_saved_sources: bool,
        ingredient_gaps: list[str],
    ) -> list[str]:
        gaps = list(ingredient_gaps)
        if not include_saved_sources:
            gaps.append("saved_sources_skipped")
        if not matches:
            gaps.append("no_culinary_source_trace")
        elif matches[0]["score"] <= 0:
            gaps.append("weak_saved_source_match")
        return gaps

    def _personalization_hints(
        self,
        voice_input: str | None,
        dietary_preferences: list[str],
        avoid_ingredients: list[str],
    ) -> list[str]:
        hints = []
        text = (voice_input or "").lower()
        if "quick" in text or "fast" in text:
            hints.append("User prefers speed for this session.")
        if "snack" in text:
            hints.append("User framed this as a snack.")
        if dietary_preferences:
            hints.append(f"Keep dietary preferences active: {', '.join(dietary_preferences)}.")
        if avoid_ingredients:
            hints.append(f"Avoidance list should persist: {', '.join(avoid_ingredients)}.")
        return hints[:4]

    def _risk_review(
        self,
        safety_alerts: list[str],
        allergen_flags: list[dict[str, str]],
        dietary_conflicts: list[str],
    ) -> dict[str, Any]:
        issues = []
        issues.extend(safety_alerts)
        issues.extend(f"Allergen flag: {flag['allergen']} from {flag['ingredient']}." for flag in allergen_flags)
        issues.extend(dietary_conflicts)
        if safety_alerts or dietary_conflicts:
            level = "high"
        elif allergen_flags:
            level = "medium"
        else:
            level = "low"
        return {
            "level": level,
            "issues": issues[:6],
            "requires_review": level in {"medium", "high"},
        }

    def _stop_or_continue(
        self,
        confidence: dict[str, Any],
        pantry_readiness: dict[str, Any],
        risk_review: dict[str, Any],
        source_gaps: list[str],
    ) -> dict[str, Any]:
        if risk_review["level"] == "high":
            decision = "review_before_cooking"
            reason = "Safety, dietary, or allergen issues need attention before proceeding."
        elif risk_review["level"] == "medium":
            decision = "continue_with_caution"
            reason = "Review allergen or sensitivity flags before serving."
        elif pantry_readiness["status"] == "needs_adjustment":
            decision = "adjust_then_continue"
            reason = "Pantry or equipment blockers remain."
        elif confidence["band"] == "low" or source_gaps:
            decision = "continue_with_caution"
            reason = "The plan can proceed, but confidence or source coverage is limited."
        else:
            decision = "ready_to_cook"
            reason = "Plan is sufficiently supported for a cooking session."
        return {
            "decision": decision,
            "reason": reason,
        }

    def _step_history(
        self,
        plan: list[str],
        step_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        current_step = step_state["current_step"]
        history = []
        for index, step in enumerate(plan, 1):
            if step_state["is_complete"]:
                status = "complete"
            elif index < current_step:
                status = "complete"
            elif index == current_step:
                status = "active"
            else:
                status = "pending"
            history.append({
                "step": index,
                "status": status,
                "text": step,
            })
        return history

    def _progress_percent(self, step_state: dict[str, Any]) -> int:
        total_steps = step_state["total_steps"]
        if total_steps == 0:
            return 100
        if step_state["is_complete"]:
            return 100
        completed = max(step_state["current_step"] - 1, 0)
        return int((completed / total_steps) * 100)

    def _timer_schedule(
        self,
        plan: list[str],
        estimated_total_minutes: int | None,
    ) -> list[dict[str, Any]]:
        if not estimated_total_minutes or not plan:
            return []
        per_step = max(1, estimated_total_minutes // len(plan))
        schedule = []
        elapsed = 0
        for index, step in enumerate(plan, 1):
            minutes = self._step_timer_minutes(step, estimated_total_minutes) or per_step
            elapsed += minutes
            schedule.append({
                "step": index,
                "minutes": minutes,
                "cumulative_minutes": elapsed,
            })
        return schedule

    def _voice_checkpoint(
        self,
        next_action: str,
        checkpoints: list[str],
        step_timer_minutes: int | None,
    ) -> str:
        timer_text = f" Set a {step_timer_minutes} minute timer." if step_timer_minutes else ""
        checkpoint_text = f" Check: {checkpoints[0]}" if checkpoints else ""
        return f"{next_action}{timer_text}{checkpoint_text}"

    def _session_tags(
        self,
        cooking_method: str,
        dietary_preferences: list[str],
        risk_review: dict[str, Any],
        source_gaps: list[str],
    ) -> list[str]:
        tags = ["cook_pilot", f"method_{cooking_method}", f"risk_{risk_review['level']}"]
        tags.extend(f"diet_{preference}" for preference in dietary_preferences)
        if source_gaps:
            tags.append("needs_source_review")
        return tags[:8]

    def _obsidian_links(
        self,
        source_trace: list[dict[str, Any]],
        branch_suggestions: list[dict[str, str]],
    ) -> list[str]:
        links = [f"[[{source['title']}]]" for source in source_trace]
        links.extend(f"[[Cook Pilot/{branch['title']}]]" for branch in branch_suggestions[:2])
        return links[:6]

    def _next_session_seed(
        self,
        generated_note_title: str,
        branch_suggestions: list[dict[str, str]],
        learning_prompts: list[str],
        stop_or_continue: dict[str, str],
    ) -> dict[str, Any]:
        return {
            "from_note": generated_note_title,
            "suggested_goal": branch_suggestions[0]["title"] if branch_suggestions else "Repeat and refine",
            "review_prompt": learning_prompts[0] if learning_prompts else "What should change next time?",
            "last_decision": stop_or_continue["decision"],
        }

    def _hydration_plan(
        self,
        cooking_method: str,
        heat_level: str,
        max_minutes: int | None,
    ) -> list[str]:
        plan = []
        if cooking_method in {"simmer", "pan_cook"}:
            plan.append("Keep a small cup of water or stock nearby for texture control.")
        if "medium-high" in heat_level:
            plan.append("Take a sip of water before high-attention cooking starts.")
        if max_minutes and max_minutes >= 30:
            plan.append("Set a water break at the midpoint.")
        return plan[:3]

    def _holding_plan(
        self,
        cooking_method: str,
        risk_review: dict[str, Any],
        serving_adjustments: list[str],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            return {
                "mode": "serve_promptly",
                "guidance": "Serve or cool promptly because safety-sensitive ingredients are involved.",
            }
        if cooking_method in {"simmer", "bake"}:
            return {
                "mode": "short_hold_ok",
                "guidance": "Hold briefly covered and recheck texture before serving.",
            }
        if serving_adjustments:
            return {
                "mode": "portion_first",
                "guidance": "Portion before holding so seasoning and texture stay even.",
            }
        return {
            "mode": "serve_when_ready",
            "guidance": "Best quality is right after the final adjustment.",
        }

    def _reheating_plan(
        self,
        cooking_method: str,
        leftover_guidance: list[str],
    ) -> list[str]:
        if not leftover_guidance:
            return []
        if cooking_method == "simmer":
            return ["Reheat gently with a splash of water or stock.", "Stir and check seasoning after reheating."]
        if cooking_method == "pan_cook":
            return ["Reheat in a pan over medium heat.", "Add a small splash of water if it dries out."]
        if cooking_method == "bake":
            return ["Reheat uncovered briefly to restore texture."]
        return ["Reheat only until hot, then reassess texture."]

    def _storage_label(
        self,
        generated_note_title: str,
        risk_review: dict[str, Any],
        leftover_guidance: list[str],
    ) -> dict[str, str]:
        urgency = "prompt_cool" if risk_review["level"] == "high" else "normal"
        return {
            "label": generated_note_title.replace(" Cook Session", ""),
            "cooling_priority": urgency if leftover_guidance else "not_needed",
            "note": "Label with dish name and date if storing leftovers.",
        }

    def _shopping_priority(
        self,
        shopping_list: list[str],
        substitutions: list[dict[str, Any]],
        risk_review: dict[str, Any],
    ) -> list[dict[str, str]]:
        priorities = []
        for item in shopping_list[:5]:
            priorities.append({"item": item, "priority": "optional", "reason": "Missing from matched source."})
        for substitution in substitutions[:3]:
            priorities.append({
                "item": substitution["ingredient"],
                "priority": "review",
                "reason": "Substitution or avoidance affects the plan.",
            })
        if risk_review["level"] != "low":
            priorities.append({"item": "safety check", "priority": "high", "reason": "Risk review requires attention."})
        return priorities[:6]

    def _cleanup_effort(
        self,
        cleanup_plan: list[str],
        cookware_plan: dict[str, Any],
        cooking_method: str,
    ) -> dict[str, Any]:
        score = len(cleanup_plan)
        if cookware_plan["primary"]:
            score += 1
        if cooking_method in {"bake", "pan_cook"}:
            score += 1
        level = "low" if score <= 3 else "medium" if score <= 5 else "high"
        return {
            "level": level,
            "score": score,
            "first_action": cleanup_plan[0] if cleanup_plan else "Clear the workspace.",
        }

    def _serving_window(
        self,
        cooking_method: str,
        risk_review: dict[str, Any],
        time_budget: dict[str, Any],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            return {
                "window": "serve_or_store_within_30_minutes",
                "reason": "Risk-sensitive ingredients should not linger.",
            }
        if cooking_method == "pan_cook":
            return {
                "window": "serve_immediately",
                "reason": "Pan-cooked texture is best right away.",
            }
        if time_budget["status"] == "tight":
            return {
                "window": "serve_after_final_check",
                "reason": "The plan is optimized for speed.",
            }
        return {
            "window": "serve_within_15_minutes",
            "reason": "Quality is best soon after finishing.",
        }

    def _ingredient_roles(
        self,
        available_ingredients: list[str],
        shopping_list: list[str],
        flavor_profile: list[str],
    ) -> list[dict[str, str]]:
        roles = []
        for ingredient in available_ingredients:
            if ingredient in {"beans", "chicken", "egg", "lentils"}:
                role = "protein"
            elif ingredient in {"bread", "potato", "rice"}:
                role = "base"
            elif ingredient in {"garlic", "ginger", "lemon", "onion", "salt", "turmeric"}:
                role = "seasoning"
            elif ingredient in {"apple", "carrot", "mushroom", "tomato", "zucchini"}:
                role = "produce"
            else:
                role = "support"
            roles.append({"ingredient": ingredient, "role": role, "source": "available"})
        for ingredient in shopping_list[:3]:
            roles.append({"ingredient": ingredient, "role": "missing_support", "source": "shopping_list"})
        if not roles and flavor_profile:
            roles.append({"ingredient": flavor_profile[0], "role": "flavor_direction", "source": "inferred"})
        return roles[:8]

    def _texture_targets(
        self,
        cooking_method: str,
        available_ingredients: list[str],
    ) -> list[str]:
        targets = []
        if cooking_method == "simmer":
            targets.append("brothy or saucy enough to spoon easily")
        elif cooking_method == "pan_cook":
            targets.append("hot through with intentional browning")
        elif cooking_method == "bake":
            targets.append("set structure with light edge color")
        elif cooking_method == "blend":
            targets.append("smooth and pourable")
        else:
            targets.append("cohesive enough to serve cleanly")
        if "rice" in available_ingredients:
            targets.append("rice grains tender, not mushy")
        if "beans" in available_ingredients or "lentils" in available_ingredients:
            targets.append("legumes tender but not broken down unless desired")
        return targets[:4]

    def _flavor_adjustment_ladder(
        self,
        flavor_profile: list[str],
        avoid_ingredients: list[str],
    ) -> list[str]:
        ladder = ["Taste before changing anything."]
        if "acidic" not in flavor_profile and "lemon" not in avoid_ingredients:
            ladder.append("Add a small acidic lift if the dish tastes flat.")
        if "savory" not in flavor_profile:
            ladder.append("Add a savory base note before adding more salt.")
        if "sweet" in flavor_profile:
            ladder.append("Balance sweetness with salt, acid, or warmth.")
        ladder.append("Adjust one variable at a time, then taste again.")
        return ladder[:5]

    def _waste_reduction_plan(
        self,
        available_ingredients: list[str],
        shopping_list: list[str],
        cleanup_plan: list[str],
    ) -> list[str]:
        plan = []
        if shopping_list:
            plan.append("Use available ingredients before buying optional items.")
        if "lemon" in available_ingredients:
            plan.append("Use zest before juicing if the peel is clean.")
        if any(item in available_ingredients for item in ["carrot", "onion", "zucchini"]):
            plan.append("Save clean vegetable trimmings for stock if practical.")
        if cleanup_plan:
            plan.append("Store leftovers before washing final cookware.")
        return plan[:4]

    def _plating_variations(
        self,
        cooking_method: str,
        servings: int | None,
        plating_suggestion: str | None,
    ) -> list[str]:
        variations = []
        if plating_suggestion:
            variations.append(plating_suggestion)
        if servings and servings > 1:
            variations.append("Serve family-style with garnish or finishing salt on the side.")
        if cooking_method == "simmer":
            variations.append("Use deep bowls and leave a clean rim.")
        elif cooking_method == "pan_cook":
            variations.append("Plate browned pieces on top so texture stays visible.")
        return variations[:4]

    def _confidence_drivers(
        self,
        confidence: dict[str, Any],
        suitability: dict[str, Any],
        source_trace: list[dict[str, Any]],
        source_gaps: list[str],
    ) -> dict[str, Any]:
        positives = [f"Suitability score {suitability['score']}."]
        if source_trace:
            positives.append("Saved culinary source is attached.")
        negatives = list(source_gaps)
        if confidence["band"] == "low":
            negatives.append("low_confidence_band")
        return {
            "band": confidence["band"],
            "positive": positives,
            "negative": negatives,
        }

    def _interruption_recovery(
        self,
        cooking_method: str,
        step_state: dict[str, Any],
        risk_review: dict[str, Any],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            action = "Pause only after securing safety-sensitive ingredients."
        elif cooking_method in {"simmer", "bake"}:
            action = "Lower heat or set a timer before stepping away."
        elif cooking_method == "pan_cook":
            action = "Turn heat down or off before stepping away from the pan."
        else:
            action = "Stop at the current step and resume from the active instruction."
        return {
            "resume_step": str(step_state["current_step"]),
            "action": action,
        }

    def _quality_gate(
        self,
        stop_or_continue: dict[str, str],
        risk_review: dict[str, Any],
        pantry_readiness: dict[str, Any],
        confidence: dict[str, Any],
    ) -> dict[str, Any]:
        blockers = []
        if stop_or_continue["decision"] == "review_before_cooking":
            blockers.append("risk_review_required")
        if pantry_readiness["status"] == "needs_adjustment":
            blockers.append("pantry_adjustment_required")
        if confidence["band"] == "low":
            blockers.append("low_confidence")
        status = "blocked" if blockers else "pass_with_review" if risk_review["requires_review"] else "pass"
        return {
            "status": status,
            "blockers": blockers,
            "review_required": risk_review["requires_review"],
        }

    def _constraint_summary(
        self,
        max_minutes: int | None,
        servings: int | None,
        dietary_preferences: list[str],
        avoid_ingredients: list[str],
        equipment_gaps: list[str],
    ) -> dict[str, Any]:
        return {
            "time": f"{max_minutes} minutes" if max_minutes else "not specified",
            "servings": str(servings) if servings else "not specified",
            "dietary_preferences": dietary_preferences,
            "avoid_ingredients": avoid_ingredients,
            "equipment_gaps": equipment_gaps,
        }

    def _assumption_log(
        self,
        include_saved_sources: bool,
        source_trace: list[dict[str, Any]],
        max_minutes: int | None,
        servings: int | None,
    ) -> list[str]:
        assumptions = []
        if include_saved_sources and not source_trace:
            assumptions.append("No saved culinary source was found, so improvisation is required.")
        if not include_saved_sources:
            assumptions.append("Saved sources were intentionally skipped.")
        if not max_minutes:
            assumptions.append("Timing estimate is inferred from plan length and method.")
        if not servings:
            assumptions.append("Serving count was not specified.")
        return assumptions

    def _missing_info_questions(
        self,
        available_ingredients: list[str],
        equipment: list[str],
        servings: int | None,
        dietary_preferences: list[str],
        source_gaps: list[str],
    ) -> list[str]:
        questions = []
        if not available_ingredients:
            questions.append("Which ingredients are definitely available?")
        if not equipment:
            questions.append("Which cookware is ready to use?")
        if not servings:
            questions.append("How many servings should this make?")
        if not dietary_preferences:
            questions.append("Any dietary constraints for the people eating?")
        if source_gaps:
            questions.append("Should Cook Pilot search saved culinary notes next time?")
        return questions[:5]

    def _adaptation_notes(
        self,
        substitutions: list[dict[str, Any]],
        equipment_gaps: list[str],
        time_budget: dict[str, Any],
        risk_review: dict[str, Any],
    ) -> list[str]:
        notes = []
        if substitutions:
            notes.append("Confirm substitutions before heat starts.")
        if equipment_gaps:
            notes.append("Adapt the method to available equipment.")
        if time_budget["status"] == "tight":
            notes.append("Cut smaller and simplify optional steps.")
        if risk_review["requires_review"]:
            notes.append("Review risk flags before serving.")
        return notes

    def _rehearse_script(
        self,
        title: str,
        next_action: str,
        stop_or_continue: dict[str, str],
        voice_checkpoint: str,
    ) -> str:
        return f"{title}: {stop_or_continue['decision']}. Start with: {next_action} Voice cue: {voice_checkpoint}"

    def _final_checklist(
        self,
        quality_gate: dict[str, Any],
        doneness_cues: list[str],
        serving_window: dict[str, str],
        storage_label: dict[str, str],
    ) -> list[str]:
        checklist = [f"Quality gate: {quality_gate['status']}."]
        checklist.extend(doneness_cues[:2])
        checklist.append(f"Serving window: {serving_window['window']}.")
        if storage_label["cooling_priority"] != "not_needed":
            checklist.append(f"Storage label ready: {storage_label['label']}.")
        return checklist

    def _aroma_notes(
        self,
        cooking_method: str,
        flavor_profile: list[str],
        sensory_cues: list[str],
    ) -> list[str]:
        notes = list(sensory_cues[:2])
        if "savory" in flavor_profile:
            notes.append("savory aroma should smell rounded, not raw")
        if "warm" in flavor_profile:
            notes.append("warm spices should smell fragrant, not scorched")
        if not notes and cooking_method == "blend":
            notes.append("aroma should stay fresh and clean")
        return notes[:4]

    def _table_setup(
        self,
        servings: int | None,
        serving_window: dict[str, str],
        plating_variations: list[str],
    ) -> dict[str, Any]:
        style = "family_style" if servings and servings > 2 else "individual"
        return {
            "style": style,
            "timing": serving_window["window"],
            "setup_notes": plating_variations[:2] or ["Keep serving surface clear and ready."],
        }

    def _pairing_suggestions(
        self,
        cooking_method: str,
        flavor_profile: list[str],
        nutrition_focus: dict[str, Any],
    ) -> list[str]:
        suggestions = []
        if "starch" not in nutrition_focus["groups"] and cooking_method != "bake":
            suggestions.append("Add rice, bread, potato, or another starch if this needs to be more filling.")
        if "acidic" in flavor_profile:
            suggestions.append("Pair with something creamy, starchy, or mild.")
        if "sweet" in flavor_profile:
            suggestions.append("Pair with something salty or tangy for balance.")
        if not suggestions:
            suggestions.append("Serve with a simple fresh side.")
        return suggestions[:4]

    def _portioning_plan(
        self,
        servings: int | None,
        batch_plan: dict[str, Any],
        leftover_guidance: list[str],
    ) -> dict[str, Any]:
        count = servings or 1
        return {
            "servings": count,
            "mode": "reserve_leftovers_first" if leftover_guidance else batch_plan["mode"],
            "guidance": "Portion gently before final garnish." if count > 1 else "Serve as a single portion.",
        }

    def _feedback_metrics(
        self,
        texture_targets: list[str],
        flavor_adjustment_ladder: list[str],
        learning_prompts: list[str],
    ) -> list[dict[str, str]]:
        metrics = []
        if texture_targets:
            metrics.append({"metric": "texture", "question": texture_targets[0]})
        if flavor_adjustment_ladder:
            metrics.append({"metric": "flavor", "question": flavor_adjustment_ladder[0]})
        for prompt in learning_prompts[:2]:
            metrics.append({"metric": "learning", "question": prompt})
        return metrics[:5]

    def _success_criteria(
        self,
        doneness_cues: list[str],
        quality_gate: dict[str, Any],
        stop_or_continue: dict[str, str],
    ) -> list[str]:
        criteria = []
        criteria.extend(doneness_cues[:2])
        criteria.append(f"Quality gate is {quality_gate['status']}.")
        criteria.append(f"Decision is {stop_or_continue['decision']}.")
        return criteria[:5]

    def _provenance_summary(
        self,
        source_trace: list[dict[str, Any]],
        source_gaps: list[str],
        confidence_drivers: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source_count": len(source_trace),
            "gap_count": len(source_gaps),
            "confidence_band": confidence_drivers["band"],
            "source_titles": [source["title"] for source in source_trace],
        }

    def _preheat_plan(
        self,
        cooking_method: str,
        cookware_plan: dict[str, Any],
        time_budget: dict[str, Any],
    ) -> dict[str, str]:
        if cooking_method == "bake":
            timing = "start_now" if time_budget["status"] != "tight" else "start_immediately"
            action = "Preheat the oven before final prep and warm the tray only if the recipe benefits from crisp edges."
        elif cooking_method == "pan_cook":
            timing = "after_prep"
            action = "Heat the pan only after knife work is done so the first ingredients do not scorch."
        elif cooking_method == "simmer":
            timing = "after_base_prep"
            action = "Set the pot on low heat after the base is ready, then raise heat once liquid is added."
        elif cooking_method == "blend":
            timing = "not_needed"
            action = "No preheat needed; assemble blender parts and keep liquid nearby for texture control."
        else:
            timing = "as_needed"
            action = "Delay heat until ingredients and tools are within reach."
        return {
            "timing": timing,
            "primary_tool": cookware_plan["primary"] or "available cookware",
            "action": action,
        }

    def _seasoning_strategy(
        self,
        flavor_profile: list[str],
        avoid_ingredients: list[str],
        dietary_preferences: list[str],
    ) -> list[str]:
        strategy = ["Season in small rounds and taste between changes."]
        if "savory" in flavor_profile or "umami" in flavor_profile:
            strategy.append("Build savory depth before adding extra salt.")
        if "acidic" in flavor_profile:
            strategy.append("Hold back some acid for a final brightness check.")
        if "sweet" in flavor_profile:
            strategy.append("Balance sweetness with a pinch of salt or a mild acidic note.")
        if avoid_ingredients:
            strategy.append(f"Do not use avoided ingredients as seasoning shortcuts: {', '.join(avoid_ingredients)}.")
        if dietary_preferences:
            strategy.append(f"Check seasonings against dietary preferences: {', '.join(dietary_preferences)}.")
        return strategy

    def _allergen_safe_serving(
        self,
        allergen_flags: list[dict[str, str]],
        risk_review: dict[str, Any],
        servings: int | None,
    ) -> dict[str, Any]:
        if not allergen_flags:
            return {
                "status": "no_known_flags",
                "separate_serving_needed": False,
                "guidance": "No common allergen flags were detected from known ingredients.",
            }
        allergens = sorted({flag["allergen"] for flag in allergen_flags})
        serving_note = f"Label all {servings} servings" if servings else "Label the serving dish"
        return {
            "status": "review_required" if risk_review["requires_review"] else "flagged",
            "separate_serving_needed": True,
            "allergens": allergens,
            "guidance": f"{serving_note} and keep utensils separate for: {', '.join(allergens)}.",
        }

    def _kid_friendly_adjustment(
        self,
        flavor_profile: list[str],
        heat_level: str,
        risk_review: dict[str, Any],
    ) -> list[str]:
        adjustments = ["Keep one portion mildly seasoned until after tasting."]
        if "acidic" in flavor_profile:
            adjustments.append("Add sharp or acidic elements at the table for sensitive eaters.")
        if "umami" in flavor_profile or "savory" in flavor_profile:
            adjustments.append("Offer a plain starch or bread-like side if the flavor is intense.")
        if "high" in heat_level or risk_review["level"] == "high":
            adjustments.append("Cool and inspect a small portion before serving to children.")
        return adjustments

    def _make_ahead_window(
        self,
        cooking_method: str,
        leftover_guidance: list[str],
        serving_window: dict[str, str],
    ) -> dict[str, str]:
        if cooking_method == "simmer":
            window = "same_day_or_next_day"
            guidance = "Simmered dishes can usually rest well; reheat gently and recheck thickness."
        elif cooking_method == "bake":
            window = "same_day_best"
            guidance = "Bake close to serving if crispness matters; refresh briefly before serving."
        elif cooking_method == "pan_cook":
            window = "serve_best_fresh"
            guidance = "Prep components ahead, but cook close to serving for texture."
        else:
            window = "short_window"
            guidance = "Prep ahead only if texture will not suffer."
        if leftover_guidance:
            guidance = f"{guidance} Follow leftover rule: {leftover_guidance[0]}"
        return {
            "window": window,
            "serving_timing": serving_window["window"],
            "guidance": guidance,
        }

    def _emergency_fallback(
        self,
        available_ingredients: list[str],
        cooking_method: str,
        equipment_gaps: list[str],
        quality_gate: dict[str, Any],
    ) -> dict[str, str]:
        base = ", ".join(available_ingredients[:3]) if available_ingredients else "the safest available ingredients"
        if quality_gate["status"] == "blocked":
            action = f"Pause the plan and make a simple low-risk plate from {base}."
        elif equipment_gaps:
            action = f"Skip the missing-tool method and use {base} in the simplest available cookware."
        elif cooking_method == "pan_cook":
            action = f"Lower heat, add a splash of liquid, and turn {base} into a quick soft saute."
        elif cooking_method == "simmer":
            action = f"Add liquid and simmer {base} until tender enough to serve simply."
        elif cooking_method == "bake":
            action = f"Slice {base} smaller and use a quick pan or raw-prep version if the oven path fails."
        else:
            action = f"Simplify to {base}, season lightly, and stop before quality drops."
        return {
            "trigger": "time, tool, safety, or confidence problem",
            "action": action,
        }

    def _voice_command_map(
        self,
        suggested_commands: list[str],
        step_state: dict[str, Any],
    ) -> dict[str, str]:
        command_map = {
            "next": "advance to the next cooking step",
            "repeat": "repeat the current instruction",
            "back": "return to the previous step",
            "stop": "finish the session and switch to serving or storage",
        }
        active = {command: command_map[command] for command in suggested_commands if command in command_map}
        active["where_am_i"] = f"report current step {step_state['current_step']} of {step_state['total_steps']}"
        return active

    def _equipment_safety_check(
        self,
        cookware_plan: dict[str, Any],
        equipment_gaps: list[str],
        risk_review: dict[str, Any],
    ) -> dict[str, Any]:
        checks = ["Keep handles stable and clear one heat-safe landing zone."]
        if cookware_plan["primary"]:
            checks.append(f"Confirm the {cookware_plan['primary']} is clean, dry, and sized for the batch.")
        if equipment_gaps:
            checks.append(f"Do not improvise with unsafe substitutes for: {', '.join(equipment_gaps)}.")
        if risk_review["requires_review"]:
            checks.append("Review risk flags before switching tools or serving.")
        return {
            "status": "review_required" if equipment_gaps or risk_review["requires_review"] else "ready",
            "checks": checks,
        }

    def _timing_buffer_plan(
        self,
        time_budget: dict[str, Any],
        estimated_total_minutes: int | None,
        timer_schedule: list[dict[str, Any]],
    ) -> dict[str, Any]:
        target = estimated_total_minutes or time_budget["target_minutes"]
        if time_budget["status"] == "tight":
            buffer_minutes = 2
            guidance = "Use only essential steps and start serving setup early."
        elif target and target >= 40:
            buffer_minutes = 10
            guidance = "Reserve a longer buffer for simmering, cooling, and texture checks."
        else:
            buffer_minutes = 5
            guidance = "Keep a small buffer for tasting, plating, and cleanup."
        return {
            "buffer_minutes": buffer_minutes,
            "target_minutes": target,
            "last_timer_step": timer_schedule[-1]["step"] if timer_schedule else None,
            "guidance": guidance,
        }

    def _serving_temperature(
        self,
        cooking_method: str,
        risk_review: dict[str, Any],
        serving_window: dict[str, str],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            target = "serve_hot_or_chill_promptly"
            guidance = "Serve hot immediately, or cool quickly and refrigerate."
        elif cooking_method == "bake":
            target = "warm"
            guidance = "Let steam settle briefly so crisp or baked texture holds."
        elif cooking_method == "simmer":
            target = "hot"
            guidance = "Serve hot after a final stir and thickness check."
        else:
            target = "ready_to_eat"
            guidance = "Serve when texture and seasoning are at their best."
        return {
            "target": target,
            "window": serving_window["window"],
            "guidance": guidance,
        }

    def _garnish_plan(
        self,
        flavor_profile: list[str],
        available_ingredients: list[str],
        avoid_ingredients: list[str],
    ) -> list[str]:
        plan = []
        if "lemon" in available_ingredients and "lemon" not in avoid_ingredients:
            plan.append("Finish with a small lemon accent only after tasting.")
        if "fresh" in flavor_profile:
            plan.append("Use fresh elements at the end so they stay bright.")
        if "creamy" in flavor_profile:
            plan.append("Add creamy elements off heat to keep texture smooth.")
        if not plan:
            plan.append("Keep garnish minimal and only add it if it improves the final bite.")
        return plan

    def _salt_acid_balance(
        self,
        flavor_profile: list[str],
        seasoning_strategy: list[str],
    ) -> dict[str, Any]:
        next_move = "taste_before_adjusting"
        if "acidic" in flavor_profile:
            next_move = "check_acid_last"
        elif "sweet" in flavor_profile:
            next_move = "add_tiny_salt_if_flat"
        return {
            "next_move": next_move,
            "has_acid": "acidic" in flavor_profile,
            "has_savory_depth": "savory" in flavor_profile or "umami" in flavor_profile,
            "reminder": seasoning_strategy[0] if seasoning_strategy else "Taste before changing the dish.",
        }

    def _leftover_label_details(
        self,
        storage_label: dict[str, str],
        leftover_guidance: list[str],
        risk_review: dict[str, Any],
    ) -> dict[str, str]:
        cooling_deadline = "cool_within_2_hours" if risk_review["level"] == "high" else "cool_before_covering"
        note = leftover_guidance[0] if leftover_guidance else "Label with dish name and date."
        return {
            "label": storage_label["label"],
            "cooling_deadline": cooling_deadline,
            "note": note,
        }

    def _cleanup_reset_cue(
        self,
        cleanup_effort: dict[str, Any],
        cookware_plan: dict[str, Any],
        safety_alerts: list[str],
    ) -> dict[str, str]:
        tool = cookware_plan["primary"] or "main tool"
        if safety_alerts:
            cue = f"Sanitize surfaces after handling risk ingredients, then wash the {tool}."
        else:
            cue = f"Reset the counter and wash the {tool} once it is cool enough."
        return {
            "level": cleanup_effort["level"],
            "cue": cue,
        }

    def _portion_scaling_notes(
        self,
        servings: int | None,
        portioning_plan: dict[str, Any],
        serving_adjustments: list[str],
    ) -> dict[str, Any]:
        target_servings = servings or portioning_plan["servings"]
        notes = list(serving_adjustments)
        if not notes:
            notes.append("Keep portions flexible and season lightly until the final taste.")
        if target_servings and target_servings >= 5:
            notes.append("Scale seasoning in two passes so the batch stays balanced.")
        return {
            "servings": target_servings,
            "mode": portioning_plan["mode"],
            "notes": notes,
        }

    def _prep_order(
        self,
        mise_en_place: dict[str, list[str]],
        prep_checklist: list[str],
        cooking_method: str,
    ) -> list[str]:
        order = []
        if mise_en_place["tools_ready"]:
            order.append(f"Set tools first: {', '.join(mise_en_place['tools_ready'][:3])}.")
        if mise_en_place["prep_first"]:
            order.append(f"Prep first: {', '.join(mise_en_place['prep_first'][:4])}.")
        order.extend(prep_checklist[:2])
        if cooking_method in {"pan_cook", "bake"}:
            order.append("Start heat only after the first ingredients are ready.")
        return order or ["Choose tools, prep ingredients, then start heat."]

    def _heat_recovery_plan(
        self,
        cooking_method: str,
        heat_level: str,
        rescue_tips: list[str],
    ) -> dict[str, str]:
        if cooking_method == "pan_cook":
            action = "Drop heat, move food off the hottest spot, and add a splash of liquid if needed."
        elif cooking_method == "bake":
            action = "Lower oven heat or cover loosely if edges color before the center is ready."
        elif cooking_method == "simmer":
            action = "Lower to a gentle bubble and add liquid in small amounts if the pot tightens."
        else:
            action = "Pause, simplify, and adjust texture before continuing."
        return {
            "heat_level": heat_level,
            "action": action,
            "first_rescue_tip": rescue_tips[0] if rescue_tips else action,
        }

    def _doneness_verification(
        self,
        doneness_cues: list[str],
        risk_review: dict[str, Any],
        cooking_method: str,
    ) -> dict[str, Any]:
        checks = doneness_cues[:2] or ["Taste and confirm the texture is intentional."]
        if risk_review["level"] == "high":
            checks.append("Confirm higher-risk ingredients are fully cooked before serving.")
        return {
            "method": cooking_method,
            "requires_extra_check": risk_review["requires_review"],
            "checks": checks,
        }

    def _serving_sequence(
        self,
        serving_temperature: dict[str, str],
        plating_variations: list[str],
        table_setup: dict[str, Any],
    ) -> list[str]:
        sequence = [
            f"Set table for {table_setup['style']} service.",
            f"Serve at {serving_temperature['target']} within {serving_temperature['window']}.",
        ]
        if plating_variations:
            sequence.append(plating_variations[0])
        sequence.append("Label leftovers before the kitchen reset.")
        return sequence

    def _voice_summary_card(
        self,
        title: str,
        next_action: str,
        timing_buffer_plan: dict[str, Any],
        risk_review: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "headline": title,
            "say_now": next_action,
            "buffer": f"{timing_buffer_plan['buffer_minutes']} minute buffer",
            "risk": risk_review["level"],
        }

    def _post_cook_review_prompt(
        self,
        feedback_metrics: list[dict[str, str]],
        success_criteria: list[str],
        next_session_seed: dict[str, Any],
    ) -> dict[str, str]:
        metric_question = feedback_metrics[0]["question"] if feedback_metrics else "What should change next time?"
        success_check = success_criteria[0] if success_criteria else "Was the final dish worth repeating?"
        return {
            "question": metric_question,
            "success_check": success_check,
            "next_goal": next_session_seed["suggested_goal"],
        }

    def _allergen_cross_contact_plan(
        self,
        allergen_flags: list[dict[str, str]],
        dietary_conflicts: list[str],
    ) -> dict[str, Any]:
        allergens = sorted({flag["allergen"] for flag in allergen_flags})
        review_needed = bool(allergens or dietary_conflicts)
        actions = []
        if allergens:
            actions.append("Use clean tools and serving surfaces before handling flagged ingredients.")
            actions.append(f"Label servings that include: {', '.join(allergens)}.")
        if dietary_conflicts:
            actions.append("Confirm dietary conflicts before cooking or serving.")
        return {
            "review_needed": review_needed,
            "allergens": allergens,
            "actions": actions or ["No cross-contact controls needed beyond normal clean prep."],
        }

    def _cook_mode(
        self,
        active_attention: dict[str, Any],
        time_budget: dict[str, Any],
        risk_review: dict[str, Any],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            mode = "supervised"
        elif time_budget["status"] == "tight":
            mode = "speed_run"
        elif active_attention["level"] == "high":
            mode = "hands_on"
        else:
            mode = "steady"
        return {
            "mode": mode,
            "attention": active_attention["level"],
            "timing": time_budget["status"],
        }

    def _shopping_trip_plan(
        self,
        shopping_priority: list[dict[str, str]],
        pantry_readiness: dict[str, Any],
        max_minutes: int | None,
    ) -> dict[str, Any]:
        must_buy = [item["item"] for item in shopping_priority if item["priority"] in {"required", "review", "high"}]
        optional = [item["item"] for item in shopping_priority if item["priority"] == "optional"]
        if pantry_readiness["status"] == "ready":
            mode = "skip_shop"
        elif max_minutes and max_minutes <= 20:
            mode = "cook_now_minimize_shop"
        else:
            mode = "short_shop"
        return {
            "mode": mode,
            "must_buy": must_buy,
            "optional": optional[:3],
        }

    def _sensory_stop_signals(
        self,
        cooking_method: str,
        risk_review: dict[str, Any],
        sensory_cues: list[str],
    ) -> list[str]:
        signals = ["Stop and reassess if smell turns burnt, sour, or smoky."]
        if cooking_method == "pan_cook":
            signals.append("Pause if the pan smokes or food sticks faster than you can stir.")
        elif cooking_method == "bake":
            signals.append("Pause if edges darken before the center is close to done.")
        elif cooking_method == "simmer":
            signals.append("Pause if boiling is aggressive or the pot bottom starts catching.")
        if risk_review["requires_review"]:
            signals.append("Stop before serving until risk checks are confirmed.")
        if sensory_cues:
            signals.append(f"Expected cue to recover toward: {sensory_cues[0]}")
        return signals

    def _plating_timing_plan(
        self,
        serving_sequence: list[str],
        serving_window: dict[str, str],
        plating_suggestion: str | None,
    ) -> dict[str, str]:
        first_move = serving_sequence[0] if serving_sequence else "Set serving dishes before the final taste."
        return {
            "first_move": first_move,
            "window": serving_window["window"],
            "finish": plating_suggestion or "Plate simply after the final seasoning check.",
        }

    def _leftover_risk_flags(
        self,
        leftover_guidance: list[str],
        risk_review: dict[str, Any],
        available_ingredients: list[str],
    ) -> list[str]:
        flags = []
        if risk_review["level"] == "high":
            flags.append("High-risk leftovers need prompt cooling and clear labels.")
        if "rice" in available_ingredients:
            flags.append("Rice leftovers need shallow cooling and prompt refrigeration.")
        if leftover_guidance:
            flags.append(leftover_guidance[0])
        return flags or ["No special leftover risk flags detected."]

    def _voice_recovery_prompts(
        self,
        interruption_recovery: dict[str, str],
        emergency_fallback: dict[str, str],
        quality_gate: dict[str, Any],
    ) -> list[str]:
        prompts = [
            f"Resume at step {interruption_recovery['resume_step']}: {interruption_recovery['action']}",
            f"Fallback: {emergency_fallback['action']}",
        ]
        if quality_gate["status"] == "blocked":
            prompts.insert(0, "Pause and clear the quality gate before continuing.")
        return prompts

    def _prep_risk_order(
        self,
        prep_order: list[str],
        safety_alerts: list[str],
        allergen_cross_contact_plan: dict[str, Any],
    ) -> list[str]:
        order = []
        if safety_alerts:
            order.append("Handle safety-sensitive ingredients before ready-to-eat prep.")
        if allergen_cross_contact_plan["review_needed"]:
            order.append("Set clean tools aside for allergen-sensitive servings before prep starts.")
        order.extend(prep_order[:3])
        return order or ["Prep low-risk ingredients first, then start heat."]

    def _appliance_load_plan(
        self,
        cookware_plan: dict[str, Any],
        cooking_method: str,
        servings: int | None,
    ) -> dict[str, str]:
        primary = cookware_plan["primary"] or "available cookware"
        if servings and servings >= 5:
            load = "large_batch"
            guidance = f"Do not crowd the {primary}; cook in batches if heat drops."
        elif cooking_method == "bake":
            load = "single_layer"
            guidance = f"Spread food evenly on the {primary} for predictable browning."
        elif cooking_method == "pan_cook":
            load = "medium_load"
            guidance = f"Keep the {primary} less than two-thirds full so stirring stays easy."
        else:
            load = "normal"
            guidance = f"Use the {primary} with enough headroom for stirring and bubbling."
        return {
            "primary_tool": primary,
            "load": load,
            "guidance": guidance,
        }

    def _taste_calibration(
        self,
        flavor_profile: list[str],
        salt_acid_balance: dict[str, Any],
        seasoning_strategy: list[str],
    ) -> dict[str, Any]:
        checkpoints = ["Taste once before adding more seasoning."]
        if "acidic" in flavor_profile:
            checkpoints.append("Check acid after salt, not before.")
        if "sweet" in flavor_profile:
            checkpoints.append("Balance sweetness with salt or acid in tiny steps.")
        if "savory" in flavor_profile or "umami" in flavor_profile:
            checkpoints.append("Check depth before adding more salt.")
        return {
            "next_move": salt_acid_balance["next_move"],
            "checkpoints": checkpoints,
            "baseline": seasoning_strategy[0] if seasoning_strategy else "Taste first.",
        }

    def _serving_role_assignments(
        self,
        servings: int | None,
        cook_mode: dict[str, str],
        table_setup: dict[str, Any],
    ) -> dict[str, Any]:
        helpers_needed = bool(servings and servings >= 4) or cook_mode["mode"] == "supervised"
        roles = ["cook: stay with heat and final seasoning."]
        if helpers_needed:
            roles.append("helper: set table, label restrictions, and clear landing zone.")
        roles.append(f"service: use {table_setup['style']} plating.")
        return {
            "helpers_needed": helpers_needed,
            "roles": roles,
        }

    def _confidence_recheck(
        self,
        confidence: dict[str, Any],
        quality_gate: dict[str, Any],
        stop_or_continue: dict[str, str],
    ) -> dict[str, Any]:
        triggers = []
        if confidence["band"] != "high":
            triggers.append("Confidence is not high; verify the next step before heat.")
        if quality_gate["status"] == "blocked":
            triggers.append("Quality gate is blocked.")
        if stop_or_continue["decision"] != "continue":
            triggers.append(f"Decision is {stop_or_continue['decision']}.")
        return {
            "required": bool(triggers),
            "score": confidence["score"],
            "triggers": triggers or ["No confidence recheck needed before continuing."],
        }

    def _cleanup_timeline(
        self,
        cleanup_plan: list[str],
        cleanup_effort: dict[str, Any],
        timing_buffer_plan: dict[str, Any],
    ) -> dict[str, Any]:
        first = cleanup_effort.get("first_action", "Clear one landing zone.")
        timeline = [f"Before heat: {first}"]
        if cleanup_plan:
            timeline.append(f"During buffer: {cleanup_plan[0]}")
        timeline.append(f"After serving: use {timing_buffer_plan['buffer_minutes']} minute buffer for reset.")
        return {
            "level": cleanup_effort["level"],
            "timeline": timeline,
        }

    def _next_cook_memory_patch(
        self,
        next_session_seed: dict[str, Any],
        feedback_metrics: list[dict[str, str]],
        source_gaps: list[str],
    ) -> dict[str, Any]:
        prompts = [metric["question"] for metric in feedback_metrics[:2]]
        if source_gaps:
            prompts.append("Add or link a trusted culinary source before repeating.")
        return {
            "suggested_goal": next_session_seed["suggested_goal"],
            "remember": prompts or ["Record what worked and what should change."],
            "source_gap_count": len(source_gaps),
        }

    def _timing_pressure_flags(
        self,
        time_budget: dict[str, Any],
        active_attention: dict[str, Any],
        timing_buffer_plan: dict[str, Any],
    ) -> dict[str, Any]:
        flags = []
        if time_budget["status"] == "tight":
            flags.append("Tight time budget: skip optional steps and plate simply.")
        if active_attention["level"] == "high":
            flags.append("High attention: avoid leaving the heat unattended.")
        if timing_buffer_plan["buffer_minutes"] <= 2:
            flags.append("Small buffer: start serving setup early.")
        return {
            "level": "high" if flags else "normal",
            "flags": flags or ["Timing pressure is normal."],
        }

    def _substitution_confidence(
        self,
        substitutions: list[dict[str, Any]],
        dietary_conflicts: list[str],
        shopping_list: list[str],
    ) -> dict[str, Any]:
        if dietary_conflicts:
            level = "review_required"
        elif substitutions:
            level = "medium"
        else:
            level = "high"
        blockers = list(dietary_conflicts[:3])
        return {
            "level": level,
            "available_swaps": len(substitutions),
            "missing_items": shopping_list[:5],
            "blockers": blockers,
        }

    def _nutrition_balance_check(
        self,
        nutrition_focus: dict[str, Any],
        ingredient_roles: list[dict[str, str]],
    ) -> dict[str, Any]:
        groups = set(nutrition_focus["groups"])
        missing = []
        if not ({"protein", "plant_protein"} & groups):
            missing.append("protein")
        if "vegetable" not in groups and "fruit" not in groups:
            missing.append("produce")
        if "starch" not in groups:
            missing.append("starch")
        return {
            "status": "balanced" if not missing else "needs_balance",
            "missing": missing,
            "role_count": len(ingredient_roles),
        }

    def _heat_zone_plan(
        self,
        cooking_method: str,
        heat_level: str,
        cookware_plan: dict[str, Any],
    ) -> dict[str, str]:
        tool = cookware_plan["primary"] or "cookware"
        if cooking_method == "pan_cook":
            zones = "hot center, cooler edge"
            action = f"Use the {tool} center for browning and edges for holding."
        elif cooking_method == "bake":
            zones = "middle rack"
            action = f"Keep the {tool} centered for even heat."
        elif cooking_method == "simmer":
            zones = "gentle bubble zone"
            action = f"Keep the {tool} at a steady low bubble."
        else:
            zones = "no active heat"
            action = "Use heat only after texture and seasoning are planned."
        return {
            "heat_level": heat_level,
            "zones": zones,
            "action": action,
        }

    def _source_review_queue(
        self,
        source_trace: list[dict[str, Any]],
        source_gaps: list[str],
        confidence: dict[str, Any],
    ) -> list[dict[str, str]]:
        queue = [
            {
                "title": source["title"],
                "reason": f"matched by {source['match_reason']}",
            }
            for source in source_trace[:3]
        ]
        if source_gaps:
            queue.append({"title": "Source gap review", "reason": ", ".join(source_gaps[:3])})
        if confidence["band"] == "low":
            queue.append({"title": "Confidence review", "reason": confidence["reason"]})
        return queue

    def _interruption_safety_check(
        self,
        interruption_recovery: dict[str, str],
        risk_review: dict[str, Any],
        heat_level: str,
    ) -> dict[str, str]:
        if risk_review["requires_review"]:
            action = "Turn heat down or off and complete risk checks before stepping away."
            status = "review_required"
        elif "high" in heat_level:
            action = "Lower heat before stepping away, then resume from the recorded step."
            status = "watch_heat"
        else:
            action = interruption_recovery["action"]
            status = "ready"
        return {
            "status": status,
            "resume_step": interruption_recovery["resume_step"],
            "action": action,
        }

    def _voice_handoff_brief(
        self,
        voice_summary_card: dict[str, str],
        voice_recovery_prompts: list[str],
        suggested_commands: list[str],
    ) -> dict[str, Any]:
        commands = ", ".join(suggested_commands)
        return {
            "headline": voice_summary_card["headline"],
            "say_first": voice_summary_card["say_now"],
            "recovery": voice_recovery_prompts[0] if voice_recovery_prompts else "Ask for the current step.",
            "commands": commands,
        }

    def _serving_risk_window(
        self,
        serving_window: dict[str, str],
        risk_review: dict[str, Any],
        leftover_label_details: dict[str, str],
    ) -> dict[str, str]:
        if risk_review["level"] == "high":
            priority = "serve_or_chill_promptly"
            action = f"Use {leftover_label_details['cooling_deadline']} if food is not served in time."
        else:
            priority = "serve_when_ready"
            action = serving_window["reason"]
        return {
            "window": serving_window["window"],
            "priority": priority,
            "action": action,
        }

    def _batch_hold_strategy(
        self,
        batch_plan: dict[str, Any],
        holding_plan: dict[str, str],
        appliance_load_plan: dict[str, str],
    ) -> dict[str, str]:
        if batch_plan["mode"] == "large_batch":
            mode = "stagger_batches"
            guidance = f"Hold finished portions loosely covered; {appliance_load_plan['guidance']}"
        else:
            mode = holding_plan["mode"]
            guidance = holding_plan["guidance"]
        return {
            "mode": mode,
            "load": appliance_load_plan["load"],
            "guidance": guidance,
        }

    def _flavor_memory_delta(
        self,
        flavor_profile: list[str],
        taste_calibration: dict[str, Any],
        feedback_metrics: list[dict[str, str]],
    ) -> dict[str, Any]:
        focus = flavor_profile[:3] or ["balanced"]
        questions = [metric["question"] for metric in feedback_metrics if metric["metric"] in {"flavor", "learning"}]
        return {
            "focus": focus,
            "next_move": taste_calibration["next_move"],
            "questions": questions[:2] or ["What flavor adjustment should carry forward?"],
        }

    def _tool_cleanup_order(
        self,
        cookware_plan: dict[str, Any],
        cleanup_timeline: dict[str, Any],
        equipment_safety_check: dict[str, Any],
    ) -> list[str]:
        order = []
        if cookware_plan["primary"]:
            order.append(f"Let {cookware_plan['primary']} cool before washing.")
        order.extend(cleanup_timeline["timeline"][:2])
        if equipment_safety_check["status"] == "review_required":
            order.append("Sanitize reviewed tools and surfaces before storage.")
        return order or ["Clear tools, wipe surfaces, and reset the station."]

    def _ingredient_cut_size_plan(
        self,
        cooking_method: str,
        available_ingredients: list[str],
        time_budget: dict[str, Any],
    ) -> dict[str, Any]:
        if time_budget["status"] == "tight":
            size = "small_even_pieces"
            reason = "smaller pieces cook faster under a tight time budget."
        elif cooking_method == "simmer":
            size = "medium_even_pieces"
            reason = "even pieces simmer at the same pace."
        elif cooking_method == "bake":
            size = "thin_even_pieces"
            reason = "thin pieces bake more predictably."
        else:
            size = "bite_size"
            reason = "bite-size prep keeps texture easy to check."
        return {
            "size": size,
            "ingredients": available_ingredients[:5],
            "reason": reason,
        }

    def _doneness_escalation_path(
        self,
        doneness_verification: dict[str, Any],
        sensory_stop_signals: list[str],
        heat_recovery_plan: dict[str, str],
    ) -> list[str]:
        path = list(doneness_verification["checks"][:2])
        if sensory_stop_signals:
            path.append(sensory_stop_signals[0])
        path.append(heat_recovery_plan["action"])
        return path

    def _voice_timer_brief(
        self,
        timer_schedule: list[dict[str, Any]],
        step_timer_minutes: int | None,
        timing_pressure_flags: dict[str, Any],
    ) -> dict[str, Any]:
        next_timer = step_timer_minutes or 0
        return {
            "next_timer_minutes": next_timer,
            "total_timers": len(timer_schedule),
            "pressure": timing_pressure_flags["level"],
            "say": f"Set {next_timer} minute timer now." if next_timer else "No timer needed for the current step.",
        }

    def _match_payload(self, match: dict[str, Any]) -> dict[str, Any]:
        record = match["record"]
        match_reason = self._match_reason(match)
        return {
            "record_id": record.id,
            "title": record.title,
            "score": match["score"],
            "match_reason": match_reason,
            "matched_ingredients": match["matched_ingredients"],
            "avoided_ingredients": match["avoided_ingredients"],
            "risk_level": record.risk_level,
            "summary": record.summary,
        }

    def _source_trace(self, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        trace = []
        for match in matches:
            record = match["record"]
            trace.append({
                "record_id": record.id,
                "title": record.title,
                "source_type": record.source_type,
                "score": match["score"],
                "match_reason": self._match_reason(match),
                "matched_ingredients": match["matched_ingredients"],
            })
        return trace

    def _match_reason(self, match: dict[str, Any]) -> str:
        return "ingredient_overlap" if match["matched_ingredients"] else "saved_culinary_source"

    def _save_candidate(
        self,
        title: str,
        goal: str,
        available_ingredients: list[str],
        suggested_plan: list[str],
        source_trace: list[dict[str, Any]],
        suitability: dict[str, Any],
        cautions: list[str],
        pantry_readiness: dict[str, Any],
        substitutions: list[dict[str, Any]],
        prep_checklist: list[str],
        safety_alerts: list[str],
        cleanup_plan: list[str],
        cooking_method: str,
        flavor_profile: list[str],
        time_budget: dict[str, Any],
        leftover_guidance: list[str],
        plating_suggestion: str | None,
        confidence: dict[str, Any],
        allergen_flags: list[dict[str, str]],
        nutrition_focus: dict[str, Any],
        batch_plan: dict[str, Any],
        heat_level: str,
        doneness_cues: list[str],
        rescue_tips: list[str],
        mise_en_place: dict[str, list[str]],
        difficulty: dict[str, Any],
        active_attention: dict[str, Any],
        parallel_tasks: list[str],
        sensory_cues: list[str],
        cookware_plan: dict[str, Any],
        cost_estimate: dict[str, Any],
        seasonality_hint: dict[str, Any],
        generated_note_title: str,
        learning_prompts: list[str],
        branch_suggestions: list[dict[str, str]],
        source_gaps: list[str],
        personalization_hints: list[str],
        risk_review: dict[str, Any],
        stop_or_continue: dict[str, Any],
        step_history: list[dict[str, Any]],
        progress_percent: int,
        timer_schedule: list[dict[str, Any]],
        voice_checkpoint: str,
        session_tags: list[str],
        obsidian_links: list[str],
        next_session_seed: dict[str, Any],
        hydration_plan: list[str],
        holding_plan: dict[str, str],
        reheating_plan: list[str],
        storage_label: dict[str, str],
        shopping_priority: list[dict[str, str]],
        cleanup_effort: dict[str, Any],
        serving_window: dict[str, str],
        ingredient_roles: list[dict[str, str]],
        texture_targets: list[str],
        flavor_adjustment_ladder: list[str],
        waste_reduction_plan: list[str],
        plating_variations: list[str],
        confidence_drivers: dict[str, Any],
        interruption_recovery: dict[str, str],
        quality_gate: dict[str, Any],
        constraint_summary: dict[str, Any],
        assumption_log: list[str],
        missing_info_questions: list[str],
        adaptation_notes: list[str],
        rehearse_script: str,
        final_checklist: list[str],
        aroma_notes: list[str],
        table_setup: dict[str, Any],
        pairing_suggestions: list[str],
        portioning_plan: dict[str, Any],
        feedback_metrics: list[dict[str, str]],
        success_criteria: list[str],
        provenance_summary: dict[str, Any],
        preheat_plan: dict[str, str],
        seasoning_strategy: list[str],
        allergen_safe_serving: dict[str, Any],
        kid_friendly_adjustment: list[str],
        make_ahead_window: dict[str, str],
        emergency_fallback: dict[str, str],
        voice_command_map: dict[str, str],
        equipment_safety_check: dict[str, Any],
        timing_buffer_plan: dict[str, Any],
        serving_temperature: dict[str, str],
        garnish_plan: list[str],
        salt_acid_balance: dict[str, Any],
        leftover_label_details: dict[str, str],
        cleanup_reset_cue: dict[str, str],
        portion_scaling_notes: dict[str, Any],
        prep_order: list[str],
        heat_recovery_plan: dict[str, str],
        doneness_verification: dict[str, Any],
        serving_sequence: list[str],
        voice_summary_card: dict[str, str],
        post_cook_review_prompt: dict[str, str],
        allergen_cross_contact_plan: dict[str, Any],
        cook_mode: dict[str, str],
        shopping_trip_plan: dict[str, Any],
        sensory_stop_signals: list[str],
        plating_timing_plan: dict[str, str],
        leftover_risk_flags: list[str],
        voice_recovery_prompts: list[str],
        prep_risk_order: list[str],
        appliance_load_plan: dict[str, str],
        taste_calibration: dict[str, Any],
        serving_role_assignments: dict[str, Any],
        confidence_recheck: dict[str, Any],
        cleanup_timeline: dict[str, Any],
        next_cook_memory_patch: dict[str, Any],
        timing_pressure_flags: dict[str, Any],
        substitution_confidence: dict[str, Any],
        nutrition_balance_check: dict[str, Any],
        heat_zone_plan: dict[str, str],
        source_review_queue: list[dict[str, str]],
        interruption_safety_check: dict[str, str],
        voice_handoff_brief: dict[str, Any],
        serving_risk_window: dict[str, str],
        batch_hold_strategy: dict[str, str],
        flavor_memory_delta: dict[str, Any],
        tool_cleanup_order: list[str],
        ingredient_cut_size_plan: dict[str, Any],
        doneness_escalation_path: list[str],
        voice_timer_brief: dict[str, Any],
    ) -> dict[str, Any]:
        lines = [
            f"Goal: {goal}",
            f"Generated note title: {generated_note_title}",
            f"Available ingredients: {', '.join(available_ingredients) if available_ingredients else 'UNKNOWN'}",
            f"Suitability score: {suitability['score']}",
            f"Pantry readiness: {pantry_readiness['status']}",
            f"Cook Pilot confidence: {confidence['band']} ({confidence['score']})",
            f"Cooking method: {cooking_method}",
            f"Time budget: {time_budget['status']} / {time_budget['target_minutes']} minutes",
            f"Batch plan: {batch_plan['mode']}",
            f"Heat level: {heat_level}",
            f"Difficulty: {difficulty['level']}",
            f"Active attention: {active_attention['level']}",
            f"Cost estimate: {cost_estimate['band']}",
            f"Risk review: {risk_review['level']}",
            f"Cook decision: {stop_or_continue['decision']}",
            f"Progress: {progress_percent}%",
            f"Voice checkpoint: {voice_checkpoint}",
            f"Serving window: {serving_window['window']}",
            f"Cleanup effort: {cleanup_effort['level']}",
            f"Interruption recovery: step {interruption_recovery['resume_step']}",
            f"Quality gate: {quality_gate['status']}",
            f"Table setup: {table_setup['style']}",
            f"Provenance: {provenance_summary['source_count']} sources / {provenance_summary['gap_count']} gaps",
            f"Preheat plan: {preheat_plan['timing']} / {preheat_plan['primary_tool']}",
            f"Make-ahead window: {make_ahead_window['window']}",
            f"Timing buffer: {timing_buffer_plan['buffer_minutes']} minutes",
            f"Serving temperature: {serving_temperature['target']}",
            f"Portion scaling: {portion_scaling_notes['servings']} servings / {portion_scaling_notes['mode']}",
            f"Heat recovery: {heat_recovery_plan['heat_level']}",
            f"Cook mode: {cook_mode['mode']}",
            f"Appliance load: {appliance_load_plan['load']}",
            f"Confidence recheck: {confidence_recheck['required']}",
            f"Timing pressure: {timing_pressure_flags['level']}",
            f"Nutrition balance: {nutrition_balance_check['status']}",
            f"Serving risk window: {serving_risk_window['priority']}",
            f"Voice timer: {voice_timer_brief['next_timer_minutes']} minutes",
            "",
            "Plan:",
        ]
        lines.extend(f"{index}. {step}" for index, step in enumerate(suggested_plan, 1))
        if prep_checklist:
            lines.append("")
            lines.append("Prep checklist:")
            lines.extend(f"- {item}" for item in prep_checklist)
        if substitutions:
            lines.append("")
            lines.append("Substitutions:")
            lines.extend(f"- {item['ingredient']}: {', '.join(item['options'])}" for item in substitutions)
        if safety_alerts:
            lines.append("")
            lines.append("Safety alerts:")
            lines.extend(f"- {alert}" for alert in safety_alerts)
        if cleanup_plan:
            lines.append("")
            lines.append("Cleanup plan:")
            lines.extend(f"- {item}" for item in cleanup_plan)
        if flavor_profile:
            lines.append("")
            lines.append(f"Flavor profile: {', '.join(flavor_profile)}")
        if leftover_guidance:
            lines.append("")
            lines.append("Leftover guidance:")
            lines.extend(f"- {item}" for item in leftover_guidance)
        if plating_suggestion:
            lines.append("")
            lines.append(f"Plating: {plating_suggestion}")
        if allergen_flags:
            lines.append("")
            lines.append("Allergen flags:")
            lines.extend(f"- {flag['allergen']}: {flag['ingredient']}" for flag in allergen_flags)
        if nutrition_focus["groups"] or nutrition_focus["notes"]:
            lines.append("")
            lines.append(f"Nutrition focus: {', '.join(nutrition_focus['groups']) if nutrition_focus['groups'] else 'UNKNOWN'}")
            lines.extend(f"- {note}" for note in nutrition_focus["notes"])
        if doneness_cues:
            lines.append("")
            lines.append("Doneness cues:")
            lines.extend(f"- {cue}" for cue in doneness_cues)
        if rescue_tips:
            lines.append("")
            lines.append("Rescue tips:")
            lines.extend(f"- {tip}" for tip in rescue_tips)
        if mise_en_place["prep_first"] or mise_en_place["tools_ready"]:
            lines.append("")
            lines.append(f"Mise en place: prep {', '.join(mise_en_place['prep_first'])}; tools {', '.join(mise_en_place['tools_ready'])}")
        if cookware_plan["primary"] or cookware_plan["alternatives"]:
            lines.append("")
            lines.append(f"Cookware plan: {cookware_plan['primary'] or 'UNKNOWN'}")
        if sensory_cues:
            lines.append("")
            lines.append("Sensory cues:")
            lines.extend(f"- {cue}" for cue in sensory_cues)
        if parallel_tasks:
            lines.append("")
            lines.append("Parallel tasks:")
            lines.extend(f"- {task}" for task in parallel_tasks)
        if seasonality_hint["seasons"]:
            lines.append("")
            lines.append(f"Seasonality: {', '.join(seasonality_hint['seasons'])}")
        if learning_prompts:
            lines.append("")
            lines.append("Learning prompts:")
            lines.extend(f"- {prompt}" for prompt in learning_prompts)
        if branch_suggestions:
            lines.append("")
            lines.append("Branch suggestions:")
            lines.extend(f"- {branch['title']}: {branch['reason']}" for branch in branch_suggestions)
        if source_gaps:
            lines.append("")
            lines.append(f"Source gaps: {', '.join(source_gaps)}")
        if personalization_hints:
            lines.append("")
            lines.append("Personalization hints:")
            lines.extend(f"- {hint}" for hint in personalization_hints)
        if timer_schedule:
            lines.append("")
            lines.append("Timer schedule:")
            lines.extend(f"- Step {item['step']}: {item['minutes']} min" for item in timer_schedule[:6])
        if step_history:
            lines.append("")
            lines.append("Step history:")
            lines.extend(f"- {item['step']}: {item['status']}" for item in step_history[:8])
        if session_tags:
            lines.append("")
            lines.append(f"Session tags: {', '.join(session_tags)}")
        if obsidian_links:
            lines.append("")
            lines.append(f"Obsidian links: {', '.join(obsidian_links)}")
        lines.append("")
        lines.append(f"Next session seed: {next_session_seed['suggested_goal']}")
        if hydration_plan:
            lines.append("")
            lines.append("Hydration plan:")
            lines.extend(f"- {item}" for item in hydration_plan)
        lines.append("")
        lines.append(f"Holding plan: {holding_plan['mode']} - {holding_plan['guidance']}")
        if reheating_plan:
            lines.append("")
            lines.append("Reheating plan:")
            lines.extend(f"- {item}" for item in reheating_plan)
        lines.append("")
        lines.append(f"Storage label: {storage_label['label']} ({storage_label['cooling_priority']})")
        if shopping_priority:
            lines.append("")
            lines.append("Shopping priority:")
            lines.extend(f"- {item['priority']}: {item['item']} - {item['reason']}" for item in shopping_priority)
        if ingredient_roles:
            lines.append("")
            lines.append("Ingredient roles:")
            lines.extend(f"- {item['ingredient']}: {item['role']}" for item in ingredient_roles)
        if texture_targets:
            lines.append("")
            lines.append("Texture targets:")
            lines.extend(f"- {target}" for target in texture_targets)
        if flavor_adjustment_ladder:
            lines.append("")
            lines.append("Flavor adjustment ladder:")
            lines.extend(f"- {item}" for item in flavor_adjustment_ladder)
        if waste_reduction_plan:
            lines.append("")
            lines.append("Waste reduction:")
            lines.extend(f"- {item}" for item in waste_reduction_plan)
        if plating_variations:
            lines.append("")
            lines.append("Plating variations:")
            lines.extend(f"- {item}" for item in plating_variations)
        lines.append("")
        lines.append(f"Confidence drivers: +{len(confidence_drivers['positive'])} / -{len(confidence_drivers['negative'])}")
        lines.append("")
        lines.append(f"Constraint summary: time {constraint_summary['time']}; servings {constraint_summary['servings']}")
        if assumption_log:
            lines.append("")
            lines.append("Assumptions:")
            lines.extend(f"- {item}" for item in assumption_log)
        if missing_info_questions:
            lines.append("")
            lines.append("Missing info questions:")
            lines.extend(f"- {item}" for item in missing_info_questions)
        if adaptation_notes:
            lines.append("")
            lines.append("Adaptation notes:")
            lines.extend(f"- {item}" for item in adaptation_notes)
        lines.append("")
        lines.append(f"Rehearse script: {rehearse_script}")
        if final_checklist:
            lines.append("")
            lines.append("Final checklist:")
            lines.extend(f"- {item}" for item in final_checklist)
        if aroma_notes:
            lines.append("")
            lines.append("Aroma notes:")
            lines.extend(f"- {item}" for item in aroma_notes)
        if pairing_suggestions:
            lines.append("")
            lines.append("Pairing suggestions:")
            lines.extend(f"- {item}" for item in pairing_suggestions)
        lines.append("")
        lines.append(f"Portioning plan: {portioning_plan['servings']} servings / {portioning_plan['mode']}")
        if feedback_metrics:
            lines.append("")
            lines.append("Feedback metrics:")
            lines.extend(f"- {item['metric']}: {item['question']}" for item in feedback_metrics)
        if success_criteria:
            lines.append("")
            lines.append("Success criteria:")
            lines.extend(f"- {item}" for item in success_criteria)
        lines.append("")
        lines.append(f"Preheat action: {preheat_plan['action']}")
        if seasoning_strategy:
            lines.append("")
            lines.append("Seasoning strategy:")
            lines.extend(f"- {item}" for item in seasoning_strategy)
        lines.append("")
        lines.append(f"Allergen-safe serving: {allergen_safe_serving['status']} - {allergen_safe_serving['guidance']}")
        if kid_friendly_adjustment:
            lines.append("")
            lines.append("Kid-friendly adjustment:")
            lines.extend(f"- {item}" for item in kid_friendly_adjustment)
        lines.append("")
        lines.append(f"Make-ahead guidance: {make_ahead_window['guidance']}")
        lines.append("")
        lines.append(f"Emergency fallback: {emergency_fallback['action']}")
        if voice_command_map:
            lines.append("")
            lines.append("Voice command map:")
            lines.extend(f"- {command}: {meaning}" for command, meaning in voice_command_map.items())
        if equipment_safety_check["checks"]:
            lines.append("")
            lines.append("Equipment safety check:")
            lines.extend(f"- {item}" for item in equipment_safety_check["checks"])
        lines.append("")
        lines.append(f"Timing buffer guidance: {timing_buffer_plan['guidance']}")
        lines.append("")
        lines.append(f"Serving temperature guidance: {serving_temperature['guidance']}")
        if garnish_plan:
            lines.append("")
            lines.append("Garnish plan:")
            lines.extend(f"- {item}" for item in garnish_plan)
        lines.append("")
        lines.append(f"Salt-acid balance: {salt_acid_balance['next_move']}")
        lines.append("")
        lines.append(f"Leftover label details: {leftover_label_details['label']} / {leftover_label_details['cooling_deadline']}")
        lines.append("")
        lines.append(f"Cleanup reset cue: {cleanup_reset_cue['cue']}")
        if portion_scaling_notes["notes"]:
            lines.append("")
            lines.append("Portion scaling notes:")
            lines.extend(f"- {item}" for item in portion_scaling_notes["notes"])
        if prep_order:
            lines.append("")
            lines.append("Prep order:")
            lines.extend(f"- {item}" for item in prep_order)
        lines.append("")
        lines.append(f"Heat recovery plan: {heat_recovery_plan['action']}")
        if doneness_verification["checks"]:
            lines.append("")
            lines.append("Doneness verification:")
            lines.extend(f"- {item}" for item in doneness_verification["checks"])
        if serving_sequence:
            lines.append("")
            lines.append("Serving sequence:")
            lines.extend(f"- {item}" for item in serving_sequence)
        lines.append("")
        lines.append(f"Voice summary card: {voice_summary_card['buffer']} / risk {voice_summary_card['risk']}")
        lines.append("")
        lines.append(f"Post-cook review prompt: {post_cook_review_prompt['question']}")
        lines.append("")
        lines.append(f"Allergen cross-contact plan: {allergen_cross_contact_plan['review_needed']}")
        lines.append("")
        lines.append(f"Shopping trip plan: {shopping_trip_plan['mode']}")
        if sensory_stop_signals:
            lines.append("")
            lines.append("Sensory stop signals:")
            lines.extend(f"- {item}" for item in sensory_stop_signals)
        lines.append("")
        lines.append(f"Plating timing plan: {plating_timing_plan['window']}")
        if leftover_risk_flags:
            lines.append("")
            lines.append("Leftover risk flags:")
            lines.extend(f"- {item}" for item in leftover_risk_flags)
        if voice_recovery_prompts:
            lines.append("")
            lines.append("Voice recovery prompts:")
            lines.extend(f"- {item}" for item in voice_recovery_prompts)
        if prep_risk_order:
            lines.append("")
            lines.append("Prep risk order:")
            lines.extend(f"- {item}" for item in prep_risk_order)
        lines.append("")
        lines.append(f"Appliance load plan: {appliance_load_plan['primary_tool']} / {appliance_load_plan['load']}")
        if taste_calibration["checkpoints"]:
            lines.append("")
            lines.append("Taste calibration:")
            lines.extend(f"- {item}" for item in taste_calibration["checkpoints"])
        if serving_role_assignments["roles"]:
            lines.append("")
            lines.append("Serving role assignments:")
            lines.extend(f"- {item}" for item in serving_role_assignments["roles"])
        if confidence_recheck["triggers"]:
            lines.append("")
            lines.append("Confidence recheck:")
            lines.extend(f"- {item}" for item in confidence_recheck["triggers"])
        if cleanup_timeline["timeline"]:
            lines.append("")
            lines.append("Cleanup timeline:")
            lines.extend(f"- {item}" for item in cleanup_timeline["timeline"])
        if next_cook_memory_patch["remember"]:
            lines.append("")
            lines.append("Next cook memory patch:")
            lines.extend(f"- {item}" for item in next_cook_memory_patch["remember"])
        if timing_pressure_flags["flags"]:
            lines.append("")
            lines.append("Timing pressure flags:")
            lines.extend(f"- {item}" for item in timing_pressure_flags["flags"])
        lines.append("")
        lines.append(f"Substitution confidence: {substitution_confidence['level']}")
        lines.append("")
        lines.append(f"Nutrition balance check: {nutrition_balance_check['status']}")
        lines.append("")
        lines.append(f"Heat zone plan: {heat_zone_plan['zones']} - {heat_zone_plan['action']}")
        if source_review_queue:
            lines.append("")
            lines.append("Source review queue:")
            lines.extend(f"- {item['title']}: {item['reason']}" for item in source_review_queue)
        lines.append("")
        lines.append(f"Interruption safety check: {interruption_safety_check['status']} - {interruption_safety_check['action']}")
        lines.append("")
        lines.append(f"Voice handoff brief: {voice_handoff_brief['commands']}")
        lines.append("")
        lines.append(f"Serving risk window: {serving_risk_window['window']} / {serving_risk_window['priority']}")
        lines.append("")
        lines.append(f"Batch hold strategy: {batch_hold_strategy['mode']} - {batch_hold_strategy['guidance']}")
        if flavor_memory_delta["questions"]:
            lines.append("")
            lines.append("Flavor memory delta:")
            lines.extend(f"- {item}" for item in flavor_memory_delta["questions"])
        if tool_cleanup_order:
            lines.append("")
            lines.append("Tool cleanup order:")
            lines.extend(f"- {item}" for item in tool_cleanup_order)
        lines.append("")
        lines.append(f"Ingredient cut size plan: {ingredient_cut_size_plan['size']} - {ingredient_cut_size_plan['reason']}")
        if doneness_escalation_path:
            lines.append("")
            lines.append("Doneness escalation path:")
            lines.extend(f"- {item}" for item in doneness_escalation_path)
        lines.append("")
        lines.append(f"Voice timer brief: {voice_timer_brief['say']}")
        if source_trace:
            lines.append("")
            lines.append("Source trace:")
            lines.extend(f"- {source['title']} ({source['record_id']})" for source in source_trace)
        if cautions:
            lines.append("")
            lines.append("Cautions:")
            lines.extend(f"- {caution}" for caution in cautions)

        return {
            "title": generated_note_title,
            "content_text": "\n".join(lines),
            "source_type": "note",
            "primary_domain": "culinary",
            "domains": ["culinary"],
            "custom_tags": session_tags,
            "related_record_ids": [source["record_id"] for source in source_trace],
            "relation_type": "derived_from",
        }

    def _record_text(self, record: ContentRecord) -> str:
        parts = [
            record.title,
            record.summary or "",
            record.transcript or "",
            record.keywords_json,
            record.sub_topics_json,
            record.custom_tags_json,
            record.domain_data_json,
        ]
        return " ".join(parts).lower()

    def _title(self, goal: str, matches: list[dict[str, Any]]) -> str:
        if matches:
            return f"Cook Pilot: {matches[0]['record'].title}"
        return f"Cook Pilot: {goal.replace('_', ' ').title()}"

    def _step_state(
        self,
        plan: list[str],
        current_step: int,
        command: str | None,
    ) -> dict[str, Any]:
        total_steps = len(plan)
        if total_steps == 0:
            return {
                "current_step": 0,
                "total_steps": 0,
                "is_complete": True,
                "next_action": "Cooking session is complete.",
            }

        normalized_command = self._normalize_command(command)
        step = max(1, min(current_step or 1, total_steps))
        if normalized_command in {"next", "continue", "done"}:
            step = min(step + 1, total_steps)
        elif normalized_command in {"back", "previous"}:
            step = max(step - 1, 1)
        elif normalized_command in {"stop", "finish", "complete"}:
            return {
                "current_step": total_steps,
                "total_steps": total_steps,
                "is_complete": True,
                "next_action": "Cooking session is complete.",
            }

        is_complete = normalized_command in {"stop", "finish", "complete"} or (
            normalized_command in {"next", "continue", "done"} and step == total_steps
        )
        return {
            "current_step": step,
            "total_steps": total_steps,
            "is_complete": is_complete,
            "next_action": plan[step - 1],
        }

    def _estimated_total_minutes(
        self,
        max_minutes: int | None,
        plan: list[str],
    ) -> int | None:
        if max_minutes:
            return max(1, max_minutes)
        if not plan:
            return None
        return max(10, min(len(plan) * 5, 45))

    def _step_timer_minutes(
        self,
        next_action: str,
        estimated_total_minutes: int | None,
    ) -> int | None:
        if next_action == "Cooking session is complete.":
            return None
        action = next_action.lower()
        if "taste" in action or "confirm" in action or "check" in action:
            return 1
        if "choose" in action or "use saved" in action or "prefer equipment" in action:
            return 2
        if "finish within" in action and estimated_total_minutes:
            return max(3, estimated_total_minutes // 2)
        if estimated_total_minutes:
            return max(2, min(estimated_total_minutes // 4, 10))
        return None

    def _checkpoints(
        self,
        next_action: str,
        cautions: list[str],
        shopping_list: list[str],
        equipment_gaps: list[str],
        dietary_conflicts: list[str],
    ) -> list[str]:
        if next_action == "Cooking session is complete.":
            return ["Serve, store leftovers safely, and save any useful adjustment notes."]

        checkpoints = []
        action = next_action.lower()
        if "base ingredients" in action:
            checkpoints.append("Confirm every base ingredient is washed, trimmed, and reachable.")
        if "saved culinary notes" in action:
            checkpoints.append("Open the matched saved note before changing the direction.")
        if "substitute" in action or "avoided" in action:
            checkpoints.append("Keep avoided ingredients physically away from the prep area.")
        if "seasoning" in action or "taste" in action:
            checkpoints.append("Adjust salt, acid, heat, and texture one at a time.")
        if "prep before cooking" in action:
            checkpoints.append("Finish knife work before turning on heat.")
        if "safety check" in action:
            checkpoints.append("Handle higher-risk ingredients before moving to ready-to-eat food.")
        if "cleanup" in action:
            checkpoints.append("Clear the workspace without interrupting active cooking.")
        if shopping_list:
            checkpoints.append(f"Missing optional items: {', '.join(shopping_list[:3])}.")
        if equipment_gaps:
            checkpoints.append(f"Plan around missing equipment: {', '.join(equipment_gaps)}.")
        if dietary_conflicts:
            checkpoints.append(f"Resolve dietary conflicts: {', '.join(dietary_conflicts[:2])}.")
        if cautions:
            checkpoints.append(cautions[0])
        return checkpoints[:4]

    def _voice_text(
        self,
        title: str,
        next_action: str,
        is_complete: bool,
        cautions: list[str],
    ) -> str:
        if is_complete:
            return f"{title}. Cooking session is complete."
        caution_text = f" Caution: {cautions[0]}" if cautions else ""
        return f"{title}. Next step: {next_action}{caution_text}"

    def _normalize_command(self, command: str | None) -> str:
        text = (command or "").strip().lower()
        if not text:
            return ""
        if text in {"next", "continue", "done", "back", "previous", "stop", "finish", "complete"}:
            return text
        if "next" in text or "continue" in text or "done" in text:
            return "next"
        if "back" in text or "previous" in text:
            return "previous"
        if "stop" in text or "finish" in text or "complete" in text:
            return "stop"
        return text

    def _clean_terms(self, values: list[str] | None) -> list[str]:
        return [value.strip().lower() for value in values or [] if value and value.strip()]

    def _ingredients_from_voice(self, voice_input: str | None) -> list[str]:
        if not voice_input:
            return []
        text = voice_input.lower()
        return [ingredient for ingredient in self.COMMON_INGREDIENTS if ingredient in text]

    def _merge_unique(self, first: list[str], second: list[str]) -> list[str]:
        merged = []
        for value in first + second:
            if value not in merged:
                merged.append(value)
        return merged


cook_pilot_engine = CookPilotEngine()

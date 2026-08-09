def caps_for(user, module: str):
    prof = getattr(user, 'employee_profile', None)
    if not prof:
        return {"view": False, "edit": False}

    module = module.lower().replace(" ", "_")
    can_view = getattr(prof, f"can_view_{module}", False)
    can_edit = getattr(prof, f"can_edit_{module}", False)
    return {"view": bool(can_view or can_edit), "edit": bool(can_edit)}

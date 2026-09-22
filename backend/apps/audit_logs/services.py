from apps.audit_logs.context import get_current_ip, get_current_user


def log_action(
    action,
    entity_type,
    entity_id="",
    description="",
    previous_value=None,
    new_value=None,
    user=None,
    ip_address=None,
):
    """Central helper for recording an audit trail entry. Import lazily to
    avoid AppRegistryNotReady issues when called from module-level code."""
    from apps.audit_logs.models import AuditLog

    return AuditLog.objects.create(
        user=user or get_current_user(),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        description=description,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=ip_address or get_current_ip(),
    )

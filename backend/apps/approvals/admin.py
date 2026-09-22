from django.contrib import admin

from apps.approvals.models import ApprovalAction, ApprovalMatrixRule, ApprovalStep, ApprovalWorkflow


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ("invoice", "status", "current_step_number", "created_at")
    list_filter = ("status",)
    inlines = [ApprovalStepInline]


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ("step", "actor", "action", "created_at")
    list_filter = ("action",)


@admin.register(ApprovalMatrixRule)
class ApprovalMatrixRuleAdmin(admin.ModelAdmin):
    list_display = ("min_amount", "max_amount", "required_roles", "is_active")

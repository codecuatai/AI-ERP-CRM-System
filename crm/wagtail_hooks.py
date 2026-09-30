from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AIAnalysis, CareTask, Customer, Interaction, LeadRequest, SalesRecord


@register_snippet
class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    list_display = ["full_name", "company", "email", "ai_segment", "ai_score", "is_active"]
    list_filter = ["ai_segment", "is_active"]
    search_fields = ["full_name", "email", "company"]
    inspect_view_enabled = True


@register_snippet
class LeadRequestViewSet(SnippetViewSet):
    model = LeadRequest
    icon = "inbox"
    list_display = ["customer", "solution_interest", "status", "created_at"]
    list_filter = ["status", "solution_interest", "created_at"]
    search_fields = ["customer__full_name", "customer__company", "request_text"]
    inspect_view_enabled = True


@register_snippet
class InteractionViewSet(SnippetViewSet):
    model = Interaction
    icon = "comment"
    list_display = ["customer", "kind", "subject", "occurred_at"]
    list_filter = ["kind", "occurred_at"]
    search_fields = ["customer__full_name", "subject", "content"]
    inspect_view_enabled = True


@register_snippet
class CareTaskViewSet(SnippetViewSet):
    model = CareTask
    icon = "list-ul"
    list_display = ["title", "customer", "assignee", "due_at", "priority", "status"]
    list_filter = ["status", "priority", "kind", "due_at"]
    search_fields = ["title", "description", "customer__full_name", "customer__company"]
    inspect_view_enabled = True


@register_snippet
class AIAnalysisViewSet(SnippetViewSet):
    model = AIAnalysis
    icon = "search"
    list_display = ["customer", "segment", "score", "provider", "created_at"]
    list_filter = ["segment", "provider", "created_at"]
    search_fields = ["customer__full_name", "summary", "recommendation"]
    inspect_view_enabled = True


@register_snippet
class SalesRecordViewSet(SnippetViewSet):
    model = SalesRecord
    icon = "doc-full"
    list_display = ["reference", "customer", "amount", "closed_at", "status"]
    list_filter = ["status", "closed_at"]
    search_fields = ["reference", "customer__full_name", "customer__company"]
    inspect_view_enabled = True

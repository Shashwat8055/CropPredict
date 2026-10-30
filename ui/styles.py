"""
CropPricePredict - UI Design System & Styling
Redirects to root styles module for maximum cross-platform compatibility.
"""
from styles import (
    get_custom_css,
    render_metric_card,
    render_status_badge,
    render_role_badge
)

__all__ = [
    "get_custom_css",
    "render_metric_card",
    "render_status_badge",
    "render_role_badge"
]

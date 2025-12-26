"""
Apex SaaS Framework - Custom Implementation
Version: 0.3.24

A lightweight SaaS framework providing:
- Authentication (signup, login, token management)
- Payment integration (PayPal wrapper)
- User management
- Multi-tenancy support (optional)

This module is designed to be a drop-in solution for FastAPI applications.
"""

__version__ = "0.3.24"
__author__ = "Legal-Ops Team"

from apex.client import Client
from apex.models import Base, quick_user

__all__ = [
    "Client",
    "Base",
    "quick_user",
    "__version__"
]

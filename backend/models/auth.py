"""
User model using Apex SaaS Framework.
"""
# Import User directly from apex.models
# The apex module provides a complete User model with:
# - id (UUID), email, hashed_password
# - first_name, last_name, username
# - is_active, is_superuser
# - created_at, updated_at, last_login

from apex.models import User

__all__ = ["User"]

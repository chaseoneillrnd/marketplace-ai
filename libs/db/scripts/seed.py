"""Seed script — idempotent. Safe to run multiple times."""

from sqlalchemy import text

from skillhub_db.session import SessionLocal

STUB_USER_ID = "00000000-0000-0000-0000-000000000001"

DIVISIONS = [
    ("engineering-org", "Engineering Org", "#3B82F6"),
    ("product-org", "Product Org", "#8B5CF6"),
    ("finance-legal", "Finance & Legal", "#10B981"),
    ("people-hr", "People & HR", "#F59E0B"),
    ("operations", "Operations", "#EF4444"),
    ("executive-office", "Executive Office", "#6366F1"),
    ("sales-marketing", "Sales & Marketing", "#EC4899"),
    ("customer-success", "Customer Success", "#14B8A6"),
]

CATEGORIES = [
    ("engineering", "Engineering", 1),
    ("product", "Product", 2),
    ("data", "Data", 3),
    ("security", "Security", 4),
    ("finance", "Finance", 5),
    ("general", "General", 6),
    ("hr", "HR", 7),
    ("research", "Research", 8),
    ("operations", "Operations", 9),
]

FEATURE_FLAGS = [
    ("llm_judge_enabled", False, "Enable LLM judge for submission Gate 2"),
    ("featured_skills_v2", False, "Enable v2 featured skills layout"),
    ("gamification_enabled", False, "Enable gamification features"),
    ("mcp_install_enabled", True, "Enable MCP install method"),
]


def seed() -> None:
    """Run all seeds idempotently."""
    db = SessionLocal()
    try:
        # Seed divisions
        for slug, name, color in DIVISIONS:
            db.execute(
                text(
                    "INSERT INTO divisions (slug, name, color) "
                    "VALUES (:slug, :name, :color) "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"slug": slug, "name": name, "color": color},
            )

        # Seed categories
        for slug, name, sort_order in CATEGORIES:
            db.execute(
                text(
                    "INSERT INTO categories (slug, name, sort_order) "
                    "VALUES (:slug, :name, :sort_order) "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"slug": slug, "name": name, "sort_order": sort_order},
            )

        # Seed feature flags
        for key, enabled, description in FEATURE_FLAGS:
            db.execute(
                text(
                    "INSERT INTO feature_flags (key, enabled, description) "
                    "VALUES (:key, :enabled, :description) "
                    "ON CONFLICT (key) DO NOTHING"
                ),
                {"key": key, "enabled": enabled, "description": description},
            )

        # Seed stub user
        db.execute(
            text(
                "INSERT INTO users (id, email, username, name, division, role, "
                "is_platform_team, is_security_team) "
                "VALUES (:id, :email, :username, :name, :division, :role, "
                ":is_platform_team, :is_security_team) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": STUB_USER_ID,
                "email": "test@acme.com",
                "username": "test",
                "name": "Test User",
                "division": "engineering-org",
                "role": "Senior Engineer",
                "is_platform_team": False,
                "is_security_team": False,
            },
        )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed complete.")

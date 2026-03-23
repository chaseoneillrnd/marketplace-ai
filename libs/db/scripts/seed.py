"""Seed script — idempotent. Safe to run multiple times.

Seeds the SkillHub database with realistic data across all categories,
divisions, install methods, and sort-order variations for local development.
"""

import hashlib
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pathlib import Path

from sqlalchemy import text

from skillhub_db.session import SessionLocal

# Ensure the scripts directory is on sys.path so seed_data can be imported
# regardless of the working directory (e.g., when imported from tests).
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from seed_data import (
    ALL_SKILLS,
    CATEGORIES,
    DIVISIONS,
    FEATURE_FLAGS,
    SEED_FAVORITES,
    SEED_INSTALLS,
    SEED_REVIEWS,
    SEED_USERS,
)

# Bayesian rating constants — must match services/reviews.py
BAYESIAN_C = 5
BAYESIAN_M = Decimal("3.0")

# ---------------------------------------------------------------------------
# ANSI colors for terminal output
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


def _header(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'━' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'━' * 60}{RESET}")


def _section(title: str) -> None:
    print(f"\n{BOLD}{BLUE}▸ {title}{RESET}")


def _ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def _skip(msg: str) -> None:
    print(f"  {DIM}⊘ {msg}{RESET}")


def _warn(msg: str) -> None:
    print(f"  {YELLOW}⚠ {msg}{RESET}")


def _err(msg: str) -> None:
    print(f"  {RED}✗ {msg}{RESET}", file=sys.stderr)


def _item(msg: str) -> None:
    print(f"  {DIM}│{RESET} {msg}")


# ---------------------------------------------------------------------------
# Main seed entry point
# ---------------------------------------------------------------------------


def seed() -> None:
    """Run all seeds idempotently with progress output."""
    _header("SkillHub Database Seed")
    print(f"  {DIM}Timestamp: {datetime.now(timezone.utc).isoformat()}{RESET}")
    print(f"  {DIM}Data: {len(SEED_USERS)} users, {len(ALL_SKILLS)} skills, {len(SEED_REVIEWS)} reviews{RESET}")

    t_start = time.monotonic()
    errors: list[str] = []

    db = SessionLocal()
    try:
        n_div = _seed_divisions(db)
        n_cat = _seed_categories(db)
        n_flag = _seed_feature_flags(db)
        n_user_new, n_user_skip = _seed_users(db)
        n_skill_new, n_skill_skip, skill_errors = _seed_skills(db)
        n_rev_new, n_rev_skip, rev_errors = _seed_reviews(db)
        n_inst_new, n_inst_skip = _seed_installs(db)
        n_fav_new, n_fav_skip = _seed_favorites(db)

        errors.extend(skill_errors)
        errors.extend(rev_errors)

        # Reconcile counters from actual rows
        n_reconciled = _reconcile_counters(db)

        db.commit()
        _ok(f"{GREEN}Commit successful{RESET}")

        # ── Final summary ──
        elapsed = time.monotonic() - t_start
        _header("Seed Summary")

        rows = [
            ("Divisions", n_div, len(DIVISIONS) - n_div),
            ("Categories", n_cat, len(CATEGORIES) - n_cat),
            ("Feature Flags", n_flag, len(FEATURE_FLAGS) - n_flag),
            ("Users", n_user_new, n_user_skip),
            ("Skills", n_skill_new, n_skill_skip),
            ("Reviews", n_rev_new, n_rev_skip),
            ("Installs", n_inst_new, n_inst_skip),
            ("Favorites", n_fav_new, n_fav_skip),
        ]
        print(f"  {'Entity':<16} {'Created':>8} {'Skipped':>8}")
        print(f"  {DIM}{'─' * 34}{RESET}")
        for label, created, skipped in rows:
            c_str = f"{GREEN}{created}{RESET}" if created > 0 else f"{DIM}0{RESET}"
            s_str = f"{YELLOW}{skipped}{RESET}" if skipped > 0 else f"{DIM}0{RESET}"
            print(f"  {label:<16} {c_str:>17} {s_str:>17}")

        # ── Coverage breakdown ──
        _section("Coverage Breakdown")
        cat_counts = Counter(s["category"] for s in ALL_SKILLS)
        method_counts = Counter(s["install_method"] for s in ALL_SKILLS)
        sens_counts = Counter(s["data_sensitivity"] for s in ALL_SKILLS)
        author_counts = Counter(s["author_type"] for s in ALL_SKILLS)

        print(f"  {BOLD}Categories:{RESET}  ", end="")
        print("  ".join(f"{cat} {DIM}({n}){RESET}" for cat, n in sorted(cat_counts.items())))

        print(f"  {BOLD}Install:{RESET}     ", end="")
        print("  ".join(f"{m} {DIM}({n}){RESET}" for m, n in sorted(method_counts.items())))

        print(f"  {BOLD}Sensitivity:{RESET} ", end="")
        print("  ".join(f"{s} {DIM}({n}){RESET}" for s, n in sorted(sens_counts.items())))

        print(f"  {BOLD}Author:{RESET}      ", end="")
        print("  ".join(f"{a} {DIM}({n}){RESET}" for a, n in sorted(author_counts.items())))

        n_featured = sum(1 for s in ALL_SKILLS if s["featured"])
        n_verified = sum(1 for s in ALL_SKILLS if s["verified"])
        n_unverified = len(ALL_SKILLS) - n_verified
        print(f"  {BOLD}Featured:{RESET}    {n_featured}   {BOLD}Verified:{RESET} {n_verified}   {BOLD}Unverified:{RESET} {n_unverified}")

        # ── Errors ──
        if errors:
            _section(f"{RED}Errors ({len(errors)}){RESET}")
            for e in errors:
                _err(e)
        else:
            print(f"\n  {GREEN}No errors{RESET}")

        print(f"\n  {DIM}Completed in {elapsed:.2f}s{RESET}")
        print()

    except Exception as exc:
        db.rollback()
        _err(f"Fatal error — rolled back: {exc}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Division, category, and flag seeds
# ---------------------------------------------------------------------------


def _seed_divisions(db) -> int:  # noqa: ANN001
    _section(f"Divisions ({len(DIVISIONS)})")
    created = 0
    for slug, name, color in DIVISIONS:
        result = db.execute(
            text(
                "INSERT INTO divisions (slug, name, color) "
                "VALUES (:slug, :name, :color) "
                "ON CONFLICT (slug) DO UPDATE SET color = :color"
            ),
            {"slug": slug, "name": name, "color": color},
        )
        # rowcount=1 for both insert and update with ON CONFLICT DO UPDATE
        _item(f"{name:<22} {DIM}{color}{RESET}")
        created += 1
    _ok(f"{created} divisions upserted")
    return created


def _seed_categories(db) -> int:  # noqa: ANN001
    _section(f"Categories ({len(CATEGORIES)})")
    created = 0
    for slug, name, sort_order in CATEGORIES:
        result = db.execute(
            text(
                "INSERT INTO categories (slug, name, sort_order) "
                "VALUES (:slug, :name, :sort_order) "
                "ON CONFLICT (slug) DO NOTHING"
            ),
            {"slug": slug, "name": name, "sort_order": sort_order},
        )
        if result.rowcount > 0:
            _ok(f"{name}")
            created += 1
        else:
            _skip(f"{name} (exists)")
    return created


def _seed_feature_flags(db) -> int:  # noqa: ANN001
    _section(f"Feature Flags ({len(FEATURE_FLAGS)})")
    created = 0
    for key, enabled, description in FEATURE_FLAGS:
        result = db.execute(
            text(
                "INSERT INTO feature_flags (key, enabled, description) "
                "VALUES (:key, :enabled, :description) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {"key": key, "enabled": enabled, "description": description},
        )
        status = f"{GREEN}on{RESET}" if enabled else f"{DIM}off{RESET}"
        if result.rowcount > 0:
            _ok(f"{key} [{status}]")
            created += 1
        else:
            _skip(f"{key} [{status}] (exists)")
    return created


# ---------------------------------------------------------------------------
# User seeds
# ---------------------------------------------------------------------------


def _seed_users(db) -> tuple[int, int]:  # noqa: ANN001
    _section(f"Users ({len(SEED_USERS)})")
    created = 0
    skipped = 0
    for u in SEED_USERS:
        result = db.execute(
            text(
                "INSERT INTO users (id, email, username, name, division, role, "
                "is_platform_team, is_security_team) "
                "VALUES (:id, :email, :username, :name, :division, :role, "
                ":is_platform_team, :is_security_team) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            u,
        )
        badges = ""
        if u["is_platform_team"]:
            badges += f" {MAGENTA}[platform]{RESET}"
        if u["is_security_team"]:
            badges += f" {RED}[security]{RESET}"
        if result.rowcount > 0:
            _ok(f"{u['name']:<24} {DIM}{u['division']:<18}{RESET} {u['role']}{badges}")
            created += 1
        else:
            _skip(f"{u['name']} (exists)")
            skipped += 1
    return created, skipped


# ---------------------------------------------------------------------------
# Skill seeds
# ---------------------------------------------------------------------------


def _seed_skills(db) -> tuple[int, int, list[str]]:  # noqa: ANN001
    _section(f"Skills ({len(ALL_SKILLS)})")
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0
    errors: list[str] = []

    # Group skills by category for organized output
    by_category: dict[str, list[dict]] = {}
    for s in ALL_SKILLS:
        by_category.setdefault(s["category"], []).append(s)

    for category in sorted(by_category):
        skills = by_category[category]
        print(f"\n  {BOLD}{category.upper()}{RESET} {DIM}({len(skills)} skills){RESET}")

        for s in skills:
            # Skip if already seeded
            existing = db.execute(
                text("SELECT id FROM skills WHERE slug = :slug"),
                {"slug": s["slug"]},
            ).fetchone()
            if existing:
                _skip(f"{s['name']}")
                skipped += 1
                continue

            skill_id = str(uuid.uuid4())

            try:
                # Use days_ago / updated_days_ago for varied dates
                days_ago = s.get("days_ago", 30)
                updated_days_ago = s.get("updated_days_ago", days_ago)
                created_at = now - timedelta(days=days_ago)
                updated_at = now - timedelta(days=updated_days_ago)
                published_at = created_at

                db.execute(
                    text(
                        "INSERT INTO skills (id, slug, name, short_desc, category, author_id, "
                        "author_type, current_version, install_method, data_sensitivity, "
                        "external_calls, verified, featured, featured_order, status, "
                        "install_count, fork_count, favorite_count, view_count, review_count, "
                        "avg_rating, trending_score, published_at, created_at, updated_at) "
                        "VALUES (:id, :slug, :name, :short_desc, :category, :author_id, "
                        ":author_type, :current_version, :install_method, :data_sensitivity, "
                        ":external_calls, :verified, :featured, :featured_order, :status, "
                        ":install_count, :fork_count, :favorite_count, :view_count, "
                        ":review_count, :avg_rating, :trending_score, :published_at, "
                        ":created_at, :updated_at)"
                    ),
                    {
                        "id": skill_id,
                        "slug": s["slug"],
                        "name": s["name"],
                        "short_desc": s["short_desc"],
                        "category": s["category"],
                        "author_id": s.get("author_id", SEED_USERS[0]["id"]),
                        "author_type": s["author_type"],
                        "current_version": s["current_version"],
                        "install_method": s["install_method"],
                        "data_sensitivity": s["data_sensitivity"],
                        "external_calls": s.get("external_calls", False),
                        "verified": s["verified"],
                        "featured": s["featured"],
                        "featured_order": s.get("featured_order"),
                        "status": "published",
                        "install_count": s["install_count"],
                        "fork_count": s.get("fork_count", 0),
                        "favorite_count": s.get("favorite_count", 0),
                        "view_count": s["install_count"] * 3,
                        "review_count": s["review_count"],
                        "avg_rating": s["avg_rating"],
                        "trending_score": s["trending_score"],
                        "published_at": published_at,
                        "created_at": created_at,
                        "updated_at": updated_at,
                    },
                )

                # Seed skill version
                db.execute(
                    text(
                        "INSERT INTO skill_versions (id, skill_id, version, content, "
                        "frontmatter, changelog, content_hash, published_at) "
                        "VALUES (:id, :skill_id, :version, :content, :frontmatter, "
                        ":changelog, :content_hash, :published_at)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "skill_id": skill_id,
                        "version": s["current_version"],
                        "content": s["content"],
                        "frontmatter": "{}",
                        "changelog": "Initial release",
                        "content_hash": hashlib.sha256(s["content"].encode()).hexdigest()[:16],
                        "published_at": published_at,
                    },
                )

                # Seed divisions
                n_divs = 0
                for div_slug in s["divisions"]:
                    db.execute(
                        text(
                            "INSERT INTO skill_divisions (skill_id, division_slug) "
                            "VALUES (:sid, :div)"
                        ),
                        {"sid": skill_id, "div": div_slug},
                    )
                    n_divs += 1

                # Seed tags
                n_tags = 0
                for tag in s["tags"]:
                    db.execute(
                        text("INSERT INTO skill_tags (skill_id, tag) VALUES (:sid, :tag)"),
                        {"sid": skill_id, "tag": tag},
                    )
                    n_tags += 1

                # Seed trigger phrases
                n_triggers = 0
                for phrase in s.get("triggers", []):
                    db.execute(
                        text(
                            "INSERT INTO trigger_phrases (id, skill_id, phrase) "
                            "VALUES (:id, :sid, :phrase)"
                        ),
                        {"id": str(uuid.uuid4()), "sid": skill_id, "phrase": phrase},
                    )
                    n_triggers += 1

                # Build status badges
                badges = []
                if s["featured"]:
                    badges.append(f"{YELLOW}featured{RESET}")
                if s["verified"]:
                    badges.append(f"{GREEN}verified{RESET}")
                else:
                    badges.append(f"{DIM}unverified{RESET}")
                badges.append(s["install_method"])
                badges.append(s["data_sensitivity"])
                badge_str = f" {DIM}[{', '.join(badges)}]{RESET}"

                meta = (
                    f"{DIM}v{s['current_version']}  "
                    f"★{s['avg_rating']:.1f}  "
                    f"↓{s['install_count']}  "
                    f"{n_divs} divs  "
                    f"{n_tags} tags  "
                    f"{n_triggers} triggers{RESET}"
                )

                _ok(f"{s['name']}{badge_str}")
                _item(meta)

                created += 1

            except Exception as exc:
                error_msg = f"Skill '{s['slug']}': {exc}"
                errors.append(error_msg)
                _err(error_msg)

    print()
    _ok(f"{created} skills created, {skipped} skipped")
    return created, skipped, errors


# ---------------------------------------------------------------------------
# Review seeds
# ---------------------------------------------------------------------------


def _seed_reviews(db) -> tuple[int, int, list[str]]:  # noqa: ANN001
    """Seed reviews. Links reviews to skills by slug and users by index."""
    _section(f"Reviews ({len(SEED_REVIEWS)})")
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0
    errors: list[str] = []

    # Track reviews per skill for summary
    reviews_per_skill: Counter[str] = Counter()

    for r in SEED_REVIEWS:
        # Look up skill ID from slug
        row = db.execute(
            text("SELECT id FROM skills WHERE slug = :slug"),
            {"slug": r["skill_slug"]},
        ).fetchone()
        if not row:
            error_msg = f"Review for '{r['skill_slug']}': skill not found"
            errors.append(error_msg)
            _warn(error_msg)
            continue

        skill_id = str(row[0])

        if r["user_index"] >= len(SEED_USERS):
            error_msg = f"Review for '{r['skill_slug']}': user_index {r['user_index']} out of range"
            errors.append(error_msg)
            _err(error_msg)
            continue

        user_id = SEED_USERS[r["user_index"]]["id"]
        user_name = SEED_USERS[r["user_index"]]["name"]

        # Skip if review already exists for this skill+user pair
        existing = db.execute(
            text(
                "SELECT 1 FROM reviews WHERE skill_id = :sid AND user_id = :uid"
            ),
            {"sid": skill_id, "uid": user_id},
        ).fetchone()
        if existing:
            skipped += 1
            continue

        try:
            review_id = str(uuid.uuid4())
            review_date = now - timedelta(days=r.get("days_ago", 15))

            db.execute(
                text(
                    "INSERT INTO reviews (id, skill_id, user_id, rating, body, "
                    "helpful_count, unhelpful_count, created_at, updated_at) "
                    "VALUES (:id, :sid, :uid, :rating, :body, :helpful, :unhelpful, "
                    ":created_at, :updated_at)"
                ),
                {
                    "id": review_id,
                    "sid": skill_id,
                    "uid": user_id,
                    "rating": r["rating"],
                    "body": r["body"],
                    "helpful": r["rating"] * 2 if r["rating"] >= 4 else r["rating"],
                    "unhelpful": 0 if r["rating"] >= 3 else 2,
                    "created_at": review_date,
                    "updated_at": review_date,
                },
            )

            stars = f"{'★' * r['rating']}{'☆' * (5 - r['rating'])}"
            _ok(f"{stars} {r['skill_slug']} {DIM}← {user_name}{RESET}")
            reviews_per_skill[r["skill_slug"]] += 1
            created += 1

        except Exception as exc:
            error_msg = f"Review for '{r['skill_slug']}' by user {r['user_index']}: {exc}"
            errors.append(error_msg)
            _err(error_msg)

    # Review distribution summary
    if reviews_per_skill:
        print(f"\n  {BOLD}Review distribution:{RESET}")
        for slug, count in reviews_per_skill.most_common():
            bar = "█" * count
            print(f"  {DIM}│{RESET} {slug:<30} {bar} {DIM}({count}){RESET}")

    print()
    _ok(f"{created} reviews created, {skipped} skipped")
    return created, skipped, errors


# ---------------------------------------------------------------------------
# Install seeds
# ---------------------------------------------------------------------------


def _seed_installs(db) -> tuple[int, int]:  # noqa: ANN001
    """Seed install rows. Links installs to skills by slug and users by index."""
    _section(f"Installs ({len(SEED_INSTALLS)})")
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0

    for inst in SEED_INSTALLS:
        row = db.execute(
            text("SELECT id FROM skills WHERE slug = :slug"),
            {"slug": inst["skill_slug"]},
        ).fetchone()
        if not row:
            _warn(f"Install for '{inst['skill_slug']}': skill not found")
            continue

        skill_id = str(row[0])
        user_id = SEED_USERS[inst["user_index"]]["id"]

        # Skip if install already exists for this skill+user pair
        existing = db.execute(
            text("SELECT 1 FROM installs WHERE skill_id = :sid AND user_id = :uid"),
            {"sid": skill_id, "uid": user_id},
        ).fetchone()
        if existing:
            skipped += 1
            continue

        install_date = now - timedelta(days=inst.get("days_ago", 7))
        db.execute(
            text(
                "INSERT INTO installs (id, skill_id, user_id, version, method, installed_at) "
                "VALUES (:id, :sid, :uid, :version, :method, :installed_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "sid": skill_id,
                "uid": user_id,
                "version": inst["version"],
                "method": inst["method"],
                "installed_at": install_date,
            },
        )
        _ok(f"{inst['skill_slug']} {DIM}← user {inst['user_index']}{RESET}")
        created += 1

    _ok(f"{created} installs created, {skipped} skipped")
    return created, skipped


# ---------------------------------------------------------------------------
# Favorite seeds
# ---------------------------------------------------------------------------


def _seed_favorites(db) -> tuple[int, int]:  # noqa: ANN001
    """Seed favorite rows. Links favorites to skills by slug and users by index."""
    _section(f"Favorites ({len(SEED_FAVORITES)})")
    created = 0
    skipped = 0

    for fav in SEED_FAVORITES:
        row = db.execute(
            text("SELECT id FROM skills WHERE slug = :slug"),
            {"slug": fav["skill_slug"]},
        ).fetchone()
        if not row:
            _warn(f"Favorite for '{fav['skill_slug']}': skill not found")
            continue

        skill_id = str(row[0])
        user_id = SEED_USERS[fav["user_index"]]["id"]

        # Skip if favorite already exists (composite PK)
        existing = db.execute(
            text("SELECT 1 FROM favorites WHERE skill_id = :sid AND user_id = :uid"),
            {"sid": skill_id, "uid": user_id},
        ).fetchone()
        if existing:
            skipped += 1
            continue

        db.execute(
            text(
                "INSERT INTO favorites (user_id, skill_id) "
                "VALUES (:uid, :sid)"
            ),
            {"uid": user_id, "sid": skill_id},
        )
        _ok(f"{fav['skill_slug']} {DIM}← user {fav['user_index']}{RESET}")
        created += 1

    _ok(f"{created} favorites created, {skipped} skipped")
    return created, skipped


# ---------------------------------------------------------------------------
# Post-seed reconciliation
# ---------------------------------------------------------------------------


def _reconcile_counters(db) -> int:  # noqa: ANN001
    """Reconcile all skill counters from actual row counts.

    For each published skill:
    - review_count = COUNT of reviews
    - avg_rating = Bayesian: (C * m + sum_ratings) / (C + count)
    - install_count = COUNT of installs (where uninstalled_at IS NULL)
    - favorite_count = COUNT of favorites
    - fork_count = COUNT of forks
    - trending_score = recalculated from formula

    Returns number of skills reconciled.
    """
    _section("Reconciling Counters")
    now = datetime.now(timezone.utc)

    skills = db.execute(
        text("SELECT id, slug, published_at FROM skills WHERE status = 'published'")
    ).fetchall()

    reconciled = 0
    for skill_row in skills:
        skill_id = str(skill_row[0])
        slug = skill_row[1]
        published_at = skill_row[2]

        # Review count and sum
        rev_result = db.execute(
            text(
                "SELECT COUNT(*), COALESCE(SUM(rating), 0) "
                "FROM reviews WHERE skill_id = :sid"
            ),
            {"sid": skill_id},
        ).fetchone()
        review_count = rev_result[0]
        sum_ratings = Decimal(str(rev_result[1]))

        # Bayesian avg_rating
        avg_rating = (BAYESIAN_C * BAYESIAN_M + sum_ratings) / (BAYESIAN_C + review_count)
        avg_rating = round(avg_rating, 2)

        # Install count (active installs only)
        inst_result = db.execute(
            text(
                "SELECT COUNT(*) FROM installs "
                "WHERE skill_id = :sid AND uninstalled_at IS NULL"
            ),
            {"sid": skill_id},
        ).fetchone()
        install_count = inst_result[0]

        # Favorite count
        fav_result = db.execute(
            text("SELECT COUNT(*) FROM favorites WHERE skill_id = :sid"),
            {"sid": skill_id},
        ).fetchone()
        favorite_count = fav_result[0]

        # Fork count
        fork_result = db.execute(
            text("SELECT COUNT(*) FROM forks WHERE original_skill_id = :sid"),
            {"sid": skill_id},
        ).fetchone()
        fork_count = fork_result[0]

        # View count (keep existing or default to 0)
        view_result = db.execute(
            text("SELECT view_count FROM skills WHERE id = :sid"),
            {"sid": skill_id},
        ).fetchone()
        view_count = view_result[0] if view_result else 0

        # Trending score: (installs*3 + favorites*2 + views*0.1 + avg_rating*10) * decay
        days_since = 0.0
        if published_at:
            delta = now - published_at
            days_since = delta.total_seconds() / 86400
        decay = 1.0 / (1.0 + days_since / 30.0)
        raw = (
            float(install_count) * 3
            + float(favorite_count) * 2
            + float(view_count) * 0.1
            + float(avg_rating) * 10
        )
        trending_score = Decimal(str(round(raw * decay, 4)))

        db.execute(
            text(
                "UPDATE skills SET "
                "review_count = :review_count, "
                "avg_rating = :avg_rating, "
                "install_count = :install_count, "
                "favorite_count = :favorite_count, "
                "fork_count = :fork_count, "
                "trending_score = :trending_score "
                "WHERE id = :sid"
            ),
            {
                "sid": skill_id,
                "review_count": review_count,
                "avg_rating": float(avg_rating),
                "install_count": install_count,
                "favorite_count": favorite_count,
                "fork_count": fork_count,
                "trending_score": float(trending_score),
            },
        )
        reconciled += 1

    _ok(f"{reconciled} skills reconciled")
    return reconciled


if __name__ == "__main__":
    seed()

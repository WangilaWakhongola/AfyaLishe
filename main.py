#!/usr/bin/env python3
"""
afya_lishe/main.py
================
Afya Lishe - Nutrition Tracking & Meal Planning System
-------------------------------------------------------
A command-line application for tracking daily food intake and creating
structured meal plans. Nutritional data (calories, protein, carbohydrates,
and fat) is calculated per gram of food consumed and persisted locally as
JSON. Reference targets are based on WHO general adult dietary guidelines.

Usage:
    python main.py

Data files:
    data/food_log.json   -- daily meal entries keyed by ISO date
    data/meal_plans.json -- user-defined named meal plans

Author : Afya Lishe Project
Python : 3.8+
"""

import json
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR   = Path("data")
LOG_FILE   = DATA_DIR / "food_log.json"
MEALS_FILE = DATA_DIR / "meal_plans.json"

# Nutritional values per 100 g: calories (kcal), protein (g), carbs (g), fat (g)
FOOD_DB = {
    "ugali":        {"calories": 360, "protein":  3.6, "carbs": 79.0, "fat":  0.6},
    "sukuma wiki":  {"calories":  35, "protein":  3.0, "carbs":  5.0, "fat":  0.7},
    "beans":        {"calories": 347, "protein": 21.0, "carbs": 63.0, "fat":  1.2},
    "rice":         {"calories": 365, "protein":  7.1, "carbs": 80.0, "fat":  0.7},
    "chicken":      {"calories": 239, "protein": 27.0, "carbs":  0.0, "fat": 14.0},
    "fish":         {"calories": 206, "protein": 22.0, "carbs":  0.0, "fat": 12.0},
    "milk":         {"calories":  61, "protein":  3.2, "carbs":  4.8, "fat":  3.3},
    "banana":       {"calories":  89, "protein":  1.1, "carbs": 23.0, "fat":  0.3},
    "sweet potato": {"calories":  86, "protein":  1.6, "carbs": 20.0, "fat":  0.1},
    "eggs":         {"calories": 155, "protein": 13.0, "carbs":  1.1, "fat": 11.0},
    "avocado":      {"calories": 160, "protein":  2.0, "carbs":  9.0, "fat": 15.0},
    "groundnuts":   {"calories": 567, "protein": 26.0, "carbs": 16.0, "fat": 49.0},
}

# WHO general adult daily reference values
DAILY_TARGETS = {
    "calories": 2000,
    "protein":    50,
    "carbs":     275,
    "fat":        65,
}

LINE_WIDTH = 54


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Create the data directory if it does not already exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_json(path: Path) -> dict:
    """Load and return JSON from *path*, or an empty dict if missing."""
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_json(path: Path, data: dict) -> None:
    """Serialise *data* to *path* as formatted JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def today_key() -> str:
    """Return today's date as an ISO-8601 string (YYYY-MM-DD)."""
    return date.today().isoformat()


def print_header(title: str) -> None:
    print(f"\n{'=' * LINE_WIDTH}")
    print(f"  {title}")
    print(f"{'=' * LINE_WIDTH}")


def print_separator() -> None:
    print("-" * LINE_WIDTH)


# ---------------------------------------------------------------------------
# Feature: food database
# ---------------------------------------------------------------------------

def show_food_database() -> None:
    """Display all foods in the database with their nutritional values."""
    print_header("FOOD DATABASE")
    print(f"  {'Food':<18} {'Cal':>6} {'Protein':>8} {'Carbs':>7} {'Fat':>6}")
    print_separator()
    for food, nutrients in FOOD_DB.items():
        print(
            f"  {food.title():<18}"
            f" {nutrients['calories']:>6}"
            f" {nutrients['protein']:>7}g"
            f" {nutrients['carbs']:>6}g"
            f" {nutrients['fat']:>5}g"
        )
    print("\n  * All values are per 100 g of food.")


# ---------------------------------------------------------------------------
# Feature: meal logging
# ---------------------------------------------------------------------------

def log_meal() -> None:
    """Prompt the user to log a food entry and append it to today's log."""
    print_header("LOG A MEAL")
    log   = load_json(LOG_FILE)
    today = today_key()
    log.setdefault(today, [])

    print("  Available foods:", ", ".join(f.title() for f in FOOD_DB))

    food_name = input("\n  Food name : ").strip().lower()
    if food_name not in FOOD_DB:
        print(f"  ERROR: '{food_name}' not found in the database.")
        return

    try:
        grams = float(input("  Amount (g): ").strip())
        if grams <= 0:
            raise ValueError
    except ValueError:
        print("  ERROR: Please enter a positive number for grams.")
        return

    meal_type = (
        input("  Meal type  (breakfast / lunch / dinner / snack): ")
        .strip()
        .lower()
        or "other"
    )

    nutrients = FOOD_DB[food_name]
    factor    = grams / 100.0

    entry = {
        "time":      datetime.now().strftime("%H:%M"),
        "meal_type": meal_type,
        "food":      food_name,
        "grams":     grams,
        "calories":  round(nutrients["calories"] * factor, 1),
        "protein":   round(nutrients["protein"]  * factor, 1),
        "carbs":     round(nutrients["carbs"]    * factor, 1),
        "fat":       round(nutrients["fat"]      * factor, 1),
    }

    log[today].append(entry)
    save_json(LOG_FILE, log)

    print(
        f"\n  Logged: {grams}g {food_name.title()} -- "
        f"{entry['calories']} kcal | "
        f"{entry['protein']}g protein | "
        f"{entry['carbs']}g carbs | "
        f"{entry['fat']}g fat"
    )


# ---------------------------------------------------------------------------
# Feature: daily summary
# ---------------------------------------------------------------------------

def view_daily_summary() -> None:
    """Print a tabulated summary of all meals logged today with nutrient totals."""
    print_header("DAILY SUMMARY")
    log     = load_json(LOG_FILE)
    today   = today_key()
    entries = log.get(today, [])

    if not entries:
        print("  No meals have been logged for today.")
        return

    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

    print(f"\n  Date: {today}\n")
    print(f"  {'Time':<6} {'Type':<10} {'Food':<16} {'g':>5} {'kcal':>6} {'Pro':>5} {'Carb':>6} {'Fat':>5}")
    print_separator()

    for entry in entries:
        print(
            f"  {entry['time']:<6}"
            f" {entry['meal_type'].title():<10}"
            f" {entry['food'].title():<16}"
            f" {entry['grams']:>5}"
            f" {entry['calories']:>6}"
            f" {entry['protein']:>4}g"
            f" {entry['carbs']:>5}g"
            f" {entry['fat']:>4}g"
        )
        for key in totals:
            totals[key] += entry[key]

    print_separator()
    print(
        f"  {'TOTAL':<33}"
        f" {totals['calories']:>6}"
        f" {totals['protein']:>4}g"
        f" {totals['carbs']:>5}g"
        f" {totals['fat']:>4}g"
    )

    print("\n  Reference targets (WHO general adult guidelines):")
    for key, target in DAILY_TARGETS.items():
        unit   = "kcal" if key == "calories" else "g"
        actual = round(totals[key], 1)
        diff   = round(actual - target, 1)
        status = f"+{diff}" if diff >= 0 else str(diff)
        print(f"    {key.title():<10}: target {target:>5} {unit}  |  actual {actual:>7} {unit}  |  {status} {unit}")


# ---------------------------------------------------------------------------
# Feature: meal plans
# ---------------------------------------------------------------------------

def create_meal_plan() -> None:
    """Interactively build and save a named meal plan."""
    print_header("CREATE MEAL PLAN")
    plans = load_json(MEALS_FILE)

    name = input("  Plan name (e.g. 'Week 1 Balanced'): ").strip()
    if not name:
        print("  ERROR: Plan name cannot be empty.")
        return

    plan = {}
    for meal in ("Breakfast", "Lunch", "Dinner", "Snack"):
        raw = input(f"  {meal:<12} foods (comma-separated, blank to skip): ").strip()
        if raw:
            plan[meal.lower()] = [item.strip().lower() for item in raw.split(",") if item.strip()]

    plans[name] = {"created": today_key(), "meals": plan}
    save_json(MEALS_FILE, plans)
    print(f"\n  Meal plan '{name}' saved successfully.")


def view_meal_plans() -> None:
    """List all saved meal plans and their contents."""
    print_header("SAVED MEAL PLANS")
    plans = load_json(MEALS_FILE)

    if not plans:
        print("  No meal plans have been saved yet.")
        return

    for name, data in plans.items():
        print(f"\n  Plan    : {name}")
        print(f"  Created : {data['created']}")
        for meal, foods in data.get("meals", {}).items():
            print(f"    {meal.title():<12}: {', '.join(f.title() for f in foods)}")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = {
    "1": ("View food database",    show_food_database),
    "2": ("Log a meal",            log_meal),
    "3": ("View today's summary",  view_daily_summary),
    "4": ("Create a meal plan",    create_meal_plan),
    "5": ("View saved meal plans", view_meal_plans),
    "6": ("Exit",                  None),
}


def main() -> None:
    """Entry point: initialise data directory and run the interactive menu loop."""
    ensure_data_dir()

    print_header("AFYA LISHE -- Nutrition Tracking & Meal Planning")
    print("  Welcome. Select an option below to get started.")

    while True:
        print("\n  MENU")
        print_separator()
        for key, (label, _) in MENU.items():
            print(f"  [{key}]  {label}")
        print_separator()

        choice = input("  Option: ").strip()

        if choice == "6":
            print("\n  Session ended. Goodbye.\n")
            break
        elif choice in MENU:
            MENU[choice][1]()
        else:
            print("  ERROR: Invalid option. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()

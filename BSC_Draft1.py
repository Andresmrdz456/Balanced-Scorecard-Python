import sqlite3
import pandas as pd

# Define perspectives for the Balanced Scorecard
PERSPECTIVES = ["Financial", "Customer", "Internal Processes", "Learning & Growth"]

class Perspective:
    def __init__(self, name):
        self.name = name
        self.kpis = []

    def add_kpi(self, kpi):
        self.kpis.append(kpi)

class KPI:
    def __init__(self, name, target, actual, weight=1):
        self.name = name
        self.target = target
        self.actual = actual
        self.weight = weight
        self.score = self.calculate_score()

    def calculate_score(self):
        return round((self.actual / self.target) * 100 if self.target else 0, 2)

class DatabaseManager:
    def __init__(self, db_name="bsc.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS kpis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perspective TEXT,
            name TEXT,
            target REAL,
            actual REAL,
            weight REAL,
            score REAL,
            UNIQUE(perspective, name)
        )
        """)
        self.conn.commit()

    def update_kpi(self, perspective, kpi_name, new_target, new_actual):
        existing = self.cursor.execute("SELECT 1 FROM kpis WHERE perspective = ? AND name = ?", (perspective, kpi_name)).fetchone()
        if not existing:
            print(f"❗ KPI '{kpi_name}' not found in perspective '{perspective}'. Cannot update.")
            return
        new_score = round((new_actual / new_target) * 100 if new_target else 0, 2)
        self.cursor.execute("""
          UPDATE kpis
          SET target = ?, actual = ?, score = ?
          WHERE perspective = ? AND name = ?
        """, (new_target, new_actual, new_score, perspective, kpi_name))
        self.conn.commit()

    def delete_kpi(self, perspective, kpi_name):
        self.cursor.execute("""
          DELETE FROM kpis
          WHERE perspective = ? AND name = ?
        """, (perspective, kpi_name))
        self.conn.commit()

    def add_kpi(self, perspective, kpi):
        existing = self.cursor.execute("SELECT 1 FROM kpis WHERE perspective = ? AND name = ?", (perspective, kpi.name)).fetchone()
        if existing:
            raise ValueError(f"❗ A KPI named '{kpi.name}' already exists in the '{perspective}' perspective. Please choose a unique name.")
        print(f"Adding KPI: {kpi.name} | Target: {kpi.target} | Actual: {kpi.actual} | Score: {kpi.score}")
        self.cursor.execute("""
        INSERT INTO kpis (perspective, name, target, actual, weight, score)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (perspective, kpi.name, kpi.target, kpi.actual, kpi.weight, kpi.score))
        self.conn.commit()

    def get_kpis_by_perspective(self):
        self.cursor.execute("SELECT perspective, name, target, actual, score FROM kpis")
        rows = self.cursor.fetchall()
        grouped = {perspective: [] for perspective in PERSPECTIVES}
        for row in rows:
            grouped[row[0]].append({"KPI": row[1], "Target": row[2], "Actual": row[3], "Score": row[4]})
        return grouped

class BalancedScorecard:
    def __init__(self):
        self.db = DatabaseManager()

    def add_kpi(self, perspective, kpi_name, target, actual, weight=1):
        kpi = KPI(kpi_name, target, actual, weight)
        self.db.add_kpi(perspective, kpi)

    def display_report(self):
        print("\n📊 Balanced Scorecard Report:\n")
        grouped_data = self.db.get_kpis_by_perspective()
        for perspective, kpis in grouped_data.items():
            print(f"{perspective} Perspective:")
            df = pd.DataFrame(kpis)
            if not df.empty:
                print(df.to_string(index=False))
            else:
                print(" No KPIs added yet.")
            print("-" * 50)

    def edit_kpi(self, perspective, kpi_name, new_target, new_actual):
        self.db.update_kpi(perspective, kpi_name, new_target, new_actual)

    def delete_kpi(self, perspective, kpi_name):
        self.db.delete_kpi(perspective, kpi_name)

# CLI Menu

def interactive_menu():
    bsc = BalancedScorecard()

    while True:
        print("\n🔷 Balanced Scorecard CLI Menu")
        print("1. Add a new KPI")
        print("2. View report")
        print("3. Edit a KPI")
        print("4. Delete a KPI")
        print("5. Exit")

        choice = input("Choose an option (1-5): ").strip().lower()

        def get_valid_perspective():
            for i, p in enumerate(PERSPECTIVES):
                print(f"{i + 1}. {p}")
            p_input = input("Select perspective (number or name): ").strip().lower()
            if p_input in [str(i + 1) for i in range(len(PERSPECTIVES))]:
                return PERSPECTIVES[int(p_input) - 1]
            matches = [p for p in PERSPECTIVES if p.lower() == p_input]
            return matches[0] if matches else None


        if choice in ["1", "add a new kpi", "1. add a new kpi"]:
            print("\n➕ Add New KPI")
            perspective = get_valid_perspective()
            if perspective is None:
                print("❌ Invalid perspective choice.")
                continue
            kpi_name = input("Enter KPI name: ").strip()
            try:
                # Normalize input for case-insensitive match
                existing = bsc.db.cursor.execute("SELECT 1 FROM kpis WHERE LOWER(perspective) = ? AND LOWER(name) = ?", (perspective.lower(), kpi_name.lower())).fetchone()
                if existing:
                    raise ValueError(f"❗ A KPI named '{kpi_name}' already exists in the '{perspective}' perspective. Please choose a unique name.")
                target = float(input("Enter target value: "))
                actual = float(input("Enter actual value: "))
                bsc.add_kpi(perspective, kpi_name, target, actual)
            except ValueError as ve:
                print(f"❗ Error: {ve}")


        elif choice in ["2", "view report", "2. view report"]:
            bsc.display_report()

        elif choice in ["3", "edit a kpi", "3. edit a kpi"]:
            print("\n✏️ Edit KPI")
            perspective = get_valid_perspective()
            if perspective is None:
                print("❌ Invalid perspective choice.")
                continue
            grouped_data = bsc.db.get_kpis_by_perspective()
            print("\nAvailable KPIs:")
            for kpi in grouped_data.get(perspective, []):
                print(f"- {kpi['KPI']}")
            kpi_name = input("Enter the KPI name to edit: ").strip()
            try:
                new_target = float(input("Enter the new target value: "))
                new_actual = float(input("Enter the new actual value: "))
                bsc.edit_kpi(perspective, kpi_name, new_target, new_actual)
                print("✅ KPI update attempted. If no update was made, the KPI may not exist.")
            except ValueError:
                print("❌ Invalid number input.")

        elif choice in ["4", "delete a kpi", "4. delete a kpi"]:
            print("\n🗑️ Delete KPI")
            perspective = get_valid_perspective()
            if perspective is None:
                print("❌ Invalid perspective choice.")
                continue
            grouped_data = bsc.db.get_kpis_by_perspective()
            print("\nAvailable KPIs:")
            for kpi in grouped_data.get(perspective, []):
                print(f"- {kpi['KPI']}")
            kpi_name = input("Enter the KPI name to delete: ").strip()
            confirm = input(f"⚠️ Are you sure you want to delete '{kpi_name}' from '{perspective}'? (yes/no): ").strip().lower()
            if confirm == "yes":
                bsc.delete_kpi(perspective, kpi_name)
                print("🗑️ KPI deleted.")
            else:
                print("❎ Deletion cancelled.")

        elif choice in ["5", "exit", "5. exit"]:
            print("👋 Exiting. Goodbye!")
            break

        else:
            print("❗ Invalid option. Please select a valid number or label.")

if __name__ == "__main__":
    interactive_menu()



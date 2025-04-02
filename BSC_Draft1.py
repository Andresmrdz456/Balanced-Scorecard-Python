import argparse
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
            score REAL
        )
        """)
        self.conn.commit()
    
    def add_kpi(self, perspective, kpi):
        self.cursor.execute("""
        INSERT INTO kpis (perspective, name, target, actual, weight, score)
        VALUES (?, ?, ?, ?, ?, ?)""", 
        (perspective, kpi.name, kpi.target, kpi.actual, kpi.weight, kpi.score))
        self.conn.commit()
    
    def get_kpis(self):
        self.cursor.execute("SELECT * FROM kpis")
        return self.cursor.fetchall()

class BalancedScorecard:
    def __init__(self):
        self.perspectives = {perspective: Perspective(perspective) for perspective in PERSPECTIVES}
        self.db = DatabaseManager()
    
    def add_kpi(self, perspective, kpi_name, target, actual, weight=1):
        if perspective not in self.perspectives:
            print(f"Invalid perspective: {perspective}")
            return
        kpi = KPI(kpi_name, target, actual, weight)
        self.perspectives[perspective].add_kpi(kpi)
        self.db.add_kpi(perspective, kpi)
        print(f"KPI '{kpi_name}' added under '{perspective}' with score: {kpi.score}")
        
    def display_report(self):
        print("\nBalanced Scorecard Report:\n")
        for perspective, data in self.perspectives.items():
            print(f"{perspective} Perspective:")
            df = pd.DataFrame([{ "KPI": kpi.name, "Target": kpi.target, "Actual": kpi.actual, "Score": kpi.score } for kpi in data.kpis])
            if not df.empty:
                print(df.to_string(index=False))
            else:
                print(" No KPIs added yet.")
            print("-" * 50)

# CLI functionality
def main():
    parser = argparse.ArgumentParser(description="CLI for Balanced Scorecard Management")
    parser.add_argument("--perspective", type=str, help="Perspective of the KPI", choices=PERSPECTIVES)
    parser.add_argument("--kpi", type=str, help="Name of the KPI")
    parser.add_argument("--target", type=float, help="Target value of the KPI")
    parser.add_argument("--actual", type=float, help="Actual value achieved")
    parser.add_argument("--report", action='store_true', help="Display Balanced Scorecard report")
    
    args = parser.parse_args()
    
    bsc = BalancedScorecard()
    
    if args.perspective and args.kpi and args.target is not None and args.actual is not None:
        bsc.add_kpi(args.perspective, args.kpi, args.target, args.actual)
    
    if args.report:
        bsc.display_report()
    print("Parsed arguments:", args)

    if not args.report and not all([args.perspective, args.kpi, args.target is not None, args.actual is not None]):
        raise ValueError("❗ No action specified.\nUse the following examples:\n"
                        "  ➤ Add a KPI:\n"
                        "     --perspective \"Financial\" --kpi \"Revenue Growth\" --target 100 --actual 80\n"
                        "  ➤ Show report:\n"
                        "     --report")

if __name__ == "__main__":
    main()

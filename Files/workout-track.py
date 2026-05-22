#!/usr/bin/env python3
"""
Workout Tracker Suite - Day 3: Complete Workout Dashboard
Full-featured training dashboard with templates, 1RM calc, timers, and analytics.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import threading


# Plate configs (from Day 1)
PLATE_COLORS_LBS = {45: '#FF0000', 35: '#FFD700', 25: '#00FF00', 10: '#FFFFFF', 5: '#0000FF', 2.5: '#FF4444'}
PLATE_SIZES_LBS = {45: (20, 70), 35: (18, 60), 25: (16, 50), 10: (14, 40), 5: (12, 35), 2.5: (10, 25)}
PLATES_LBS = [45, 35, 25, 10, 5, 2.5]

# Exercises
EXERCISES = ['Bench Press', 'Squat', 'Deadlift', 'Overhead Press', 'Barbell Row', 'Pull-ups', 'Dips']

# Workout templates
TEMPLATES = {
    'Push Day': [
        ('Bench Press', 4, 8, 180),
        ('Overhead Press', 3, 10, 120),
        ('Incline DB Press', 3, 12, 90),
        ('Lateral Raises', 3, 15, 60),
        ('Tricep Extensions', 3, 12, 60),
    ],
    'Pull Day': [
        ('Deadlift', 3, 5, 180),
        ('Pull-ups', 3, 10, 120),
        ('Barbell Row', 4, 8, 120),
        ('Face Pulls', 3, 15, 60),
        ('Bicep Curls', 3, 12, 60),
    ],
    'Leg Day': [
        ('Squat', 4, 6, 180),
        ('Romanian Deadlift', 3, 10, 120),
        ('Leg Press', 3, 12, 90),
        ('Leg Curls', 3, 15, 60),
        ('Calf Raises', 4, 20, 60),
    ]
}

# Strength standards (multiplier of bodyweight)
STRENGTH_STANDARDS = {
    'Bench Press': {'Beginner': 0.75, 'Novice': 1.0, 'Intermediate': 1.25, 'Advanced': 1.5, 'Elite': 1.75},
    'Squat': {'Beginner': 1.0, 'Novice': 1.5, 'Intermediate': 2.0, 'Advanced': 2.5, 'Elite': 3.0},
    'Deadlift': {'Beginner': 1.25, 'Novice': 1.75, 'Intermediate': 2.25, 'Advanced': 2.75, 'Elite': 3.25},
}


class WorkoutDashboard:
    """Complete workout tracking dashboard"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏋️ Complete Workout Dashboard")
        self.root.geometry("1000x700")
        
        # State
        self.bar_weight = 45
        self.workouts_file = Path('workouts.csv')
        self.bodyweight = 180  # Default
        
        # Timers
        self.workout_start_time = None
        self.workout_running = False
        self.rest_time = 120
        self.rest_running = False
        self.rest_start = None
        
        # Create UI
        self.create_widgets()
        self.calculate_plates()
    
    def create_widgets(self):
        """Create tabbed interface"""
        # Title
        title = tk.Label(self.root, text="🏋️ COMPLETE WORKOUT DASHBOARD", font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_plate_calc_tab()
        self.create_logger_tab()
        self.create_templates_tab()
        self.create_1rm_tab()
        self.create_timer_tab()
        self.create_analytics_tab()
    
    def create_plate_calc_tab(self):
        """Plate calculator tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Plate Calculator")
        
        # Input
        input_frame = tk.Frame(tab)
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Target Weight:", font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        self.weight_var = tk.StringVar(value="225")
        tk.Entry(input_frame, textvariable=self.weight_var, width=10, font=('Arial', 14)).pack(side=tk.LEFT, padx=5)
        tk.Label(input_frame, text="lbs", font=('Arial', 12)).pack(side=tk.LEFT)
        
        self.weight_var.trace('w', lambda *args: self.calculate_plates())
        
        # Presets
        preset_frame = tk.Frame(tab)
        preset_frame.pack(pady=10)
        
        for w in [135, 185, 225, 315, 405]:
            tk.Button(preset_frame, text=str(w), width=6,
                     command=lambda x=w: self.weight_var.set(str(x))).pack(side=tk.LEFT, padx=3)
        
        # Canvas
        self.canvas = tk.Canvas(tab, width=700, height=200, bg='white', relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=20)
        
        # Plates list
        self.plates_text = tk.Text(tab, height=5, width=50, font=('Arial', 10), state=tk.DISABLED)
        self.plates_text.pack()
    
    def create_logger_tab(self):
        """Workout logger tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Log Workout")
        
        # Input frame
        input_frame = tk.LabelFrame(tab, text="Log Exercise", font=('Arial', 11, 'bold'), padx=10, pady=10)
        input_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(input_frame, text="Exercise:").grid(row=0, column=0, padx=5, pady=5)
        self.exercise_var = tk.StringVar(value=EXERCISES[0])
        ttk.Combobox(input_frame, textvariable=self.exercise_var, values=EXERCISES, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="Sets:").grid(row=1, column=0, padx=5, pady=5)
        self.sets_var = tk.StringVar(value="3")
        tk.Entry(input_frame, textvariable=self.sets_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="Reps:").grid(row=2, column=0, padx=5, pady=5)
        self.reps_var = tk.StringVar(value="8")
        tk.Entry(input_frame, textvariable=self.reps_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="Weight (lbs):").grid(row=3, column=0, padx=5, pady=5)
        self.log_weight_var = tk.StringVar(value="225")
        tk.Entry(input_frame, textvariable=self.log_weight_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="RPE (1-10):").grid(row=4, column=0, padx=5, pady=5)
        self.rpe_var = tk.StringVar(value="8")
        tk.Entry(input_frame, textvariable=self.rpe_var, width=10).grid(row=4, column=1, padx=5, pady=5)
        
        tk.Button(input_frame, text="LOG WORKOUT", command=self.log_workout,
                 bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'), padx=20, pady=10).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Today's summary
        summary_frame = tk.LabelFrame(tab, text="Today's Workouts", font=('Arial', 11, 'bold'), padx=10, pady=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.today_text = scrolledtext.ScrolledText(summary_frame, height=10, font=('Arial', 10))
        self.today_text.pack(fill=tk.BOTH, expand=True)
    
    def create_templates_tab(self):
        """Workout templates tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Templates")
        
        tk.Label(tab, text="WORKOUT TEMPLATES", font=('Arial', 14, 'bold')).pack(pady=20)
        
        # Template selector
        select_frame = tk.Frame(tab)
        select_frame.pack(pady=10)
        
        tk.Label(select_frame, text="Select Template:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        self.template_var = tk.StringVar(value=list(TEMPLATES.keys())[0])
        ttk.Combobox(select_frame, textvariable=self.template_var, values=list(TEMPLATES.keys()),
                    width=20, state='readonly').pack(side=tk.LEFT, padx=5)
        tk.Button(select_frame, text="Show Template", command=self.show_template).pack(side=tk.LEFT, padx=5)
        
        # Template display
        self.template_text = scrolledtext.ScrolledText(tab, height=15, width=80, font=('Courier', 10))
        self.template_text.pack(padx=20, pady=10)
    
    def create_1rm_tab(self):
        """1RM calculator tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="1RM Calculator")
        
        tk.Label(tab, text="ONE-REP MAX CALCULATOR", font=('Arial', 14, 'bold')).pack(pady=20)
        
        # Input
        input_frame = tk.Frame(tab)
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Weight Lifted:", font=('Arial', 11)).grid(row=0, column=0, padx=10, pady=10)
        self.rm_weight_var = tk.StringVar(value="225")
        tk.Entry(input_frame, textvariable=self.rm_weight_var, width=10, font=('Arial', 12)).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(input_frame, text="lbs", font=('Arial', 11)).grid(row=0, column=2, padx=5, pady=10)
        
        tk.Label(input_frame, text="Reps Performed:", font=('Arial', 11)).grid(row=1, column=0, padx=10, pady=10)
        self.rm_reps_var = tk.StringVar(value="8")
        tk.Entry(input_frame, textvariable=self.rm_reps_var, width=10, font=('Arial', 12)).grid(row=1, column=1, padx=10, pady=10)
        
        tk.Button(input_frame, text="Calculate 1RM", command=self.calculate_1rm,
                 bg='#2196F3', fg='white', font=('Arial', 11, 'bold'), padx=20, pady=10).grid(row=2, column=0, columnspan=3, pady=20)
        
        # Results
        self.rm_results_text = scrolledtext.ScrolledText(tab, height=12, width=70, font=('Courier', 10))
        self.rm_results_text.pack(padx=20, pady=10)
    
    def create_timer_tab(self):
        """Session timer tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Timer")
        
        tk.Label(tab, text="WORKOUT TIMER", font=('Arial', 14, 'bold')).pack(pady=20)
        
        # Workout timer
        timer_frame = tk.LabelFrame(tab, text="Total Workout Time", font=('Arial', 11, 'bold'), padx=20, pady=20)
        timer_frame.pack(pady=20)
        
        self.workout_time_label = tk.Label(timer_frame, text="00:00", font=('Arial', 48, 'bold'))
        self.workout_time_label.pack(pady=20)
        
        btn_frame = tk.Frame(timer_frame)
        btn_frame.pack()
        
        tk.Button(btn_frame, text="Start Workout", command=self.start_workout_timer,
                 bg='#4CAF50', fg='white', font=('Arial', 10), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=self.stop_workout_timer,
                 bg='#f44336', fg='white', font=('Arial', 10), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Rest timer
        rest_frame = tk.LabelFrame(tab, text="Rest Timer", font=('Arial', 11, 'bold'), padx=20, pady=20)
        rest_frame.pack(pady=20)
        
        self.rest_time_label = tk.Label(rest_frame, text="2:00", font=('Arial', 36, 'bold'))
        self.rest_time_label.pack(pady=15)
        
        rest_btn_frame = tk.Frame(rest_frame)
        rest_btn_frame.pack()
        
        tk.Label(rest_btn_frame, text="Rest Duration:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        rest_options = [60, 90, 120, 180]
        self.rest_duration_var = tk.IntVar(value=120)
        for duration in rest_options:
            tk.Radiobutton(rest_btn_frame, text=f"{duration}s", variable=self.rest_duration_var,
                          value=duration).pack(side=tk.LEFT, padx=5)
        
        tk.Button(rest_frame, text="Start Rest Timer", command=self.start_rest_timer,
                 bg='#FF9800', fg='white', font=('Arial', 10), padx=15, pady=8).pack(pady=10)
        
        self.rest_alert_label = tk.Label(rest_frame, text="", font=('Arial', 11, 'bold'), fg='#4CAF50')
        self.rest_alert_label.pack(pady=5)
    
    def create_analytics_tab(self):
        """Analytics and reports tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Analytics")
        
        tk.Label(tab, text="PROGRESS ANALYTICS", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Controls
        control_frame = tk.Frame(tab)
        control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Exercise:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.analytics_exercise_var = tk.StringVar(value=EXERCISES[0])
        ttk.Combobox(control_frame, textvariable=self.analytics_exercise_var, values=EXERCISES,
                    width=15, state='readonly').pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Update Chart", command=self.update_analytics_chart,
                 bg='#2196F3', fg='white', font=('Arial', 9), padx=10, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(control_frame, text="Export Report", command=self.export_report,
                 bg='#4CAF50', fg='white', font=('Arial', 9), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Chart
        self.analytics_fig = Figure(figsize=(8, 4), dpi=80)
        self.analytics_ax = self.analytics_fig.add_subplot(111)
        
        self.analytics_canvas = FigureCanvasTkAgg(self.analytics_fig, master=tab)
        self.analytics_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Recommendations
        self.recommendations_label = tk.Label(tab, text="", font=('Arial', 10), justify=tk.LEFT)
        self.recommendations_label.pack(pady=10)
    
    # === Plate Calculator Methods ===
    
    def calculate_plates(self):
        """Calculate plates (from Day 1)"""
        try:
            target = float(self.weight_var.get())
        except ValueError:
            return
        
        if target <= self.bar_weight:
            self.display_plates([], target)
            return
        
        smallest_increment = min(PLATES_LBS) * 2
        target = round(target / smallest_increment) * smallest_increment
        weight_per_side = (target - self.bar_weight) / 2
        
        plates_needed = []
        remaining = weight_per_side
        
        for plate in sorted(PLATES_LBS, reverse=True):
            count = int(remaining / plate)
            if count > 0:
                plates_needed.append((plate, count))
                remaining -= plate * count
        
        self.display_plates(plates_needed, target)
    
    def display_plates(self, plates_needed, total_weight):
        """Display plates on canvas"""
        self.canvas.delete('all')
        
        bar_length = 500
        bar_x = 100
        bar_y = 100
        
        self.canvas.create_line(bar_x, bar_y, bar_x + bar_length, bar_y, fill='#888', width=15)
        
        if plates_needed:
            x_offset = bar_x - 5
            for plate_weight, count in plates_needed:
                for _ in range(count):
                    color = PLATE_COLORS_LBS.get(plate_weight, '#CCC')
                    width, height = PLATE_SIZES_LBS.get(plate_weight, (10, 30))
                    
                    self.canvas.create_rectangle(x_offset - width, bar_y - height/2,
                                                 x_offset, bar_y + height/2,
                                                 fill=color, outline='black', width=2)
                    self.canvas.create_text(x_offset - width/2, bar_y - height/2 - 12,
                                          text=str(plate_weight), font=('Arial', 8, 'bold'))
                    x_offset -= width + 3
            
            x_offset = bar_x + bar_length + 5
            for plate_weight, count in plates_needed:
                for _ in range(count):
                    color = PLATE_COLORS_LBS.get(plate_weight, '#CCC')
                    width, height = PLATE_SIZES_LBS.get(plate_weight, (10, 30))
                    
                    self.canvas.create_rectangle(x_offset, bar_y - height/2,
                                                 x_offset + width, bar_y + height/2,
                                                 fill=color, outline='black', width=2)
                    self.canvas.create_text(x_offset + width/2, bar_y - height/2 - 12,
                                          text=str(plate_weight), font=('Arial', 8, 'bold'))
                    x_offset += width + 3
        
        self.plates_text.config(state=tk.NORMAL)
        self.plates_text.delete(1.0, tk.END)
        
        if not plates_needed:
            self.plates_text.insert(tk.END, "Empty bar only!")
        else:
            for plate, count in plates_needed:
                self.plates_text.insert(tk.END, f"• {count} × {plate} lbs\n")
        
        self.plates_text.config(state=tk.DISABLED)
    
    # === Logger Methods ===
    
    def log_workout(self):
        """Log workout to CSV"""
        try:
            exercise = self.exercise_var.get()
            sets = int(self.sets_var.get())
            reps = int(self.reps_var.get())
            weight = float(self.log_weight_var.get())
            rpe = int(self.rpe_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
            return
        
        volume = sets * reps * weight
        
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'exercise': exercise,
            'sets': sets,
            'reps': reps,
            'weight': weight,
            'rpe': rpe,
            'volume': volume
        }
        
        df = pd.DataFrame([data])
        df.to_csv(self.workouts_file, mode='a', header=not self.workouts_file.exists(), index=False)
        
        messagebox.showinfo("Success", f"✓ Logged: {exercise} {sets}×{reps} @ {weight} lbs")
        self.load_today_summary()
    
    def load_today_summary(self):
        """Load today's workouts"""
        if not self.workouts_file.exists():
            return
        
        df = pd.read_csv(self.workouts_file)
        today = datetime.now().strftime('%Y-%m-%d')
        today_df = df[df['date'] == today]
        
        self.today_text.delete(1.0, tk.END)
        
        if today_df.empty:
            self.today_text.insert(tk.END, "No workouts logged today")
        else:
            self.today_text.insert(tk.END, f"Today's Workouts ({today}):\n\n")
            for _, row in today_df.iterrows():
                self.today_text.insert(tk.END,
                    f"• {row['exercise']}: {row['sets']}×{row['reps']} @ {row['weight']} lbs (RPE {row['rpe']})\n")
            
            total_volume = today_df['volume'].sum()
            self.today_text.insert(tk.END, f"\nTotal Volume: {total_volume:,.0f} lbs")
    
    # === Template Methods ===
    
    def show_template(self):
        """Show selected template"""
        template_name = self.template_var.get()
        exercises = TEMPLATES[template_name]
        
        self.template_text.delete(1.0, tk.END)
        self.template_text.insert(tk.END, f"{template_name.upper()}\n")
        self.template_text.insert(tk.END, "=" * 60 + "\n\n")
        
        for i, (exercise, sets, reps, rest) in enumerate(exercises, 1):
            self.template_text.insert(tk.END, f"{i}. {exercise}\n")
            self.template_text.insert(tk.END, f"   Sets: {sets}  Reps: {reps}  Rest: {rest}s\n\n")
    
    # === 1RM Calculator Methods ===
    
    def calculate_1rm(self):
        """Calculate 1RM using multiple formulas"""
        try:
            weight = float(self.rm_weight_var.get())
            reps = int(self.rm_reps_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
            return
        
        # Formulas
        epley = weight * (1 + reps/30)
        brzycki = weight * (36 / (37 - reps))
        lander = (100 * weight) / (101.3 - 2.67123 * reps)
        lombardi = weight * (reps ** 0.10)
        
        average = (epley + brzycki + lander + lombardi) / 4
        
        self.rm_results_text.delete(1.0, tk.END)
        self.rm_results_text.insert(tk.END, "ONE-REP MAX ESTIMATES\n")
        self.rm_results_text.insert(tk.END, "=" * 50 + "\n\n")
        self.rm_results_text.insert(tk.END, f"Epley:     {epley:.1f} lbs\n")
        self.rm_results_text.insert(tk.END, f"Brzycki:   {brzycki:.1f} lbs\n")
        self.rm_results_text.insert(tk.END, f"Lander:    {lander:.1f} lbs\n")
        self.rm_results_text.insert(tk.END, f"Lombardi:  {lombardi:.1f} lbs\n\n")
        self.rm_results_text.insert(tk.END, f"Average:   {average:.1f} lbs\n\n")
        self.rm_results_text.insert(tk.END, "=" * 50 + "\n\n")
        self.rm_results_text.insert(tk.END, "TRAINING PERCENTAGES:\n\n")
        self.rm_results_text.insert(tk.END, f"90% (Strength):    {average * 0.9:.1f} lbs\n")
        self.rm_results_text.insert(tk.END, f"80% (Hypertrophy): {average * 0.8:.1f} lbs\n")
        self.rm_results_text.insert(tk.END, f"70% (Endurance):   {average * 0.7:.1f} lbs\n")
    
    # === Timer Methods ===
    
    def start_workout_timer(self):
        """Start workout timer"""
        if not self.workout_running:
            self.workout_start_time = time.time()
            self.workout_running = True
            self.update_workout_timer()
    
    def stop_workout_timer(self):
        """Stop workout timer"""
        self.workout_running = False
    
    def update_workout_timer(self):
        """Update workout timer display"""
        if self.workout_running:
            elapsed = int(time.time() - self.workout_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.workout_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_workout_timer)
    
    def start_rest_timer(self):
        """Start rest timer"""
        if not self.rest_running:
            self.rest_time = self.rest_duration_var.get()
            self.rest_start = time.time()
            self.rest_running = True
            self.rest_alert_label.config(text="")
            self.update_rest_timer()
    
    def update_rest_timer(self):
        """Update rest timer display"""
        if self.rest_running:
            elapsed = int(time.time() - self.rest_start)
            remaining = max(0, self.rest_time - elapsed)
            
            minutes = remaining // 60
            seconds = remaining % 60
            self.rest_time_label.config(text=f"{minutes}:{seconds:02d}")
            
            if remaining == 0:
                self.rest_running = False
                self.rest_alert_label.config(text="🔔 Rest complete! Time for next set.")
            else:
                self.root.after(1000, self.update_rest_timer)
    
    # === Analytics Methods ===
    
    def update_analytics_chart(self):
        """Update analytics chart"""
        if not self.workouts_file.exists():
            return
        
        df = pd.read_csv(self.workouts_file)
        exercise = self.analytics_exercise_var.get()
        ex_df = df[df['exercise'] == exercise].copy()
        
        if ex_df.empty:
            return
        
        ex_df['date'] = pd.to_datetime(ex_df['date'])
        ex_df = ex_df.sort_values('date')
        
        self.analytics_ax.clear()
        self.analytics_ax.plot(ex_df['date'], ex_df['weight'], marker='o', linewidth=2, markersize=8, color='#4CAF50')
        self.analytics_ax.set_xlabel('Date')
        self.analytics_ax.set_ylabel('Weight (lbs)')
        self.analytics_ax.set_title(f'{exercise} Progress')
        self.analytics_ax.grid(True, alpha=0.3)
        self.analytics_fig.autofmt_xdate()
        
        self.analytics_canvas.draw()
        
        # Recommendations
        if len(ex_df) >= 3:
            last_3 = ex_df.tail(3)
            avg_rpe = last_3['rpe'].mean()
            last_weight = ex_df.iloc[-1]['weight']
            
            if avg_rpe < 8.5:
                recommendation = f"✓ Progressive Overload: Increase to {last_weight + 5} lbs next session"
            else:
                recommendation = f"⚠ Maintain current weight ({last_weight} lbs) - High RPE"
            
            self.recommendations_label.config(text=recommendation)
    
    def export_report(self):
        """Export workout report"""
        if not self.workouts_file.exists():
            messagebox.showinfo("Info", "No workout data")
            return
        
        df = pd.read_csv(self.workouts_file)
        
        report = "=" * 60 + "\n"
        report += "WORKOUT PROGRESS REPORT\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n"
        report += "=" * 60 + "\n\n"
        
        report += "PERSONAL RECORDS:\n"
        report += "-" * 60 + "\n"
        
        for exercise in EXERCISES:
            ex_df = df[df['exercise'] == exercise]
            if not ex_df.empty:
                max_row = ex_df.loc[ex_df['weight'].idxmax()]
                report += f"{exercise}: {max_row['weight']} lbs × {max_row['reps']} reps ({max_row['date']})\n"
        
        report += "\n" + "=" * 60 + "\n"
        
        with open('workout_report.txt', 'w') as f:
            f.write(report)
        
        messagebox.showinfo("Success", "Report exported to workout_report.txt")


def main():
    """Main function"""
    root = tk.Tk()
    app = WorkoutDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()

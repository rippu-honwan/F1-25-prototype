#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 Analysis Script
User data vs Pro driver (FastF1) comparison analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
import warnings
import platform

warnings.filterwarnings('ignore')

# Japanese font support - OS specific
if platform.system() == 'Darwin':  # macOS
    matplotlib.rcParams['font.family'] = 'Hiragino Sans'
elif platform.system() == 'Windows':
    matplotlib.rcParams['font.family'] = 'MS Gothic'
else:  # Linux
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'

matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (14, 10)


class Phase1Analysis:
    """Phase 1 Analysis Class"""
    
    def __init__(self, user_csv_path):
        """Initialize"""
        self.user_data = None
        self.pro_data = None
        self.csv_path = user_csv_path
        self.pro_driver_name = "Pro Driver (No data)"
        self.is_real_data = False
        
    def load_user_data(self):
        """Load user telemetry data"""
        print("\n" + "="*60)
        print("Step 1: Load User Data")
        print("="*60)
        
        self.user_data = pd.read_csv(self.csv_path)
        print(f"✓ Data loaded: {len(self.user_data)} rows")
        print(f"✓ Columns: {list(self.user_data.columns)}")
        
        print(f"\n✓ Session time: {self.user_data['session_time'].min():.1f}s - {self.user_data['session_time'].max():.1f}s")
        print(f"✓ Drive time: {(self.user_data['session_time'].max() - self.user_data['session_time'].min()):.1f} sec")
        
        self.user_data['throttle'] = self.user_data['throttle'] / 255
        self.user_data['brake'] = self.user_data['brake'] / 255
        
        print(f"\n[Basic Stats]")
        print(f"  Max speed: {self.user_data['speed_kph'].max():.1f} km/h")
        print(f"  Avg speed: {self.user_data['speed_kph'].mean():.1f} km/h")
        print(f"  Min speed: {self.user_data['speed_kph'].min():.1f} km/h")
        
        return self.user_data
    
    def extract_pro_data(self, year=2024, gp='Monza', session_type='Q1'):
        """Extract pro driver data from FastF1"""
        print("\n" + "="*60)
        print("Step 2: Extract FastF1 Pro Driver Data")
        print("="*60)
        
        try:
            import fastf1
            print(f"✓ FastF1 session loading: {year} {gp} {session_type}")
            
            session = fastf1.get_session(year, gp, session_type)
            session.load()
            
            laps = session.laps.iloc[:30]
            fastest_lap = laps.loc[laps['LapTime'].idxmin()]
            self.pro_driver_name = f"{fastest_lap['Driver']} (2024 {gp} Q1)"
            print(f"✓ Fastest driver: {fastest_lap['Driver']}")
            print(f"✓ Fastest lap time: {fastest_lap['LapTime']}")
            
            self.pro_data = fastest_lap.get_telemetry()
            print(f"✓ Telemetry extracted: {len(self.pro_data)} data points")
            
            self.is_real_data = True
            return self.pro_data
            
        except Exception as e:
            print(f"✗ FastF1 Error: {e}")
            print("\n✓ Generating simulation data...")
            self.pro_driver_name = "Simulation Pro Driver"
            self.is_real_data = False
            self.pro_data = self._generate_dummy_pro_data()
            return self.pro_data
    
    def _generate_dummy_pro_data(self):
        """Generate demo pro driver data (when FastF1 unavailable)"""
        n = len(self.user_data)
        
        dummy_data = pd.DataFrame({
            'Time': np.linspace(0, 120, n),
            'Speed': self.user_data['speed_kph'].values * 1.08 + np.random.normal(0, 2, n),
            'Throttle': np.where(
                self.user_data['speed_kph'].values < self.user_data['speed_kph'].mean(),
                self.user_data['throttle'].values * 0.85,
                self.user_data['throttle'].values
            ),
            'Brake': np.where(
                self.user_data['speed_kph'].values > self.user_data['speed_kph'].mean() * 0.9,
                self.user_data['brake'].values * 1.15,
                self.user_data['brake'].values
            ),
            'Steering': self.user_data['steering'].values * 0.92,
        })
        
        dummy_data['Throttle'] = dummy_data['Throttle'].clip(0, 1)
        dummy_data['Brake'] = dummy_data['Brake'].clip(0, 1)
        dummy_data['Steering'] = dummy_data['Steering'].clip(-1, 1)
        
        return dummy_data
    
    def visualize_user_data(self):
        """Visualize user telemetry data"""
        print("\n" + "="*60)
        print("Step 3: Visualize User Data")
        print("="*60)
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        fig.suptitle('Your Telemetry Data - Monza', fontsize=16, fontweight='bold')
        
        time = self.user_data['session_time']
        
        axes[0].plot(time, self.user_data['speed_kph'], color='#1f77b4', linewidth=1.5)
        axes[0].set_title('Speed vs Session Time', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Speed (km/h)')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=self.user_data['speed_kph'].mean(), color='red', linestyle='--', alpha=0.5, label=f'Avg: {self.user_data["speed_kph"].mean():.1f}')
        axes[0].legend()
        
        axes[1].plot(time, self.user_data['throttle'] * 100, label='Throttle', color='green', linewidth=1.5)
        axes[1].plot(time, self.user_data['brake'] * 100, label='Brake', color='red', linewidth=1.5)
        axes[1].set_title('Throttle vs Brake Input', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Input (0-100%)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        axes[2].plot(time, self.user_data['steering'], color='purple', linewidth=1.5)
        axes[2].set_title('Steering Angle', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('Steering (-1 ~ +1)')
        axes[2].grid(True, alpha=0.3)
        
        axes[3].plot(time, self.user_data['rpm'], color='orange', linewidth=1.5)
        axes[3].set_title('Engine RPM', fontsize=12, fontweight='bold')
        axes[3].set_ylabel('RPM')
        axes[3].set_xlabel('Session Time (s)')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = Path('analysis_results/your_telemetry_overview.png')
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Graph saved: {output_path}")
        plt.close()
    
    def visualize_comparison(self):
        """Visualize user vs pro driver comparison"""
        print("\n" + "="*60)
        print("Step 4: Generate Comparison Graphs")
        print("="*60)
        
        data_type = "[REAL DATA]" if self.is_real_data else "[SIMULATION]"
        print(f"\nComparison: {data_type} {self.pro_driver_name}")
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        
        title = f'You vs {self.pro_driver_name} - Monza'
        if not self.is_real_data:
            title += ' (Simulation)'
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        your_time = np.linspace(0, 1, len(self.user_data))
        pro_time = np.linspace(0, 1, len(self.pro_data))
        
        axes[0].plot(your_time, self.user_data['speed_kph'], label='You', linewidth=2, color='#1f77b4')
        axes[0].plot(pro_time, self.pro_data['Speed'], label='Pro Driver', linewidth=2, color='#ff7f0e', alpha=0.7)
        axes[0].set_title('Speed Comparison', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Speed (km/h)')
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)
        
        axes[1].plot(your_time, self.user_data['throttle'] * 100, label='You', linewidth=2, color='#2ca02c')
        axes[1].plot(pro_time, self.pro_data['Throttle'] * 100, label='Pro Driver', linewidth=2, color='#d62728', alpha=0.7)
        axes[1].set_title('Throttle Input Comparison', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Throttle (%)')
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)
        
        axes[2].plot(your_time, self.user_data['brake'] * 100, label='You', linewidth=2, color='#9467bd')
        axes[2].plot(pro_time, self.pro_data['Brake'] * 100, label='Pro Driver', linewidth=2, color='#8c564b', alpha=0.7)
        axes[2].set_title('Brake Input Comparison', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('Brake (%)')
        axes[2].legend(loc='upper right')
        axes[2].grid(True, alpha=0.3)
        
        axes[3].plot(your_time, self.user_data['steering'], label='You', linewidth=2, color='#e377c2')
        axes[3].plot(pro_time, self.pro_data['Steering'], label='Pro Driver', linewidth=2, color='#7f7f7f', alpha=0.7)
        axes[3].set_title('Steering Input Comparison', fontsize=12, fontweight='bold')
        axes[3].set_ylabel('Steering Angle')
        axes[3].set_xlabel('Lap Progress')
        axes[3].legend(loc='upper right')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = Path('analysis_results/you_vs_pro_comparison.png')
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Graph saved: {output_path}")
        plt.close()
    
    def analyze_statistics(self):
        """Statistical analysis and correlation calculation"""
        print("\n" + "="*60)
        print("Step 5: Statistical Analysis")
        print("="*60)
        
        data_type = "[REAL]" if self.is_real_data else "[SIMULATION]"
        print(f"\nComparison against: {data_type} {self.pro_driver_name}")
        
        your_speed_norm = (self.user_data['speed_kph'] - self.user_data['speed_kph'].min()) / (self.user_data['speed_kph'].max() - self.user_data['speed_kph'].min())
        pro_speed_norm = (self.pro_data['Speed'] - self.pro_data['Speed'].min()) / (self.pro_data['Speed'].max() - self.pro_data['Speed'].min())
        
        print("\n[SPEED ANALYSIS]")
        print(f"  Your max speed: {self.user_data['speed_kph'].max():.1f} km/h")
        print(f"  Pro max speed: {self.pro_data['Speed'].max():.1f} km/h")
        print(f"  Difference: {self.pro_data['Speed'].max() - self.user_data['speed_kph'].max():+.1f} km/h")
        
        print(f"\n  Your avg speed: {self.user_data['speed_kph'].mean():.1f} km/h")
        print(f"  Pro avg speed: {self.pro_data['Speed'].mean():.1f} km/h")
        speed_diff_pct = (self.pro_data['Speed'].mean() - self.user_data['speed_kph'].mean()) / self.user_data['speed_kph'].mean() * 100
        print(f"  Difference: {speed_diff_pct:+.1f}%")
        
        print("\n[THROTTLE ANALYSIS]")
        print(f"  Your avg throttle: {self.user_data['throttle'].mean():.1%}")
        print(f"  Pro avg throttle: {self.pro_data['Throttle'].mean():.1%}")
        throttle_corr = self.user_data['throttle'].corr(self.pro_data['Throttle'].iloc[:len(self.user_data)])
        print(f"  Synchronization: {throttle_corr:.3f}")
        
        print("\n[BRAKE ANALYSIS]")
        print(f"  Your avg brake: {self.user_data['brake'].mean():.1%}")
        print(f"  Pro avg brake: {self.pro_data['Brake'].mean():.1%}")
        brake_corr = self.user_data['brake'].corr(self.pro_data['Brake'].iloc[:len(self.user_data)])
        print(f"  Synchronization: {brake_corr:.3f}")
        
        print("\n[STEERING ANALYSIS]")
        print(f"  Your avg steering: {self.user_data['steering'].mean():.3f}")
        print(f"  Pro avg steering: {self.pro_data['Steering'].mean():.3f}")
        steer_corr = self.user_data['steering'].corr(self.pro_data['Steering'].iloc[:len(self.user_data)])
        print(f"  Precision: {steer_corr:.3f}")
        
        print("\n" + "="*60)
        print("Improvement Points")
        print("="*60)
        
        if self.pro_data['Speed'].mean() > self.user_data['speed_kph'].mean():
            print(f"\n! SPEED: {speed_diff_pct:.1f}% slower than pro")
            print(f"  -> Improve throttle timing and pedal input force")
        
        if abs(throttle_corr) < 0.7:
            print(f"\n! THROTTLE TIMING: Low sync ({throttle_corr:.3f})")
            print(f"  -> Your acceleration timing differs from the pro")
        
        if abs(brake_corr) < 0.7:
            print(f"\n! BRAKE TIMING: Low sync ({brake_corr:.3f})")
            print(f"  -> Try braking earlier like the pro does")
        
        print("\n" + "="*60)
    
    def run_full_analysis(self):
        """Run full analysis"""
        print("\n" + "🏁"*20)
        print("\nPhase 1 Analysis Start - You vs Professional Driver")
        print("\n" + "🏁"*20)
        
        self.load_user_data()
        self.extract_pro_data()
        self.visualize_user_data()
        self.visualize_comparison()
        self.analyze_statistics()
        
        print("\n" + "="*60)
        print("✓ Phase 1 Analysis Complete!")
        print("="*60)
        print("\nGenerated files:")
        print("  1. analysis_results/your_telemetry_overview.png")
        print("  2. analysis_results/you_vs_pro_comparison.png")
        print(f"\nComparison against: {self.pro_driver_name}")
        if not self.is_real_data:
            print("  Note: Simulation data (FastF1 unavailable)")
        print("\nNext step: Phase 2 - Corner Analysis")
        print("="*60 + "\n")


if __name__ == "__main__":
    data_file = "telemetry_data/telemetry_monza_5laps_final_20251228_185844.csv"
    
    analyzer = Phase1Analysis(data_file)
    analyzer.run_full_analysis()

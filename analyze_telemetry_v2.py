#!/usr/bin/env python3
"""
F1 25 Telemetry Analysis V2
Analyze telemetry data from f1_recorder_final.py
"""

import csv
import statistics
import sys
import os
from collections import defaultdict


def load_telemetry(csv_file):
    """Load telemetry data from CSV"""
    telemetry_data = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            telemetry_data.append(row)
    
    return telemetry_data


def analyze_speed(telemetry_data):
    """Analyze speed data"""
    speeds = []
    
    for row in telemetry_data:
        if row['speed_kph']:
            try:
                speed = int(row['speed_kph'])
                if 0 < speed < 400:
                    speeds.append(speed)
            except ValueError:
                pass
    
    if not speeds:
        return None
    
    return {
        'average': statistics.mean(speeds),
        'max': max(speeds),
        'min': min(speeds),
        'median': statistics.median(speeds),
        'stdev': statistics.stdev(speeds) if len(speeds) > 1 else 0,
        'total_samples': len(speeds),
    }


def analyze_inputs(telemetry_data):
    """Analyze throttle and brake inputs"""
    throttles = []
    brakes = []
    
    for row in telemetry_data:
        try:
            if row.get('throttle'):
                throttle = int(row['throttle'])
                if 0 <= throttle <= 100:
                    throttles.append(throttle)
            
            if row.get('brake'):
                brake = int(row['brake'])
                if 0 <= brake <= 100:
                    brakes.append(brake)
        except ValueError:
            pass
    
    if not throttles or not brakes:
        return None
    
    return {
        'throttle': {
            'average': statistics.mean(throttles),
            'max': max(throttles),
            'min': min(throttles),
            'full_throttle_percent': (sum(1 for t in throttles if t > 95) / len(throttles)) * 100,
            'samples': len(throttles),
        },
        'brake': {
            'average': statistics.mean(brakes),
            'max': max(brakes),
            'min': min(brakes),
            'braking_percent': (sum(1 for b in brakes if b > 10) / len(brakes)) * 100,
            'samples': len(brakes),
        }
    }


def analyze_rpm(telemetry_data):
    """Analyze RPM data"""
    rpms = []
    
    for row in telemetry_data:
        if row.get('rpm'):
            try:
                rpm = int(row['rpm'])
                if 0 < rpm < 20000:
                    rpms.append(rpm)
            except ValueError:
                pass
    
    if not rpms:
        return None
    
    return {
        'average': statistics.mean(rpms),
        'max': max(rpms),
        'min': min(rpms),
        'samples': len(rpms),
    }


def print_analysis(csv_file):
    """Print complete analysis"""
    print("🏎️  F1 25 Telemetry Analysis V2")
    print("=" * 60)
    print(f"File: {csv_file}\n")
    
    # Load data
    print("📊 Loading data...")
    telemetry_data = load_telemetry(csv_file)
    print(f"   Loaded {len(telemetry_data)} data points\n")
    
    # Speed analysis
    print("🏁 Speed Analysis")
    print("-" * 60)
    speed_stats = analyze_speed(telemetry_data)
    if speed_stats:
        print(f"   Average Speed:     {speed_stats['average']:.1f} kph")
        print(f"   Max Speed:         {speed_stats['max']} kph")
        print(f"   Min Speed:         {speed_stats['min']} kph")
        print(f"   Median Speed:      {speed_stats['median']:.1f} kph")
        print(f"   Speed Variation:   {speed_stats['stdev']:.1f} kph (stdev)")
        print(f"   Data Samples:      {speed_stats['total_samples']}")
        
        if 150 < speed_stats['average'] < 300:
            print(f"   ✅ Speed data looks correct!")
        else:
            print(f"   ⚠️  Speed data might be incorrect")
        print()
    else:
        print("   No speed data found\n")
    
    # Input analysis
    print("🎮 Input Analysis")
    print("-" * 60)
    input_stats = analyze_inputs(telemetry_data)
    if input_stats:
        print(f"   Throttle:")
        print(f"      Average:         {input_stats['throttle']['average']:.1f}%")
        print(f"      Max:             {input_stats['throttle']['max']}%")
        print(f"      Min:             {input_stats['throttle']['min']}%")
        print(f"      Full Throttle:   {input_stats['throttle']['full_throttle_percent']:.1f}% of time")
        print(f"\n   Brake:")
        print(f"      Average:         {input_stats['brake']['average']:.1f}%")
        print(f"      Max:             {input_stats['brake']['max']}%")
        print(f"      Min:             {input_stats['brake']['min']}%")
        print(f"      Braking:         {input_stats['brake']['braking_percent']:.1f}% of time\n")
        
        # Check if throttle/brake are swapped
        if input_stats['throttle']['average'] < 20 and input_stats['brake']['average'] > 40:
            print(f"   ⚠️  WARNING: Throttle/Brake might be swapped!\n")
    else:
        print("   No input data found\n")
    
    # RPM analysis
    print("🕐 RPM Analysis")
    print("-" * 60)
    rpm_stats = analyze_rpm(telemetry_data)
    if rpm_stats:
        print(f"   Average RPM:       {rpm_stats['average']:.0f}")
        print(f"   Max RPM:           {rpm_stats['max']}")
        print(f"   Min RPM:           {rpm_stats['min']}")
        print(f"   Data Samples:      {rpm_stats['samples']}")
        
        if 8000 < rpm_stats['average'] < 16000:
            print(f"   ✅ RPM data looks reasonable!\n")
        else:
            print(f"   ⚠️  RPM data might be incorrect\n")
    else:
        print("   No RPM data found\n")
    
    print("=" * 60)
    print("Analysis complete! 🏁")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        import glob
        csv_files = sorted(glob.glob('telemetry_data/*.csv'), key=os.path.getmtime, reverse=True)
        
        if not csv_files:
            print("❌ No telemetry CSV files found in telemetry_data/")
            sys.exit(1)
        
        csv_file = csv_files[0]
        print(f"📄 Using most recent file: {csv_file}\n")
    else:
        csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    print_analysis(csv_file)


if __name__ == "__main__":
    main()

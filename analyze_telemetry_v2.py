#!/usr/bin/env python3
"""
F1 25 Telemetry Analysis V2
Analyze telemetry data from f1_recorder_v2.py
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
                if 0 < speed < 400:  # Reasonable F1 speed range
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
            if row['throttle']:
                throttle = int(row['throttle'])
                if 0 <= throttle <= 100:
                    throttles.append(throttle)
            
            if row['brake']:
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
            'full_throttle_percent': (sum(1 for t in throttles if t > 95) / len(throttles)) * 100,
            'samples': len(throttles),
        },
        'brake': {
            'average': statistics.mean(brakes),
            'max': max(brakes),
            'braking_percent': (sum(1 for b in brakes if b > 10) / len(brakes)) * 100,
            'samples': len(brakes),
        }
    }


def analyze_laps(telemetry_data):
    """Analyze lap-by-lap performance"""
    laps = defaultdict(list)
    
    for row in telemetry_data:
        if row['lap_number'] and row['speed_kph']:
            try:
                lap_num = int(row['lap_number'])
                speed = int(row['speed_kph'])
                if 0 < speed < 400 and lap_num > 0:
                    laps[lap_num].append(speed)
            except ValueError:
                pass
    
    if not laps:
        return None
    
    lap_stats = {}
    for lap_num, speeds in sorted(laps.items()):
        if speeds:
            lap_stats[lap_num] = {
                'average_speed': statistics.mean(speeds),
                'max_speed': max(speeds),
                'samples': len(speeds),
            }
    
    return lap_stats


def analyze_consistency(lap_stats):
    """Calculate consistency across laps"""
    if not lap_stats or len(lap_stats) < 2:
        return None
    
    avg_speeds = [stats['average_speed'] for stats in lap_stats.values()]
    
    return {
        'lap_count': len(lap_stats),
        'consistency_stdev': statistics.stdev(avg_speeds),
        'speed_range': max(avg_speeds) - min(avg_speeds),
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
        
        # Data quality check
        if 150 < speed_stats['average'] < 250:
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
        print(f"      Average:        {input_stats['throttle']['average']:.1f}%")
        print(f"      Max:            {input_stats['throttle']['max']}%")
        print(f"      Full Throttle:  {input_stats['throttle']['full_throttle_percent']:.1f}% of time")
        print(f"\n   Brake:")
        print(f"      Average:        {input_stats['brake']['average']:.1f}%")
        print(f"      Max:            {input_stats['brake']['max']}%")
        print(f"      Braking:        {input_stats['brake']['braking_percent']:.1f}% of time\n")
    else:
        print("   No input data found\n")
    
    # Lap-by-lap analysis
    print("📈 Lap-by-Lap Analysis")
    print("-" * 60)
    lap_stats = analyze_laps(telemetry_data)
    if lap_stats:
        for lap_num, stats in sorted(lap_stats.items()):
            print(f"   Lap {lap_num}: Avg {stats['average_speed']:.1f} kph, "
                  f"Max {stats['max_speed']} kph, "
                  f"({stats['samples']} samples)")
        print()
    else:
        print("   No lap data found\n")
    
    # Consistency analysis
    if lap_stats:
        print("🎯 Consistency Analysis")
        print("-" * 60)
        consistency = analyze_consistency(lap_stats)
        if consistency:
            print(f"   Laps Completed:        {consistency['lap_count']}")
            print(f"   Consistency (stdev):   {consistency['consistency_stdev']:.2f} kph")
            print(f"   Speed Range:           {consistency['speed_range']:.2f} kph")
            
            if consistency['consistency_stdev'] < 5:
                print(f"   ✅ Excellent consistency!")
            elif consistency['consistency_stdev'] < 10:
                print(f"   👍 Good consistency")
            else:
                print(f"   ⚠️  Could improve consistency")
            print()
    
    print("=" * 60)
    print("Analysis complete! 🏁")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # Find most recent CSV
        import glob
        csv_files = sorted(glob.glob('telemetry_data/*.csv'), key=os.path.getmtime, reverse=True)
        
        if not csv_files:
            print("❌ No telemetry CSV files found in telemetry_data/")
            print("\nUsage: python3 analyze_telemetry_v2.py <csv_file>")
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

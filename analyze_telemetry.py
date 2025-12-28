#!/usr/bin/env python3
"""
F1 25 Telemetry Analysis
Analyze your driving data from recorded telemetry
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
        if row['speed'] and row['packet_type'] == '6':
            try:
                speed = int(row['speed'])
                if speed > 0:  # Filter out invalid readings
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
    }


def analyze_inputs(telemetry_data):
    """Analyze throttle and brake inputs"""
    throttles = []
    brakes = []
    
    for row in telemetry_data:
        if row['packet_type'] == '6':
            try:
                if row['throttle']:
                    throttles.append(int(row['throttle']))
                if row['brake']:
                    brakes.append(int(row['brake']))
            except ValueError:
                pass
    
    if not throttles or not brakes:
        return None
    
    return {
        'throttle': {
            'average': statistics.mean(throttles),
            'max': max(throttles),
            'full_throttle_percent': (sum(1 for t in throttles if t > 95) / len(throttles)) * 100,
        },
        'brake': {
            'average': statistics.mean(brakes),
            'max': max(brakes),
            'braking_percent': (sum(1 for b in brakes if b > 10) / len(brakes)) * 100,
        }
    }


def analyze_consistency(telemetry_data):
    """Analyze driving consistency"""
    # Group data by frame intervals (simulate laps)
    frame_groups = defaultdict(list)
    
    for row in telemetry_data:
        if row['speed'] and row['frame_id'] and row['packet_type'] == '6':
            try:
                frame = int(row['frame_id'])
                speed = int(row['speed'])
                # Group into 1000-frame buckets (rough lap approximation)
                bucket = frame // 10000
                frame_groups[bucket].append(speed)
            except ValueError:
                pass
    
    if len(frame_groups) < 2:
        return None
    
    # Calculate average speed per bucket
    bucket_averages = [statistics.mean(speeds) for speeds in frame_groups.values() if speeds]
    
    if not bucket_averages:
        return None
    
    return {
        'segments': len(bucket_averages),
        'average_speed_per_segment': bucket_averages,
        'consistency_stdev': statistics.stdev(bucket_averages) if len(bucket_averages) > 1 else 0,
    }


def print_analysis(csv_file):
    """Print complete analysis"""
    print("🏎️  F1 25 Telemetry Analysis")
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
        print(f"   Speed Variation:   {speed_stats['stdev']:.1f} kph (stdev)\n")
    else:
        print("   No speed data found\n")
    
    # Input analysis
    print("🎮 Input Analysis")
    print("-" * 60)
    input_stats = analyze_inputs(telemetry_data)
    if input_stats:
        print(f"   Throttle:")
        print(f"      Average:        {input_stats['throttle']['average']:.1f}%")
        print(f"      Full Throttle:  {input_stats['throttle']['full_throttle_percent']:.1f}% of time")
        print(f"\n   Brake:")
        print(f"      Average:        {input_stats['brake']['average']:.1f}%")
        print(f"      Braking:        {input_stats['brake']['braking_percent']:.1f}% of time\n")
    else:
        print("   No input data found\n")
    
    # Consistency analysis
    print("📈 Consistency Analysis")
    print("-" * 60)
    consistency = analyze_consistency(telemetry_data)
    if consistency:
        print(f"   Segments Analyzed:     {consistency['segments']}")
        print(f"   Consistency Score:     {consistency['consistency_stdev']:.2f} kph")
        print(f"   (Lower is more consistent)")
        
        if consistency['consistency_stdev'] < 5:
            print(f"   ✅ Excellent consistency!")
        elif consistency['consistency_stdev'] < 10:
            print(f"   👍 Good consistency")
        else:
            print(f"   ⚠️  Improve consistency - vary less between segments")
        
        print(f"\n   Segment Speeds:")
        for i, avg in enumerate(consistency['average_speed_per_segment'], 1):
            print(f"      Segment {i}: {avg:.1f} kph")
    else:
        print("   Not enough data for consistency analysis")
    
    print("\n" + "=" * 60)
    print("Analysis complete! 🏁")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # Find most recent CSV
        import glob
        csv_files = sorted(glob.glob('telemetry_data/*.csv'), key=os.path.getmtime, reverse=True)
        
        if not csv_files:
            print("❌ No telemetry CSV files found in telemetry_data/")
            print("\nUsage: python3 analyze_telemetry.py <csv_file>")
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

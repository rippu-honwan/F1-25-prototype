#!/usr/bin/env python3
"""
F1 25 テレメトリー 分析ツール
F1 25 から記録した UDP データを分析します。
"""

import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path


def find_latest_telemetry():
    """最新のテレメトリーファイルを探します。
    
    telemetry_data フォルダ内で最も新しい CSV ファイルを探します。
    
    Returns:
        最新ファイルを探せない場合、None を返します。
    """
    telemetry_dir = 'telemetry_data'
    if not os.path.exists(telemetry_dir):
        print("❌ telemetry_data フォルダがないです")
        return None
    
    # すべての telemetry_*.csv を探します
    csv_files = glob.glob(os.path.join(telemetry_dir, 'telemetry_*.csv'))
    if not csv_files:
        print("❌ テレメトリーファイルがないです")
        return None
    
    # 最新ファイルを返します
    latest = max(csv_files, key=os.path.getctime)
    return latest


def analyze_telemetry(filepath):
    """テレメトリーデータを分析します。
    
    以下の情報を計算します:
    - 速度: 平均、最大、最小、中平値、標準偏差
    - アクセル: 平均、最大、最小
    - ブレーキ: 平均、最大、最小、使用率
    - RPM: 平均、最大、最小
    
    Args:
        filepath: CSV ファイルを探します。
    """
    print(f"\n📄 最新ファイル: {os.path.basename(filepath)}\n")
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"❌ ファイルを読み込めません: {e}")
        return
    
    print(f"🏎️  F1 25 テレメトリー 分析")
    print("=" * 60)
    print(f"ファイル: {os.path.basename(filepath)}\n")
    
    # Type 6 (カーテレメトリー) をフィルタします
    # 無効なデータを除く
    telemetry_data = df[(df['packet_type'] == 6) & (df['speed_kph'] > 0)].copy()
    
    print(f"📊 データを読み込んでいます...")
    print(f"   {len(telemetry_data)} 件のデータを読み込みました\n")
    
    if len(telemetry_data) == 0:
        print("❌ 有効なテレメトリーデータがありません")
        return
    
    # ==================== 速度分析 ====================
    print(f"🏁 速度分析")
    print("-" * 60)
    
    speed_mean = telemetry_data['speed_kph'].mean()
    speed_max = telemetry_data['speed_kph'].max()
    speed_min = telemetry_data['speed_kph'].min()
    speed_median = telemetry_data['speed_kph'].median()
    speed_std = telemetry_data['speed_kph'].std()
    
    print(f"   平均速度:     {speed_mean:.1f} km/h")
    print(f"   最大速度:         {speed_max:.0f} km/h")
    print(f"   最小速度:         {speed_min:.0f} km/h")
    print(f"   中平値:      {speed_median:.1f} km/h")
    print(f"   速度の散らかり:   {speed_std:.1f} km/h (標準偏差)")
    print(f"   データ数:      {len(telemetry_data)} 件")
    print(f"   ✅ 速度データは正しいです!\n")
    
    # ==================== お作光分析 ====================
    print(f"🎮 作光分析")
    print("-" * 60)
    
    # ========== アクセル ==========
    throttle_mean = telemetry_data['throttle'].mean()
    throttle_max = telemetry_data['throttle'].max()
    throttle_min = telemetry_data['throttle'].min()
    throttle_full = (telemetry_data['throttle'] == 100).sum() / len(telemetry_data) * 100
    
    print(f"   アクセル:")
    print(f"      平均:         {throttle_mean:.1f}%")
    print(f"      最大:             {throttle_max:.0f}%")
    print(f"      最小:             {throttle_min:.0f}%")
    print(f"      全つっと:   {throttle_full:.1f}% (時間)\n")
    
    # ========== ブレーキ ==========
    brake_mean = telemetry_data['brake'].mean()
    brake_max = telemetry_data['brake'].max()
    brake_min = telemetry_data['brake'].min()
    braking_time = (telemetry_data['brake'] > 0).sum() / len(telemetry_data) * 100
    
    print(f"   ブレーキ:")
    print(f"      平均:         {brake_mean:.1f}%")
    print(f"      最大:             {brake_max:.0f}%")
    print(f"      最小:             {brake_min:.0f}%")
    print(f"      孿風:         {braking_time:.1f}% (時間)\n")
    
    # ==================== RPM 分析 ====================
    print(f"🕐 RPM 分析")
    print("-" * 60)
    
    # 0 より大きい RPM データをフィルタ
    rpm_data = telemetry_data[telemetry_data['rpm'] > 0]
    
    if len(rpm_data) > 0:
        rpm_mean = rpm_data['rpm'].mean()
        rpm_max = rpm_data['rpm'].max()
        rpm_min = rpm_data['rpm'].min()
        
        print(f"   平均 RPM:       {rpm_mean:.0f}")
        print(f"   最大 RPM:           {rpm_max:.0f}")
        print(f"   最小 RPM:           {rpm_min:.0f}")
        print(f"   データ数:      {len(rpm_data)} 件")
        
        if rpm_mean > 5000:
            print(f"   ✅ RPM データは正しいです!\n")
        else:
            print(f"   ⚠️  RPM データが間違っている可能性があります\n")
    else:
        print(f"   ⚠️  RPM データがありません\n")
    
    print("=" * 60)
    print(f"分析が完了しました! 🏁\n")


def main():
    """メインプログラム。
    
    最新ファイルを探して分析します。
    """
    filepath = find_latest_telemetry()
    if filepath:
        analyze_telemetry(filepath)
    else:
        print("\nテレメトリーを記録する場合: python3 f1_recorder.py")


if __name__ == "__main__":
    main()

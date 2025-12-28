#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 分析スクリプト
ユーザーデータ vs 職業選手（2025 Max Verstappen）の対比分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
import warnings
import platform

warnings.filterwarnings('ignore')

# 日本語フォント設定 - OS別対応
if platform.system() == 'Darwin':  # macOS
    matplotlib.rcParams['font.family'] = 'Hiragino Sans'
elif platform.system() == 'Windows':
    matplotlib.rcParams['font.family'] = 'MS Gothic'
else:  # Linux
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'

matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (14, 10)


class Phase1Analysis:
    """Phase 1分析クラス"""
    
    def __init__(self, user_csv_path, pro_driver_name="Max Verstappen", pro_driver_year=2025):
        """初期化"""
        self.user_data = None
        self.pro_data = None
        self.csv_path = user_csv_path
        self.pro_driver_name = pro_driver_name
        self.pro_driver_year = pro_driver_year
        self.is_real_data = False
        
    def load_user_data(self):
        """ユーザーテレメトリーデータ読み込み"""
        print("\n" + "="*60)
        print("ステップ 1: ユーザーデータ読み込み")
        print("="*60)
        
        self.user_data = pd.read_csv(self.csv_path)
        print(f"✓ データ読み込み完了: {len(self.user_data)} 行")
        print(f"✓ カラム: {list(self.user_data.columns)}")
        
        print(f"\n✓ セッション時間: {self.user_data['session_time'].min():.1f}s - {self.user_data['session_time'].max():.1f}s")
        print(f"✓ 走行時間: {(self.user_data['session_time'].max() - self.user_data['session_time'].min()):.1f}秒")
        
        # ✅ CSV形式の正規化: throttle/brake を 0-255 から 0-1 に変換
        self.user_data['throttle'] = self.user_data['throttle'] / 255
        self.user_data['brake'] = self.user_data['brake'] / 255
        
        # 基本統計
        print(f"\n【基本統計】")
        print(f"  最高速: {self.user_data['speed_kph'].max():.1f} km/h")
        print(f"  平均速: {self.user_data['speed_kph'].mean():.1f} km/h")
        print(f"  最低速: {self.user_data['speed_kph'].min():.1f} km/h")
        
        return self.user_data
    
    def extract_pro_data(self):
        """FastF1から職業選手（2025 Max Verstappen）データ抽出"""
        print("\n" + "="*60)
        print(f"ステップ 2: {self.pro_driver_name} ({self.pro_driver_year}) データ抽出")
        print("="*60)
        
        try:
            import fastf1
            print(f"✓ FastF1セッション読み込み中...")
            
            # 2025年のレースデータを取得（Abu Dhabi最終戦）
            try:
                print(f"✓ {self.pro_driver_year} Abu Dhabi 最終戦を試す...")
                session = fastf1.get_session(self.pro_driver_year, 'Abu Dhabi', 'R')
                session.load()
                print(f"✓ {self.pro_driver_year} Abu Dhabi レース 読み込み成功")
            except:
                print(f"✓ Qatar レースを試す...")
                session = fastf1.get_session(self.pro_driver_year, 'Qatar', 'R')
                session.load()
                print(f"✓ {self.pro_driver_year} Qatar レース 読み込み成功")
            
            # Max Verstappen (VER) のデータを検索
            driver_laps = session.laps[session.laps['Driver'] == 'VER']
            
            if len(driver_laps) == 0:
                print(f"✗ {self.pro_driver_name} (VER) のデータが見つかりません")
                print("✓ デモ用データを生成します...")
                self.is_real_data = False
                self.pro_data = self._generate_dummy_pro_data()
                return self.pro_data
            
            # 最速ラップを取得
            fastest_lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]
            print(f"✓ ドライバー: {fastest_lap['Driver']} ({self.pro_driver_name})")
            print(f"✓ 最速ラップ時間: {fastest_lap['LapTime']}")
            
            # テレメトリー抽出
            self.pro_data = fastest_lap.get_telemetry()
            print(f"✓ テレメトリーデータ抽出: {len(self.pro_data)} データポイント")
            
            # データ正規化 (FastF1が制供する形式に依存)
            if 'Speed' in self.pro_data.columns:
                self.pro_data['Speed'] = self.pro_data['Speed'].astype(float)
            if 'Throttle' in self.pro_data.columns:
                self.pro_data['Throttle'] = self.pro_data['Throttle'].astype(float) / 100  # 0-100 -> 0-1
            if 'Brake' in self.pro_data.columns:
                self.pro_data['Brake'] = self.pro_data['Brake'].astype(float) / 100  # 0-100 -> 0-1
            
            self.is_real_data = True
            return self.pro_data
            
        except Exception as e:
            print(f"✗ FastF1エラー: {e}")
            print("✓ デモ用データを生成します...")
            self.is_real_data = False
            self.pro_data = self._generate_dummy_pro_data()
            return self.pro_data
    
    def _generate_dummy_pro_data(self):
        """デモ用職業選手データ生成（FastF1が使えない場合）"""
        n = len(self.user_data)
        
        # ユーザーデータより若干高いパフォーマンスのデータ生成
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
        
        # 負の値をクリップ
        dummy_data['Throttle'] = dummy_data['Throttle'].clip(0, 1)
        dummy_data['Brake'] = dummy_data['Brake'].clip(0, 1)
        dummy_data['Steering'] = dummy_data['Steering'].clip(-1, 1)
        
        return dummy_data
    
    def visualize_user_data(self):
        """ユーザーテレメトリーデータ可視化"""
        print("\n" + "="*60)
        print("ステップ 3: ユーザーデータ可視化")
        print("="*60)
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        fig.suptitle('あなたのテレメトリーデータ - モンツァ', fontsize=16, fontweight='bold')
        
        time = self.user_data['session_time']
        
        # グラフ 1: 速度
        axes[0].plot(time, self.user_data['speed_kph'], color='#1f77b4', linewidth=1.5)
        axes[0].set_title('速度 vs セッション時間', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('速度 (km/h)')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=self.user_data['speed_kph'].mean(), color='red', linestyle='--', alpha=0.5, label=f'平均: {self.user_data["speed_kph"].mean():.1f}')
        axes[0].legend()
        
        # グラフ 2: 油門/ブレーキ
        axes[1].plot(time, self.user_data['throttle'] * 100, label='油門', color='green', linewidth=1.5)
        axes[1].plot(time, self.user_data['brake'] * 100, label='ブレーキ', color='red', linewidth=1.5)
        axes[1].set_title('油門 vs ブレーキ入力', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('入力 (0-100%)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        # グラフ 3: ステアリング
        axes[2].plot(time, self.user_data['steering'], color='purple', linewidth=1.5)
        axes[2].set_title('ステアリング角度', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('ステアリング (-1 ~ +1)')
        axes[2].grid(True, alpha=0.3)
        
        # グラフ 4: RPM
        axes[3].plot(time, self.user_data['rpm'], color='orange', linewidth=1.5)
        axes[3].set_title('エンジン RPM', fontsize=12, fontweight='bold')
        axes[3].set_ylabel('RPM')
        axes[3].set_xlabel('セッション時間 (秒)')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = Path('analysis_results/your_telemetry_overview.png')
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ グラフ保存: {output_path}")
        plt.close()
    
    def visualize_comparison(self):
        """ユーザー vs 職業選手対比可視化"""
        print("\n" + "="*60)
        print(f"ステップ 4: 対比グラフ生成 (vs {self.pro_driver_name})")
        print("="*60)
        
        data_type = "[実数値]" if self.is_real_data else "[シミュレーション]"
        print(f"\n対比寛手: {data_type} {self.pro_driver_name}")
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        
        title = f'あなた vs {self.pro_driver_name} ({self.pro_driver_year}) - モンツァ'
        if not self.is_real_data:
            title += ' [シミュ]'
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        # 時間軸の正規化
        your_time = np.linspace(0, 1, len(self.user_data))
        pro_time = np.linspace(0, 1, len(self.pro_data))
        
        # グラフ 1: 速度対比
        axes[0].plot(your_time, self.user_data['speed_kph'], label='あなた', linewidth=2, color='#1f77b4')
        axes[0].plot(pro_time, self.pro_data['Speed'], label=f'{self.pro_driver_name}', linewidth=2, color='#ff7f0e', alpha=0.7)
        axes[0].set_title('速度対比', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('速度 (km/h)')
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)
        
        # グラフ 2: 油門対比
        axes[1].plot(your_time, self.user_data['throttle'] * 100, label='あなた', linewidth=2, color='#2ca02c')
        axes[1].plot(pro_time, self.pro_data['Throttle'] * 100, label=f'{self.pro_driver_name}', linewidth=2, color='#d62728', alpha=0.7)
        axes[1].set_title('油門入力対比', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('油門 (0-100%)')
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)
        
        # グラフ 3: ブレーキ対比
        axes[2].plot(your_time, self.user_data['brake'] * 100, label='あなた', linewidth=2, color='#9467bd')
        axes[2].plot(pro_time, self.pro_data['Brake'] * 100, label=f'{self.pro_driver_name}', linewidth=2, color='#8c564b', alpha=0.7)
        axes[2].set_title('ブレーキ入力対比', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('ブレーキ (0-100%)')
        axes[2].legend(loc='upper right')
        axes[2].grid(True, alpha=0.3)
        
        # グラフ 4: ステアリング対比
        axes[3].plot(your_time, self.user_data['steering'], label='あなた', linewidth=2, color='#e377c2')
        axes[3].plot(pro_time, self.pro_data['Steering'], label=f'{self.pro_driver_name}', linewidth=2, color='#7f7f7f', alpha=0.7)
        axes[3].set_title('ステアリング入力対比', fontsize=12, fontweight='bold')
        axes[3].set_ylabel('ステアリング角度')
        axes[3].set_xlabel('ラップ進捗 (0=開始, 1=終了)')
        axes[3].legend(loc='upper right')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = Path('analysis_results/you_vs_pro_comparison.png')
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ グラフ保存: {output_path}")
        plt.close()
    
    def analyze_statistics(self):
        """統計分析と相関性計算"""
        print("\n" + "="*60)
        print("ステップ 5: 統計分析")
        print("="*60)
        
        data_type = "[実数値]" if self.is_real_data else "[シミュ]"
        print(f"\n対比寛手: {data_type} {self.pro_driver_name}")
        
        # データの正規化（比較用）
        your_speed_norm = (self.user_data['speed_kph'] - self.user_data['speed_kph'].min()) / (self.user_data['speed_kph'].max() - self.user_data['speed_kph'].min())
        pro_speed_norm = (self.pro_data['Speed'] - self.pro_data['Speed'].min()) / (self.pro_data['Speed'].max() - self.pro_data['Speed'].min())
        
        print("\n【速度分析】")
        print(f"  あなたの最高速: {self.user_data['speed_kph'].max():.1f} km/h")
        print(f"  {self.pro_driver_name}の最高速: {self.pro_data['Speed'].max():.1f} km/h")
        print(f"  差異: {self.pro_data['Speed'].max() - self.user_data['speed_kph'].max():+.1f} km/h")
        
        print(f"\n  あなたの平均速: {self.user_data['speed_kph'].mean():.1f} km/h")
        print(f"  {self.pro_driver_name}の平均速: {self.pro_data['Speed'].mean():.1f} km/h")
        speed_diff_pct = (self.pro_data['Speed'].mean() - self.user_data['speed_kph'].mean()) / self.user_data['speed_kph'].mean() * 100
        print(f"  差畩: {speed_diff_pct:+.1f}%")
        
        print("\n【油門分析】")
        print(f"  あなたの平均油門: {self.user_data['throttle'].mean():.1%}")
        print(f"  {self.pro_driver_name}の平均油門: {self.pro_data['Throttle'].mean():.1%}")
        throttle_corr = self.user_data['throttle'].corr(self.pro_data['Throttle'].iloc[:len(self.user_data)])
        print(f"  同期度 (相関性): {throttle_corr:.3f}")
        
        print("\n【ブレーキ分析】")
        print(f"  あなたの平均ブレーキ: {self.user_data['brake'].mean():.1%}")
        print(f"  {self.pro_driver_name}の平均ブレーキ: {self.pro_data['Brake'].mean():.1%}")
        brake_corr = self.user_data['brake'].corr(self.pro_data['Brake'].iloc[:len(self.user_data)])
        print(f"  同期度 (相関性): {brake_corr:.3f}")
        
        print("\n【ステアリング分析】")
        print(f"  あなたの平均ステアリング: {self.user_data['steering'].mean():.3f}")
        print(f"  {self.pro_driver_name}の平均ステアリング: {self.pro_data['Steering'].mean():.3f}")
        steer_corr = self.user_data['steering'].corr(self.pro_data['Steering'].iloc[:len(self.user_data)])
        print(f"  精密度 (相関性): {steer_corr:.3f}")
        
        # 詳細な改善ポイント
        print("\n" + "="*60)
        print("改善ポイント")
        print("="*60)
        
        if self.pro_data['Speed'].mean() > self.user_data['speed_kph'].mean():
            print(f"\n⚠ 速度: {self.pro_driver_name}より{speed_diff_pct:.1f}%遅い")
            print(f"  → 油門のタイミングと踏み込み力度を改善しましょう")
        
        if abs(throttle_corr) < 0.7:
            print(f"\n⚠ 油門タイミング: 同期度が低い ({throttle_corr:.3f})")
            print(f"  → {self.pro_driver_name}は加速するタイミングが異なります")
        
        if abs(brake_corr) < 0.7:
            print(f"\n⚠ ブレーキタイミング: 同期度が低い ({brake_corr:.3f})")
            print(f"  → {self.pro_driver_name}の減速ポイントをもっと早く始めましょう")
        
        print("\n" + "="*60)
    
    def run_full_analysis(self):
        """フル分析実行"""
        print("\n" + "🏁"*20)
        print(f"\nPhase 1分析スタート - あなた vs {self.pro_driver_name} ({self.pro_driver_year})")
        print("\n" + "🏁"*20)
        
        # ステップ実行
        self.load_user_data()
        self.extract_pro_data()
        self.visualize_user_data()
        self.visualize_comparison()
        self.analyze_statistics()
        
        print("\n" + "="*60)
        print("✓ Phase 1分析完了！")
        print("="*60)
        print("\n生成されたファイル:")
        print("  1. analysis_results/your_telemetry_overview.png")
        print("  2. analysis_results/you_vs_pro_comparison.png")
        
        data_label = "[実数値]" if self.is_real_data else "[シミュ]" 
        print(f"\n対比寛手: {data_label} {self.pro_driver_name}")
        
        print("\n次のステップ: Phase 2 - コーナー別分析")
        print("="*60 + "\n")


if __name__ == "__main__":
    # ファイルパス設定
    data_file = "telemetry_data/telemetry_monza_5laps_final_20251228_185844.csv"
    
    # 分析実行 - 2025 Max Verstappen との比較
    analyzer = Phase1Analysis(
        data_file,
        pro_driver_name="Max Verstappen",
        pro_driver_year=2025
    )
    analyzer.run_full_analysis()

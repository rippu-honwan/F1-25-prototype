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
from datetime import datetime
import os

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


class Phase1分析:
    """Phase 1分析クラス"""
    
    def __init__(self, ユーザーCSVパス, 職業選手名="マックス・フェルスタッペン", 職業選手年号=2025):
        """初期化"""
        self.ユーザーデータ = None
        self.職業選手データ = None
        self.CSVパス = ユーザーCSVパス
        self.職業選手名 = 職業選手名
        self.職業選手年号 = 職業選手年号
        self.実数値フラグ = False
        self.取得ドライバー情報 = {}
        
    def ユーザーデータ読み込み(self):
        """ユーザーテレメトリーデータ読み込み"""
        print("\n" + "="*70)
        print("ステップ 1️⃣  : ユーザーデータ読み込み")
        print("="*70)
        
        self.ユーザーデータ = pd.read_csv(self.CSVパス)
        print(f"✓ データ読み込み完了: {len(self.ユーザーデータ)} 行")
        print(f"✓ カラム: {list(self.ユーザーデータ.columns)}")
        
        print(f"\n✓ セッション時間: {self.ユーザーデータ['session_time'].min():.1f}秒 ～ {self.ユーザーデータ['session_time'].max():.1f}秒")
        print(f"✓ 走行時間: {(self.ユーザーデータ['session_time'].max() - self.ユーザーデータ['session_time'].min()):.1f}秒")
        
        # ✅ CSV形式の正規化: throttle/brake を 0-255 から 0-1 に変換
        self.ユーザーデータ['throttle'] = self.ユーザーデータ['throttle'] / 255
        self.ユーザーデータ['brake'] = self.ユーザーデータ['brake'] / 255
        
        # 基本統計
        print(f"\n【基本統計情報】")
        print(f"  最高速: {self.ユーザーデータ['speed_kph'].max():.1f} km/h")
        print(f"  平均速: {self.ユーザーデータ['speed_kph'].mean():.1f} km/h")
        print(f"  最低速: {self.ユーザーデータ['speed_kph'].min():.1f} km/h")
        
        return self.ユーザーデータ
    
    def 職業選手データ抽出(self):
        """FastF1から職業選手（2025 Max Verstappen）データ抽出"""
        print("\n" + "="*70)
        print(f"ステップ 2️⃣  : {self.職業選手名} ({self.職業選手年号}年) データ抽出")
        print("="*70)
        
        try:
            import fastf1
            print(f"✓ FastF1 ライブラリ読み込み成功")
            print(f"✓ セッション読み込み中...")
            
            # 2025年のレースデータを取得（Abu Dhabi最終戦）
            try:
                print(f"\n  📍 試行 1: {self.職業選手年号}年 アブダビGP 最終戦 を取得中...")
                session = fastf1.get_session(self.職業選手年号, 'Abu Dhabi', 'R')
                session.load()
                gp_name = "Abu Dhabi 最終戦"
                print(f"  ✓ 成功: {self.職業選手年号}年 {gp_name} 読み込み完了")
            except:
                print(f"  ✗ Abu Dhabi が失敗。フォールバック中...")
                print(f"  📍 試行 2: {self.職業選手年号}年 カタールGP を取得中...")
                session = fastf1.get_session(self.職業選手年号, 'Qatar', 'R')
                session.load()
                gp_name = "Qatar"
                print(f"  ✓ 成功: {self.職業選手年号}年 {gp_name} 読み込み完了")
            
            # Max Verstappen (VER) のデータを検索
            print(f"\n✓ セッション内のドライバー一覧を取得中...")
            all_drivers = session.laps['Driver'].unique()
            print(f"  参加ドライバー数: {len(all_drivers)} 人")
            print(f"  ドライバー: {', '.join(sorted(all_drivers))}")
            
            # VER（マックス・フェルスタッペン）を検索
            driver_laps = session.laps[session.laps['Driver'] == 'VER']
            
            if len(driver_laps) == 0:
                print(f"\n✗ エラー: {self.職業選手名} (VER) のデータが見つかりません")
                print("✓ デモ用データを生成します...")
                self.実数値フラグ = False
                self.職業選手データ = self._デモ用データ生成()
                return self.職業選手データ
            
            # 最速ラップを取得
            print(f"\n✓ {self.職業選手名} (VER) のラップデータを検出しました")
            print(f"  総ラップ数: {len(driver_laps)} ラップ")
            
            fastest_lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]
            print(f"\n✓✓✓ ドライバー確認: {fastest_lap['Driver']} = {self.職業選手名}")
            print(f"✓✓✓ 最速ラップ時間: {fastest_lap['LapTime']}")
            print(f"✓✓✓ ラップ番号: {fastest_lap['LapNumber']}")
            
            # テレメトリー抽出
            self.職業選手データ = fastest_lap.get_telemetry()
            print(f"\n✓ テレメトリーデータ抽出成功")
            print(f"  データポイント数: {len(self.職業選手データ)} 個")
            print(f"  テレメトリー項目: {list(self.職業選手データ.columns)[:8]}... 他")
            
            # データ正規化 (FastF1が提供する形式に依存)
            if 'Speed' in self.職業選手データ.columns:
                self.職業選手データ['Speed'] = self.職業選手データ['Speed'].astype(float)
                print(f"  速度範囲: {self.職業選手データ['Speed'].min():.1f} ～ {self.職業選手データ['Speed'].max():.1f} km/h")
            
            if 'Throttle' in self.職業選手データ.columns:
                self.職業選手データ['Throttle'] = self.職業選手データ['Throttle'].astype(float) / 100  # 0-100 -> 0-1
            
            if 'Brake' in self.職業選手データ.columns:
                self.職業選手データ['Brake'] = self.職業選手データ['Brake'].astype(float) / 100  # 0-100 -> 0-1
            
            # ドライバー情報を保存（証明用）
            self.取得ドライバー情報 = {
                'ドライバーコード': 'VER',
                'ドライバー名': fastest_lap['Driver'],
                'チーム': fastest_lap.get('Team', '不明'),
                'グランプリ': gp_name,
                '年号': self.職業選手年号,
                '最速ラップ': str(fastest_lap['LapTime']),
                'データ取得時刻': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'テレメトリーポイント': len(self.職業選手データ)
            }
            
            self.実数値フラグ = True
            print(f"\n✓✓✓ 実数値データの取得に成功しました！✓✓✓")
            return self.職業選手データ
            
        except Exception as e:
            print(f"\n✗ FastF1エラー: {e}")
            print("✓ デモ用データを生成します...")
            self.実数値フラグ = False
            self.職業選手データ = self._デモ用データ生成()
            return self.職業選手データ
    
    def _デモ用データ生成(self):
        """デモ用職業選手データ生成（FastF1が使えない場合）"""
        n = len(self.ユーザーデータ)
        
        # ユーザーデータより若干高いパフォーマンスのデータ生成
        demo_data = pd.DataFrame({
            'Time': np.linspace(0, 120, n),
            'Speed': self.ユーザーデータ['speed_kph'].values * 1.08 + np.random.normal(0, 2, n),
            'Throttle': np.where(
                self.ユーザーデータ['speed_kph'].values < self.ユーザーデータ['speed_kph'].mean(),
                self.ユーザーデータ['throttle'].values * 0.85,
                self.ユーザーデータ['throttle'].values
            ),
            'Brake': np.where(
                self.ユーザーデータ['speed_kph'].values > self.ユーザーデータ['speed_kph'].mean() * 0.9,
                self.ユーザーデータ['brake'].values * 1.15,
                self.ユーザーデータ['brake'].values
            ),
            'Steering': self.ユーザーデータ['steering'].values * 0.92,
        })
        
        # 負の値をクリップ
        demo_data['Throttle'] = demo_data['Throttle'].clip(0, 1)
        demo_data['Brake'] = demo_data['Brake'].clip(0, 1)
        demo_data['Steering'] = demo_data['Steering'].clip(-1, 1)
        
        print(f"✓ デモデータ生成完了: {len(demo_data)} データポイント")
        return demo_data
    
    def ユーザーデータ可視化(self):
        """ユーザーテレメトリーデータ可視化"""
        print("\n" + "="*70)
        print("ステップ 3️⃣  : ユーザーデータ可視化")
        print("="*70)
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        fig.suptitle('あなたのテレメトリーデータ - モンツァ', fontsize=16, fontweight='bold')
        
        time = self.ユーザーデータ['session_time']
        
        # グラフ 1: 速度
        axes[0].plot(time, self.ユーザーデータ['speed_kph'], color='#1f77b4', linewidth=1.5)
        axes[0].set_title('速度 vs セッション時間', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('速度 (km/h)')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=self.ユーザーデータ['speed_kph'].mean(), color='red', linestyle='--', alpha=0.5, label=f'平均: {self.ユーザーデータ["speed_kph"].mean():.1f}')
        axes[0].legend()
        
        # グラフ 2: 油門/ブレーキ
        axes[1].plot(time, self.ユーザーデータ['throttle'] * 100, label='油門', color='green', linewidth=1.5)
        axes[1].plot(time, self.ユーザーデータ['brake'] * 100, label='ブレーキ', color='red', linewidth=1.5)
        axes[1].set_title('油門 vs ブレーキ入力', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('入力 (0-100%)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        # グラフ 3: ステアリング
        axes[2].plot(time, self.ユーザーデータ['steering'], color='purple', linewidth=1.5)
        axes[2].set_title('ステアリング角度', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('ステアリング (-1 ～ +1)')
        axes[2].grid(True, alpha=0.3)
        
        # グラフ 4: RPM
        axes[3].plot(time, self.ユーザーデータ['rpm'], color='orange', linewidth=1.5)
        axes[3].set_title('エンジン RPM', fontsize=12, fontweight='bold')
        axes[3].set_ylabel('RPM')
        axes[3].set_xlabel('セッション時間 (秒)')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = Path('analysis_results/your_telemetry_overview.png')
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ グラフ保存: {output_path}")
        print(f"✓ ファイルサイズ: {os.path.getsize(output_path) / 1024:.1f} KB")
        plt.close()
    
    def 職業選手対比可視化(self):
        """ユーザー vs 職業選手対比可視化"""
        print("\n" + "="*70)
        print(f"ステップ 4️⃣  : 対比グラフ生成 (vs {self.職業選手名})")
        print("="*70)
        
        data_type = "【実数値】" if self.実数値フラグ else "【シミュレーション】"
        print(f"\n対比対象: {data_type} {self.職業選手名}")
        
        # 安全チェック: Speed をクリップして不正な値を防ぐ
        speed_data = self.職業選手データ['Speed'].values.clip(0, 400)
        throttle_data = self.職業選手データ['Throttle'].values.clip(0, 1)
        brake_data = self.職業選手データ['Brake'].values.clip(0, 1)
        steering_data = self.職業選手データ['Steering'].values.clip(-1, 1)
        
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        
        title = f'あなた vs {self.職業選手名} ({self.職業選手年号}年) - モンツァ'
        if not self.実数値フラグ:
            title += ' 【シミュ】'
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        # 時間軸の正規化
        your_time = np.linspace(0, 1, len(self.ユーザーデータ))
        pro_time = np.linspace(0, 1, len(speed_data))
        
        # グラフ 1: 速度対比
        axes[0].plot(your_time, self.ユーザーデータ['speed_kph'], label='あなた', linewidth=2, color='#1f77b4')
        axes[0].plot(pro_time, speed_data, label=f'{self.職業選手名}', linewidth=2, color='#ff7f0e', alpha=0.7)
        axes[0].set_title('速度対比', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('速度 (km/h)')
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)
        
        # グラフ 2: 油門対比
        axes[1].plot(your_time, self.ユーザーデータ['throttle'] * 100, label='あなた', linewidth=2, color='#2ca02c')
        axes[1].plot(pro_time, throttle_data * 100, label=f'{self.職業選手名}', linewidth=2, color='#d62728', alpha=0.7)
        axes[1].set_title('油門入力対比', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('油門 (0-100%)')
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)
        
        # グラフ 3: ブレーキ対比
        axes[2].plot(your_time, self.ユーザーデータ['brake'] * 100, label='あなた', linewidth=2, color='#9467bd')
        axes[2].plot(pro_time, brake_data * 100, label=f'{self.職業選手名}', linewidth=2, color='#8c564b', alpha=0.7)
        axes[2].set_title('ブレーキ入力対比', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('ブレーキ (0-100%)')
        axes[2].legend(loc='upper right')
        axes[2].grid(True, alpha=0.3)
        
        # グラフ 4: ステアリング対比
        axes[3].plot(your_time, self.ユーザーデータ['steering'], label='あなた', linewidth=2, color='#e377c2')
        axes[3].plot(pro_time, steering_data, label=f'{self.職業選手名}', linewidth=2, color='#7f7f7f', alpha=0.7)
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
        print(f"✓ ファイルサイズ: {os.path.getsize(output_path) / 1024:.1f} KB")
        plt.close()
    
    def 統計分析(self):
        """統計分析と相関性計算"""
        print("\n" + "="*70)
        print("ステップ 5️⃣  : 統計分析")
        print("="*70)
        
        data_type = "【実数値】" if self.実数値フラグ else "【シミュ】"
        print(f"\n対比対象: {data_type} {self.職業選手名}")
        
        # 取得したドライバー情報を表示（証明）
        if self.取得ドライバー情報:
            print("\n" + "="*70)
            print("✓✓✓ データ取得情報の確認 ✓✓✓")
            print("="*70)
            for key, value in self.取得ドライバー情報.items():
                print(f"  {key}: {value}")
            print("="*70)
        
        # データの正規化（比較用）
        your_speed_norm = (self.ユーザーデータ['speed_kph'] - self.ユーザーデータ['speed_kph'].min()) / (self.ユーザーデータ['speed_kph'].max() - self.ユーザーデータ['speed_kph'].min())
        pro_speed_norm = (self.職業選手データ['Speed'] - self.職業選手データ['Speed'].min()) / (self.職業選手データ['Speed'].max() - self.職業選手データ['Speed'].min())
        
        print("\n【🏎️ 速度分析】")
        print(f"  あなたの最高速: {self.ユーザーデータ['speed_kph'].max():.1f} km/h")
        print(f"  {self.職業選手名}の最高速: {self.職業選手データ['Speed'].max():.1f} km/h")
        print(f"  差異: {self.職業選手データ['Speed'].max() - self.ユーザーデータ['speed_kph'].max():+.1f} km/h")
        
        print(f"\n  あなたの平均速: {self.ユーザーデータ['speed_kph'].mean():.1f} km/h")
        print(f"  {self.職業選手名}の平均速: {self.職業選手データ['Speed'].mean():.1f} km/h")
        speed_diff_pct = (self.職業選手データ['Speed'].mean() - self.ユーザーデータ['speed_kph'].mean()) / self.ユーザーデータ['speed_kph'].mean() * 100
        print(f"  差畩: {speed_diff_pct:+.1f}%")
        
        print("\n【⚙️ 油門分析】")
        print(f"  あなたの平均油門: {self.ユーザーデータ['throttle'].mean():.1%}")
        print(f"  {self.職業選手名}の平均油門: {self.職業選手データ['Throttle'].mean():.1%}")
        throttle_corr = self.ユーザーデータ['throttle'].corr(self.職業選手データ['Throttle'].iloc[:len(self.ユーザーデータ)])
        print(f"  同期度 (相関性): {throttle_corr:.3f}")
        
        print("\n【🛑 ブレーキ分析】")
        print(f"  あなたの平均ブレーキ: {self.ユーザーデータ['brake'].mean():.1%}")
        print(f"  {self.職業選手名}の平均ブレーキ: {self.職業選手データ['Brake'].mean():.1%}")
        brake_corr = self.ユーザーデータ['brake'].corr(self.職業選手データ['Brake'].iloc[:len(self.ユーザーデータ)])
        print(f"  同期度 (相関性): {brake_corr:.3f}")
        
        print("\n【🎯 ステアリング分析】")
        print(f"  あなたの平均ステアリング: {self.ユーザーデータ['steering'].mean():.3f}")
        print(f"  {self.職業選手名}の平均ステアリング: {self.職業選手データ['Steering'].mean():.3f}")
        steer_corr = self.ユーザーデータ['steering'].corr(self.職業選手データ['Steering'].iloc[:len(self.ユーザーデータ)])
        print(f"  精密度 (相関性): {steer_corr:.3f}")
        
        # 詳細な改善ポイント
        print("\n" + "="*70)
        print("🔧 改善ポイント")
        print("="*70)
        
        if self.職業選手データ['Speed'].mean() > self.ユーザーデータ['speed_kph'].mean():
            print(f"\n⚠️  速度: {self.職業選手名}より{speed_diff_pct:.1f}%遅い")
            print(f"  → 油門のタイミングと踏み込み力度を改善しましょう")
        
        if abs(throttle_corr) < 0.7:
            print(f"\n⚠️  油門タイミング: 同期度が低い ({throttle_corr:.3f})")
            print(f"  → {self.職業選手名}は加速するタイミングが異なります")
        
        if abs(brake_corr) < 0.7:
            print(f"\n⚠️  ブレーキタイミング: 同期度が低い ({brake_corr:.3f})")
            print(f"  → {self.職業選手名}の減速ポイントをもっと早く始めましょう")
        
        print("\n" + "="*70)
    
    def フル分析実行(self):
        """フル分析実行"""
        print("\n" + "🏁🏁🏁🏁🏁"*4)
        print(f"\nPhase 1分析スタート 🏎️")
        print(f"あなた vs {self.職業選手名} ({self.職業選手年号}年)")
        print("\n" + "🏁🏁🏁🏁🏁"*4)
        
        # ステップ実行
        self.ユーザーデータ読み込み()
        self.職業選手データ抽出()
        self.ユーザーデータ可視化()
        self.職業選手対比可視化()
        self.統計分析()
        
        print("\n" + "="*70)
        print("✓✓✓ Phase 1分析完了！ ✓✓✓")
        print("="*70)
        print("\n📊 生成されたファイル:")
        print("  1. analysis_results/your_telemetry_overview.png")
        print("  2. analysis_results/you_vs_pro_comparison.png")
        
        # ファイルサイズ確認
        try:
            f1_size = os.path.getsize('analysis_results/your_telemetry_overview.png') / 1024
            f2_size = os.path.getsize('analysis_results/you_vs_pro_comparison.png') / 1024
            print(f"\n📊 ファイル情報:")
            print(f"  1. {f1_size:.1f} KB")
            print(f"  2. {f2_size:.1f} KB")
        except:
            pass
        
        data_label = "【実数値】" if self.実数値フラグ else "【シミュ】" 
        print(f"\n対比対象: {data_label} {self.職業選手名}")
        
        print("\n📈 次のステップ: Phase 2 - コーナー別分析")
        print("="*70 + "\n")


if __name__ == "__main__":
    # ファイルパス設定
    data_file = "telemetry_data/telemetry_monza_5laps_final_20251228_185844.csv"
    
    # 分析実行 - 2025 Max Verstappen との比較
    analyzer = Phase1分析(
        data_file,
        職業選手名="マックス・フェルスタッペン (Max Verstappen)",
        職業選手年号=2025
    )
    analyzer.フル分析実行()

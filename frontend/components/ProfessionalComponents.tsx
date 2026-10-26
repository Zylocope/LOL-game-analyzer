import React from 'react';
import { Zap, TrendingUp, Shield, Swords } from 'lucide-react';

/**
 * StatCard - Professional stat display component
 * Used for displaying team stats, champion stats, and metrics
 */
interface StatCardProps {
  icon?: React.ReactNode;
  label: string;
  value: string | number;
  unit?: string;
  change?: number; // percentage change
  variant?: 'default' | 'success' | 'danger' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  unit,
  change,
  variant = 'default',
  size = 'md',
  onClick,
}) => {
  const sizeClasses = {
    sm: 'p-3 gap-2',
    md: 'p-4 gap-3',
    lg: 'p-6 gap-4',
  };

  const variantClasses = {
    default: 'bg-gray-800/40 border-gray-700/50 text-gray-100',
    success: 'bg-green-900/20 border-green-700/50 text-green-100',
    danger: 'bg-red-900/20 border-red-700/50 text-red-100',
    warning: 'bg-yellow-900/20 border-yellow-700/50 text-yellow-100',
  };

  const iconColor = {
    default: 'text-gray-500',
    success: 'text-green-500',
    danger: 'text-red-500',
    warning: 'text-yellow-500',
  };

  return (
    <div
      onClick={onClick}
      className={`
        card-elevated flex flex-col
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        hover:bg-opacity-50 transition-all duration-200
        ${onClick ? 'cursor-pointer' : ''}
      `}
    >
      <div className="flex items-start justify-between">
        {icon && (
          <div className={`${iconColor[variant]}`}>
            {icon}
          </div>
        )}
        {change !== undefined && (
          <div className={`text-caption font-bold ${
            change > 0 ? 'text-green-400' : change < 0 ? 'text-red-400' : 'text-gray-400'
          }`}>
            {change > 0 ? '+' : ''}{change}%
          </div>
        )}
      </div>
      <div>
        <div className="text-caption text-gray-400 mb-1">
          {label}
        </div>
        <div className="text-heading-2 font-bold">
          {value}
          {unit && <span className="text-body-sm text-gray-500 ml-1">{unit}</span>}
        </div>
      </div>
    </div>
  );
};

/**
 * ComparisonCard - Side-by-side comparison component
 * Displays two values with better/worse indication
 */
interface ComparisonCardProps {
  label: string;
  blueValue: string | number;
  redValue: string | number;
  unit?: string;
  blueWins?: boolean; // if true, blue value is better
}

export const ComparisonCard: React.FC<ComparisonCardProps> = ({
  label,
  blueValue,
  redValue,
  unit,
  blueWins,
}) => {
  const getValue = (value: string | number, team: 'blue' | 'red') => (
    <div className={`
      text-center flex-1
      ${blueWins === (team === 'blue') ? 'text-green-400 font-bold' : 'text-gray-400'}
    `}>
      {value}
      {unit && <div className="text-caption text-gray-500">{unit}</div>}
    </div>
  );

  return (
    <div className="card-elevated p-4">
      <div className="text-caption text-gray-400 mb-3">{label}</div>
      <div className="flex items-center justify-between gap-3">
        {getValue(blueValue, 'blue')}
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-700 to-transparent" />
        {getValue(redValue, 'red')}
      </div>
    </div>
  );
};

/**
 * WinrateIndicator - Visual representation of win rate
 * Shows percentage in a professional gauge style
 */
interface WinrateIndicatorProps {
  winrate: number; // 0-100
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const WinrateIndicator: React.FC<WinrateIndicatorProps> = ({
  winrate,
  size = 'md',
  showLabel = true,
}) => {
  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-20 h-20',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-body-sm',
    lg: 'text-body-lg',
  };

  // Determine color based on winrate
  const getColor = (wr: number) => {
    if (wr >= 55) return 'text-green-400';
    if (wr >= 50) return 'text-blue-400';
    if (wr >= 45) return 'text-yellow-400';
    return 'text-red-400';
  };

  const strokeColor = {
    'text-green-400': '#4ADE80',
    'text-blue-400': '#60A5FA',
    'text-yellow-400': '#FACC15',
    'text-red-400': '#F87171',
  };

  const circumference = 2 * Math.PI * 30;
  const strokeDashoffset = circumference - (winrate / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        className={`${sizeClasses[size]} transform -rotate-90`}
        viewBox="0 0 64 64"
      >
        {/* Background circle */}
        <circle
          cx="32"
          cy="32"
          r="30"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx="32"
          cy="32"
          r="30"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          className={`${getColor(winrate)} transition-all duration-500`}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: strokeDashoffset,
          }}
        />
      </svg>
      {showLabel && (
        <div className={`text-center ${textSizeClasses[size]}`}>
          <div className={`font-bold ${getColor(winrate)}`}>{winrate}%</div>
          <div className="text-gray-500 text-caption">Winrate</div>
        </div>
      )}
    </div>
  );
};

/**
 * MatchupBadge - Shows champion matchup information
 * Displays advantage/disadvantage with visual indicators
 */
interface MatchupBadgeProps {
  champion: string;
  advantage?: 'favorable' | 'even' | 'unfavorable';
  winrate?: number;
  pickrate?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const MatchupBadge: React.FC<MatchupBadgeProps> = ({
  champion,
  advantage = 'even',
  winrate,
  pickrate,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  const advantageClasses = {
    favorable: 'bg-green-900/30 border-green-700 text-green-200',
    even: 'bg-gray-800/30 border-gray-700 text-gray-200',
    unfavorable: 'bg-red-900/30 border-red-700 text-red-200',
  };

  const advantageIcons = {
    favorable: <TrendingUp size={14} />,
    even: <Swords size={14} />,
    unfavorable: <TrendingUp size={14} className="rotate-180" />,
  };

  return (
    <div className={`
      card-elevated flex items-center gap-2 border
      ${sizeClasses[size]}
      ${advantageClasses[advantage]}
    `}>
      {advantageIcons[advantage]}
      <div>
        <div className="font-bold">{champion}</div>
        {(winrate !== undefined || pickrate !== undefined) && (
          <div className="text-caption opacity-75">
            {winrate && `${winrate}% WR`}
            {winrate && pickrate && ' · '}
            {pickrate && `${pickrate}% PR`}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * PredictionBanner - Large banner for match prediction result
 * Shows win prediction with confidence
 */
interface PredictionBannerProps {
  blueWinChance: number; // 0-100
  confidence: number; // 0-100
  blueTeam: string;
  redTeam: string;
}

export const PredictionBanner: React.FC<PredictionBannerProps> = ({
  blueWinChance,
  confidence,
  blueTeam,
  redTeam,
}) => {
  const winner = blueWinChance > 50 ? 'blue' : blueWinChance < 50 ? 'red' : 'even';
  const redWinChance = 100 - blueWinChance;

  return (
    <div className="relative overflow-hidden rounded-xl border border-gray-700 bg-gray-900/50">
      {/* Gradient background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/50 to-red-900/50" />
      </div>

      {/* Content */}
      <div className="relative p-6 z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="text-center flex-1">
            <div className="text-heading-2 font-bold text-blue-400">{blueTeam}</div>
            <div className="text-display-1 font-black text-blue-400">{blueWinChance}%</div>
          </div>

          <div className="flex flex-col items-center gap-2 px-4">
            <div className="text-heading-3 font-bold text-gray-300">VS</div>
            <div className="text-caption text-gray-500">
              {confidence}% Confidence
            </div>
          </div>

          <div className="text-center flex-1">
            <div className="text-heading-2 font-bold text-red-400">{redTeam}</div>
            <div className="text-display-1 font-black text-red-400">{redWinChance}%</div>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-red-500 transition-all duration-500"
              style={{
                width: `${blueWinChance}%`,
              }}
            />
          </div>
        </div>

        {/* Confidence message */}
        <div className="mt-4 text-center">
          <div className="text-body-sm text-gray-400">
            {confidence >= 80 && '🎯 High Confidence Prediction'}
            {confidence >= 60 && confidence < 80 && '⚖️ Moderate Confidence'}
            {confidence < 60 && '⚠️ Low Confidence - Close Match'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default {
  StatCard,
  ComparisonCard,
  WinrateIndicator,
  MatchupBadge,
  PredictionBanner,
};

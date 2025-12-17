import React from 'react';
import { AnalysisResult } from '../types';
import { TrendingUp, AlertTriangle, CheckCircle2, Trophy, BrainCircuit, Target, Zap, Shield } from 'lucide-react';

interface AnalysisPanelProps {
  analysis: AnalysisResult | null;
  loading: boolean;
  blueName: string;
  redName: string;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ analysis, loading, blueName, redName }) => {
  // Loading State
  if (loading) {
    return (
      <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-center p-8 relative overflow-hidden rounded-2xl bg-gray-900/20 border border-gray-800">
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        <div className="relative z-10 flex flex-col items-center">
          <div className="w-24 h-24 mb-6 relative">
            <div className="absolute inset-0 rounded-full border-4 border-gray-800"></div>
            <div className="absolute inset-0 rounded-full border-4 border-t-esport-gold border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
            <div className="absolute inset-4 rounded-full border-2 border-esport-gold/30 animate-pulse"></div>
            <BrainCircuit className="absolute inset-0 m-auto text-esport-gold animate-pulse" size={32} />
          </div>
          <h3 className="text-3xl font-display font-bold text-white tracking-[0.2em] mb-2 animate-pulse">
            NEURAL SCANNING
          </h3>
          <p className="text-esport-gold/80 text-sm tracking-widest uppercase">
            Processing Match Variables...
          </p>
        </div>
      </div>
    );
  }

  // Empty State
  if (!analysis) {
    return (
      <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-center p-8 rounded-2xl bg-gray-900/20 border-2 border-dashed border-gray-800/50 group hover:border-gray-700 transition-all">
        <div className="w-20 h-20 bg-gray-800/50 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
          <TrendingUp size={32} className="text-gray-600 group-hover:text-esport-gold transition-colors" />
        </div>
        <h3 className="font-display text-2xl font-bold text-gray-300 mb-2">AWAITING DATA</h3>
        <p className="text-gray-500 text-sm max-w-xs mx-auto">
          Complete the draft phase and initialize the prediction engine to generate insights.
        </p>
      </div>
    );
  }

  // Active Analysis State
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-1 h-6 bg-esport-gold rounded-full"></div>
        <h2 className="text-xl font-display font-bold text-white tracking-widest uppercase">
          Match <span className="text-esport-gold">Prediction</span>
        </h2>
      </div>

      {/* Win Probability Card */}
      <div className="relative p-6 rounded-2xl bg-gray-900/40 border border-gray-800 overflow-hidden shadow-xl">
        {/* Background Gradients */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-esport-red/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-esport-blue/5 rounded-full blur-3xl -ml-16 -mb-16 pointer-events-none"></div>

        <div className="relative z-10">
          <div className="flex justify-between items-center mb-6">
            {/* Blue Side Stats */}
            <div className="text-left">
              <div className="flex items-center gap-2 mb-1">
                 <Shield size={14} className="text-esport-blue" />
                 <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{blueName}</span>
              </div>
              <div className="text-5xl font-display font-bold text-white drop-shadow-[0_0_10px_rgba(0,168,255,0.5)]">
                {analysis.winProbability.blue}<span className="text-2xl text-gray-500">%</span>
              </div>
            </div>

            {/* VS Badge */}
            <div className="flex flex-col items-center">
               <span className="text-xs text-gray-600 font-bold uppercase tracking-widest mb-1">Win Rate</span>
               <div className="w-px h-8 bg-gray-700"></div>
            </div>

            {/* Red Side Stats */}
            <div className="text-right">
              <div className="flex items-center gap-2 mb-1 justify-end">
                 <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{redName}</span>
                 <Shield size={14} className="text-esport-red" />
              </div>
              <div className="text-5xl font-display font-bold text-white drop-shadow-[0_0_10px_rgba(255,51,51,0.5)]">
                {analysis.winProbability.red}<span className="text-2xl text-gray-500">%</span>
              </div>
            </div>
          </div>

          {/* Probability Bar */}
          <div className="h-3 bg-gray-800 rounded-full overflow-hidden flex relative shadow-inner">
             {/* Middle Marker */}
             <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/20 z-20 -translate-x-1/2"></div>
             
             <div 
               className="h-full bg-gradient-to-r from-blue-900 to-esport-blue shadow-[0_0_20px_rgba(0,168,255,0.6)]" 
               style={{ width: `${analysis.winProbability.blue}%` }}
             />
             <div 
               className="h-full bg-gradient-to-l from-red-900 to-esport-red shadow-[0_0_20px_rgba(255,51,51,0.6)]" 
               style={{ width: `${analysis.winProbability.red}%` }}
             />
          </div>
        </div>
      </div>

      {/* AI Insight Module */}
      <div className="rounded-2xl bg-gray-900/20 border border-esport-gold/30 p-5 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-esport-gold"></div>
        <div className="absolute -right-4 -top-4 text-esport-gold/5 group-hover:text-esport-gold/10 transition-colors">
           <BrainCircuit size={80} />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-esport-gold" />
            <h3 className="text-esport-gold font-bold text-xs uppercase tracking-widest">Tactical Analysis</h3>
          </div>
          <p className="text-gray-300 text-sm leading-relaxed font-medium">
            {analysis.reasoning}
          </p>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Key Factors */}
        <div className="bg-gray-900/20 rounded-2xl border border-gray-800 p-4 hover:border-gray-700 transition-colors">
           <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
             <AlertTriangle size={16} className="text-esport-accent" />
             <h4 className="text-gray-300 text-xs font-bold uppercase tracking-wider">Crucial Factors</h4>
           </div>
           <ul className="space-y-3">
             {analysis.keyFactors.map((factor, i) => (
               <li key={i} className="text-xs text-gray-400 flex gap-2 items-start">
                 <span className="text-esport-accent mt-0.5">►</span> 
                 <span className="leading-tight">{factor}</span>
               </li>
             ))}
           </ul>
        </div>

        {/* Win Conditions */}
        <div className="bg-gray-900/20 rounded-2xl border border-gray-800 p-4 hover:border-gray-700 transition-colors">
           <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
             <Target size={16} className="text-green-500" />
             <h4 className="text-gray-300 text-xs font-bold uppercase tracking-wider">Win Conditions</h4>
           </div>
           
           <div className="space-y-4">
              <div className="bg-blue-900/10 p-2 rounded border-l-2 border-esport-blue">
                <span className="text-[10px] text-esport-blue font-bold uppercase mb-1 block opacity-80">{blueName}</span>
                <ul className="space-y-1">
                  {analysis.winConditions.blue.map((wc, i) => (
                    <li key={i} className="text-[10px] text-gray-400 truncate flex items-center gap-1.5">
                       <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                       {wc}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-red-900/10 p-2 rounded border-l-2 border-esport-red">
                <span className="text-[10px] text-esport-red font-bold uppercase mb-1 block opacity-80">{redName}</span>
                <ul className="space-y-1">
                  {analysis.winConditions.red.map((wc, i) => (
                    <li key={i} className="text-[10px] text-gray-400 truncate flex items-center gap-1.5">
                       <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                       {wc}
                    </li>
                  ))}
                </ul>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
};
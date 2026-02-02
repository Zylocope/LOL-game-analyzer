import { Role } from '../types';

export interface PresetTeam {
  name: string;
  id: string;
  logo?: string;
  players: { role: Role; name: string }[];
}

export const PRESET_TEAMS: PresetTeam[] = [
  {
    name: "T1",
    id: "t1",
    logo: "t1.png",
    players: [
      { role: 'Top', name: 'Zeus' },
      { role: 'Jungle', name: 'Oner' },
      { role: 'Mid', name: 'Faker' },
      { role: 'Bot', name: 'Gumayusi' },
      { role: 'Support', name: 'Keria' }
    ]
  },
  {
    name: "Gen.G",
    id: "geng",
    logo: "gen_g.png",
    players: [
      { role: 'Top', name: 'Kiin' },
      { role: 'Jungle', name: 'Canyon' },
      { role: 'Mid', name: 'Chovy' },
      { role: 'Bot', name: 'Peyz' },
      { role: 'Support', name: 'Lehends' }
    ]
  },
  {
    name: "Hanwha Life Esports",
    id: "hle",
    logo: "hanwha_life_esports.png",
    players: [
      { role: 'Top', name: 'Doran' },
      { role: 'Jungle', name: 'Peanut' },
      { role: 'Mid', name: 'Zeka' },
      { role: 'Bot', name: 'Viper' },
      { role: 'Support', name: 'Delight' }
    ]
  },
  {
    name: "Dplus KIA",
    id: "dk",
    logo: "dplus_kia.png",
    players: [
      { role: 'Top', name: 'Kingen' },
      { role: 'Jungle', name: 'Lucid' },
      { role: 'Mid', name: 'ShowMaker' },
      { role: 'Bot', name: 'Aiming' },
      { role: 'Support', name: 'Kellin' }
    ]
  },
  {
    name: "KT Rolster",
    id: "kt",
    logo: "kt_rolster.png",
    players: [
      { role: 'Top', name: 'PerfecT' },
      { role: 'Jungle', name: 'Pyosik' },
      { role: 'Mid', name: 'Bdd' },
      { role: 'Bot', name: 'Deft' },
      { role: 'Support', name: 'BeryL' }
    ]
  },

  {
    name: "Bilibili Gaming",
    id: "blg",
    logo: "bilibili_gaming.png",
    players: [
      { role: 'Top', name: 'Bin' },
      { role: 'Jungle', name: 'Xun' },
      { role: 'Mid', name: 'Knight' },
      { role: 'Bot', name: 'Elk' },
      { role: 'Support', name: 'ON' }
    ]
  },
  {
    name: "Top Esports",
    id: "tes",
    logo: "top_esports.png",
    players: [
      { role: 'Top', name: '369' },
      { role: 'Jungle', name: 'Tian' },
      { role: 'Mid', name: 'Creme' },
      { role: 'Bot', name: 'JackeyLove' },
      { role: 'Support', name: 'Meiko' }
    ]
  },
  {
    name: "JD Gaming",
    id: "jdg",
    logo: "jd_gaming.png",
    players: [
      { role: 'Top', name: 'Sheer' },
      { role: 'Jungle', name: 'Kanavi' },
      { role: 'Mid', name: 'Yagao' },
      { role: 'Bot', name: 'Ruler' },
      { role: 'Support', name: 'Missing' }
    ]
  },
  {
    name: "LNG Esports",
    id: "lng",
    logo: "lngesports.png",
    players: [
      { role: 'Top', name: 'Zika' },
      { role: 'Jungle', name: 'Weiwei' },
      { role: 'Mid', name: 'Scout' },
      { role: 'Bot', name: 'GALA' },
      { role: 'Support', name: 'Hang' }
    ]
  },
  {
    name: "Weibo Gaming",
    id: "wbg",
    logo: "weibo_gaming.png",
    players: [
      { role: 'Top', name: 'Breathe' },
      { role: 'Jungle', name: 'Tarzan' },
      { role: 'Mid', name: 'Xiaohu' },
      { role: 'Bot', name: 'Light' },
      { role: 'Support', name: 'Crisp' }
    ]
  },

  {
    name: "G2 Esports",
    id: "g2",
    logo: "g2esports.png",
    players: [
      { role: 'Top', name: 'BrokenBlade' },
      { role: 'Jungle', name: 'Yike' },
      { role: 'Mid', name: 'Caps' },
      { role: 'Bot', name: 'Hans Sama' },
      { role: 'Support', name: 'Mikyx' }
    ]
  },
  {
    name: "Fnatic",
    id: "fnc",
    logo: "fnatic.png",
    players: [
      { role: 'Top', name: 'Oscarinin' },
      { role: 'Jungle', name: 'Razork' },
      { role: 'Mid', name: 'Humanoid' },
      { role: 'Bot', name: 'Noah' },
      { role: 'Support', name: 'Jun' }
    ]
  },
  {
    name: "Team BDS",
    id: "bds",
    logo: "team_bds.png",
    players: [
      { role: 'Top', name: 'Adam' },
      { role: 'Jungle', name: 'Sheo' },
      { role: 'Mid', name: 'nuc' },
      { role: 'Bot', name: 'Ice' },
      { role: 'Support', name: 'Labrov' }
    ]
  },
  {
    name: "MAD Lions KOI",
    id: "mdk",
    logo: "mad_lions.png",
    players: [
      { role: 'Top', name: 'Myrwn' },
      { role: 'Jungle', name: 'Elyoya' },
      { role: 'Mid', name: 'Fresskowy' },
      { role: 'Bot', name: 'Supa' },
      { role: 'Support', name: 'Alvaro' }
    ]
  },

  {
    name: "Team Liquid",
    id: "tl",
    logo: "team_liquid.png",
    players: [
      { role: 'Top', name: 'Impact' },
      { role: 'Jungle', name: 'UmTi' },
      { role: 'Mid', name: 'APA' },
      { role: 'Bot', name: 'Yeon' },
      { role: 'Support', name: 'CoreJJ' }
    ]
  },
  {
    name: "FlyQuest",
    id: "fly",
    logo: "flyquest.png",
    players: [
      { role: 'Top', name: 'Bwipo' },
      { role: 'Jungle', name: 'Inspired' },
      { role: 'Mid', name: 'Quad' },
      { role: 'Bot', name: 'Massu' },
      { role: 'Support', name: 'Busio' }
    ]
  },
  {
    name: "Cloud9",
    id: "c9",
    logo: "cloud9.png",
    players: [
      { role: 'Top', name: 'Thanatos' },
      { role: 'Jungle', name: 'Blaber' },
      { role: 'Mid', name: 'Jojopyun' },
      { role: 'Bot', name: 'Berserker' },
      { role: 'Support', name: 'Vulcan' }
    ]
  },
  {
    name: "100 Thieves",
    id: "100t",
    logo: "100thieves.png",
    players: [
      { role: 'Top', name: 'Sniper' },
      { role: 'Jungle', name: 'River' },
      { role: 'Mid', name: 'Quid' },
      { role: 'Bot', name: 'Tomo' },
      { role: 'Support', name: 'Eyla' }
    ]
  },

  {
    name: "PSG Talon",
    id: "psg",
    logo: "psg.png",
    players: [
      { role: 'Top', name: 'Azhi' },
      { role: 'Jungle', name: 'JunJia' },
      { role: 'Mid', name: 'Maple' },
      { role: 'Bot', name: 'Betty' },
      { role: 'Support', name: 'Woody' }
    ]
  },
  {
    name: "GAM Esports",
    id: "gam",
    logo: "gam.png",
    players: [
      { role: 'Top', name: 'Kiaya' },
      { role: 'Jungle', name: 'Levi' },
      { role: 'Mid', name: 'Emo' },
      { role: 'Bot', name: 'EasyLove' },
      { role: 'Support', name: 'Elio' }
    ]
  },
  
  {
    name: "T1 Esports Academy",
    id: "t1ca",
    logo: "t1.png",
    players: [
      { role: 'Top', name: 'Dal' },
      { role: 'Jungle', name: 'Guwon' },
      { role: 'Mid', name: 'Poby' },
      { role: 'Bot', name: 'Smash' },
      { role: 'Support', name: 'Rekkles' }
    ]
  },
  {
    name: "DK Challengers",
    id: "dkcl",
    logo: "dplus_kia.png",
    players: [
      { role: 'Top', name: 'Siwoo' },
      { role: 'Jungle', name: 'Sharvel' },
      { role: 'Mid', name: 'Saint' },
      { role: 'Bot', name: 'Wayne' },
      { role: 'Support', name: 'Moham' }
    ]
  },
  {
    name: "Karmine Corp Blue",
    id: "kcb",
    logo: "karmine_corp_blue.png",
    players: [
      { role: 'Top', name: 'Maynter' },
      { role: 'Jungle', name: '113' },
      { role: 'Mid', name: 'Abbedagge' },
      { role: 'Bot', name: 'Caliste' },
      { role: 'Support', name: 'Fleshy' }
    ]
  }
];
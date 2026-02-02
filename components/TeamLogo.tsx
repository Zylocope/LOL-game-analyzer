import React, { useState } from 'react';

export interface TeamLogoProps {
  team: {
    id: string;
    name: string;
    logo?: string;
  };
  className?: string;
}

export const TEAM_FILENAME_MAP: Record<string, string> = {
  "100 Thieves": "100thieves.png",
  "100t": "100thieves.png",
  "Anyone's Legend": "anyone_s_legend.png",
  "Ascension Gaming": "ascensiongaming.png",
  "Astralis": "astralis.png",
  "BNK FEARX": "bnkfearx.png",
  "BRION": "brion.png",
  "Bilibili Gaming": "bilibili_gaming.png",
  "Bombers": "bombers.png",
  "CTBC Flying Oyster": "ctbcflyingoyster.png",
  "Cloud9": "cloud9.png",
  "Clutch Gaming": "clutch_gaming.png",
  "Counter Logic Gaming": "counter_logic_gaming.png",
  "DN Freecs": "dnfreecs.png",
  "DRX": "drx.png",
  "DetonatioN FocusMe": "detonationfocusme.png",
  "Dignitas": "dignitas.png",
  "Dire Wolves": "dire_wolves.png",
  "Dominus Esports": "dominusesports.png",
  "Dplus KIA": "dplus_kia.png",
  "ES Sharks": "essharks.png",
  "EVOS Esports": "evosesports.png",
  "Echo Fox": "echo_fox.png",
  "EDward Gaming": "edward_gaming.png",
  "Ever8 Winners": "ever8winners.png",
  "Evil Geniuses": "evil_geniuses_na.png",
  "Excel Esports": "excelesports.png",
  "FC Schalke 04 Esports": "fcschalke04esports.png",
  "FURIA": "furia.png",
  "Fenerbahçe Esports": "fenerbaheesports.png",
  "Flash Wolves": "flash_wolves.png",
  "FlyQuest": "flyquest.png",
  "Fnatic": "fnatic.png",
  "FunPlus Phoenix": "funplus_phoenix.png",
  "G2 Esports": "g2esports.png",
  "GAM Esports": "gam_esports.png",
  "Gambit Esports": "gambitesports.png",
  "Gen.G": "gen_g.png",
  "GiantX": "giantx.png",
  "Golden Guardians": "golden_guardians.png",
  "Griffin": "griffin.png",
  "Hanwha Life Esports": "hanwha_life_esports.png",
  "INTZ": "intz.png",
  "Immortals": "immortals.png",
  "Invictus Gaming": "invictus_gaming.png",
  "Isurus": "isurus.png",
  "JD Gaming": "jd_gaming.png",
  "Jin Air Green Wings": "jinairgreenwings.png",
  "KOI": "koi.png",
  "KSV eSports": "ksvesports.png",
  "KT Rolster": "kt_rolster.png",
  "KaBuM! Esports": "kabumesports.png",
  "Kaos Latin Gamers": "kaoslatingamers.png",
  "Karmine Corp": "karmine_corp.png",
  "Karmine Corp Blue": "karmine_corp_blue.png",
  "Kingzone DragonX": "kingzonedragonx.png",
  "Kongdoo Monster": "kongdoomonster.png",
  "LGD Gaming": "lgd_gaming.png",
  "LNG Esports": "lngesports.png",
  "LOUD": "loud.png",
  "Liiv SANDBOX": "liivsandbox.png",
  "MAD Lions": "mad_lions.png",
  "MAD Lions KOI": "mad_lions.png",
  "MEGA": "mega.png",
  "MVP": "mvp.png",
  "Misfits Gaming": "misfits_gaming.png",
  "Movistar KOI": "movistarkoi.png",
  "Movistar R7": "movistarr7.png",
  "NRG Kia": "nrg.png",
  "NRG": "nrg.png",
  "Natus Vincere": "natus_vincere.png",
  "Ninjas in Pyjamas": "ninjas_in_pyjamas_cn.png",
  "Nongshim RedForce": "nongshim_redforce.png",
  "OKSavingsBank BRION": "oksavingsbankbrion.png",
  "Oh My God": "oh_my_god.png",
  "OpTic Gaming": "optic_gaming.png",
  "Origen": "origen.png",
  "Oxygen Esports": "oxygen_gaming.png",
  "PENTAGRAM": "pentagram.png",
  "Papara SuperMassive": "paparasupermassive.png",
  "Pentanet.GG": "pentanetgg.png",
  "Phong Vũ Buffalo": "phongvbuffalo.png",
  "ROX Tigers": "roxtigers.png",
  "Rare Atom": "rare_atom.png",
  "Rogue": "rogue.png",
  "Rogue Warriors": "rogue.png",
  "Royal Never Give Up": "royal_never_give_up.png",
  "SK Gaming": "sk_gaming.png",
  "SK Telecom T1": "sktelecomt1.png",
  "SeolHaeOne Prince": "seolhaeoneprince.png",
  "Seorabeol Gaming": "seorabeolgaming.png",
  "Shopify Rebellion": "shopifyrebellion.png",
  "SinoDragon Gaming": "sinodragongaming.png",
  "Snake Esports": "snakeesports.png",
  "Splyce": "splyce.png",
  "Suning": "suning.png",
  "T1": "t1.png",
  "TALON": "talon.png",
  "TSM": "tsm.png",
  "Team BDS": "team_bds.png",
  "Team BattleComics": "teambattlecomics.png",
  "Team Dynamics": "teamdynamics.png",
  "Team Heretics": "team_heretics.png",
  "Team Liquid": "team_liquid.png",
  "Team WE": "team_we.png",
  "Team Vitality": "teamvitality.png",
  "ThunderTalk Gaming": "thundertalkgaming.png",
  "Top Esports": "top_esports.png",
  "Ultra Prime": "ultraprime.png",
  "Unicorns of Love.CIS": "unicornsoflovecis.png",
  "VSG": "vsg.png",
  "Vega Squadron": "vegasquadron.png",
  "Vici Gaming": "vicigaming.png",
  "Victory Five": "victoryfive.png",
  "Weibo Gaming": "weibo_gaming.png",
  "bbq Olivers": "bbqolivers.png",
  "eStar": "estar.png",
  "inf": "inf.png",
  "paiN Gaming": "paingaming.png",
  "İstanbul Wildcats": "istanbulwildcats.png"
};

export const TeamLogo: React.FC<TeamLogoProps> = ({ team, className }) => {
  const mappedLogo = TEAM_FILENAME_MAP[team.name] || TEAM_FILENAME_MAP[team.id];

  const attempts = [
    ...(mappedLogo ? [`/teams/${mappedLogo}`] : []),
    ...(team.logo ? [`/teams/${team.logo}`] : []),
    `/teams/${team.id}.png`,
    `/teams/${team.name.toLowerCase().replace(/[\s.]+/g, '_')}.png`,
    `/teams/${team.name.toLowerCase().replace(/[^a-z0-9]/g, '')}.png`,
    `/teams/${team.name.replace(/ /g, '')}.png`,
    `/teams/${team.id}_logo.png`
  ];

  const [srcIndex, setSrcIndex] = useState(0);
  const [hasError, setHasError] = useState(false);

  const handleError = () => {
    if (srcIndex < attempts.length - 1) {
      setSrcIndex(prev => prev + 1);
    } else {
      setHasError(true);
    }
  };

  if (hasError) {
    return (
       <div className={`flex items-center justify-center bg-gray-800 rounded p-2 ${className}`}>
          <span className="text-[10px] text-gray-500 font-mono text-center leading-tight">
            {team.name.substring(0, 3).toUpperCase()}
          </span>
       </div>
    );
  }

  return (
    <img 
      src={attempts[srcIndex]} 
      alt={team.name}
      className={`object-contain ${className}`}
      onError={handleError}
    />
  );
};

"""
SkillSphere Dynamic SVG Badge Generator for GitHub Profile READMEs.
Generates responsive, retina-grade SVG graphics displaying a user's League tier,
streak days, total XP, and duel records with zero external image dependencies.
Supports multi-theme styling (dark, cyberpunk, light, gold) and styles (card, compact).
"""
import html


THEME_CONFIGS = {
    'dark': {
        'bg_start': '#0f172a', 'bg_end': '#1e1b4b', 'stroke': '#334155',
        'text_title': '#ffffff', 'text_sub': '#94a3b8', 'text_val': '#f8fafc', 'text_lbl': '#64748b'
    },
    'cyberpunk': {
        'bg_start': '#050510', 'bg_end': '#1a0b2e', 'stroke': '#ec4899',
        'text_title': '#38bdf8', 'text_sub': '#f472b6', 'text_val': '#a7f3d0', 'text_lbl': '#c084fc'
    },
    'light': {
        'bg_start': '#ffffff', 'bg_end': '#f1f5f9', 'stroke': '#cbd5e1',
        'text_title': '#0f172a', 'text_sub': '#475569', 'text_val': '#0f172a', 'text_lbl': '#64748b'
    },
    'gold': {
        'bg_start': '#1c1917', 'bg_end': '#292524', 'stroke': '#d97706',
        'text_title': '#fef08a', 'text_sub': '#fbbf24', 'text_val': '#fef08a', 'text_lbl': '#b45309'
    }
}


def generate_github_badge_svg(
    username: str,
    tier: str,
    total_xp: int,
    streak: int,
    duels_won: int = 0,
    theme: str = 'dark',
    style: str = 'card'
) -> str:
    """
    Returns high-definition SVG string formatted for embedding in GitHub READMEs.
    Supports themes: 'dark', 'cyberpunk', 'light', 'gold'
    Supports styles: 'card' (460x150), 'compact' (340x68)
    """
    safe_username = html.escape(username)
    safe_tier = html.escape(tier.upper() if tier else 'BRONZE')
    
    tier_colors = {
        'DIAMOND': {'start': '#06b6d4', 'end': '#3b82f6', 'border': '#60a5fa', 'label': 'Diamond League'},
        'GOLD': {'start': '#f59e0b', 'end': '#d97706', 'border': '#fbbf24', 'label': 'Gold League'},
        'SILVER': {'start': '#94a3b8', 'end': '#64748b', 'border': '#cbd5e1', 'label': 'Silver League'},
        'BRONZE': {'start': '#b45309', 'end': '#78350f', 'border': '#f59e0b', 'label': 'Bronze League'},
    }
    
    tier_info = tier_colors.get(safe_tier, tier_colors['BRONZE'])
    tier_label = tier_info['label']
    border_color = tier_info['border']
    grad_start = tier_info['start']
    grad_end = tier_info['end']
    
    t_cfg = THEME_CONFIGS.get(theme.lower(), THEME_CONFIGS['dark'])
    avatar_initial = safe_username[:1].upper() if safe_username else 'S'
    
    # 1. Compact Style (Shield Banner)
    if style.lower() == 'compact':
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="350" height="68" viewBox="0 0 350 68" fill="none" role="img" aria-label="SkillSphere Badge for {safe_username}">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="350" y2="68" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t_cfg['bg_start']}"/>
      <stop offset="100%" stop-color="{t_cfg['bg_end']}"/>
    </linearGradient>
    <linearGradient id="tierGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{grad_start}"/>
      <stop offset="100%" stop-color="{grad_end}"/>
    </linearGradient>
    <style>
      .t-user {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 13px; font-weight: 700; fill: {t_cfg['text_title']}; }}
      .t-meta {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; font-weight: 600; fill: {t_cfg['text_val']}; }}
      .t-tier {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 9px; font-weight: 700; fill: #ffffff; letter-spacing: 0.5px; }}
    </style>
  </defs>

  <rect x="1" y="1" width="348" height="66" rx="12" fill="url(#bgGrad)" stroke="{t_cfg['stroke']}" stroke-width="1.2"/>

  <!-- Avatar Circle -->
  <g transform="translate(14, 14)">
    <circle cx="20" cy="20" r="18" fill="url(#tierGrad)"/>
    <text x="20" y="25" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="13" font-weight="800" fill="#ffffff">{avatar_initial}</text>
  </g>

  <!-- User Info & Tier -->
  <g transform="translate(60, 20)">
    <text x="0" y="12" class="t-user">{safe_username}</text>
    <rect x="0" y="19" width="85" height="18" rx="9" fill="url(#tierGrad)"/>
    <text x="42" y="32" text-anchor="middle" class="t-tier">{tier_label}</text>
  </g>

  <!-- Compact Stat Chips -->
  <g transform="translate(200, 22)">
    <text x="0" y="12" class="t-meta">⚡ {total_xp:,} XP</text>
    <text x="0" y="29" class="t-meta" fill="#f97316">🔥 {streak}d streak</text>
    <text x="75" y="12" class="t-meta">⚔️ {duels_won} wins</text>
    <text x="75" y="29" font-family="-apple-system, sans-serif" font-size="9px" font-weight="600" fill="#10b981">✓ Verified</text>
  </g>
</svg>"""

    # 2. Card Style (Default Showcase Card)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="460" height="150" viewBox="0 0 460 150" fill="none" role="img" aria-label="SkillSphere Badge for {safe_username}">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="460" y2="150" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t_cfg['bg_start']}"/>
      <stop offset="100%" stop-color="{t_cfg['bg_end']}"/>
    </linearGradient>
    <linearGradient id="tierGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{grad_start}"/>
      <stop offset="100%" stop-color="{grad_end}"/>
    </linearGradient>
    <linearGradient id="fireGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f97316"/>
      <stop offset="100%" stop-color="#ef4444"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="{grad_start}" flood-opacity="0.35"/>
    </filter>
    <style>
      .text-title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 15px; font-weight: 700; fill: {t_cfg['text_title']}; }}
      .text-sub {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; font-weight: 500; fill: {t_cfg['text_sub']}; }}
      .text-val {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; font-weight: 700; fill: {t_cfg['text_val']}; }}
      .text-lbl {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 10px; font-weight: 600; fill: {t_cfg['text_lbl']}; text-transform: uppercase; letter-spacing: 0.5px; }}
      .tier-badge {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 10px; font-weight: 700; fill: #ffffff; letter-spacing: 0.5px; }}
    </style>
  </defs>

  <!-- Card Background -->
  <rect x="1" y="1" width="458" height="148" rx="14" fill="url(#bgGrad)" stroke="{t_cfg['stroke']}" stroke-width="1.5"/>
  <rect x="1" y="1" width="458" height="148" rx="14" fill="none" stroke="{border_color}" stroke-opacity="0.3" stroke-width="1.5"/>

  <!-- Brand Sphere Icon & User Header -->
  <g transform="translate(18, 16)">
    <!-- Avatar Circle with Initial -->
    <circle cx="20" cy="20" r="18" fill="url(#tierGrad)" filter="url(#glow)"/>
    <text x="20" y="25" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="14" font-weight="800" fill="#ffffff">{avatar_initial}</text>
    
    <!-- User Handle & Brand -->
    <text x="46" y="16" class="text-title">{safe_username}</text>
    <text x="46" y="32" class="text-sub">SkillSphere Verified Engineer</text>
  </g>

  <!-- League Tier Pill -->
  <g transform="translate(325, 18)">
    <rect x="0" y="0" width="118" height="24" rx="12" fill="url(#tierGrad)"/>
    <text x="59" y="16" text-anchor="middle" class="tier-badge">{tier_label}</text>
  </g>

  <!-- Divider Line -->
  <line x1="20" y1="64" x2="440" y2="64" stroke="{t_cfg['stroke']}" stroke-width="1" stroke-opacity="0.8"/>

  <!-- Stats Grid -->
  <!-- 1. Total XP -->
  <g transform="translate(26, 80)">
    <path d="M10 2L3 11h6l-2 9 8-10h-6l3-8z" fill="#facc15" transform="scale(0.85) translate(0, 0)"/>
    <text x="22" y="14" class="text-val">{total_xp:,} XP</text>
    <text x="22" y="28" class="text-lbl">Experience</text>
  </g>

  <!-- 2. Daily Streak -->
  <g transform="translate(142, 80)">
    <path d="M8.5 14.5A4.5 4.5 0 0 0 13 10c0-4-4.5-7.5-4.5-7.5S4 6 4 10a4.5 4.5 0 0 0 4.5 4.5z" fill="url(#fireGrad)" transform="scale(1.2) translate(0, -1)"/>
    <text x="22" y="14" class="text-val">{streak} Days</text>
    <text x="22" y="28" class="text-lbl">Streak</text>
  </g>

  <!-- 3. Skill Duels Won -->
  <g transform="translate(254, 80)">
    <path d="M14.5 2.5L12 5l-2.5-2.5L7 5l2.5 2.5L2 15l1 1 7.5-7.5 2.5 2.5 2.5-2.5-2.5-2.5 2.5-2.5-3-3.5z" fill="#a855f7" transform="scale(0.9) translate(0, 0)"/>
    <text x="22" y="14" class="text-val">{duels_won} Wins</text>
    <text x="22" y="28" class="text-lbl">1v1 Duels</text>
  </g>

  <!-- 4. Verified Platform Tag -->
  <g transform="translate(365, 80)">
    <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm-1 14.5l-4-4 1.41-1.41L11 13.67l6.59-6.59L19 8.5l-8 8z" fill="#10b981" transform="scale(0.85) translate(0, 0)"/>
    <text x="20" y="14" class="text-val">Verified</text>
    <text x="20" y="28" class="text-lbl">Platform</text>
  </g>

  <!-- Bottom Subtitle / Link Hint -->
  <text x="440" y="138" text-anchor="end" font-family="-apple-system, sans-serif" font-size="9" fill="{t_cfg['text_lbl']}">skillsphere-cyan.vercel.app</text>
</svg>"""
    return svg

"""Per-theme HTML fragment builders.

This is the module that makes the five themes genuinely different layouts
rather than palette swaps of the same markup. website_generator.py owns
*data* (WebsiteSchema); this module owns each theme's opinion about how
that data should be *structured* as HTML — a code block for developer-dark,
a magazine-style numbered case study for executive-black-gold, an
alternating feature section for modern-saas, and so on.

Every public render_*() function takes a TemplateTheme and dispatches to a
theme-specific private implementation. Adding a 6th theme means adding one
row to each dispatch table — the rest of the codebase (website_generator.py,
tests) only ever calls the public functions.
"""

from __future__ import annotations

import re

from src.website.render_utils import build_initials, cap_list, clean_tel, escape, fake_hex, slugify, truncate
from src.website.website_schema import (
    CareerPathContent,
    ContactContent,
    HeroContent,
    ProjectContent,
    SkillCategoryContent,
)
from src.website.website_schema import TemplateTheme as T

# ── Length guards (Milestone 6) ─────────────────────────────────────────────
# AI-generated project titles have no hard length limit coming out of the
# model. Left unguarded, a long one overflows a spotlight card, breaks a
# code-tab filename, or hides behind a horizontal scrollbar. These caps are
# deliberately generous — they exist to catch outliers, not to chop every
# normal title — and the full text is always preserved in a `title=`
# attribute so nothing is actually lost, just visually capped.
_TITLE_MAX = 70           # prose headings: cards, blockquotes, watermarks
_TITLE_MAX_NARROW = 34    # tight inline contexts: code tabs, filenames
_TECH_MAX = 6             # technologies shown per project before "+N more"
_SKILL_ITEMS_MAX = 10     # skills shown per category before "+N more"


def _truncated_heading(title: str, max_len: int = _TITLE_MAX) -> tuple[str, str]:
    """Return (display_text, title_attr) for a heading that needs a length
    guard — title_attr is empty when no truncation happened."""
    display = truncate(title, max_len)
    full = escape(title) if display != title else ""
    return escape(display), full

# ════════════════════════════════════════════════════════════════════════════
# MINIMAL WHITE / ORANGE — sidebar bio site (Linear / Vercel / Stripe Docs)
# ════════════════════════════════════════════════════════════════════════════


def _minimal_hero_extra(hero: HeroContent, contact: ContactContent) -> str:
    return ""  # the sidebar template already carries everything it needs


def _minimal_social(contact: ContactContent) -> str:
    links = []
    if contact.email:
        links.append(f'<a class="hero-social-link" href="mailto:{escape(contact.email)}">Email</a>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        links.append(f'<a class="hero-social-link" href="{escape(href)}" target="_blank" rel="noopener">LinkedIn</a>')
    if not links:
        return ""
    return '<div class="hero-social">' + "".join(links) + "</div>"


def _minimal_skills(categories: list[SkillCategoryContent]) -> str:
    if not categories:
        return '<span class="skill-badge">No skills listed</span>'
    groups = []
    for cat in categories:
        visible, overflow = cap_list(cat.items, _SKILL_ITEMS_MAX)
        badges = "\n        ".join(f'<span class="skill-badge">{escape(s)}</span>' for s in visible)
        if overflow:
            badges += f'\n        <span class="skill-badge skill-badge-more">+{overflow} more</span>'
        groups.append(
            f'<div class="skill-group">\n'
            f'  <span class="skill-group-label">{escape(cat.category)}</span>\n'
            f'  <div class="skill-group-items">\n    {badges}\n  </div>\n'
            f'</div>'
        )
    return "\n      ".join(groups)


def _minimal_tech_tags(technologies: list[str]) -> str:
    if not technologies:
        return ""
    visible, overflow = cap_list(technologies, _TECH_MAX)
    tags = "".join(f'<span class="tech-tag">{escape(t)}</span>' for t in visible)
    if overflow:
        tags += f'<span class="tech-tag tech-tag-more">+{overflow}</span>'
    return f'<div class="project-tech" aria-label="Technologies used">{tags}</div>'


def _minimal_project_links(item: ProjectContent) -> str:
    code = (
        f'<a class="project-link" href="{escape(item.github_url)}" target="_blank" rel="noopener">'
        f'<span class="project-link-icon" aria-hidden="true">&lt;/&gt;</span> Code</a>'
        if item.github_url else
        '<span class="project-link project-link-placeholder"><span class="project-link-icon" aria-hidden="true">&lt;/&gt;</span> Add GitHub link</span>'
    )
    demo = (
        f'<a class="project-link" href="{escape(item.demo_url)}" target="_blank" rel="noopener">'
        f'<span class="project-link-icon" aria-hidden="true">&#8599;</span> Live demo</a>'
        if item.demo_url else
        '<span class="project-link project-link-placeholder"><span class="project-link-icon" aria-hidden="true">&#8599;</span> Add live demo</span>'
    )
    return f'<div class="project-links">{code}{demo}</div>'


def _minimal_projects(items: list[ProjectContent]) -> str:
    if not items:
        return '<div class="project-card"><h3>No projects listed</h3></div>'
    spotlight, rest = items[0], items[1:]
    spot_text, spot_full = _truncated_heading(spotlight.title)
    spot_title_attr = f' title="{spot_full}"' if spot_full else ""
    spotlight_html = (
        f'<article class="project-card project-spotlight">\n'
        f'  <div class="spotlight-index" aria-hidden="true">{spotlight.index:02d}</div>\n'
        f'  <span class="spotlight-kicker">Featured Project</span>\n'
        f'  <h3{spot_title_attr}>{spot_text}</h3>\n'
        f'  <p class="project-problem">{escape(spotlight.problem)}</p>\n'
        f'  {_minimal_tech_tags(spotlight.technologies)}\n'
        f'  <p class="project-outcome"><strong>Outcome:</strong> {escape(spotlight.outcome)}</p>\n'
        f'  {_minimal_project_links(spotlight)}\n'
        f'</article>'
    )
    if not rest:
        return spotlight_html
    rows = []
    for item in rest:
        row_text, row_full = _truncated_heading(item.title)
        row_title_attr = f' title="{row_full}"' if row_full else ""
        rows.append(
            f'<div class="project-row">\n'
            f'  <span class="project-row-index" aria-hidden="true">{item.index:02d}</span>\n'
            f'  <div class="project-row-body">\n'
            f'    <h3{row_title_attr}>{row_text}</h3>\n'
            f'    <p class="project-problem">{escape(item.problem)}</p>\n'
            f'    {_minimal_tech_tags(item.technologies)}\n'
            f'    <p class="project-outcome"><strong>Outcome:</strong> {escape(item.outcome)}</p>\n'
            f'    {_minimal_project_links(item)}\n'
            f'  </div>\n'
            f'</div>'
        )
    return spotlight_html + '\n\n    <div class="project-list">\n      ' + "\n      ".join(rows) + "\n    </div>"


def _minimal_career(items: list[CareerPathContent]) -> str:
    if not items:
        return '<div class="career-card"><h3>No career paths listed</h3></div>'
    total = len(items)
    nodes = [
        f'<div class="timeline-item">\n'
        f'  <div class="timeline-marker" aria-hidden="true"><span class="timeline-index">{item.index:02d}</span></div>\n'
        f'  <div class="career-card timeline-content">\n'
        f'    <span class="timeline-kicker">Path {item.index:02d} / {total:02d}</span>\n'
        f'    <h3>{escape(item.title)}</h3>\n'
        f'  </div>\n'
        f'</div>'
        for item in items
    ]
    return '<div class="timeline">\n      ' + "\n      ".join(nodes) + "\n    </div>"


def _contact_row(label: str, value: str, href: str | None) -> str:
    value_html = escape(value)
    inner = f'<a class="contact-value" href="{escape(href)}">{value_html}</a>' if href else f'<span class="contact-value">{value_html}</span>'
    return f'<div class="contact-item">\n  <span class="contact-label">{escape(label)}</span>\n  {inner}\n</div>'


def _minimal_contact(contact: ContactContent) -> str:
    if not contact.has_contact_info:
        return '<p class="contact-fallback">No contact information provided.</p>'
    items = []
    if contact.email:
        items.append(_contact_row("Email", contact.email, f"mailto:{contact.email}"))
    if contact.phone:
        items.append(_contact_row("Phone", contact.phone, f"tel:{clean_tel(contact.phone)}"))
    if contact.location:
        items.append(_contact_row("Location", contact.location, None))
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        items.append(_contact_row("LinkedIn", contact.linkedin, href))
    return '<div class="contact-grid">\n      ' + "\n      ".join(items) + "\n    </div>"


# ════════════════════════════════════════════════════════════════════════════
# EXECUTIVE BLACK / GOLD — editorial, centered, serif (law-firm-partner energy)
# ════════════════════════════════════════════════════════════════════════════


def _executive_hero_extra(hero: HeroContent, contact: ContactContent) -> str:
    return ""


def _executive_social(contact: ContactContent) -> str:
    parts = []
    if contact.email:
        parts.append(f'<a href="mailto:{escape(contact.email)}">Email</a>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        parts.append(f'<a href="{escape(href)}" target="_blank" rel="noopener">LinkedIn</a>')
    if not parts:
        return ""
    return '<div class="exec-social">' + ' <span class="exec-social-sep">/</span> '.join(parts) + "</div>"


def _executive_skills(categories: list[SkillCategoryContent]) -> str:
    if not categories:
        return '<p class="exec-skills-empty">No skills listed.</p>'
    groups = []
    for cat in categories:
        visible, overflow = cap_list(cat.items, _SKILL_ITEMS_MAX)
        items_html = ' <span class="exec-dot">&middot;</span> '.join(escape(s) for s in visible)
        if overflow:
            items_html += f' <span class="exec-dot">&middot;</span> <span class="exec-skill-more">+{overflow} more</span>'
        groups.append(
            f'<div class="exec-skill-row">\n'
            f'  <span class="exec-skill-label">{escape(cat.category)}</span>\n'
            f'  <span class="exec-skill-items">{items_html}</span>\n'
            f'</div>'
        )
    return "\n      ".join(groups)


def _executive_projects(items: list[ProjectContent]) -> str:
    if not items:
        return '<p>No projects listed.</p>'
    blocks = []
    for item in items:
        title_text, title_full = _truncated_heading(item.title)
        title_attr = f' title="{title_full}"' if title_full else ""
        visible_tech, tech_overflow = cap_list(item.technologies, _TECH_MAX)
        tech = " &middot; ".join(escape(t) for t in visible_tech)
        if tech_overflow:
            tech += f" &middot; +{tech_overflow} more"
        tech_html = f'<p class="exec-project-tech">{tech}</p>' if tech else ""
        code_html = (
            f'<a class="exec-link" href="{escape(item.github_url)}" target="_blank" rel="noopener">View code &rarr;</a>'
            if item.github_url else '<span class="exec-link exec-link-muted">Code unavailable</span>'
        )
        demo_html = (
            f'<a class="exec-link" href="{escape(item.demo_url)}" target="_blank" rel="noopener">Live &rarr;</a>'
            if item.demo_url else '<span class="exec-link exec-link-muted">Demo unavailable</span>'
        )
        blocks.append(
            f'<article class="exec-project">\n'
            f'  <span class="exec-numeral" aria-hidden="true">{item.index:02d}</span>\n'
            f'  <h3{title_attr}>{title_text}</h3>\n'
            f'  <p class="exec-project-problem">{escape(item.problem)}</p>\n'
            f'  {tech_html}\n'
            f'  <blockquote class="exec-outcome">{escape(item.outcome)}</blockquote>\n'
            f'  <div class="exec-project-links">{code_html}{demo_html}</div>\n'
            f'</article>'
        )
    return "\n      ".join(blocks)


def _executive_career(items: list[CareerPathContent]) -> str:
    if not items:
        return '<p>No career paths listed.</p>'
    rows = [
        f'<div class="exec-path">\n'
        f'  <span class="exec-numeral" aria-hidden="true">{item.index:02d}</span>\n'
        f'  <h3>{escape(item.title)}</h3>\n'
        f'</div>'
        for item in items
    ]
    return "\n      ".join(rows)


def _executive_contact(contact: ContactContent) -> str:
    if not contact.has_contact_info:
        return '<p class="exec-contact-empty">No contact information provided.</p>'
    rows = []
    if contact.email:
        rows.append(f'<a class="exec-contact-email" href="mailto:{escape(contact.email)}">{escape(contact.email)}</a>')
    details = []
    if contact.phone:
        details.append(escape(contact.phone))
    if contact.location:
        details.append(escape(contact.location))
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        details.append(f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(contact.linkedin)}</a>')
    detail_html = (
        '<p class="exec-contact-details">' + ' <span class="exec-dot">&middot;</span> '.join(details) + "</p>"
        if details else ""
    )
    return "\n      ".join(rows) + "\n      " + detail_html


# ════════════════════════════════════════════════════════════════════════════
# DEVELOPER DARK — code-editor chrome (file tree, tabs, syntax-style blocks)
# ════════════════════════════════════════════════════════════════════════════


def _developer_hero_extra(hero: HeroContent, contact: ContactContent) -> str:
    return (
        '<div class="terminal-block">'
        '<p><span class="term-prompt">$</span> whoami</p>'
        f'<p class="term-out">{escape(hero.name)}</p>'
        '<p><span class="term-prompt">$</span> cat role.txt</p>'
        f'<p class="term-out">{escape(hero.role)}</p>'
        '<p><span class="term-prompt">$</span> cat mission.txt</p>'
        f'<p class="term-out">{escape(hero.headline)}<span class="term-cursor" aria-hidden="true"></span></p>'
        '</div>'
    )


def _developer_social(contact: ContactContent) -> str:
    lines = []
    if contact.email:
        lines.append(f'<span class="env-key">EMAIL</span>=<a class="env-val" href="mailto:{escape(contact.email)}">{escape(contact.email)}</a>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        lines.append(f'<span class="env-key">LINKEDIN</span>=<a class="env-val" href="{escape(href)}" target="_blank" rel="noopener">{escape(contact.linkedin)}</a>')
    if not lines:
        return ""
    return '<div class="hero-env">' + "<br>".join(lines) + "</div>"


def _developer_skills(categories: list[SkillCategoryContent]) -> str:
    if not categories:
        return '<pre class="code-block">{}</pre>'
    lines = ['<span class="tok-punc">{</span>']
    for i, cat in enumerate(categories):
        key = re.sub(r"[^a-z0-9]+", "_", cat.category.lower()).strip("_")
        visible, overflow = cap_list(cat.items, _SKILL_ITEMS_MAX)
        items_str = ", ".join(f'<span class="tok-string">"{escape(s)}"</span>' for s in visible)
        if overflow:
            items_str += f', <span class="tok-comment">/* +{overflow} more */</span>'
        comma = "," if i < len(categories) - 1 else ""
        lines.append(
            f'  <span class="tok-key">"{escape(key)}"</span><span class="tok-punc">:</span> '
            f'<span class="tok-punc">[</span>{items_str}<span class="tok-punc">]</span>{comma}'
        )
    lines.append('<span class="tok-punc">}</span>')
    return '<pre class="code-block">' + "\n".join(lines) + "</pre>"


def _developer_project_block(item: ProjectContent) -> str:
    short_title = truncate(item.title, _TITLE_MAX_NARROW)
    fn_name = "".join(w.capitalize() for w in slugify(short_title).split("-"))
    fn_name = fn_name[0].lower() + fn_name[1:] if fn_name else "project"
    comment_title = truncate(item.title, _TITLE_MAX)
    comment_problem = truncate(item.problem, 90)
    comment_outcome = truncate(item.outcome, 90)
    visible_tech, tech_overflow = cap_list(item.technologies, _TECH_MAX)
    tech_str = ", ".join(f'<span class="tok-string">"{escape(t)}"</span>' for t in visible_tech)
    if tech_overflow:
        tech_str += f', <span class="tok-comment">/* +{tech_overflow} more */</span>'
    github_line = (
        f'<a class="code-link" href="{escape(item.github_url)}" target="_blank" rel="noopener">$ git clone {escape(item.github_url)}</a>'
        if item.github_url else '<span class="code-link-placeholder">$ git remote add origin &lt;add-your-repo&gt;</span>'
    )
    demo_line = (
        f'<a class="code-link" href="{escape(item.demo_url)}" target="_blank" rel="noopener">$ open {escape(item.demo_url)}</a>'
        if item.demo_url else '<span class="code-link-placeholder">$ open &lt;add-live-demo-url&gt;</span>'
    )
    return (
        f'<div class="code-project">\n'
        f'  <div class="code-tab-bar"><span class="code-tab">{escape(slugify(short_title))}.js</span></div>\n'
        f'  <pre class="code-block code-project-body">'
        f'<span class="tok-line-no">{item.index:02d}</span><span class="tok-comment">// {escape(comment_title)}</span>\n'
        f'<span class="tok-line-no">  </span><span class="tok-key">function</span> <span class="tok-fn">{escape(fn_name)}</span><span class="tok-punc">() {{</span>\n'
        f'<span class="tok-line-no">  </span>  <span class="tok-comment">// problem: {escape(comment_problem)}</span>\n'
        f'<span class="tok-line-no">  </span>  <span class="tok-key">const</span> stack <span class="tok-punc">=</span> <span class="tok-punc">[</span>{tech_str}<span class="tok-punc">]</span><span class="tok-punc">;</span>\n'
        f'<span class="tok-line-no">  </span>  <span class="tok-comment">// result: {escape(comment_outcome)}</span>\n'
        f'<span class="tok-line-no">  </span><span class="tok-punc">}}</span>'
        f'</pre>\n'
        f'  <div class="code-project-links">{github_line}{demo_line}</div>\n'
        f'</div>'
    )


def _developer_projects(items: list[ProjectContent]) -> str:
    if not items:
        return '<p>No projects listed.</p>'
    return "\n      ".join(_developer_project_block(item) for item in items)


def _developer_career(items: list[CareerPathContent]) -> str:
    if not items:
        return '<p>No career paths listed.</p>'
    rows = []
    for item in items:
        commit_hash = fake_hex(item.title + str(item.index))
        rows.append(
            f'<div class="commit-row">\n'
            f'  <span class="commit-dot" aria-hidden="true"></span>\n'
            f'  <span class="commit-hash">{commit_hash}</span>\n'
            f'  <span class="commit-msg">feat: grew into <strong>{escape(item.title)}</strong></span>\n'
            f'</div>'
        )
    return '<div class="commit-log">\n      ' + "\n      ".join(rows) + "\n    </div>"


def _developer_contact(contact: ContactContent) -> str:
    if not contact.has_contact_info:
        return '<pre class="code-block">$ cat contact.sh\n<span class="tok-comment"># no contact information provided</span></pre>'
    lines = ['<span class="term-prompt">$</span> cat contact.sh']
    if contact.email:
        lines.append(f'<span class="tok-key">EMAIL</span><span class="tok-punc">=</span><a class="code-link" href="mailto:{escape(contact.email)}">{escape(contact.email)}</a>')
    if contact.phone:
        lines.append(f'<span class="tok-key">PHONE</span><span class="tok-punc">=</span><span class="tok-string">"{escape(contact.phone)}"</span>')
    if contact.location:
        lines.append(f'<span class="tok-key">LOCATION</span><span class="tok-punc">=</span><span class="tok-string">"{escape(contact.location)}"</span>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        lines.append(f'<span class="tok-key">LINKEDIN</span><span class="tok-punc">=</span><a class="code-link" href="{escape(href)}" target="_blank" rel="noopener">{escape(contact.linkedin)}</a>')
    return '<pre class="code-block">' + "\n".join(lines) + "</pre>"


# ════════════════════════════════════════════════════════════════════════════
# CREATIVE PORTFOLIO — bold editorial collage (agency / designer energy)
# ════════════════════════════════════════════════════════════════════════════


def _creative_hero_extra(hero: HeroContent, contact: ContactContent) -> str:
    return ""


def _creative_social(contact: ContactContent) -> str:
    links = []
    if contact.email:
        links.append(f'<a class="creative-social-btn" href="mailto:{escape(contact.email)}" aria-label="Email">@</a>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        links.append(f'<a class="creative-social-btn" href="{escape(href)}" target="_blank" rel="noopener" aria-label="LinkedIn">in</a>')
    if not links:
        return ""
    return '<div class="creative-social">' + "".join(links) + "</div>"


_TILE_VARIANTS = ["tile-ink", "tile-coral", "tile-outline"]


def _creative_skills(categories: list[SkillCategoryContent]) -> str:
    if not categories:
        return '<span class="skill-tile tile-outline">No skills listed</span>'
    groups = []
    for gi, cat in enumerate(categories):
        rotate = "rotate-l" if gi % 2 == 0 else "rotate-r"
        visible, overflow = cap_list(cat.items, _SKILL_ITEMS_MAX)
        tiles = "".join(
            f'<span class="skill-tile {_TILE_VARIANTS[i % len(_TILE_VARIANTS)]}">{escape(s)}</span>'
            for i, s in enumerate(visible)
        )
        if overflow:
            tiles += f'<span class="skill-tile tile-outline">+{overflow} more</span>'
        groups.append(
            f'<div class="creative-skill-group">\n'
            f'  <span class="creative-skill-label {rotate}">{escape(cat.category)}</span>\n'
            f'  <div class="creative-skill-tiles">{tiles}</div>\n'
            f'</div>'
        )
    return "\n      ".join(groups)


def _creative_projects(items: list[ProjectContent]) -> str:
    if not items:
        return '<p>No projects listed.</p>'
    blocks = []
    for i, item in enumerate(items):
        band = "band-tint" if i % 2 == 1 else ""
        title_text, title_full = _truncated_heading(item.title)
        title_attr = f' title="{title_full}"' if title_full else ""
        visible_tech, tech_overflow = cap_list(item.technologies, _TECH_MAX)
        tech = "".join(
            f'<span class="chip chip-{"coral" if j % 2 == 0 else "teal"}">{escape(t)}</span>'
            for j, t in enumerate(visible_tech)
        )
        if tech_overflow:
            tech += f'<span class="chip chip-outline">+{tech_overflow} more</span>'
        code_html = (
            f'<a class="creative-link" href="{escape(item.github_url)}" target="_blank" rel="noopener">Code &#8599;</a>'
            if item.github_url else '<span class="creative-link creative-link-muted">Add GitHub link</span>'
        )
        demo_html = (
            f'<a class="creative-link" href="{escape(item.demo_url)}" target="_blank" rel="noopener">Live &#8599;</a>'
            if item.demo_url else '<span class="creative-link creative-link-muted">Add live demo</span>'
        )
        blocks.append(
            f'<article class="creative-project {band}">\n'
            f'  <span class="creative-watermark" aria-hidden="true">{item.index:02d}</span>\n'
            f'  <div class="creative-project-inner">\n'
            f'    <h3{title_attr}>{title_text}</h3>\n'
            f'    <p class="creative-problem">{escape(item.problem)}</p>\n'
            f'    <div class="creative-tech">{tech}</div>\n'
            f'    <p class="creative-outcome"><strong>Outcome —</strong> {escape(item.outcome)}</p>\n'
            f'    <div class="creative-project-links">{code_html}{demo_html}</div>\n'
            f'  </div>\n'
            f'</article>'
        )
    return "\n      ".join(blocks)


def _creative_career(items: list[CareerPathContent]) -> str:
    if not items:
        return '<p>No career paths listed.</p>'
    cards = []
    for i, item in enumerate(items):
        rotate = "rotate-l" if i % 2 == 0 else "rotate-r"
        cards.append(
            f'<div class="creative-career-card {rotate}">\n'
            f'  <span class="creative-career-index">{item.index:02d}</span>\n'
            f'  <h3>{escape(item.title)}</h3>\n'
            f'</div>'
        )
    return '<div class="creative-career-row">\n      ' + "\n      ".join(cards) + "\n    </div>"


def _creative_contact(contact: ContactContent) -> str:
    if not contact.has_contact_info:
        return '<p class="creative-contact-empty">No contact information provided.</p>'
    rows = []
    if contact.email:
        rows.append(f'<a class="creative-contact-email" href="mailto:{escape(contact.email)}">{escape(contact.email)}</a>')
    chips = []
    if contact.phone:
        chips.append(escape(contact.phone))
    if contact.location:
        chips.append(escape(contact.location))
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        chips.append(f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(contact.linkedin)}</a>')
    chips_html = (
        '<div class="creative-contact-chips">' + "".join(f'<span class="creative-contact-chip">{c}</span>' for c in chips) + "</div>"
        if chips else ""
    )
    return "\n      ".join(rows) + "\n      " + chips_html


# ════════════════════════════════════════════════════════════════════════════
# MODERN SAAS — landing-page chrome (navbar, hero stats, feature grid, CTA band)
# ════════════════════════════════════════════════════════════════════════════


def _saas_hero_extra(hero: HeroContent, contact: ContactContent) -> str:
    return ""  # stats row is built separately in build_website_schema/render (needs counts)


def _saas_stats_row(skill_count: int, project_count: int, path_count: int) -> str:
    stats = [
        (str(project_count), "Featured Projects"),
        (str(skill_count), "Skill Areas"),
        (str(path_count), "Career Paths"),
    ]
    chips = "".join(
        f'<div class="saas-stat"><span class="saas-stat-num">{n}</span><span class="saas-stat-label">{escape(l)}</span></div>'
        for n, l in stats
    )
    return f'<div class="saas-stats-row">{chips}</div>'


def _saas_social(contact: ContactContent) -> str:
    links = []
    if contact.email:
        links.append(f'<a class="saas-nav-link" href="mailto:{escape(contact.email)}">Email</a>')
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        links.append(f'<a class="saas-nav-link" href="{escape(href)}" target="_blank" rel="noopener">LinkedIn</a>')
    if not links:
        return ""
    return '<div class="saas-nav-social">' + "".join(links) + "</div>"


_FEATURE_ICONS = ["&#9679;", "&#9670;", "&#9651;", "&#9632;", "&#10022;"]


def _saas_skills(categories: list[SkillCategoryContent]) -> str:
    if not categories:
        return '<div class="saas-feature-card"><h3>No skills listed</h3></div>'
    cards = []
    for i, cat in enumerate(categories):
        icon = _FEATURE_ICONS[i % len(_FEATURE_ICONS)]
        visible, overflow = cap_list(cat.items, _SKILL_ITEMS_MAX)
        items_str = ", ".join(escape(s) for s in visible)
        if overflow:
            items_str += f", +{overflow} more"
        cards.append(
            f'<div class="saas-feature-card">\n'
            f'  <span class="saas-feature-icon" aria-hidden="true">{icon}</span>\n'
            f'  <h3>{escape(cat.category)}</h3>\n'
            f'  <p>{items_str}</p>\n'
            f'</div>'
        )
    return '<div class="saas-feature-grid">\n      ' + "\n      ".join(cards) + "\n    </div>"


def _saas_projects(items: list[ProjectContent]) -> str:
    if not items:
        return '<p>No projects listed.</p>'
    rows = []
    for i, item in enumerate(items):
        flip = "saas-case-flip" if i % 2 == 1 else ""
        title_text, title_full = _truncated_heading(item.title)
        title_attr = f' title="{title_full}"' if title_full else ""
        visible_tech, tech_overflow = cap_list(item.technologies, _TECH_MAX)
        tags = "".join(f'<span class="saas-tag">{escape(t)}</span>' for t in visible_tech)
        if tech_overflow:
            tags += f'<span class="saas-tag saas-tag-more">+{tech_overflow} more</span>'
        code_html = (
            f'<a class="saas-case-link" href="{escape(item.github_url)}" target="_blank" rel="noopener">View repository &rarr;</a>'
            if item.github_url else '<span class="saas-case-link saas-case-link-muted">Add a repository link</span>'
        )
        demo_html = (
            f'<a class="saas-case-link" href="{escape(item.demo_url)}" target="_blank" rel="noopener">View live &rarr;</a>'
            if item.demo_url else '<span class="saas-case-link saas-case-link-muted">Add a live demo</span>'
        )
        rows.append(
            f'<div class="saas-case {flip}">\n'
            f'  <div class="saas-case-visual" aria-hidden="true"><span>{item.index:02d}</span></div>\n'
            f'  <div class="saas-case-body">\n'
            f'    <span class="saas-case-kicker">Case Study {item.index:02d}</span>\n'
            f'    <h3{title_attr}>{title_text}</h3>\n'
            f'    <p class="saas-case-problem">{escape(item.problem)}</p>\n'
            f'    <div class="saas-case-tags">{tags}</div>\n'
            f'    <p class="saas-case-outcome"><strong>Outcome:</strong> {escape(item.outcome)}</p>\n'
            f'    <div class="saas-case-links">{code_html}{demo_html}</div>\n'
            f'  </div>\n'
            f'</div>'
        )
    return "\n      ".join(rows)


def _saas_career(items: list[CareerPathContent]) -> str:
    if not items:
        return '<p>No career paths listed.</p>'
    total = len(items)
    steps = []
    for item in items:
        steps.append(
            f'<div class="saas-step">\n'
            f'  <div class="saas-step-circle">{item.index}</div>\n'
            f'  <h3>{escape(item.title)}</h3>\n'
            f'</div>'
        )
        if item.index < total:
            steps.append('<div class="saas-step-arrow" aria-hidden="true">&rarr;</div>')
    return '<div class="saas-steps">\n      ' + "\n      ".join(steps) + "\n    </div>"


def _saas_contact(contact: ContactContent) -> str:
    if not contact.has_contact_info:
        return '<p class="saas-contact-empty">No contact information provided.</p>'
    rows = []
    if contact.email:
        rows.append(f'<a class="saas-cta-button" href="mailto:{escape(contact.email)}">{escape(contact.email)}</a>')
    details = []
    if contact.phone:
        details.append(escape(contact.phone))
    if contact.location:
        details.append(escape(contact.location))
    if contact.linkedin:
        href = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        details.append(f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(contact.linkedin)}</a>')
    detail_html = (
        '<p class="saas-contact-details">' + ' &nbsp;&middot;&nbsp; '.join(details) + "</p>" if details else ""
    )
    return "\n      ".join(rows) + "\n      " + detail_html


# ════════════════════════════════════════════════════════════════════════════
# DISPATCH TABLES — the only place that needs updating to add a 6th theme
# ════════════════════════════════════════════════════════════════════════════

_HERO_EXTRA = {
    T.MINIMAL: _minimal_hero_extra,
    T.EXECUTIVE: _executive_hero_extra,
    T.DEVELOPER: _developer_hero_extra,
    T.CREATIVE: _creative_hero_extra,
    T.SAAS: _saas_hero_extra,
}

_SOCIAL = {
    T.MINIMAL: _minimal_social,
    T.EXECUTIVE: _executive_social,
    T.DEVELOPER: _developer_social,
    T.CREATIVE: _creative_social,
    T.SAAS: _saas_social,
}

_SKILLS = {
    T.MINIMAL: _minimal_skills,
    T.EXECUTIVE: _executive_skills,
    T.DEVELOPER: _developer_skills,
    T.CREATIVE: _creative_skills,
    T.SAAS: _saas_skills,
}

_PROJECTS = {
    T.MINIMAL: _minimal_projects,
    T.EXECUTIVE: _executive_projects,
    T.DEVELOPER: _developer_projects,
    T.CREATIVE: _creative_projects,
    T.SAAS: _saas_projects,
}

_CAREER = {
    T.MINIMAL: _minimal_career,
    T.EXECUTIVE: _executive_career,
    T.DEVELOPER: _developer_career,
    T.CREATIVE: _creative_career,
    T.SAAS: _saas_career,
}

_CONTACT = {
    T.MINIMAL: _minimal_contact,
    T.EXECUTIVE: _executive_contact,
    T.DEVELOPER: _developer_contact,
    T.CREATIVE: _creative_contact,
    T.SAAS: _saas_contact,
}


def render_hero_extra(theme: T, hero: HeroContent, contact: ContactContent) -> str:
    return _HERO_EXTRA[theme](hero, contact)


def render_social(theme: T, contact: ContactContent) -> str:
    return _SOCIAL[theme](contact)


def render_skills(theme: T, categories: list[SkillCategoryContent]) -> str:
    return _SKILLS[theme](categories)


def render_projects(theme: T, items: list[ProjectContent]) -> str:
    return _PROJECTS[theme](items)


def render_career(theme: T, items: list[CareerPathContent]) -> str:
    return _CAREER[theme](items)


def render_contact(theme: T, contact: ContactContent) -> str:
    return _CONTACT[theme](contact)


def render_saas_stats_row(skill_count: int, project_count: int, path_count: int) -> str:
    return _saas_stats_row(skill_count, project_count, path_count)

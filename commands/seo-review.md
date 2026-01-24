---
description: Conduct thorough SEO review using Google Search Console data and Core Web Vitals
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, WebFetch, mcp__gsc-server__*, mcp__pagespeed__*, mcp__google-analytics__*
---

# SEO Review

Conduct a comprehensive SEO review for a website using Google Search Console data, Google Analytics behavioral data, Core Web Vitals analysis, and performance metrics to identify improvements and create an actionable plan.

## Arguments

- `$ARGUMENTS` - The site URL to review (e.g., "nomadkaraoke.com" or "sc-domain:nomadkaraoke.com")

## Overview

This command performs a thorough SEO analysis covering:
1. **Search Performance** - Queries, clicks, impressions, CTR, position trends (GSC)
2. **User Behavior** - Engagement, bounce rate, session duration, conversions (GA)
3. **Core Web Vitals** - LCP, CLS, INP (the metrics Google uses for ranking)
4. **Indexing Status** - Which pages are indexed, crawl issues
5. **Content Opportunities** - Low-hanging fruit for improvement
6. **Technical SEO** - Sitemaps, mobile usability, structured data

## Instructions

### Step 1: Identify the Site

Parse the site URL from arguments. If not provided or ambiguous, list available properties:

```
Use mcp__gsc-server__list_properties to show available sites
```

Format the site_url correctly:
- Domain properties: `sc-domain:example.com`
- URL prefix properties: `https://example.com/`

### Step 2: Gather Search Console Data

Collect comprehensive data from GSC. Run these in sequence:

#### 2a. Performance Overview (Last 28 Days)
```
mcp__gsc-server__get_performance_overview(site_url="...", days=28)
```

#### 2b. Top Queries (What people search for)
```
mcp__gsc-server__get_search_analytics(site_url="...", dimensions="query", days=28)
```

#### 2c. Top Pages (Which pages get traffic)
```
mcp__gsc-server__get_search_analytics(site_url="...", dimensions="page", days=28)
```

#### 2d. Device Breakdown
```
mcp__gsc-server__get_search_analytics(site_url="...", dimensions="device", days=28)
```

#### 2e. Country Breakdown
```
mcp__gsc-server__get_search_analytics(site_url="...", dimensions="country", days=28)
```

#### 2f. Trend Analysis (Compare periods)
```
mcp__gsc-server__compare_search_periods(
  site_url="...",
  period1_start="[28 days ago]",
  period1_end="[14 days ago]",
  period2_start="[14 days ago]",
  period2_end="[today]",
  dimensions="query"
)
```

#### 2g. Sitemap Status
```
mcp__gsc-server__list_sitemaps_enhanced(site_url="...")
```

### Step 3: Google Analytics Data (User Behavior)

GA data shows what happens AFTER users reach your site. This complements GSC's search journey data with engagement and conversion insights.

#### 3a. Identify the GA Property

First, find the matching GA4 property:
```
mcp__google-analytics__get_account_summaries()
```

Match the property to your site. Note the property_id (e.g., "355766149" or "properties/355766149").

#### 3b. Overall Traffic & Engagement (Last 28 Days)

Get a high-level view of site engagement:
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["date"],
  metrics=["sessions", "totalUsers", "newUsers", "engagementRate", "averageSessionDuration", "bounceRate", "screenPageViews"]
)
```

#### 3c. Traffic Sources (Organic vs Other)

Understand how organic search compares to other channels:
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["sessionDefaultChannelGroup"],
  metrics=["sessions", "totalUsers", "engagementRate", "averageSessionDuration", "conversions"]
)
```

#### 3d. Organic Search Landing Pages

See which pages receive organic traffic and how users engage:
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["landingPage"],
  metrics=["sessions", "totalUsers", "engagementRate", "bounceRate", "averageSessionDuration"],
  dimension_filter={"filter": {"field_name": "sessionDefaultChannelGroup", "string_filter": {"match_type": 1, "value": "Organic Search", "case_sensitive": false}}},
  order_bys=[{"metric": {"metric_name": "sessions"}, "desc": true}],
  limit=20
)
```

#### 3e. Device & Geographic Breakdown

Compare with GSC device/country data:
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["deviceCategory"],
  metrics=["sessions", "engagementRate", "bounceRate", "averageSessionDuration"]
)
```

```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["country"],
  metrics=["sessions", "engagementRate", "bounceRate"],
  order_bys=[{"metric": {"metric_name": "sessions"}, "desc": true}],
  limit=10
)
```

#### 3f. Engagement by Page (Content Quality Signals)

Identify pages with poor engagement (potential content issues):
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[{"start_date": "28daysAgo", "end_date": "yesterday"}],
  dimensions=["pagePath"],
  metrics=["screenPageViews", "engagementRate", "bounceRate", "averageSessionDuration"],
  order_bys=[{"metric": {"metric_name": "screenPageViews"}, "desc": true}],
  limit=25
)
```

#### 3g. Trend Comparison (GA)

Compare engagement trends between periods:
```
mcp__google-analytics__run_report(
  property_id="...",
  date_ranges=[
    {"start_date": "28daysAgo", "end_date": "15daysAgo", "name": "Previous"},
    {"start_date": "14daysAgo", "end_date": "yesterday", "name": "Recent"}
  ],
  dimensions=["dateRange"],
  metrics=["sessions", "totalUsers", "engagementRate", "bounceRate", "averageSessionDuration"]
)
```

### Step 4: Core Web Vitals Analysis

**CRITICAL**: Google uses Core Web Vitals as a ranking signal. All three must be "green" for ranking benefit:
- **LCP** (Largest Contentful Paint): < 2.5 seconds
- **CLS** (Cumulative Layout Shift): < 0.1
- **INP** (Interaction to Next Paint): < 200ms

#### 4a. Test Homepage (Mobile - Primary)
```
mcp__pagespeed__run_pagespeed_test(
  url="https://[site]/",
  strategy="mobile",
  category=["performance", "accessibility", "seo", "best-practices"]
)
```

#### 4b. Test Homepage (Desktop)
```
mcp__pagespeed__run_pagespeed_test(
  url="https://[site]/",
  strategy="desktop",
  category=["performance", "accessibility", "seo", "best-practices"]
)
```

#### 4c. Test Top Traffic Pages
For the top 3-5 pages from Step 2c, run PageSpeed tests to identify performance issues on high-value pages.

#### 4d. Test Long-Tail Performance (Important!)
Per the guidance: If URL groupings show poor performance but popular pages are green, test a page with a random query param to get uncached CrUX data:
```
mcp__pagespeed__run_pagespeed_test(
  url="https://[site]/some-page?psi_test=1",
  strategy="mobile",
  category=["performance"]
)
```

### Step 5: Indexing Analysis

Check indexing status for important pages:

#### 5a. Inspect Key Pages
```
mcp__gsc-server__batch_url_inspection(
  site_url="...",
  urls="https://[site]/\nhttps://[site]/page1\nhttps://[site]/page2"
)
```

#### 5b. Check for Indexing Issues
```
mcp__gsc-server__check_indexing_issues(
  site_url="...",
  urls="[top pages from analytics]"
)
```

### Step 6: Identify Opportunities

Analyze the data to find:

#### Quick Wins (High Impact, Low Effort)
- **Position 4-10 queries**: Close to page 1, small improvements could boost significantly
- **High impressions, low CTR**: Title/meta description improvements needed
- **High CTR, low impressions**: Content expansion opportunities

```
mcp__gsc-server__get_advanced_search_analytics(
  site_url="...",
  dimensions="query",
  sort_by="impressions",
  sort_direction="descending",
  row_limit=100
)
```

Filter for:
- Queries with position 4-10 (almost page 1)
- Queries with CTR < 2% but impressions > 100 (title/meta issues)
- Queries with position 1-3 but low impressions (content depth opportunity)

#### Page-Level Analysis
For underperforming pages, get query breakdown:
```
mcp__gsc-server__get_search_by_page_query(
  site_url="...",
  page_url="https://[specific-page]",
  days=28
)
```

#### Content Structure Analysis
Identify if the site needs more focused pages:

1. **Homepage overload** - If homepage ranks for many diverse queries, it's likely trying to do too much. Each distinct topic should have its own page.

2. **Missing landing pages** - High-impression queries without dedicated pages are missed opportunities. These should become focused content.

3. **Thin content** - Pages ranking position 15+ with low engagement often lack depth. Consider expanding with genuine expertise.

Look for patterns like:
- Homepage appearing for queries that deserve dedicated pages
- Multiple unrelated queries hitting the same page
- High impressions but poor position (content not focused enough)

**Recommendation format:**
```
## Content Structure Opportunities

Your homepage currently ranks for X distinct topic clusters. Consider creating:

| New Page | Target Queries | Current Position | Opportunity |
|----------|----------------|------------------|-------------|
| /[topic] | [queries] | #X (on homepage) | Dedicated page |
| /[topic] | [queries] | Not ranking | New content |

Use `/seo-content [topic]` to create each page with your genuine expertise.
```

### Step 7: Generate Report

Create a comprehensive report with this structure:

```markdown
# SEO Review: [site]
**Date:** [today]
**Period:** Last 28 days

## Executive Summary
[2-3 sentence overview of site health and key findings]

## Search Performance (GSC)

| Metric | Value | Trend |
|--------|-------|-------|
| Total Clicks | X | +/- X% |
| Total Impressions | X | +/- X% |
| Average CTR | X% | +/- X% |
| Average Position | X | +/- X |

## User Engagement (GA)

| Metric | Value | Trend |
|--------|-------|-------|
| Sessions | X | +/- X% |
| Users | X | +/- X% |
| Engagement Rate | X% | +/- X% |
| Bounce Rate | X% | +/- X% |
| Avg Session Duration | Xm Xs | +/- X% |

**Traffic Sources:**
| Channel | Sessions | Engagement Rate |
|---------|----------|-----------------|
| Organic Search | X | X% |
| Direct | X | X% |
| Referral | X | X% |
| [Other] | X | X% |

**Organic Search Quality:** [Assessment of organic traffic engagement vs other channels]

## Core Web Vitals Status

**Mobile (Primary):**
| Metric | Value | Status | Target |
|--------|-------|--------|--------|
| LCP | Xs | [status] | < 2.5s |
| CLS | X | [status] | < 0.1 |
| INP | Xms | [status] | < 200ms |

**Desktop:**
[Same table]

**Verdict:** [All green = eligible for ranking boost / Needs work]

## Top Performing Queries
[Table of top 10 queries with clicks, impressions, CTR, position]

## Top Performing Pages
[Table of top 10 pages with metrics]

## Opportunities Identified

### Quick Wins (Do These First)
1. **[Opportunity]** - [Specific action] - Expected impact: [High/Medium]
2. ...

### Content Improvements
1. **[Page/Query]** - [What to improve] - [Why]
2. ...

*Use `/seo-content` to create new pages or expand thin content with your genuine expertise*

### Engagement Issues (from GA)
Pages with high traffic but poor engagement signals:
| Page | Sessions | Bounce Rate | Engagement | Issue |
|------|----------|-------------|------------|-------|
| [page] | X | X% | X% | [diagnosis] |

*High bounce + low engagement often indicates content mismatch with search intent*

### Technical Fixes
1. **[Issue]** - [How to fix] - [Priority]
2. ...

## Indexing Status
- Pages indexed: X
- Pages with issues: X
- [List any specific issues]

## Recommendations by Priority

### P0 - Critical (Fix Immediately)
- [ ] [Action item]

### P1 - Important (This Week)
- [ ] [Action item]

### P2 - Recommended (This Month)
- [ ] [Action item]

### P3 - Nice to Have (Backlog)
- [ ] [Action item]

## Next Steps
1. [First action to take]
2. [Second action]
3. [Third action]
```

### Step 8: Offer Implementation Help

After presenting the report, offer to help implement improvements:

```
## Ready to Implement?

I can help you with:
1. **Content optimization** - Improve titles, meta descriptions, headings
2. **Performance fixes** - Optimize images, reduce JS, improve LCP
3. **Technical SEO** - Fix structured data, improve internal linking
4. **New content** - Use `/seo-content` to create pages targeting opportunity keywords
   - Break up homepage into focused topic pages
   - Create dedicated landing pages for high-impression queries
   - Build out educational content that establishes expertise

Which area would you like to focus on first?
```

## Key Principles (From Expert Guidance)

1. **Core Web Vitals are the priority** - Don't obsess over Lighthouse scores. Focus on LCP < 2.5s, CLS < 0.1, INP < 200ms. All three must be green for Google to use performance as a ranking signal.

2. **Content is king** - Performance only matters as a tiebreaker when content quality is equal. Great performance won't save bad content.

3. **Check CrUX data, not just lab data** - PageSpeed Insights shows both. CrUX (real user data) is what Google uses for ranking.

4. **Long-tail pages matter** - If URL groupings show poor metrics but individual popular pages are green, your long-tail (low-traffic) pages are dragging down the average. These pages often have cache misses and full reloads.

5. **Green is good enough** - Once you're in the green zone, additional performance improvements won't boost rankings (though they may improve user engagement).

6. **GA engagement signals content quality** - While Google doesn't directly use GA data for ranking, engagement metrics reveal content issues:
   - High bounce rate + low session duration → Content doesn't match search intent
   - Good GSC impressions but poor GA engagement → Users find you but don't stay
   - Compare organic vs direct engagement → Organic visitors have different expectations

7. **GSC + GA together tell the full story** - GSC shows how users FIND you (search journey), GA shows what they DO after arriving (user journey). Optimize both.

8. **Multiple focused pages beat one bloated page** - A dedicated page for each topic ranks better than cramming everything into the homepage. Each page should target specific keywords and user intents. Use `/seo-content` to create genuinely valuable pages that reflect your expertise.

## Related Commands

| Command | Purpose |
|---------|---------|
| `/seo-content` | Create high-quality content through interview process |
| `/plan` | Create implementation plan for SEO fixes |
| `/implement` | Execute the plan |
| `/shipit` | Ship changes to production |

## Tips

- Run this review monthly to track progress
- Compare periods to identify trends (improving vs declining)
- Focus on pages that are "almost there" (position 4-10) for quick wins
- Don't chase 100% Lighthouse scores - focus on passing Core Web Vitals
